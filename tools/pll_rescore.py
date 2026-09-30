#!/usr/bin/env python3
"""Can the decoder score a transcript it did not generate?

Everything we have tried so far reads only what the decoder EXPORTS -- vote counts and
word confidences aggregated into a confusion network. On those, the ceiling is low: a
per-slot model reaches 4-10 % of its headroom, a segment scorer 0.3 %, and a nearest
neighbour estimate of E[edits | features] cannot even match ROVER. Two readings remain, and
they lead to very different projects:

  the information is IN the decoder and the exported confidences throw it away
      -> export better signals; no retraining
  the decoder never had it
      -> the training objective has to change, which is months of GPU

This decides between them, with forward passes only. A masked diffusion decoder can score
ANY target sequence, not just its own samples: mask a random subset of the target's tokens,
run the denoiser, and read off the log-probability it assigns to the tokens it cannot see.
Averaged over masks that is a pseudo-log-likelihood, the same quantity the model was trained
to maximise. So we take a menu of stitched transcripts, ask the model how much it likes each
one, and see whether that ranks them.

If it ranks them, the decoder has the answer and the combination step was reading the wrong
channel -- which is a positive result and cheap to exploit. If it does not, then the signal
that distinguishes the right composition from the wrong one is not in the model at all, and
the retraining argument stops being a hunch.

On Kaggle, leave --dumps out: the candidates are decoded here, so nothing has to be
uploaded and no ids have to line up between two runs.

    PYTHONPATH=src python3 tools/pll_rescore.py \\
        --manifest $DATA/manifests/earnings22.jsonl \\
        --max_utts 150 --menu 128 --masks 8 --batch 24 \\
        --out results/pll_earnings22.json

Off the GPU, --dry builds the menus from existing dumps and prints the ceiling the
likelihood is being asked to reach, and --report re-prints a finished run. Use --dry first:
if the menu oracle is not well below ROVER on that set, the run cannot show anything and
the menu needs widening before any GPU time is spent.

Pick hard sets. On ls-test-clean the menu oracle sits 1.5 WER under ROVER and a positive
result would be hard to see; on earnings22 and ami it is 6 to 8 WER under, which is room
to measure in.
"""

from __future__ import annotations

import argparse
import glob
import gzip
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

import numpy as np
from rapidfuzz.distance import Levenshtein

import compose
import scorers as S
from switch_oracle import slot_matrix

# torch, soundfile and the model live behind the functions that need them: --dry has to run
# on a laptop with none of them installed, so that the menu and the bookkeeping can be
# checked before a GPU hour is spent on them.

EPS = compose.EPS
ROVER = dict(alpha=0.5, eps=0.7)


# --------------------------------------------------------------------------- the menu

def build_menu(row, K, n_rand, rng):
    """Transcripts to rank: every whole candidate, ROVER's output, and random stitchings."""
    cands = [S.normalize(c["text"]).split() for c in row["candidates"]][:K]
    confs = None
    if all("word_conf" in c for c in row["candidates"][:K]):
        confs = [c["word_conf"] for c in row["candidates"][:K]]
    k = len(cands)
    if k < 2:
        return None
    lens = [len(c) for c in cands]
    Lm = [[Levenshtein.distance(cands[i], cands[j]) for j in range(k)] for i in range(k)]
    mbr = [-sum(Lm[i][j] / max(lens[j], 1) for j in range(k) if j != i) / (k - 1)
           for i in range(k)]
    p = int(np.argmax(mbr))
    slots = compose.confusion_network(cands, p, confs, None)
    M, owner = slot_matrix(cands, p, with_map=True)
    T = len(M)

    rover = compose.rover(slots, float(k), ROVER["alpha"], ROVER["eps"])
    picks = compose.rover_slot_picks(slots, float(k), ROVER["alpha"], ROVER["eps"])
    col, seen = [], set()
    for t in range(T):
        o = owner[t]
        col.append(EPS if o in seen else picks[o])
        seen.add(o)
    M = [r + [col[t]] for t, r in enumerate(M)]

    def path(t, i, j):
        return [w for w in ([M[x][i] for x in range(t)] + [M[x][j] for x in range(t, T)])
                if w != EPS]

    menu, tags, texts = [], [], set()
    def add(words, tag):
        s = " ".join(words)
        if s and s not in texts:
            texts.add(s)
            menu.append(words)
            tags.append(tag)
    for c in range(k):
        add(path(0, c, c), "candidate")
    add(rover, "rover")
    for _ in range(n_rand):
        add(path(rng.randrange(T + 1), rng.randrange(k + 1), rng.randrange(k + 1)), "stitch")
    if len(menu) < 3:
        # AMI has utterances where every candidate decodes to nothing; there is no ranking
        # problem there and an empty menu crashes the reporting rather than saying so.
        return None
    return dict(menu=menu, tags=tags, rover=rover, k=k)


