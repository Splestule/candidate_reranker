#!/usr/bin/env bash
# Everything the paper needs from one Kaggle session (GPU T4 x2, internet on). From the repo root:
#
#   bash tools/run_kaggle_all.sh /tmp/campaign_data
#   STEPS="4 5" TREEK_DUMPS=/kaggle/input/.../dumps.tar bash tools/run_kaggle_all.sh /tmp/campaign_data
#
# 1. final pipeline at full scale on the campaign dumps (13 sets x 400, flat K=32)
# 2. GPT-2 as an external LM feature on the same cache
# 3. new decode: flat and tree-early at K = 4, 8, 15, 32 (13 sets x 200)
# 4. per-candidate acoustic scores for every arm of step 3
# 5. the cost/quality table: upstream Whisfusion vs MBR / ROVER / iROVER-style / final, flat vs
#    tree-early, measured decode times, legacy and Whisper normalisation
#
# STEPS picks which steps run; TREEK_DUMPS points at the dumps.tar a previous step 3 packed, so
# steps 4-5 can run without decoding again. Results are packed into results/kaggle_all.tar.gz
# after every step, so a session that hits Kaggle's 12 h limit keeps what it finished.
set -uo pipefail
DATA="${1:?usage: bash tools/run_kaggle_all.sh <data dir>}"
UP="${UP:-$PWD/Whisfusion}"
STEPS="${STEPS:-1 2 3 4 5}"
SETS="ls-dev-clean,ls-dev-other,ls-test-clean,ls-test-other,ami,earnings22,voxpopuli,gigaspeech,spgispeech,common_voice,ls-tc-babble5,ls-tc-babble0,ls-tc-white5"
KS="4 8 15 32"
TREEK_HOURS="${TREEK_HOURS:-5}"
log() { echo "[$(date +%H:%M:%S)] $*"; }
want() { case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }
pack() {
  tar czf results/kaggle_all.tar.gz $(ls results/*.txt results/*.log results/treek_config.json \
      results/treek/dumps.tar 2>/dev/null) 2>/dev/null || true
  log "packed results/kaggle_all.tar.gz"
}

# step 1 clones Whisfusion and installs requirements; later steps need both too
if [ ! -d "$UP/src/lit_gpt" ]; then
  git clone -q https://github.com/taeyoun811/Whisfusion.git "$UP"
  git -C "$UP" checkout -q aa9afe3688ccd15ebf096ec9845d67925d1a3aea
fi
python3 -c "import lightning, soundfile, rapidfuzz" 2>/dev/null || pip install -q -r requirements-kaggle.txt
export PYTHONPATH="$PWD/src:$UP/src:$PWD/tools"

if want 1; then
  log "step 1: final pipeline at full scale"
  bash tools/run_audio_slots.sh "$DATA" || log "!! step 1 failed, continuing"
  pack
fi

if want 2; then
  log "step 2: GPT-2 external LM"
  python3 -u tools/ext_lm.py --cache results/audio_cache_full.pkl --out results/gpt2_slots_full.pkl \
      2>&1 | tee results/ext_lm_full.txt
  pack
fi

if want 3; then
  log "step 3: flat vs tree-early decode over K"
  python3 - "$TREEK_HOURS" <<'PY'
import json, sys
json.dump({"plan": "treek", "models": ["whisfusion"], "run_hours": float(sys.argv[1]),
           "tail_minutes": 10, "shard_size": 200, "tree_shards": 1, "treek_ks": [4, 8, 15, 32],
           "tree_sets": ["ls-dev-clean", "ls-dev-other", "ls-test-clean", "ls-test-other", "ami",
                         "earnings22", "voxpopuli", "gigaspeech", "spgispeech", "common_voice",
                         "ls-tc-babble5", "ls-tc-babble0", "ls-tc-white5"]},
          open("results/treek_config.json", "w"), indent=2)
PY
  python3 -u -m campaign.run --config results/treek_config.json --root results/treek --data "$DATA" \
      2>&1 | tee results/treek_run.log
  pack
fi

if want 4; then
  log "step 4: acoustic scores for every treek arm"
  if [ ! -d results/treek/dumps ] && [ -n "${TREEK_DUMPS:-}" ]; then
    mkdir -p results/treek && tar xf "$TREEK_DUMPS" -C results/treek
  fi
  # the manifests must exist for the audio; prep is a no-op for sets already there
  MISSING=""
  for s in ${SETS//,/ }; do [ -f "$DATA/manifests/$s.jsonl" ] || MISSING="$MISSING $s"; done
  [ -z "$MISSING" ] || python3 -m campaign.prep_data --data "$DATA" --only $MISSING
  ls -d results/treek/dumps/*treek | head -3
  ARMS=$(for k in $KS; do printf "flat-k%s,tree-early-k%s," "$k" "$k"; done)
  python3 -u tools/cand_audio.py --data "$DATA" --dumps_root results/treek/dumps --sets "$SETS" \
      --per_set 200 --arm "${ARMS%,}" --pattern "whisfusion__{set}__s00__treek/{arm}.jsonl.gz" \
      --out results/cand_audio_treek.pkl 2>&1 | tee results/cand_audio_treek.log
  pack
fi

if want 5; then
  log "step 5: cost/quality table"
  python3 -u tools/treek_eval.py --cand results/cand_audio_treek.pkl --ks "$(echo $KS | tr ' ' ',')" \
      2>&1 | tee results/treek_eval.txt
  pack
fi
log "done"
