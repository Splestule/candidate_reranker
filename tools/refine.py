#!/usr/bin/env python3
"""Consensus re-denoising: the composition becomes the decoder's input, not only its output.

Every combiner so far reads what the decoder exported for K candidates it generated
independently. Two things were measured to be missing (paper/SKELETON.md 5b-7): a score that
is comparable across alternatives, and words that no candidate proposed. A masked diffusion
decoder can supply both if it is asked the right question, and the confusion network says
which question: where the candidates disagree, and what everybody agrees on around it.

For each utterance and each contested slot (candidates disagree, or the consensus word is
unsure) the consensus transcript -- ROVER as shipped -- is written back into the decoder's
input with that slot masked, the audio is attended as at decoding, and the decoder reads it:

  refill   the slot (or a run of adjacent contested slots, the gap is segment-shaped) is
           masked at the token lengths its alternatives have and filled by argmax. A word
           no candidate had becomes a new alternative of the slot; stitching the refilled
           groups into the consensus gives new whole candidates ("refined"), conditioned on
           the composition instead of drawn independently of it.
  score    every alternative of the slot, new ones included, is placed in the SAME consensus
           context: lp_self = mean log p of its own tokens with them masked, lp_nb = log p of
           the neighbouring consensus words' tokens with the alternative visible. Epsilon is
           scored by lp_nb alone. Unlike the step-zero acoustic reading (no context) and the
           whole-transcript PLL (each transcript in its own context), alternatives here are
           compared under identical conditions. Stored per slot and word as
           [lp_self mean, lp_nb sum, lp_self sum]; None where not measured.

No training, no reference: the inputs are the candidates and the audio. Output per record is
keyed by the slot index of the network k_curve.build constructs over the same candidates, so
tools/refine_eval.py can attach it to the frozen evaluation pipeline.

    PYTHONPATH=src:Whisfusion/src:tools python3 tools/refine.py --cand results/cand_audio.pkl \\
        --data /tmp/campaign_data --arms anchor-k8 --out results/refine/refine_k8.pkl
"""

from __future__ import annotations

import argparse
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

EPS = ""


def contested(slots, top, n, max_slots, conf_thr):
    """Slots worth re-reading: real disagreement, or a consensus word the candidates are unsure of."""
    out = []
    for i, s in enumerate(slots):
        live = [w for w, v in s.items() if v[0] > 0]
        share = s.get(top[i], [0.0, 0.0])[0] / max(n, 1)
        conf = s[top[i]][1] / max(s[top[i]][0], 1e-9) if top[i] != EPS and top[i] in s else 1.0
        if len(live) >= 2 or (top[i] != EPS and conf < conf_thr):
            out.append((share, conf, i))
    out.sort()
    return sorted(i for _, _, i in out[:max_slots])


