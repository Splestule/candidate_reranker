#!/usr/bin/env bash
# Consensus re-denoising (Kaggle, GPU T4 x2, internet on). From the repo root:
#
#   bash tools/run_refine.sh /tmp/campaign_data
#
# No decoding and no training: the candidates are explorer run 2's anchor-k8 and anchor-k4
# arms (results/cand_audio.pkl, s00 train + s01 test of all 13 sets), so every number is
# directly comparable with the explorer evaluations.
#
# 0. smoke test: tools/refine.py on 8 utterances; stops the run if it fails or if the
#    tokeniser does not round-trip the consensus
# 1. tools/refine.py, K=8 on GPU 0 and K=4 on GPU 1 in parallel
# 2. tools/refine_eval.py, 3 seeds
#
# Results are packed into results/refine_all.tar.gz after every step. STEPS="2" reruns only
# the evaluation.
set -uo pipefail
DATA="${1:?usage: bash tools/run_refine.sh <data dir>}"
UP="${UP:-$PWD/Whisfusion}"
STEPS="${STEPS:-0 1 2}"
CAND="${CAND:-results/cand_audio.pkl}"
DEV="ls-dev-clean ls-dev-other"
TEST="ls-test-clean ls-test-other ami earnings22 voxpopuli gigaspeech spgispeech common_voice ls-tc-babble5 ls-tc-babble0 ls-tc-white5"
R=results/refine
mkdir -p "$R"
log() { echo "[$(date +%H:%M:%S)] $*"; }
want() { case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }
pack() {
  tar czf results/refine_all.tar.gz $(ls "$R"/*.txt "$R"/*.log "$R"/*.pkl 2>/dev/null) 2>/dev/null || true
  log "packed results/refine_all.tar.gz"
}

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

if want 0; then
  log "step 0: smoke test"
  set -e
  rm -f "$R/smoke.pkl"
  python3 -u tools/refine.py --cand "$CAND" --data "$DATA" --arms anchor-k8 --limit 8 \
      --out "$R/smoke.pkl" 2>&1 | grep -v "Loading weights" | tee "$R/smoke.log"
  python3 - "$R/smoke.pkl" "$R/smoke.log" <<'PY'
import pickle, re, sys
out = pickle.loads(open(sys.argv[1], "rb").read())
assert len(out) >= 4, f"only {len(out)} records refined"
rt = float(re.findall(r"round trip ([\d.]+)%", open(sys.argv[2]).read())[-1])
assert rt >= 90, f"tokeniser round trip {rt}%: the consensus is not what the decoder reads"
n_feat = sum(len(v["feats"]) for v in out.values())
assert n_feat > 0, "no slot was scored"
key, rec = next(iter(out.items()))
print("example", key, "contested", rec["contested"], "props", rec["props"])
for c in rec["refined"]:
    print("  refined:", " ".join(c["words"]))
print(f"{len(out)} records, {n_feat} scored slots, round trip {rt}%")
PY
  set +e
  log "smoke test passed"
fi

if want 1; then
  log "step 1: refine K=8 (GPU 0) and K=4 (GPU 1)"
  CUDA_VISIBLE_DEVICES=0 timeout 18000 python3 -u tools/refine.py --cand "$CAND" --data "$DATA" \
      --arms anchor-k8 --out "$R/refine_k8.pkl" 2>&1 | grep --line-buffered -v "Loading weights" > "$R/refine_k8.log" &
  P8=$!
  CUDA_VISIBLE_DEVICES=1 timeout 18000 python3 -u tools/refine.py --cand "$CAND" --data "$DATA" \
      --arms anchor-k4 --out "$R/refine_k4.pkl" 2>&1 | grep --line-buffered -v "Loading weights" > "$R/refine_k4.log" &
  P4=$!
  while kill -0 $P8 2>/dev/null || kill -0 $P4 2>/dev/null; do
    sleep 600
    log "K=8: $(tail -n 1 "$R/refine_k8.log")"
    log "K=4: $(tail -n 1 "$R/refine_k4.log")"
    pack
  done
  wait $P8; wait $P4
  tail -n 2 "$R/refine_k8.log" "$R/refine_k4.log"
  pack
fi

if want 2; then
  log "step 2: evaluation"
  timeout 7200 python3 -u tools/refine_eval.py --cand "$CAND" \
      --refine "$R/refine_k8.pkl,$R/refine_k4.pkl" 2>&1 | tee "$R/eval.txt"
  pack
fi
log "done"