# ------------------------------------------------------------------ pseudo-log-likelihood

def to_ids(wf, texts, seq_len, bos, pad):
    import torch

    out = torch.full((len(texts), seq_len), pad, dtype=torch.long)
    lens = []
    for i, t in enumerate(texts):
        ids = wf.tokenizer(t, add_special_tokens=False)["input_ids"][: seq_len - 1]
        out[i, 0] = bos
        out[i, 1: 1 + len(ids)] = torch.tensor(ids, dtype=torch.long)
        lens.append(1 + len(ids))
    return out, lens


def pll(wf, cond, texts, seq_len, masks, ratios, batch, gen):
    """Mean log-probability the model gives the masked tokens of each text.

    The mask positions are shared across texts, so a difference between two rows is a
    difference in the model's opinion and not in which positions happened to be hidden.
    Eight paired patterns are worth more here than fifty independent ones.
    """
    import torch

    bos = wf.tokenizer.bos_token_id
    bos = 0 if bos is None else bos
    pad = wf.pad_token_id
    if pad is None:
        pad = 0
    ids, lens = to_ids(wf, texts, seq_len, bos, pad)
    ids = ids.to(wf.device)
    span = min(max(lens) + 8, seq_len)                  # no point masking a sea of padding
    mask_id = wf.mask_token_id

    total = torch.zeros(len(texts), dtype=torch.float64)
    n_pos = 0
    with torch.no_grad():
        for m in range(masks):
            ratio = ratios[m % len(ratios)]
            r = torch.rand(span, device=wf.device, generator=gen)
            pos = (r < ratio).nonzero(as_tuple=True)[0]
            pos = pos[pos > 0]
            if pos.numel() == 0:
                continue
            n_pos += int(pos.numel())

            if ratio >= 1.0:
                # Everything is masked, so the input does not depend on the text being
                # scored: ONE forward gives the distribution for every candidate at once.
                # It is also the only setting with no context leak -- at ratio < 1 the
                # unmasked half of a short transcript is mostly padding, which tells the
                # model "this sequence is short" without the audio having any say, and short
                # transcripts then win on padding alone. Cheap and clean; the price is that
                # it scores each position independently.
                probe = torch.full((1, seq_len), mask_id, dtype=torch.long, device=wf.device)
                probe[0, 0] = bos
                logits = wf.model(idx=probe, condition=cond)
                lp = torch.log_softmax(logits[0, pos, :].float(), dim=-1)
                tgt = ids[:, pos].clamp(max=lp.size(-1) - 1)          # (n_texts, n_pos)
                cols = torch.arange(pos.numel(), device=lp.device)[None, :]
                total += lp[cols, tgt].sum(1).double().cpu()             # lp is (n_pos, vocab)
                continue

            for st in range(0, len(texts), batch):
                chunk = ids[st: st + batch]
                masked = chunk.clone()
                masked[:, pos] = mask_id
                logits = wf.model(idx=masked, condition=cond.expand(len(chunk), -1, -1))
                lp = torch.log_softmax(logits[:, pos, :].float(), dim=-1)
                tgt = chunk[:, pos].clamp(max=lp.size(-1) - 1)
                total[st: st + batch] += (lp.gather(-1, tgt.unsqueeze(-1)).squeeze(-1)
                                          .sum(1).double().cpu())
    if n_pos == 0:
        return None
    return (total / n_pos).numpy()


def spearman(a, b):
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    ra -= ra.mean(); rb -= rb.mean()
    d = float(np.sqrt((ra * ra).sum() * (rb * rb).sum()))
    return float((ra * rb).sum() / d) if d > 0 else 0.0


