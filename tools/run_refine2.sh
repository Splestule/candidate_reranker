#!/usr/bin/env bash
# Refine run 2 (Kaggle, GPU T4 x2, internet on): cheap consensus scoring, the single-hypothesis
# ablation, the trained refiner against its plain control, in-loop composition on tree-early
# decoding, and GPT-2 stacked on top. From the repo root:
#
#   bash tools/run_refine2.sh /tmp/campaign_data
#
# Nothing from run 1 is recomputed: its full scoring (about 60 decoder passes per utterance)
# gave final +score 24.01 / 25.18 at K=8 / K=4 on these candidates, folds and seeds, and the
# evaluation is deterministic, so those numbers stand as the reference.
#
# Decoder passes per utterance (one pass = one 256-token row through the decoder):
#   anchor-k8 flat decode 32, tree-k8 19, loop-k8 11 (+1 for the joint consensus pass)
#   scoring: joint 1, slot ~7 (one per contested slot)
#
# 0. smoke test of every piece on a few utterances; stops the run if anything fails
# 1. two GPU chains in parallel
#      GPU 0: tree-early decode with a snapshot (tree-k8, loop-k8) -> joint + slot scoring of
#             both -> 3 refiner adapters -> slot scoring with them (anchor-k8/k4, loop-k8)
#      GPU 1: joint, slot and single-context slot scoring of anchor-k8/k4 -> 3 plain adapters
#             -> slot scoring with them
#    One adapter per fold of the evaluation's set-level CV, trained on shard 0 of the other folds'
#    test sets and applied only to its own fold's sets.
# 2. external-LM slot scores for the four arms: GPT-2 (124M) and TinyLlama-1.1B (Whisfusion's
#    tokenizer, the teacher if a refiner is distilled from an LM later)
# 3. tools/refine_eval.py, 3 seeds
#
# Packed into results/refine2_all.tar.gz every 10 minutes and after each step.
set -uo pipefail
DATA="${1:?usage: bash tools/run_refine2.sh <data dir>}"
UP="${UP:-$PWD/Whisfusion}"
STEPS="${STEPS:-0 1 2 3}"
CAND="${CAND:-results/cand_audio.pkl}"
TRAIN_STEPS="${TRAIN_STEPS:-600}"
POLL="${POLL:-600}"
TINY="${TINY:-TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T}"
DEV="ls-dev-clean ls-dev-other"
TEST="ls-test-clean ls-test-other ami earnings22 voxpopuli gigaspeech spgispeech common_voice ls-tc-babble5 ls-tc-babble0 ls-tc-white5"
R=results/refine2
LOOP=$R/loop_cand.pkl
mkdir -p "$R"
log() { echo "[$(date +%H:%M:%S)] $*"; }
want() { case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }
pack() {
  tar czf results/refine2_all.tar.gz $(ls "$R"/*.txt "$R"/*.log "$R"/*.pkl "$R"/*.pt 2>/dev/null) 2>/dev/null || true
  log "packed results/refine2_all.tar.gz"
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

FOLD_SETS=(); TRAIN_SETS=()
for f in 0 1 2; do
  FOLD_SETS[$f]=$(python3 -c "import final_compare as F; s=list(F.FOLDS[$f]); print(','.join(s + (['ls-dev-clean','ls-dev-other'] if $f == 0 else [])))")
  TRAIN_SETS[$f]=$(python3 -c "import final_compare as F; print(','.join(x for g, fo in enumerate(F.FOLDS) if g != $f for x in fo))")
done

refine() {   # name cand arms mode context [extra args]
  local name=$1 cand=$2 arms=$3 mode=$4 ctx=$5
  shift 5
  timeout 3600 python3 -u tools/refine.py --cand "$cand" --data "$DATA" --arms "$arms" --mode "$mode" \
      --context "$ctx" --out "$R/$name.pkl" "$@" 2>&1 | quiet > "$R/$name.log"
}

if want 0; then
  log "step 0: smoke test"
  set -e
  S=$R/smoke
  mkdir -p "$S"
  rm -f "$S"/*.pkl "$S"/*.pt
  python3 -u tools/loop_decode.py --like "$CAND" --data "$DATA" --limit 4 --out "$S/loop.pkl" 2>&1 | quiet
  for spec in "joint consensus" "slot consensus" "slot single"; do
    set -- $spec
    python3 -u tools/refine.py --cand "$CAND" --data "$DATA" --arms anchor-k8 --limit 6 --mode $1 \
        --context $2 --out "$S/$1_$2.pkl" 2>&1 | quiet | tail -n 1
  done
  python3 -u tools/refine.py --cand "$S/loop.pkl" --data "$DATA" --arms loop-k8,tree-k8 --mode joint \
      --out "$S/loop_joint.pkl" 2>&1 | quiet | tail -n 1
  python3 -u tools/train_refiner.py --mode refine --cand "$CAND" --data "$DATA" --sets ami,earnings22 \
      --steps 10 --bs 8 --out "$S/refine.pt" 2>&1 | quiet | tail -n 2
  python3 -u tools/refine.py --cand "$CAND" --data "$DATA" --arms anchor-k8 --sets ami --limit 4 --mode slot \
      --lora "$S/refine.pt" --out "$S/lora.pkl" 2>&1 | quiet | tail -n 1
  for m in gpt2 "$TINY"; do
    python3 -u tools/gpt_slots.py --cand "$CAND" --arm anchor-k8 --model "$m" --limit 5 \
        --out "$S/lm_$(basename $m).pkl" 2>&1 | grep -v Warning | tail -n 1
  done
  python3 - "$S" <<'PY'
import pickle, sys
S = sys.argv[1]
loop = pickle.loads(open(f"{S}/loop.pkl", "rb").read())
arms = sorted({r["arm"] for r in loop})
assert arms == ["loop-k8", "tree-k8"] and len(loop) >= 6, f"loop_decode: {len(loop)} records, arms {arms}"
for r in loop[:2]:
    ok = [c for c in r["cands"] if c["conf"] is not None]
    print(r["arm"], r["id"], f"{len(ok)}/{len(r['cands'])} usable;", " ".join(r["cands"][0]["words"]), "| ref:", " ".join(r["ref"]))
    assert len(ok) >= 2, "loop_decode candidates without confidences"
for m in ("gpt2", "TinyLlama-1.1B-intermediate-step-1431k-3T"):
    out = pickle.loads(open(f"{S}/lm_{m}.pkl", "rb").read())
    k, v = next(iter(out.items()))
    assert len(out) >= 3 and any(v), f"LM {m}: {len(out)} scored"
    print("LM", m, k[1], v[:2])
for name, need in (("joint_consensus", 4), ("slot_consensus", 4), ("slot_single", 4), ("loop_joint", 6), ("lora", 2)):
    out = pickle.loads(open(f"{S}/{name}.pkl", "rb").read())
    n_feat = sum(len(v["feats"]) for v in out.values())
    assert len(out) >= need and n_feat > 0, f"{name}: {len(out)} records, {n_feat} scored slots"
    k, v = next(iter((k, v) for k, v in out.items() if v["feats"]))
    i = next(iter(v["feats"]))
    print(name, len(out), "records;", k[1], "slot", i, {w: round(x[0], 2) for w, x in v["feats"][i].items()})
PY
  set +e
  log "smoke test passed"
  pack
fi

chain0() {
  export CUDA_VISIBLE_DEVICES=0
  log "GPU 0: tree-early decode with snapshot"
  timeout 5400 python3 -u tools/loop_decode.py --like "$CAND" --data "$DATA" --out "$LOOP" 2>&1 | quiet > "$R/loop_decode.log"
  log "GPU 0: joint and slot scoring of tree-k8 / loop-k8"
  refine loop_joint "$LOOP" loop-k8,tree-k8 joint consensus
  refine loop_slot "$LOOP" loop-k8,tree-k8 slot consensus
  train_and_apply refine
  log "GPU 0: chain done"
}

chain1() {
  export CUDA_VISIBLE_DEVICES=1
  log "GPU 1: joint / slot / single-context scoring of anchor-k8, anchor-k4"
  refine anchor_joint "$CAND" anchor-k8,anchor-k4 joint consensus
  refine anchor_slot "$CAND" anchor-k8,anchor-k4 slot consensus
  refine anchor_single "$CAND" anchor-k8,anchor-k4 slot single
  train_and_apply plain
  log "GPU 1: chain done"
}

train_and_apply() {   # mode
  local mode=$1
  for f in 0 1 2; do
    log "GPU $CUDA_VISIBLE_DEVICES: train $mode adapter, fold $f"
    timeout 2100 python3 -u tools/train_refiner.py --mode "$mode" --cand "$CAND" --data "$DATA" \
        --sets "${TRAIN_SETS[$f]}" --steps "$TRAIN_STEPS" --out "$R/${mode}_f$f.pt" 2>&1 | quiet \
        > "$R/train_${mode}_f$f.log"
  done
  for f in 0 1 2; do
    [ -f "$R/${mode}_f$f.pt" ] || { log "no $mode adapter for fold $f"; continue; }
    log "GPU $CUDA_VISIBLE_DEVICES: slot scoring with $mode adapter, fold $f"
    refine "${mode}_anchor_f$f" "$CAND" anchor-k8,anchor-k4 slot consensus --sets "${FOLD_SETS[$f]}" --lora "$R/${mode}_f$f.pt"
    [ -f "$LOOP" ] && refine "${mode}_loop_f$f" "$LOOP" loop-k8 slot consensus --sets "${FOLD_SETS[$f]}" --lora "$R/${mode}_f$f.pt"
  done
}

if want 1; then
  log "step 1: both GPUs"
  chain0 > "$R/chain0.log" 2>&1 &
  P0=$!
  chain1 > "$R/chain1.log" 2>&1 &
  P1=$!
  while kill -0 $P0 2>/dev/null || kill -0 $P1 2>/dev/null; do
    sleep "$POLL"
    log "GPU 0: $(tail -n 1 "$R/chain0.log")"
    log "GPU 1: $(tail -n 1 "$R/chain1.log")"
    for f in $(ls -t "$R"/*.log | grep -v chain | head -3); do echo "   $f: $(tail -n 1 "$f")"; done
    pack
  done
  wait $P0; wait $P1
  cat "$R/chain0.log" "$R/chain1.log"
  for f in "$R"/train_*.log; do echo "== $f"; grep -E "examples|^step (0|300|600):|held-out" "$f"; done
  tail -n 1 "$R"/*.log | grep -B1 "done:" | grep -v "^--"
  pack
fi

if want 2; then
  log "step 2: external-LM slot scores, GPT-2 (GPU 0) and TinyLlama-1.1B (GPU 1)"
  lm_arms() {   # gpu model name
    export CUDA_VISIBLE_DEVICES=$1
    for spec in "$CAND anchor-k8" "$CAND anchor-k4" "$LOOP tree-k8" "$LOOP loop-k8"; do
      set -- "$1" "$2" "$3" $spec
      [ -f "$4" ] || continue
      timeout 3000 python3 -u tools/gpt_slots.py --cand "$4" --arm "$5" --model "$2" \
          --out "$R/lm_$3_$5.pkl" 2>&1 | grep -v Warning | tail -n 1
    done
  }
  lm_arms 0 gpt2 gpt2 > "$R/lm_gpt2.log" 2>&1 &
  lm_arms 1 "$TINY" tinyllama > "$R/lm_tinyllama.log" 2>&1 &
  wait
  cat "$R/lm_gpt2.log" "$R/lm_tinyllama.log"
  pack
fi

if want 3; then
  log "step 3: evaluation"
  j() { ls $R/$1 2>/dev/null | paste -sd, -; }
  lmspec() { local n=$1; echo "$n:anchor-k8=$R/lm_${n}_anchor-k8.pkl,anchor-k4=$R/lm_${n}_anchor-k4.pkl,tree-k8=$R/lm_${n}_tree-k8.pkl,loop-k8=$R/lm_${n}_loop-k8.pkl"; }
  P="anchor-k8@final>tree-k8@final;anchor-k8@final>loop-k8@final;anchor-k8@final>loop-k8@final +score [joint]"
  P="$P;tree-k8@final>loop-k8@final +score [joint];anchor-k8@final +score [slot]>loop-k8@final +score [joint]"
  P="$P;anchor-k8@final>loop-k8@final +score +tinyllama [joint];anchor-k8@final>loop-k8@final +score +gpt2 [joint]"
  P="$P;anchor-k8@final>anchor-k8@final +score +tinyllama [slot];anchor-k8@final +score [single]>anchor-k8@final +score [slot]"
  timeout 9000 python3 -u tools/refine_eval.py --cand "$CAND,$LOOP" --arms anchor-k8,anchor-k4,tree-k8,loop-k8 \
      --refine "joint=$(j '*_joint.pkl');slot=$(j '*_slot.pkl');single=$(j 'anchor_single.pkl');refiner=$(j 'refine_*_f?.pkl');plain=$(j 'plain_*_f?.pkl')" \
      --lm "$(lmspec gpt2);$(lmspec tinyllama)" --lm_variants joint,slot,refiner \
      --pairs "$P" 2>&1 | tee "$R/eval.txt"
  pack
fi
log "done"