def groups(idx, max_run):
    """Maximal runs of adjacent contested slots, split at max_run."""
    gs, cur = [], []
    for i in idx:
        if cur and (i != cur[-1] + 1 or len(cur) >= max_run):
            gs.append(cur)
            cur = []
        cur.append(i)
    if cur:
        gs.append(cur)
    return gs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True, help="cand_audio.pkl (tools/cand_audio.py)")
    ap.add_argument("--data", required=True, help="prep_data output with manifests/")
    ap.add_argument("--arms", default="anchor-k8")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max_slots", type=int, default=10)
    ap.add_argument("--max_alts", type=int, default=4)
    ap.add_argument("--max_run", type=int, default=4)
    ap.add_argument("--conf_thr", type=float, default=0.7)
    ap.add_argument("--seq_len", type=int, default=256)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--limit", type=int, default=0, help="first N records per arm (smoke test)")
    a = ap.parse_args()

    import numpy as np
    import torch
    import compose
    import crf_rover as F
    import data as dataio
    import wf_model
    from audio_slots import acoustic_reading, word_scores
    from campaign.families import Whisfusion
    from scorers import normalize

    arms = [x for x in a.arms.split(",") if x]
    recs = [r for r in pickle.loads(Path(a.cand).read_bytes()) if r["arm"] in arms]
    if a.limit:
        recs = [r for arm in arms for r in [x for x in recs if x["arm"] == arm][:a.limit]]
    out_p = Path(a.out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out = pickle.loads(out_p.read_bytes()) if out_p.exists() else {}
    print(f"{len(recs)} records on arms {arms}, {len(out)} already done", flush=True)

    wf = Whisfusion({}).wf
    tok, model, dev = wf.tokenizer, wf.model, wf.device
    mask_id, pad_id = wf.mask_token_id, wf.pad_token_id
    bos = tok.bos_token_id if tok.bos_token_id is not None else 0
    L = a.seq_len
    wcache = {}

    def wtoks(w):
        if w not in wcache:
            wcache[w] = tok(w.upper(), add_special_tokens=False)["input_ids"] if w else []
        return wcache[w]

    def build(words, mask_len=None, mask_words=()):
        """words: one entry per slot (EPS = absent). mask_len {slot: m} replaces the slot by m
        masks; mask_words masks the slot's own tokens. Returns ids and {slot: (start, end)}."""
        ids, spans = [bos], {}
        for i, w in enumerate(words):
            if mask_len and i in mask_len:
                t = [mask_id] * mask_len[i]
            elif w == EPS:
                continue
            else:
                t = wtoks(w)
                if i in mask_words:
                    t = [mask_id] * len(t)
            spans[i] = (len(ids), len(ids) + len(t))
            ids += t
        if len(ids) > L:
            return None, None
        return ids + [pad_id] * (L - len(ids)), spans

    @torch.no_grad()
    def run(seqs, cond):
        """Log-probs at every position of each sequence, only the rows asked for kept."""
        res = []
        for b in range(0, len(seqs), a.bs):
            chunk = seqs[b:b + a.bs]
            x = torch.tensor([s for s, _ in chunk], device=dev)
            logits = model(idx=x, condition=cond.expand(len(chunk), -1, -1))
            for j, (_, pos) in enumerate(chunk):
                p = torch.tensor(pos, device=dev, dtype=torch.long)
                res.append(torch.log_softmax(logits[j, p].float(), -1).cpu())
            del logits
        return res

    audio = {}
    for s in sorted({r["set"] for r in recs}):
        audio[s] = {u.id: u.audio_path for u in dataio.iter_manifest(str(Path(a.data) / "manifests" / f"{s}.jsonl"))}

    t0, n_done, rt_ok, rt_all = time.time(), 0, 0, 0
    stats = dict(slots=0, contested=0, props=0, refined=0, seqs=0)
    for r in recs:
        key = (r["arm"], r["set"], r["id"])
        if key in out or r["id"] not in audio.get(r["set"], {}):
            continue
        k = int(r["arm"].rsplit("-k", 1)[1])
        ok = [c for c in r["cands"][:k] if c["conf"] is not None]
        if len(ok) < 2:
            continue
        cands = [c["words"] for c in ok]
        bb = compose.central_index(cands)
        slots = compose.confusion_network(cands, bb, [c["conf"] for c in ok], None)
        n = float(len(ok))
        top = [F.rover_pick(s, n, 0.5, 0.7, None) for s in slots]
        cons = [w for w in top if w != EPS]
        if not cons:
            continue
        rt_all += 1
        rt_ok += int(normalize(tok.decode([t for w in cons for t in wtoks(w)])).split() == cons)
        cidx = contested(slots, top, n, a.max_slots, a.conf_thr)
        stats["slots"] += len(slots)
        stats["contested"] += len(cidx)
        cond = wf_model.encode_audio(wf, dataio.load_audio(audio[r["set"]][r["id"]]))

        # ---- pass 1: refill each contested group at the token lengths its readings have
        seqs, meta = [], []
        for g in groups(cidx, a.max_run):
            lens = set()
            for i in g if len(g) == 1 else []:
                lens |= {len(wtoks(w)) for w, v in slots[i].items() if w != EPS and v[0] > 0}
            if len(g) > 1:
                m0 = sum(len(wtoks(top[i])) for i in g)
                lens = {m0, m0 + 1} | ({m0 - 1} if m0 > 1 else set())
            for m in sorted(x for x in lens if x > 0)[:3]:
                words = list(top)
                for i in g[1:]:
                    words[i] = EPS
                ids, spans = build(words, mask_len={g[0]: m})
                if ids is None:
                    continue
                st, en = spans[g[0]]
                seqs.append((ids, list(range(st, en))))
                meta.append((tuple(g), m))
        refills = {}                                    # group -> {m: (words, mean prob)}
        for (g, m), lp in zip(meta, run(seqs, cond)):
            pr, ids = lp.max(-1)
            txt = normalize(tok.decode(ids.tolist(), skip_special_tokens=True)).split()
            refills.setdefault(g, {})[m] = (txt, float(pr.exp().mean()))
        stats["seqs"] += len(seqs)

        props = {}
        for g, by_m in refills.items():
            if len(g) == 1:
                i = g[0]
                for txt, _ in by_m.values():
                    if len(txt) == 1 and txt[0] not in slots[i]:
                        props.setdefault(i, set()).add(txt[0])
        stats["props"] += sum(len(v) for v in props.values())

        # refined whole candidates: every group replaced by its refill at the consensus length
        # (delta 0) or one token longer (delta 1), stitched into the consensus
        refined = []
        for delta in (0, 1):
            words, confs = [], []
            gi = {g[0]: g for g in refills}
            skip = set()
            for i, w in enumerate(top):
                if i in skip:
                    continue
                if i in gi and not (len(gi[i]) == 1 and w == EPS and delta == 0):
                    g = gi[i]
                    skip |= set(g[1:])
                    m0 = sum(len(wtoks(top[j])) for j in g)
                    want = m0 + delta if len(g) > 1 else len(wtoks(top[i])) + delta
                    by_m = refills[g]
                    m = want if want in by_m else min(by_m, key=lambda x: abs(x - want))
                    txt, p = by_m[m]
                    words += txt
                    confs += [p] * len(txt)
                elif w != EPS:
                    words.append(w)
                    confs.append(slots[i][w][1] / max(slots[i][w][0], 1e-9))
            if words and words != cons and all(words != x["words"] for x in refined):
                refined.append(dict(words=words, conf=confs, delta=delta))
        if refined:
            lp0 = acoustic_reading(wf, cond, L)
            for c in refined:
                sc = word_scores(wf, lp0, " ".join(w.upper() for w in c["words"]), 2)
                c["aud"] = [float(np.exp(x)) for x in sc] if sc is not None and len(sc) == len(c["words"]) else None
                c["avg_conf"] = float(np.mean(c["conf"]))
                c["source"] = "refine"
            refined = [c for c in refined if c["aud"] is not None]
        stats["refined"] += len(refined)

        # ---- pass 2: every alternative of every contested slot in the same consensus context
        seqs, meta = [], []
        for i in cidx:
            alts = sorted((w for w, v in slots[i].items() if w != EPS and v[0] > 0),
                          key=lambda w: -slots[i][w][0])[:a.max_alts]
            alts = alts + sorted(props.get(i, ())) + [EPS]
            prv = next((j for j in range(i - 1, -1, -1) if top[j] != EPS), None)
            nxt = next((j for j in range(i + 1, len(top)) if top[j] != EPS), None)
            for w in alts:
                words = list(top)
                words[i] = w
                if w != EPS:
                    ids, spans = build(words, mask_words={i})
                    if ids is not None:
                        st, en = spans[i]
                        seqs.append((ids, list(range(st, en))))
                        meta.append((i, w, "self", wtoks(w)))
                nb = [j for j in (prv, nxt) if j is not None]
                if nb:
                    ids, spans = build(words, mask_words=set(nb))
                    if ids is not None:
                        pos = [p for j in nb for p in range(*spans[j])]
                        seqs.append((ids, pos))
                        meta.append((i, w, "nb", [t for j in nb for t in wtoks(top[j])]))
        feats = {}
        for (i, w, kind, gold), lp in zip(meta, run(seqs, cond)):
            v = lp[torch.arange(len(gold)), torch.tensor(gold)]
            f = feats.setdefault(i, {}).setdefault(w, [None, None, None])
            if kind == "self":
                f[0], f[2] = float(v.mean()), float(v.sum())
            else:
                f[1] = float(v.sum())
        stats["seqs"] += len(seqs)

        out[key] = dict(n_slots=len(slots), contested=cidx, feats=feats,
                        props={i: sorted(v) for i, v in props.items()}, refined=refined)
        n_done += 1
        if n_done % 100 == 0:
            out_p.write_bytes(pickle.dumps(out))
            el = time.time() - t0
            print(f"  {n_done} records, {el / n_done:.2f} s each; per record: "
                  + ", ".join(f"{k_} {v / n_done:.1f}" for k_, v in stats.items())
                  + f"; tokeniser round trip {100 * rt_ok / max(rt_all, 1):.1f}%", flush=True)
    out_p.write_bytes(pickle.dumps(out))
    print(f"done: {n_done} records in {(time.time() - t0) / 60:.1f} min; "
          + ", ".join(f"{k_} {v / max(n_done, 1):.1f}" for k_, v in stats.items())
          + f"; tokeniser round trip {100 * rt_ok / max(rt_all, 1):.1f}%", flush=True)
    return 0 if n_done else 1


if __name__ == "__main__":
    raise SystemExit(main())
