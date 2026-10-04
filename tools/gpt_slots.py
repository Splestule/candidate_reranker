#!/usr/bin/env python3
"""External-LM slot scores for every record of one arm, on the network k_curve.build
constructs, so tools/refine_eval.py --lm can stack them with the decoder's readings.

Same quantity as tools/ext_lm.py -- log p(word | the 12 vote-top words to its left), summed
over the word's tokens -- for any causal LM on the Hub: GPT-2 (124M, the reference from
development) or TinyLlama-1.1B, which shares Whisfusion's tokenizer and is the natural teacher
if a refiner is later distilled from an LM. One output per (LM, arm): the networks differ between
arms.

    PYTHONPATH=src:tools python3 tools/gpt_slots.py --cand results/cand_audio.pkl \\
        --arm anchor-k8 --model gpt2 --out results/refine2/lm_gpt2_anchor-k8.pkl
"""

from __future__ import annotations

import argparse
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "tools")

CTX = 12


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cand", required=True, help="comma separated cand_audio-format pickles")
    ap.add_argument("--arm", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="gpt2")
    ap.add_argument("--bs", type=int, default=128)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import k_curve as KC
    import slot_eval as S

    k = int(a.arm.rsplit("-k", 1)[1])
    recs = [r for p in a.cand.split(",") for r in pickle.loads(Path(p).read_bytes()) if r["arm"] == a.arm]
    if a.limit:
        recs = recs[:a.limit]
    data = [b for b in (KC.build(r, k) for r in recs) if b is not None]
    out_p = Path(a.out)
    out = pickle.loads(out_p.read_bytes()) if out_p.exists() else {}

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(a.model)
    dt = torch.float16 if dev == "cuda" else torch.float32
    try:                                 # transformers 5 renamed torch_dtype to dtype
        lm = AutoModelForCausalLM.from_pretrained(a.model, dtype=dt)
    except TypeError:
        lm = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=dt)
    lm = lm.eval().to(dev)
    body, head = lm.base_model, lm.get_output_embeddings()
    bos = tok.bos_token_id if tok.bos_token_id is not None else tok.eos_token_id
    pad = tok.eos_token_id if tok.eos_token_id is not None else 0
    # SentencePiece tokenisers (TinyLlama) mark the word start themselves; byte-level BPE (GPT-2)
    # needs the leading space
    sp = tok.convert_ids_to_tokens(tok("a", add_special_tokens=False)["input_ids"])[0].startswith("▁")
    wc = {}

    def ids(text):
        if text not in wc:
            wc[text] = tok(text if sp else " " + text, add_special_tokens=False)["input_ids"] if text else []
        return wc[text]

    print(f"{a.arm}: {len(data)} networks, LM {a.model} on {dev} ({'sentencepiece' if sp else 'bpe'}), "
          f"{len(out)} done", flush=True)
    n_params = sum(p.numel() for p in lm.parameters())
    tm = dict(model=a.model, arm=a.arm, params=n_params, device=dev, ms=[], tokens=[], seqs=[])

    def sync():
        if dev == "cuda":
            torch.cuda.synchronize()

    t0, n = time.time(), 0
    for d in data:
        key = (d["set"], d["id"])
        if key in out:
            continue
        tops = [S.top_word(s) for s in d["slots"]]
        seqs, where = [], []
        for i, slot in enumerate(d["slots"]):
            left = " ".join([w for w in tops[:i] if w != S.EPS][-CTX:])
            cids = [bos] + ids(left)
            for w in slot:
                if w == S.EPS:
                    continue
                wids = ids(w)
                if wids:
                    seqs.append((cids, wids))
                    where.append((i, w))
        per = [{} for _ in d["slots"]]
        sync()
        t1 = time.perf_counter()
        for b in range(0, len(seqs), a.bs):
            chunk = seqs[b:b + a.bs]
            L = max(len(c) + len(w) for c, w in chunk)
            x = torch.full((len(chunk), L), pad)
            att = torch.zeros((len(chunk), L), dtype=torch.long)
            for j, (c, w) in enumerate(chunk):
                x[j, :len(c) + len(w)] = torch.tensor(c + w)
                att[j, :len(c) + len(w)] = 1
            with torch.no_grad():
                hid = body(input_ids=x.to(dev), attention_mask=att.to(dev)).last_hidden_state
                for j, (c, w) in enumerate(chunk):
                    pos = torch.arange(len(c) - 1, len(c) + len(w) - 1, device=dev)
                    lp = torch.log_softmax(head(hid[j, pos]).float(), -1)
                    i, word = where[b + j]
                    per[i][word] = float(lp[torch.arange(len(w), device=dev), torch.tensor(w, device=dev)].sum())
        sync()
        tm["ms"].append(1000 * (time.perf_counter() - t1))
        tm["tokens"].append(sum(len(c) + len(w) for c, w in seqs))
        tm["seqs"].append(len(seqs))
        out[key] = per
        n += 1
        if n % 200 == 0:
            out_p.write_bytes(pickle.dumps(out))
            print(f"  {n} scored, {(time.time() - t0) / n:.2f} s each", flush=True)
    out_p.write_bytes(pickle.dumps(out))
    import json
    Path(str(out_p) + ".timing.json").write_text(json.dumps(tm))
    if tm["ms"]:
        ms = sorted(tm["ms"])
        print(f"timing: {n_params / 1e6:.0f}M parameters, {sum(ms) / len(ms):.1f} ms per utterance "
              f"(median {ms[len(ms) // 2]:.1f}), {sum(tm['tokens']) / len(ms):.0f} tokens in "
              f"{sum(tm['seqs']) / len(ms):.1f} sequences per utterance", flush=True)
    print(f"done: {len(out)} scored in {(time.time() - t0) / 60:.1f} min", flush=True)
    return 0 if out else 1


if __name__ == "__main__":
    raise SystemExit(main())
