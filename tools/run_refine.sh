#!/usr/bin/env bash
# Consensus re-denoising, zero-shot and trained (Kaggle, GPU T4 x2, internet on). From the repo root:
#
#   bash tools/run_refine.sh /tmp/campaign_data
#
# No new decoding: the candidates are explorer run 2's anchor-k8 and anchor-k4 arms
# (results/cand_audio.pkl, s00 train + s01 test of all 13 sets), so every baseline is the
# explorer runs' own number.
#
# 0. smoke test of every piece on a few utterances; stops the run if anything fails
# 1. two GPU chains in parallel
#      GPU 0: zero-shot refine K=8 -> 3 refiner LoRAs -> refine with them (K=8, then K=4)
#      GPU 1: zero-shot refine K=4 -> 3 plain LoRAs   -> refine with them (K=8, then K=4)
#    One LoRA per fold of the evaluation's set-level CV, trained on shard 0 of the test sets
#    outside the fold and applied only to the fold's sets (the dev sets, never trained on, use
#    fold 0's), so no adapter ever reads an utterance of its own training sets at test time.
# 2. tools/refine_eval.py over the three variants, 3 seeds
#
# Everything is packed into results/refine_all.tar.gz every 10 minutes and after each step;
# refine.py saves every 100 utterances, so a step cut by its time cap still evaluates on what it
# finished. STEPS="2" reruns only the evaluation.
set -uo pipefail
DATA="${1:?usage: bash tools/run_refine.sh <data dir>}"
UP="${UP:-$PWD/Whisfusion}"
STEPS="${STEPS:-0 1 2}"
CAND="${CAND:-results/cand_audio.pkl}"
TRAIN_STEPS="${TRAIN_STEPS:-600}"
DEV="ls-dev-clean ls-dev-other"
TEST="ls-test-clean ls-test-other ami earnings22 voxpopuli gigaspeech spgispeech common_voice ls-tc-babble5 ls-tc-babble0 ls-tc-white5"
R=results/refine
mkdir -p "$R"
log() { echo "[$(date +%H:%M:%S)] $*"; }
want() { case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }
pack() {
  tar czf results/refine_all.tar.gz $(ls "$R"/*.txt "$R"/*.log "$R"/*.pkl "$R"/*.pt 2>/dev/null) 2>/dev/null || true
  log "packed results/refine_all.tar.gz"
}
quiet() { grep --line-buffered -v "Loading weights"; }

[ -f "$CAND" ] || { echo "missing $CAND: is it pushed?"; exit 1; }
if [ ! -d "$UP/src/lit_gpt" ]; then
  git clone -q https://github.com/taeyoun811/Whisfusion.git "$UP"
  git -C "$UP" checkout -q aa9afe3688ccd15ebf096ec9845d67925d1a3aea
fi
python3 -c "import lightning, soundfile, rapidfuzz, sklearn" 2>/dev/null || pip install -q -r requirements-kaggle.txt
python3 -c "import whisper_normalizer" 2>/dev/null || pip install -q whisper-normalizer
export PYTHONPATH="$PWD/src:$UP/src:$PWD/tools"
MISSING=""
for s in $DEV $TEST; do [ -f "$DATA/manifests/$s.jsonl" ] || MISSING="$MISSING $s"; done
[ -z "$MISSING" ] || python3 -m campaign.prep_data --data "$DATA" --only $MISSING

# fold f: the sets refined with adapter f; its adapter trains on the other folds' test sets
FOLD_SETS=(); TRAIN_SETS=()
for f in 0 1 2; do
  FOLD_SETS[$f]=$(python3 -c "import final_compare as F; s=list(F.FOLDS[$f]); print(','.join(s + (['ls-dev-clean','ls-dev-other'] if $f == 0 else [])))")
  TRAIN_SETS[$f]=$(python3 -c "import final_compare as F; print(','.join(x for g, fo in enumerate(F.FOLDS) if g != $f for x in fo))")
done

if want 0; then
  log "step 0: smoke test"
  set -e
  S=$R/smoke
  mkdir -p "$S"
  rm -f "$S"/*.pkl "$S"/*.pt
  python3 -u tools/refine.py --cand "$CAND" --data "$DATA" --arms anchor-k8 --limit 8 \
      --out "$S/zs.pkl" 2>&1 | quiet | tee "$S/zs.log"
  for mode in refine plain; do
    python3 -u tools/train_refiner.py --mode $mode --cand "$CAND" --data "$DATA" --sets ami,earnings22 \
        --steps 10 --bs 8 --out "$S/$mode.pt" 2>&1 | quiet | tee "$S/train_$mode.log"
  done
  python3 -u tools/refine.py --cand "$CAND" --data "$DATA" --arms anchor-k8 --sets ami --limit 4 \
      --lora "$S/refine.pt" --out "$S/lora.pkl" 2>&1 | quiet | tee "$S/lora.log"
  python3 - "$S" <<'PY'
import pickle, re, sys
S = sys.argv[1]
for name, need in (("zs", 4), ("lora", 2)):
    out = pickle.loads(open(f"{S}/{name}.pkl", "rb").read())
    assert len(out) >= need, f"{name}: only {len(out)} records refined"
    rt = float(re.findall(r"round trip ([\d.]+)%", open(f"{S}/{name}.log").read())[-1])
    assert rt >= 90, f"{name}: tokeniser round trip {rt}%: the consensus is not what the decoder reads"
    assert sum(len(v["feats"]) for v in out.values()) > 0, f"{name}: no slot was scored"
    key, rec = next(iter(out.items()))
    print(name, key, "| consensus:", " ".join(rec["consensus"]), "| refined:", " ".join(rec["cons_refined"]),
          "| single refined:", " ".join(rec["single"]["refined"]))
for mode in ("refine", "plain"):
    txt = open(f"{S}/train_{mode}.log").read()
    assert "saved" in txt, f"train {mode} did not save"
    print(mode, re.findall(r"refine examples: .*", txt)[:1], re.findall(r"step 10: .*", txt)[:1])
PY
  set +e
  log "smoke test passed"
  pack
fi

chain() {   # gpu  zero-shot-arm  lora-mode
  local g=$1 arm=$2 mode=$3
  export CUDA_VISIBLE_DEVICES=$g
  log "GPU $g: zero-shot refine $arm"
  timeout 5400 python3 -u tools/refine.py --cand "$CAND" --data "$DATA" --arms "$arm" \
      --out "$R/zs_${arm#anchor-}.pkl" 2>&1 | quiet > "$R/zs_${arm#anchor-}.log"
  for f in 0 1 2; do
    log "GPU $g: train $mode adapter, fold $f (sets ${TRAIN_SETS[$f]})"
    timeout 2100 python3 -u tools/train_refiner.py --mode "$mode" --cand "$CAND" --data "$DATA" \
        --sets "${TRAIN_SETS[$f]}" --steps "$TRAIN_STEPS" --out "$R/${mode}_f$f.pt" 2>&1 | quiet \
        > "$R/train_${mode}_f$f.log"
  done
  for a in anchor-k8 anchor-k4; do
    for f in 0 1 2; do
      [ -f "$R/${mode}_f$f.pt" ] || { log "GPU $g: no $mode adapter for fold $f"; continue; }
      log "GPU $g: refine $a with $mode adapter, fold $f"
      timeout 2400 python3 -u tools/refine.py --cand "$CAND" --data "$DATA" --arms "$a" \
          --sets "${FOLD_SETS[$f]}" --lora "$R/${mode}_f$f.pt" \
          --out "$R/${mode}_${a#anchor-}_f$f.pkl" 2>&1 | quiet > "$R/${mode}_${a#anchor-}_f$f.log"
    done
  done
  log "GPU $g: chain done"
}

if want 1; then
  log "step 1: refining and training on both GPUs"
  chain 0 anchor-k8 refine > "$R/chain0.log" 2>&1 &
  P0=$!
  chain 1 anchor-k4 plain > "$R/chain1.log" 2>&1 &
  P1=$!
  while kill -0 $P0 2>/dev/null || kill -0 $P1 2>/dev/null; do
    sleep 600
    log "GPU 0: $(tail -n 1 "$R/chain0.log")"
    log "GPU 1: $(tail -n 1 "$R/chain1.log")"
    for f in $(ls -t "$R"/*.log | head -4); do echo "   $f: $(tail -n 1 "$f")"; done
    pack
  done
  wait $P0; wait $P1
  cat "$R/chain0.log" "$R/chain1.log"
  for f in "$R"/train_*.log; do echo "== $f"; grep -E "examples|step (0|300|600):|held-out" "$f"; done
  pack
fi

if want 2; then
  log "step 2: evaluation"
  j() { ls $R/$1 2>/dev/null | paste -sd, -; }
  timeout 5400 python3 -u tools/refine_eval.py --cand "$CAND" \
      --refine "zs=$(j 'zs_k*.pkl');refiner=$(j 'refine_k*_f*.pkl');plain=$(j 'plain_k*_f*.pkl')" \
      2>&1 | tee "$R/eval.txt"
  pack
fi
log "done"
