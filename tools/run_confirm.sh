#!/usr/bin/env bash
# Confirmation run on utterances never decoded before (Kaggle, GPU T4 x2, internet on). From the
# repo root:
#
#   bash tools/run_confirm.sh /tmp/campaign_data
#
# 1. decode flat and tree-early at K = 4, 8, 15: shard s02 (utterances 400-599, untouched in
#    development) of the 11 test sets first, then s00 of all 13 sets to train on
# 2. per-candidate acoustic scores for every arm
# 3. Whisper-small (autoregressive) on the same s02 utterances
# 4. tools/confirm_eval.py: frozen pipeline, pre-registered hypotheses (docs/confirm_prereg.md)
#
# Each step has a time cap so one stuck step cannot eat the session, and results are packed
# into results/confirm_all.tar.gz after every step. STEPS="2 3 4" reruns only those steps.
set -uo pipefail
DATA="${1:?usage: bash tools/run_confirm.sh <data dir>}"
UP="${UP:-$PWD/Whisfusion}"
STEPS="${STEPS:-1 2 3 4}"
DECODE_MIN="${DECODE_MIN:-330}"   # worst case: 5.5 h decode + 2.5 + 1 + 2.5 h caps < 12 h
DEV="ls-dev-clean ls-dev-other"
TEST="ls-test-clean ls-test-other ami earnings22 voxpopuli gigaspeech spgispeech common_voice ls-tc-babble5 ls-tc-babble0 ls-tc-white5"
ARMS="flat-k4,tree-early-k4,flat-k8,tree-early-k8,flat-k15,tree-early-k15"
R=results/confirm
mkdir -p "$R"
log() { echo "[$(date +%H:%M:%S)] $*"; }
want() { case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }
pack() {
  [ -d "$R/dumps" ] && tar cf "$R/dumps.tar" -C "$R" dumps
  tar czf results/confirm_all.tar.gz $(ls "$R"/*.txt "$R"/*.log "$R"/*.json "$R"/*.jsonl \
      "$R"/*.pkl "$R/dumps.tar" 2>/dev/null) 2>/dev/null || true
  log "packed results/confirm_all.tar.gz"
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

if want 1; then
  log "step 1: decode (s02 test first, then s00 train)"
  python3 - "$DECODE_MIN" "$R/config.json" <<'PY'
import json, sys
dev = ["ls-dev-clean", "ls-dev-other"]
test = ["ls-test-clean", "ls-test-other", "ami", "earnings22", "voxpopuli", "gigaspeech",
        "spgispeech", "common_voice", "ls-tc-babble5", "ls-tc-babble0", "ls-tc-white5"]
json.dump({"plan": "treek", "models": ["whisfusion"], "run_hours": float(sys.argv[1]) / 60,
           "tail_minutes": 10, "shard_size": 200, "treek_ks": [4, 8, 15],
           "treek_shards": [2, 0], "treek_train_only": dev, "tree_sets": dev + test},
          open(sys.argv[2], "w"), indent=2)
PY
  timeout $(( DECODE_MIN * 60 + 900 )) python3 -u -m campaign.run --config "$R/config.json" \
      --root "$R" --data "$DATA" 2>&1 | tee "$R/decode.log"
  pack
fi

if want 2; then
  log "step 2: acoustic scores"
  ls -d "$R"/dumps/*treek | head -3
  timeout 9000 python3 -u tools/cand_audio.py --data "$DATA" --dumps_root "$R/dumps" \
      --sets "$(echo $DEV $TEST | tr ' ' ',')" --per_set 1000 --arm "$ARMS" \
      --pattern "whisfusion__{set}__s*__treek/{arm}.jsonl*" \
      --out "$R/cand_audio_confirm.pkl" 2>&1 | tee "$R/cand_audio.log"
  pack
fi

if want 3; then
  log "step 3: Whisper-small on the s02 utterances"
  timeout 3600 python3 -u tools/whisper_ref.py --data "$DATA" --sets "$(echo $TEST | tr ' ' ',')" \
      --shard 2 --out "$R/whisper_small_s02.jsonl" 2>&1 | tee "$R/whisper.log"
  pack
fi

if want 4; then
  log "step 4: evaluation"
  timeout 9000 python3 -u tools/confirm_eval.py --cand "$R/cand_audio_confirm.pkl" \
      --whisper "$R/whisper_small_s02.jsonl" --work "$R/eval_cache" 2>&1 | tee "$R/confirm_eval.txt"
  pack
fi
log "done"
