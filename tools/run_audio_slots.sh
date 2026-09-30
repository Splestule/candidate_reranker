#!/usr/bin/env bash
# Acoustic slot features at full scale: 13 sets x up to 400 utterances, both dump shards,
# then the final comparison (tools/final_compare.py) on the same cache.
# Needs a GPU in practice (CPU works, ~3 s per utterance). Run from the repo root:
#
#   bash tools/run_audio_slots.sh /tmp/campaign_data          # Kaggle: one cell, GPU + internet on
#
# It reuses the campaign's dumps (results/campaign-2026-09-20/dumps, committed to the repo), so
# nothing is decoded again; prep_data rebuilds exactly the audio the campaign decoded (the
# selection and the noise mixing are seeded by utterance id). Resumable: rerun the same line
# and it continues from results/audio_cache_full.pkl.
set -euo pipefail
DATA="${1:?usage: bash tools/run_audio_slots.sh <data dir>}"
PER_SET="${PER_SET:-400}"
UP="${UP:-$PWD/Whisfusion}"
SETS="ls-dev-clean ls-dev-other ls-test-clean ls-test-other ami earnings22 voxpopuli gigaspeech spgispeech common_voice ls-tc-babble5 ls-tc-babble0 ls-tc-white5"

if [ ! -d "$UP/src/lit_gpt" ]; then
  git clone -q https://github.com/taeyoun811/Whisfusion.git "$UP"
  git -C "$UP" checkout -q aa9afe3688ccd15ebf096ec9845d67925d1a3aea
fi
python3 -c "import lightning, soundfile, rapidfuzz" 2>/dev/null || pip install -q -r requirements-kaggle.txt
export PYTHONPATH="$PWD/src:$UP/src:$PWD/tools"

MISSING=""
for s in $SETS; do [ -f "$DATA/manifests/$s.jsonl" ] || MISSING="$MISSING $s"; done
[ -z "$MISSING" ] || python3 -m campaign.prep_data --data "$DATA" --only $MISSING

python3 -u tools/audio_slots.py --data "$DATA" --dumps_root results/campaign-2026-09-20/dumps \
    --shard s00,s01 --per_set "$PER_SET" --out results/audio_cache_full.pkl

for w in w0 w2; do
  python3 tools/slot_eval.py --cache results/audio_cache_full.pkl --audio "$w" \
      | tee "results/slot_eval_audio_${w}_full.txt"
done

# everything that survived in one pipeline, against Whisfusion's own selectors and ROVER
python3 -u tools/final_compare.py --cache results/audio_cache_full.pkl \
    --dumps_root results/campaign-2026-09-20/dumps --seeds 0,1,2 \
    | tee results/final_compare_full.txt
