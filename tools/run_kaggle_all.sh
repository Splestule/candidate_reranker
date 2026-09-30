#!/usr/bin/env bash
# Everything the paper needs from one Kaggle session (GPU T4 x2, internet on). From the repo root:
#
#   bash tools/run_kaggle_all.sh /tmp/campaign_data
#
# 1. final pipeline at full scale on the campaign dumps (13 sets x 400, flat K=32)
# 2. GPT-2 as an external LM feature on the same cache
# 3. new decode: flat and tree-early at K = 4, 8, 15, 32 (13 sets x 200)
# 4. per-candidate acoustic scores for every arm of step 3
# 5. the cost/quality table: upstream Whisfusion vs MBR / ROVER / iROVER-style / final, flat vs
#    tree-early, measured decode times, legacy and Whisper normalisation
#
# Every step is resumable: rerun the same line after a crash and finished work is skipped.
# Results land in results/; the last step packs them into results/kaggle_all.tar.gz.
set -uo pipefail
DATA="${1:?usage: bash tools/run_kaggle_all.sh <data dir>}"
UP="${UP:-$PWD/Whisfusion}"
SETS="ls-dev-clean,ls-dev-other,ls-test-clean,ls-test-other,ami,earnings22,voxpopuli,gigaspeech,spgispeech,common_voice,ls-tc-babble5,ls-tc-babble0,ls-tc-white5"
KS="4 8 15 32"
TREEK_HOURS="${TREEK_HOURS:-5}"
log() { echo "[$(date +%H:%M:%S)] $*"; }

# 1 -- clones Whisfusion, installs requirements, preps data, audio_slots, slot_eval, final_compare
log "step 1: final pipeline at full scale"
bash tools/run_audio_slots.sh "$DATA" || log "!! step 1 failed, continuing"
export PYTHONPATH="$PWD/src:$UP/src:$PWD/tools"

# 2
log "step 2: GPT-2 external LM"
python3 -u tools/ext_lm.py --cache results/audio_cache_full.pkl --out results/gpt2_slots_full.pkl \
    2>&1 | tee results/ext_lm_full.txt || log "!! step 2 failed, continuing"

# 3
log "step 3: flat vs tree-early decode over K"
python3 - "$TREEK_HOURS" <<'EOF'
import json, sys
json.dump({"plan": "treek", "models": ["whisfusion"], "run_hours": float(sys.argv[1]),
           "tail_minutes": 10, "shard_size": 200, "tree_shards": 1, "treek_ks": [4, 8, 15, 32],
           "tree_sets": ["ls-dev-clean", "ls-dev-other", "ls-test-clean", "ls-test-other", "ami",
                         "earnings22", "voxpopuli", "gigaspeech", "spgispeech", "common_voice",
                         "ls-tc-babble5", "ls-tc-babble0", "ls-tc-white5"]},
          open("results/treek_config.json", "w"), indent=2)
EOF
python3 -u -m campaign.run --config results/treek_config.json --root results/treek --data "$DATA" \
    2>&1 | tee results/treek_run.log || log "!! step 3 failed, continuing with what was decoded"

# 4
log "step 4: acoustic scores for every treek arm"
ARMS=$(for k in $KS; do printf "flat-k%s,tree-early-k%s," "$k" "$k"; done)
python3 -u tools/cand_audio.py --data "$DATA" --dumps_root results/treek/dumps --sets "$SETS" \
    --per_set 200 --arm "${ARMS%,}" --pattern "whisfusion__{set}__s00__treek/{arm}.jsonl.gz" \
    --out results/cand_audio_treek.pkl 2>&1 | tail -3

# 5
log "step 5: cost/quality table"
python3 -u tools/treek_eval.py --cand results/cand_audio_treek.pkl --ks "$(echo $KS | tr ' ' ',')" \
    2>&1 | tee results/treek_eval.txt

tar czf results/kaggle_all.tar.gz results/*_full.txt results/final_compare_full.txt \
    results/ext_lm_full.txt results/treek_eval.txt results/treek_run.log results/treek_config.json \
    2>/dev/null
log "done: results/kaggle_all.tar.gz"
