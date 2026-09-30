#!/usr/bin/env python3
"""Does an external language model add to the final pipeline?

The neighbour bigram is estimated from ~1200 held-out references, i.e. a tiny LM, and it is
still the second-largest gain in the pipeline. The obvious next step is a real LM. This scores
every word of every slot with GPT-2 (124M, never saw our references) given the left context
of the network's vote-top words (last 12), and adds two columns to the final pipeline's features:
log p(word | left context), summed over its tokens, and the same minus the slot's best word.
Epsilon gets zeros (the model already has an epsilon indicator).

Same set-level cross-validation and seeds as tools/final_compare.py.

    python3 tools/ext_lm.py --cache results/audio_cache.pkl --out results/gpt2_slots.pkl
"""

from __future__ import annotations

import argparse
import pickle
import random
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

import numpy as np

import crf_rover as F
import slot_lr as L
import slot_eval as S
import final_compare as FC


CTX = 12     # words of left context; enough for a word-level LM feature, keeps CPU cost sane


def score_cache(data, out_p, model_name):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_name)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    lm = AutoModelForCausalLM.from_pretrained(model_name).eval().to(dev)
    out = pickle.loads(out_p.read_bytes()) if out_p.exists() else {}
    for n, d in enumerate(data):
        key = (d["set"], d["id"])
        if key in out:
            continue
        tops = [S.top_word(s) for s in d["slots"]]
        seqs, where = [], []
        for i, slot in enumerate(d["slots"]):
            left = " ".join([w for w in tops[:i] if w != S.EPS][-CTX:])
            ctx = tok.bos_token + (" " + left if left else "")
            cids = tok(ctx)["input_ids"]
            for w in slot:
                if w == S.EPS:
                    continue
                wids = tok(" " + w)["input_ids"]
                seqs.append((cids, wids))
                where.append((i, w))
        scores = {}
        B = 256 if dev == "cuda" else 64
        for b in range(0, len(seqs), B):
            chunk = seqs[b:b + B]
            L_ = max(len(c) + len(w) for c, w in chunk)
            ids = torch.full((len(chunk), L_), tok.eos_token_id)
            att = torch.zeros((len(chunk), L_), dtype=torch.long)
            for j, (c, w) in enumerate(chunk):
                s = c + w
                ids[j, :len(s)] = torch.tensor(s)
                att[j, :len(s)] = 1
            with torch.no_grad():
                hid = lm.transformer(input_ids=ids.to(dev), attention_mask=att.to(dev)).last_hidden_state
                for j, (c, w) in enumerate(chunk):
                    pos = torch.arange(len(c) - 1, len(c) + len(w) - 1)
                    lp = torch.log_softmax(lm.lm_head(hid[j, pos]).float(), -1)
                    scores[where[b + j]] = float(lp[torch.arange(len(w)), torch.tensor(w, device=dev)].sum())
        per = [{} for _ in d["slots"]]
        for (i, w), v in scores.items():
            per[i][w] = v
        out[key] = per
        if n % 100 == 0:
            out_p.write_bytes(pickle.dumps(out))
            print(f"  {len(out)} scored", flush=True)
    out_p.write_bytes(pickle.dumps(out))
    return out


def with_gpt(d, akey, lm, gpt):
    rows = []
    for (words, X, g), gs in zip(S.prepare(d, akey, lm), gpt[(d["set"], d["id"])]):
        v = np.array([gs.get(w, 0.0) if w != S.EPS else 0.0 for w in words])
        real = np.array([w != S.EPS for w in words])
        rel = (v - (v[real].max() if real.any() else 0.0)) * real
        rows.append((words, np.hstack([X, np.stack([v, rel], 1)]), g))
    return rows


def fit(tr, akey, lm, gpt, a):
    pre = [with_gpt(d, akey, lm, gpt) for d in tr]
    Xs = [X for sl in pre for (_, X, g) in sl if g is not None]
    gs = [g for sl in pre for (_, _, g) in sl if g is not None]
    A = np.concatenate(Xs)
    mu, sd = A.mean(0), A.std(0) + 1e-9
    w, loss = L.fit([(X - mu) / sd for X in Xs], gs, a.lam, a.iters, a.lr)
    return w, mu, sd, loss


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="gpt2")
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--lm_utts", type=int, default=1200)
    ap.add_argument("--iters", type=int, default=800)
    ap.add_argument("--lam", type=float, default=1e-4)
    ap.add_argument("--lr", type=float, default=0.05)
    a = ap.parse_args()
    data = pickle.loads(Path(a.cache).read_bytes())
    gpt = score_cache(data, Path(a.out), a.model)
    akey = "aslots_w2"
    test = [d for d in data if any(d["set"] in f for f in FC.FOLDS)]
    rl = np.array([len(d["ref"]) for d in test], float)
    R = rl.sum()
    print(f"\n{len(test)} scored utterances, {a.model} as external LM\n")
    for seed in [int(x) for x in a.seeds.split(",")]:
        hy = {}
        for fold in FC.FOLDS:
            ev = [d for d in data if d["set"] in fold]
            pool = [d for d in data if d["set"] not in fold]
            random.Random(seed).shuffle(pool)
            n_lm = min(a.lm_utts, len(pool) // 3)
            bg = F.Bigram([d["ref"] for d in pool[:n_lm]])
            tr = pool[n_lm:]
            m_fin = FC.fit_arm(tr, bg, akey, a)
            m_gpt = fit(tr, akey, bg, gpt, a)
            m_gpt_only = fit(tr, akey, None, gpt, a)
            for d in ev:
                h = {"final": FC.apply_arm(d, m_fin, akey, bg)}
                for name, (w, mu, sd, _), lmx in (("final + GPT-2", m_gpt, bg),
                                                   ("acoustic + GPT-2, no bigram", m_gpt_only, None)):
                    h[name] = [words[int(np.argmax(((X - mu) / sd) @ w))]
                               for words, X, _ in with_gpt(d, akey, lmx, gpt)]
                hy[(d["set"], d["id"])] = h
        E = {m: np.array([F.edits_of(hy[(d["set"], d["id"])][m], d["ref"]) for d in test], float)
             for m in hy[(test[0]["set"], test[0]["id"])]}
        line = f"seed {seed}: " + "   ".join(f"{m} {100 * e.sum() / R:.2f}" for m, e in E.items())
        o, lo, hi = S.bootstrap(E["final"], E["final + GPT-2"], rl, seed=seed)
        print(line + f"\n   final + GPT-2 vs final: {o:+.2f} [{lo:+.2f}, {hi:+.2f}]", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
