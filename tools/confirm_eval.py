#!/usr/bin/env python3
"""Confirmation run: the development results, re-measured once on utterances never decoded before.

Everything was developed on shards s00/s01 (the first 400 utterances of every set). This
evaluates on shard s02 (utterances 400-599), with every rule, feature, grid and
hyperparameter frozen before the run. Hypotheses are fixed in docs/confirm_prereg.md and
checked automatically at the end (PASS only if it holds on every seed).

Protocols
  primary   set-level 3-fold CV exactly as in development: train on s00 of the sets outside the
            fold (dev sets always train), test on s02 of the fold's sets
  in-domain train on s00 of all 13 sets, test on s02 of all 11 test sets

Methods per (K, decode): upstream Whisfusion (mean conf), MBR, ROVER tuned, iROVER-style
(boosted stumps, same features), final, candidate oracle; and with GPT-2 as external LM:
upstream + GPT-2 and MBR + GPT-2 (candidate rescoring, weight and length bonus tuned on the
training sets) and final + GPT-2 (slot features, tools/ext_lm.py). Whisper (autoregressive,
tools/whisper_ref.py) is reported on the same utterances when its file is given.

    python3 tools/confirm_eval.py --cand results/cand_audio_confirm.pkl \\
        --whisper results/whisper_small_s02.jsonl | tee results/confirm_eval.txt
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
import random
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

import numpy as np
from rapidfuzz.distance import Levenshtein

import crf_rover as F
import slot_lr as L
import slot_eval as S
import final_compare as FC
import k_curve as KC
import ext_lm as X

UP, MBR, ROV, IRO, FIN = "upstream conf", "MBR", "ROVER tuned", "iROVER-style", "final"
UPL, MBRL, IROL, FINL = "upstream + GPT-2", "MBR + GPT-2", "iROVER-style + GPT-2", "final + GPT-2"
ORA = "candidate oracle"
TEST_SETS = [s for f in FC.FOLDS for s in f]
LM_LAMBDA = (0.0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5)
LM_BONUS = (0.0, 0.25, 0.5, 1.0, 2.0)


def fit_boost_gpt(tr, akey, lm, gpt):
    from sklearn.ensemble import HistGradientBoostingClassifier
    Xs, y = [], []
    for d in tr:
        for words, Xd, g in X.with_gpt(d, akey, lm, gpt):
            if g is None:
                continue
            Xs.append(Xd)
            y += [1 if i == g else 0 for i in range(len(words))]
    clf = HistGradientBoostingClassifier(max_depth=1, max_iter=400, learning_rate=0.1, random_state=0)
    clf.fit(np.concatenate(Xs), np.array(y))
    return clf


def apply_boost_gpt(ev, clf, akey, lm, gpt):
    pre = [X.with_gpt(d, akey, lm, gpt) for d in ev]
    p = clf.predict_proba(np.concatenate([Xd for sl in pre for (_, Xd, _) in sl]))[:, 1]
    out, at = [], 0
    for sl in pre:
        h = []
        for words, Xd, _ in sl:
            h.append(words[int(np.argmax(p[at:at + len(words)]))])
            at += len(words)
        out.append(h)
    return out


def cand_lp(B, model_name, cache_p):
    """GPT-2 log p of every candidate sentence, summed over tokens."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    cache = pickle.loads(cache_p.read_bytes()) if cache_p.exists() else {}
    todo = sorted({" ".join(t) for d in B.values() for t in d["toks"]} - set(cache))
    if todo:
        tok = AutoTokenizer.from_pretrained(model_name)
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        lm = AutoModelForCausalLM.from_pretrained(model_name).eval().to(dev)
        bs = 128 if dev == "cuda" else 32
        for b in range(0, len(todo), bs):
            chunk = todo[b:b + bs]
            seqs = [[tok.bos_token_id] + tok(" " + s)["input_ids"] if s else [tok.bos_token_id]
                    for s in chunk]
            Lm = max(map(len, seqs))
            ids = torch.full((len(seqs), Lm), tok.eos_token_id)
            att = torch.zeros((len(seqs), Lm), dtype=torch.long)
            for j, s in enumerate(seqs):
                ids[j, :len(s)] = torch.tensor(s)
                att[j, :len(s)] = 1
            with torch.no_grad():
                lp = torch.log_softmax(lm(input_ids=ids.to(dev), attention_mask=att.to(dev)).logits.float(), -1)
            for j, s in enumerate(seqs):
                if len(s) < 2:
                    cache[chunk[j]] = 0.0
                    continue
                t = torch.tensor(s[1:], device=lp.device)
                cache[chunk[j]] = float(lp[j, torch.arange(len(s) - 1), t].sum())
            if b // bs % 50 == 0:
                print(f"  candidate LM {b + len(chunk)}/{len(todo)}", flush=True)
        cache_p.write_bytes(pickle.dumps(cache))
    return cache