def report(out) -> int:
    """Sanity checks first, then the numbers. Nothing here needs a GPU."""
    R = sum(r["n_ref"] for r in out)
    better = sum(1 for r in out if r["pll_ref"] >= max(r["pll"]))
    spread = float(np.mean([max(r["pll"]) - min(r["pll"]) for r in out]))
    print(f"SANITY  the true reference outscores every menu entry on "
          f"{100.0 * better / len(out):.0f}% of utterances")
    print(f"SANITY  mean PLL spread inside an utterance {spread:.4f}")
    if spread < 1e-4:
        print("  !! the scores are flat: the mask never covered real tokens, or the model")
        print("  !! ignores the target. Nothing below means anything.")
        return 1
    if better < 0.5 * len(out):
        print("  !! the model does NOT prefer the reference to its own guesses. Read what")
        print("  !! follows as a property of this estimator, not of the decoder.")

    rov = 100.0 * sum(r["rover_e"] for r in out) / R
    orac = 100.0 * sum(min(r["edits"]) for r in out) / R
    cand = 100.0 * sum(min(e for e, t in zip(r["edits"], r["tags"]) if t == "candidate")
                       for r in out) / R
    pick = 100.0 * sum(r["edits"][int(np.argmax(r["pll"]))] for r in out) / R
    rho = float(np.mean([spearman(-np.asarray(r["pll"]), np.asarray(r["edits"]))
                         for r in out]))

    print(f"\n{'on these utterances':<42}{'WER':>8}")
    print(f"  {'ROVER as shipped':<40}{rov:>8.2f}")
    print(f"  {'best whole candidate (oracle)':<40}{cand:>8.2f}")
    print(f"  {'model likelihood picks from the menu':<40}{pick:>8.2f}")
    print(f"  {'oracle over the same menu':<40}{orac:>8.2f}")
    print(f"\n  mean within-utterance Spearman(PLL, -edits)  {rho:+.3f}")
    print(f"  share of the menu's gap recovered             "
          f"{100.0 * (rov - pick) / max(rov - orac, 1e-9):.1f}%")
    print("\n  Spearman near zero means the decoder cannot tell its own better readings from")
    print("  its worse ones, and no amount of exporting fixes that: the training objective")
    print("  is then the thing to change. Clearly positive means the signal was there all")
    print("  along and the confusion network was throwing it away.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="", help="prepared <set>.jsonl with audio paths")
    ap.add_argument("--dumps", default="",
                    help="directory holding <arm>.jsonl.gz. Leave it out and the candidates "
                         "are decoded fresh from the manifest, which is what Kaggle wants: "
                         "no dump upload, no id matching between two runs.")
    ap.add_argument("--arm", default="main")
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--max_utts", type=int, default=200)
    ap.add_argument("--menu", type=int, default=32,
                    help="random stitchings on top of the whole candidates")
    ap.add_argument("--masks", type=int, default=8)
    ap.add_argument("--ratios", default="1.0",
                    help="mask ratios, cycled over --masks patterns. 1.0 masks everything, "
                         "which costs one forward pass for the whole menu and is the only "
                         "setting where a short transcript cannot win on padding alone; "
                         "anything below 1.0 is the full ELBO and costs a pass per batch.")
    ap.add_argument("--batch", type=int, default=24)
    ap.add_argument("--seq_len", type=int, default=256)
    ap.add_argument("--steps", type=int, default=4, help="PDD steps when decoding fresh")
    ap.add_argument("--decode_seed", type=int, default=1234)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dry", action="store_true",
                    help="build the menus and print their statistics; no model, no GPU")
    ap.add_argument("--report", default="", help="re-print the report from a saved json")
    ap.add_argument("--out", default="results/pll_rescore.json")
    a = ap.parse_args()

    if a.report:
        return report(json.loads(Path(a.report).read_text()))

    rows = {}
    if a.dumps:
        for f in sorted(glob.glob(f"{a.dumps}/{a.arm}.jsonl.gz")):
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                for line in fh:
                    d = json.loads(line)
                    rows[d["id"]] = d
        if not rows:
            print(f"no {a.arm}.jsonl.gz under {a.dumps}")
            return 2
        print(f"{len(rows)} dumped utterances", flush=True)
    elif a.dry:
        print("--dry needs --dumps: there is nothing to build a menu from otherwise")
        return 2
    rng = random.Random(a.seed)

    if a.dry:
        sizes, gaps, rov_e, tot_R, skipped = [], [], 0, 0, 0
        for i, (uid, row) in enumerate(sorted(rows.items())):
            if i >= a.max_utts:
                break
            m = build_menu(row, a.k, a.menu, rng)
            ref = S.normalize(row["reference"]).split()
            if m is None or not ref:
                skipped += 1
                continue
            e = [Levenshtein.distance(ref, w) for w in m["menu"]]
            sizes.append(len(m["menu"]))
            rov_e += Levenshtein.distance(ref, m["rover"])
            gaps.append(min(e))
            tot_R += len(ref)
        if not sizes:
            print("every utterance was skipped: no candidates carry text")
            return 2
        print(f"\n{len(sizes)} menus, {np.mean(sizes):.1f} distinct transcripts each"
              + (f", {skipped} utterances skipped (no usable candidates)" if skipped else ""))
        print(f"  ROVER on these utterances        {100.0 * rov_e / tot_R:>7.2f}")
        print(f"  oracle over the menus            {100.0 * sum(gaps) / tot_R:>7.2f}")
        print("\nThat second number is the ceiling the likelihood is being asked to reach.")
        print("If it is not well below ROVER, widen the menu before spending GPU on it.")
        return 0

    if not a.manifest:
        print("--manifest is required unless --dry or --report")
        return 2
    if not Path(a.manifest).exists():
        print(f"no manifest at {a.manifest!r}. $DATA is set on Kaggle by the prepare notebook;")
        print("locally, build one with: python -m campaign.prep_data --data data --only earnings22")
        return 2
    import importlib.util
    # find_spec, not import: lit_gpt must not be imported before wf_compat installs its shims
    missing = [m for m in ("torch", "soundfile", "transformers", "lit_gpt")
               if importlib.util.find_spec(m) is None]
    if missing:
        print(f"missing: {', '.join(missing)}. This step runs the model, so it needs what the")
        print("Kaggle notebooks have: torch, requirements-kaggle.txt, and the upstream Whisfusion")
        print("checkout on PYTHONPATH (bash setup.sh clones it and fetches the checkpoints):")
        print("    PYTHONPATH=src:Whisfusion/src python3 tools/pll_rescore.py ...")
        print("--dry and --report need none of that.")
        return 2
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)

    import torch

    import data as dataio
    import wf_model
    from campaign.families import Whisfusion

    wf = Whisfusion({}).wf
    gen = torch.Generator(device=wf.device)
    gen.manual_seed(a.seed)
    ratios = [float(x) for x in a.ratios.split(",") if x.strip()]

    import decode as dec

    out, t0, seen = [], time.time(), 0
    for u in dataio.iter_manifest(a.manifest):
        if len(out) >= a.max_utts:
            break
        seen += 1
        row = rows.get(u.id)
        if rows and row is None:
            continue                          # before encoding: a manifest can be 5x the dump
        audio = dataio.load_audio(u.audio_path)
        cond = wf_model.encode_audio(wf, audio)
        if row is None:                       # decode the candidates here, same settings
            r = dec.pdd_decode(wf, cond, n_candidates=a.k, n_steps=a.steps,
                               seed=a.decode_seed)
            row = dict(id=u.id, reference=u.text,
                       candidates=[dec.candidate_to_dict(c) for c in r.candidates])
        m = build_menu(row, a.k, a.menu, rng)
        ref = S.normalize(row["reference"]).split()
        if m is None or not ref or len(m["menu"]) < 3:
            continue
        texts = [" ".join(w) for w in m["menu"]] + [" ".join(ref)]
        sc = pll(wf, cond, texts, a.seq_len, a.masks, ratios, a.batch, gen)
        if sc is None:
            continue
        out.append(dict(id=u.id, n_ref=len(ref), pll=sc[:-1].tolist(),
                        pll_ref=float(sc[-1]), tags=m["tags"],
                        # stored so pll_combine never has to rebuild the menu -- on Kaggle the
                        # candidates are decoded here and no dump exists to rebuild it from
                        menu=texts[:-1], rover=" ".join(m["rover"]),
                        cands=[" ".join(S.normalize(c["text"]).split())
                               for c in row["candidates"][:a.k]],
                        edits=[Levenshtein.distance(ref, w) for w in m["menu"]],
                        rover_e=Levenshtein.distance(ref, m["rover"])))
        if len(out) % 20 == 0:
            print(f"  {len(out)} utterances, {(time.time() - t0) / len(out):.1f} s each",
                  flush=True)
    if not out:
        print(f"nothing scored out of {seen} utterances read from the manifest"
              + (" -- the manifest ids do not match the dump ids" if rows else ""))
        return 2
    Path(a.out).write_text(json.dumps(out))
    print(f"\n{len(out)} utterances scored -> {a.out}\n", flush=True)
    return report(out)


if __name__ == "__main__":
    raise SystemExit(main())
