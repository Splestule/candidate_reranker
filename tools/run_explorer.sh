#!/usr/bin/env bash
# Explorer proof of concept (Kaggle, GPU T4 x2, internet on). From the repo root:
#
#   bash tools/run_explorer.sh /tmp/campaign_data
#
# 1. LoRA with the plain diffusion loss on LibriSpeech train-clean-100 (control)
# 2. LoRA explorer: same data, loss aimed at the anchor's step-zero errors
# 3. decode anchor-only, anchor + plain, anchor + explorer at K = 4 and 8 (half anchor, half
#    LoRA in the mixed arms): shard s01 of the 11 test sets (rows 100-199), then s00 of all 13
# 4. per-candidate acoustic scores
# 5. tools/explorer_eval.py: the frozen composition pipeline on every arm
#
# Each step has a time cap; results are packed into results/explorer_all.tar.gz after every
# step. STEPS="3 4 5" reruns only those steps.
set -uo pipefail
DATA="${1:?usage: bash tools/run_explorer.sh <data dir>}"
UP="${UP:-$PWD/Whisfusion}"
STEPS="${STEPS:-1 2 3 4 5}"
TRAIN_STEPS="${TRAIN_STEPS:-1000}"
DECODE_MIN="${DECODE_MIN:-180}"
DEV="ls-dev-clean ls-dev-other"
TEST="ls-test-clean ls-test-other ami earnings22 voxpopuli gigaspeech spgispeech common_voice ls-tc-babble5 ls-tc-babble0 ls-tc-white5"
ARMS="anchor-k4,mix-plain-k4,mix-expl-k4,anchor-k8,mix-plain-k8,mix-expl-k8"
R=results/explorer
mkdir -p "$R"
log() { echo "[$(date +%H:%M:%S)] $*"; }
want() { case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }
pack() {
  tar czf results/explorer_all.tar.gz $(ls "$R"/*.txt "$R"/*.log "$R"/*.json "$R"/*.pt \
      "$R"/*.pkl "$R/dumps.tar" 2>/dev/null) 2>/dev/null || true
  log "packed results/explorer_all.tar.gz"
}

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

for mode in plain explorer; do
  n=1; [ "$mode" = explorer ] && n=2
  if want $n; then
    log "step $n: train the $mode LoRA"
    timeout 5400 python3 -u tools/train_explorer.py --mode "$mode" --steps "$TRAIN_STEPS" \
        --out "$R/$mode.pt" 2>&1 | grep -v "Loading weights" | tee "$R/train_$mode.log"
    pack
  fi
done

if want 3; then
  log "step 3: decode (s01 test first, then s00 train)"
  python3 - "$DECODE_MIN" "$R/config.json" "$PWD/$R" <<'PY'
import json, sys
dev = ["ls-dev-clean", "ls-dev-other"]
test = ["ls-test-clean", "ls-test-other", "ami", "earnings22", "voxpopuli", "gigaspeech",
        "spgispeech", "common_voice", "ls-tc-babble5", "ls-tc-babble0", "ls-tc-white5"]
r = sys.argv[3]
arms = []
for k in (4, 8):
    arms.append({"name": f"anchor-k{k}", "K": k, "steps": 4})
    for tag, f in (("plain", "plain.pt"), ("expl", "explorer.pt")):
        arms.append({"name": f"mix-{tag}-k{k}", "K": k, "steps": 4, "n_explorer": k // 2,
                     "explorer": f"{r}/{f}"})
json.dump({"plan": "explorer", "models": ["whisfusion"], "run_hours": float(sys.argv[1]) / 60,
           "tail_minutes": 10, "shard_size": 100, "explorer_shards": [1, 0],
           "explorer_train_only": dev, "tree_sets": dev + test, "explorer_arms": arms},
          open(sys.argv[2], "w"), indent=2)
PY
  timeout $(( DECODE_MIN * 60 + 900 )) python3 -u -m campaign.run --config "$R/config.json" \
      --root "$R" --data "$DATA" 2>&1 | tee "$R/decode.log"
  pack
fi

if want 4; then
  log "step 4: acoustic scores"
  # campaign.run packs the dumps into dumps.tar and removes the directory when it finishes
  [ -d "$R/dumps" ] || tar xf "$R/dumps.tar" -C "$R"
  ls -d "$R"/dumps/*explorer | head -3
  timeout 7200 python3 -u tools/cand_audio.py --data "$DATA" --dumps_root "$R/dumps" \
      --sets "$(echo $DEV $TEST | tr ' ' ',')" --per_set 1000 --arm "$ARMS" --k 8 \
      --pattern "whisfusion__{set}__s*__explorer/{arm}.jsonl*" \
      --out "$R/cand_audio.pkl" 2>&1 | tee "$R/cand_audio.log"
  pack
fi

if want 5; then
  log "step 5: evaluation"
  timeout 3600 python3 -u tools/explorer_eval.py --cand "$R/cand_audio.pkl" 2>&1 | tee "$R/eval.txt"
  pack
fi
log "done"