def pick_lm(d, base, lp, lam, bonus):
    sc = [base[i] + lam * lp[" ".join(t)] + bonus * len(t) for i, t in enumerate(d["toks"])]
    return d["toks"][FC.argmax(sc)]


def tune_lm(tr, basef, lp):
    best = None
    for lam in LM_LAMBDA:
        for bonus in LM_BONUS:
            e = sum(F.edits_of(pick_lm(d, basef(d), lp, lam, bonus), d["ref"]) for d in tr)
            if best is None or e < best[0]:
                best = (e, lam, bonus)
    return best[1], best[2]


def up_base(d):
    return [math.log(max(c, 1e-6)) for c in d["conf"]]


def mbr_base(d):
    return d["mbr"]


def fit_all(tr, akey, seed, a, gpt, lp):
    pool = list(tr)
    random.Random(seed).shuffle(pool)
    n_lm = min(a.lm_utts, len(pool) // 3)
    lm = F.Bigram([d["ref"] for d in pool[:n_lm]])
    tr = pool[n_lm:]
    al, ep, _ = min(((al, e, sum(F.edits_of([F.rover_pick(s, float(d["n_cand"]), al, e, S.POWER)
                                              for s in d["slots"]], d["ref"]) for d in tr))
                     for al in L.GRID_ALPHA for e in L.GRID_EPS), key=lambda t: t[2])
    m = dict(lm=lm, rover=(al, ep), fin=FC.fit_arm(tr, lm, akey, a), boost=KC.fit_boost(tr, lm, akey))
    if gpt is not None:
        m["fin_gpt"] = X.fit(tr, akey, lm, gpt, a)
        m["boost_gpt"] = fit_boost_gpt(tr, akey, lm, gpt)
        m["up_lm"] = tune_lm(tr, up_base, lp)
        m["mbr_lm"] = tune_lm(tr, mbr_base, lp)
    return m


def apply_all(ev, m, akey, gpt, lp):
    lm = m["lm"]
    al, ep = m["rover"]
    bh = KC.apply_boost(ev, m["boost"], akey, lm)
    bg = apply_boost_gpt(ev, m["boost_gpt"], akey, lm, gpt) if gpt is not None else [None] * len(ev)
    out = {}
    for d, hb, hg in zip(ev, bh, bg):
        h = {UP: d["toks"][FC.argmax(d["conf"])], MBR: d["toks"][FC.argmax(d["mbr"])],
             ROV: [F.rover_pick(s, float(d["n_cand"]), al, ep, S.POWER) for s in d["slots"]],
             IRO: hb, FIN: FC.apply_arm(d, m["fin"], akey, lm),
             ORA: min(d["toks"], key=lambda t: Levenshtein.distance(d["ref"], t))}
        if gpt is not None:
            w, mu, sd, _ = m["fin_gpt"]
            h[FINL] = [words[int(np.argmax(((Xs - mu) / sd) @ w))]
                       for words, Xs, _ in X.with_gpt(d, akey, lm, gpt)]
            h[UPL] = pick_lm(d, up_base(d), lp, *m["up_lm"])
            h[MBRL] = pick_lm(d, mbr_base(d), lp, *m["mbr_lm"])
            h[IROL] = hg
        out[(d["set"], d["id"])] = h
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True)
    ap.add_argument("--whisper", default="", help="comma separated whisper_ref.py outputs")
    ap.add_argument("--ks", default="4,8,15")
    ap.add_argument("--gpt_configs", default="all", help="'all' or e.g. 15:flat,8:tree-early")
    ap.add_argument("--gpt_model", default="gpt2")
    ap.add_argument("--test_shard", type=int, default=2)
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--lm_utts", type=int, default=1200)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--lam", type=float, default=1e-4)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--work", default="results/confirm_cache")
    a = ap.parse_args()
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    recs = pickle.loads(Path(a.cand).read_bytes())
    ks = [int(x) for x in a.ks.split(",")]
    decs = ("flat", "tree-early")
    configs = [(k, dec) for k in ks for dec in decs]
    gcfg = configs if a.gpt_configs == "all" else [] if a.gpt_configs == "none" else [
        (int(x.split(":")[0]), x.split(":")[1]) for x in a.gpt_configs.split(",")]
    wn = None
    try:
        from campaign.analysis import WhisperNorm
        wn = WhisperNorm()
        wn = wn if wn.ok else None
    except Exception:
        pass

    # networks per configuration
    B = {}
    for c in configs:
        arm = f"{c[1]}-k{c[0]}" if c[1] == "tree-early" else f"flat-k{c[0]}"
        B[c] = {}
        for r in recs:
            if r["arm"] != arm:
                continue
            b = KC.build(r, c[0])
            if b is None:
                continue
            b.update(shard=r.get("shard"), ref_text=r.get("ref_text", " ".join(r["ref"])),
                     lang=r.get("lang", "en"),
                     sec=(r.get("decode_s") or 0.0) + (r.get("encode_s") or 0.0))
            B[c][(b["set"], b["id"])] = b
    test = set.intersection(*[{kk for kk, d in B[c].items() if d["shard"] == a.test_shard
                               and kk[0] in TEST_SETS} for c in configs])
    train = {c: [d for d in B[c].values() if d["shard"] != a.test_shard] for c in configs}
    print(f"test: {len(test)} utterances (shard s{a.test_shard:02d}) on "
          f"{len({kk[0] for kk in test})} sets, present in every arm; train: "
          + ", ".join(f"K={c[0]} {c[1]} {len(train[c])}" for c in configs), flush=True)
    assert not ({(d['set'], d['id']) for c in configs for d in train[c]} & test), "train/test overlap"

    gpt, lp = {}, {}
    for c in gcfg:
        tag = f"k{c[0]}_{c[1]}"
        gpt[c] = X.score_cache(list(B[c].values()), work / f"gpt2_slots_{tag}.pkl", a.gpt_model)
        lp[c] = cand_lp(B[c], a.gpt_model, work / f"gpt2_cand_{tag}.pkl")
    akey = "aslots_w2"
    seeds = [int(x) for x in a.seeds.split(",")]

    # hyp[protocol][seed][config][key] -> {method: words}
    hyp = {"primary": {}, "in-domain": {}}
    for seed in seeds:
        for proto in hyp:
            hyp[proto][seed] = {}
            for c in configs:
                g, l = gpt.get(c), lp.get(c)
                H = {}
                if proto == "primary":
                    for fold in FC.FOLDS:
                        tr = [d for d in train[c] if d["set"] not in fold]
                        ev = [B[c][kk] for kk in sorted(test) if kk[0] in fold]
                        H.update(apply_all(ev, fit_all(tr, akey, seed, a, g, l), akey, g, l))
                else:
                    ev = [B[c][kk] for kk in sorted(test)]
                    H.update(apply_all(ev, fit_all(train[c], akey, seed, a, g, l), akey, g, l))
                hyp[proto][seed][c] = H
            print(f"seed {seed} {proto}: done", flush=True)

    keys = sorted(test)
    ref = {kk: B[configs[0]][kk]["ref"] for kk in keys}
    rl = np.array([len(ref[kk]) for kk in keys], float)
    refw = {kk: (wn(B[configs[0]][kk]["ref_text"], B[configs[0]][kk]["lang"]) if wn else None) for kk in keys}
    rlw = np.array([len(refw[kk]) for kk in keys], float) if wn else None

    def edits(h_by_key):
        return np.array([F.edits_of(h_by_key[kk], ref[kk]) for kk in keys], float)

    def edits_wn(h_by_key):
        return np.array([Levenshtein.distance(refw[kk], wn(" ".join(w for w in h_by_key[kk] if w != S.EPS),
                                                          B[configs[0]][kk]["lang"])) for kk in keys], float)

    E = {}   # (proto, seed, config, method) -> edits
    for proto in hyp:
        for seed in seeds:
            for c in configs:
                H = hyp[proto][seed][c]
                for m in H[keys[0]]:
                    E[(proto, seed, c, m)] = edits({kk: H[kk][m] for kk in keys})
    sec = {c: float(np.mean([B[c][kk]["sec"] for kk in keys])) for c in configs}
    base_sec = sec[(15, "flat")] if (15, "flat") in sec else sec[configs[0]]

    whisper = {}
    for p in [x for x in a.whisper.split(",") if x and Path(x).exists()]:
        rows = {(r["set"], r["id"]): r for r in map(json.loads, Path(p).read_text().splitlines())}
        if not all(kk in rows for kk in keys):
            print(f"!! {p} misses {sum(kk not in rows for kk in keys)} test utterances, skipped")
            continue
        from scorers import normalize
        name = f"{rows[keys[0]]['model'].split('/')[-1]} (AR, beams {rows[keys[0]]['beams']})"
        hw = {kk: normalize(rows[kk]["hyp"]).split() for kk in keys}
        # Whisper writes cased, punctuated text, so its normalised WER uses the raw output
        ew = (np.array([Levenshtein.distance(refw[kk], wn(rows[kk]["hyp"], B[configs[0]][kk]["lang"]))
                        for kk in keys], float) if wn else None)
        whisper[name] = (edits(hw), ew,
                         float(np.mean([rows[kk]["sec"] for kk in keys])), hw)

    s0 = seeds[0]
    print(f"\n== WER on s{a.test_shard:02d}, primary protocol (set-level CV); mean over seeds "
          f"{a.seeds}, Whisper norm for seed {s0}; s/utt = encoder + decoding on the run's GPU\n")
    print(f"{'K':>3} {'decode':<11}{'method':<20}{'WER':>7}{'sd':>6}{'WER wn':>8}{'s/utt':>7}{'cost':>6}")
    for c in configs:
        for m in hyp["primary"][s0][c][keys[0]]:
            ws = [100 * E[("primary", s, c, m)].sum() / rl.sum() for s in seeds]
            H = hyp["primary"][s0][c]
            w_n = f"{100 * edits_wn({kk: H[kk][m] for kk in keys}).sum() / rlw.sum():8.2f}" if wn else f"{'-':>8}"
            print(f"{c[0]:>3} {c[1]:<11}{m:<20}{np.mean(ws):7.2f}{np.std(ws):6.2f}{w_n}"
                  f"{sec[c]:7.3f}{sec[c] / base_sec:6.2f}")
    for name, (e, ew, s_, _) in whisper.items():
        w_n = f"{100 * ew.sum() / rlw.sum():8.2f}" if wn else f"{'-':>8}"
        print(f"{'':>3} {'AR':<11}{name:<20}{100 * e.sum() / rl.sum():7.2f}{0:6.2f}{w_n}"
              f"{s_:7.3f}{s_ / base_sec:6.2f}")

    print("\n== in-domain protocol (train on s00 of all sets), WER mean over seeds")
    for c in configs:
        row = "  ".join(f"{m} {np.mean([100 * E[('in-domain', s, c, m)].sum() / rl.sum() for s in seeds]):.2f}"
                        for m in hyp["in-domain"][s0][c][keys[0]])
        print(f"K={c[0]:<3}{c[1]:<11}{row}")

    # pre-registered hypotheses, primary protocol, every seed must pass
    def boot(base, arm, seed):
        return S.bootstrap(base, arm, rl, seed=seed)

    results = []

    def check(name, pairs, rule):
        """pairs: list of (label, base_edits_fn(seed), arm_edits_fn(seed)); rule(lo, hi) -> bool."""
        ok_all = True
        lines = []
        for label, bf, af in pairs:
            for s in seeds:
                o, lo, hi = boot(bf(s), af(s), s)
                ok = rule(lo, hi)
                ok_all &= ok
                lines.append(f"    {label:<46} seed {s}: {o:+.2f} [{lo:+.2f}, {hi:+.2f}] {'ok' if ok else 'FAIL'}")
        results.append((name, ok_all))
        print(f"\n{name}: {'PASS' if ok_all else 'FAIL'}")
        print("\n".join(lines))

    def e(c, m):
        return lambda s: E[("primary", s, c, m)]

    print("\n== pre-registered hypotheses (docs/confirm_prereg.md); positive = second better")
    if (8, "tree-early") in configs and (15, "flat") in configs:
        check("H1 final tree-early K=8 beats upstream flat K=15 (CI > 0)",
              [("upstream flat15 -> final tree8", e((15, "flat"), UP), e((8, "tree-early"), FIN))],
              lambda lo, hi: lo > 0)
    check("H2 tree-early non-inferior to flat for final (tree - flat upper CI < 0.5)",
          [(f"K={k} flat -> tree-early", e((k, "tree-early"), FIN), e((k, "flat"), FIN)) for k in ks],
          lambda lo, hi: hi < 0.5)
    check("H3 final beats iROVER-style at K=4 and 8, same decode (CI > 0)",
          [(f"K={k} {dec} iROVER -> final", e((k, dec), IRO), e((k, dec), FIN))
           for k in ks if k in (4, 8) for dec in decs],
          lambda lo, hi: lo > 0)
    check("H4 final beats ROVER tuned everywhere (CI > 0)",
          [(f"K={c[0]} {c[1]} ROVER -> final", e(c, ROV), e(c, FIN)) for c in configs],
          lambda lo, hi: lo > 0)
    if gcfg:
        check("H5 final + GPT-2 beats upstream + GPT-2 and MBR + GPT-2 (CI > 0)",
              [(f"K={c[0]} {c[1]} {b} -> final+GPT-2", e(c, b), e(c, FINL)) for c in gcfg for b in (UPL, MBRL)],
              lambda lo, hi: lo > 0)
        check("H6 GPT-2 adds to final (CI > 0)",
              [(f"K={c[0]} {c[1]} final -> final+GPT-2", e(c, FIN), e(c, FINL)) for c in gcfg],
              lambda lo, hi: lo > 0)
    if gcfg:
        print("\n== not pre-registered: final + GPT-2 against iROVER-style with the same GPT-2 features")
        for c in gcfg:
            for sd in seeds:
                o, lo, hi = boot(E[("primary", sd, c, IROL)], E[("primary", sd, c, FINL)], sd)
                print(f"    K={c[0]} {c[1]:<11} seed {sd}: {o:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    print("\nsummary: " + ", ".join(f"{n.split()[0]} {'PASS' if ok else 'FAIL'}" for n, ok in results))

    # descriptive: per set at the headline configurations, seed s0
    show = [((15, "flat"), UP), ((15, "flat"), MBR), ((8, "tree-early"), IRO), ((8, "tree-early"), FIN)]
    if (8, "tree-early") in gcfg:
        show.append(((8, "tree-early"), FINL))
    show = [(c, m) for c, m in show if c in configs]
    head = "".join(f"{(m if len(m) < 13 else m[:12]) + ' ' + str(c[0]) + c[1][0]:>18}" for c, m in show)
    print(f"\n== per set, primary protocol, seed {s0}\n{'set':<15}{head}" +
          "".join(f"{n[:16]:>18}" for n in whisper))
    for st in TEST_SETS:
        ix = np.array([i for i, kk in enumerate(keys) if kk[0] == st])
        if not len(ix):
            continue
        R = rl[ix].sum()
        row = "".join(f"{100 * E[('primary', s0, c, m)][ix].sum() / R:18.2f}" for c, m in show)
        row += "".join(f"{100 * v[0][ix].sum() / R:18.2f}" for v in whisper.values())
        print(f"{st:<15}{row}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
