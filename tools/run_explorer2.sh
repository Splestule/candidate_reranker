#!/usr/bin/env bash
# Vote explorer, run 2 (Kaggle, GPU T4 x2, internet on). From the repo root:
#
#   bash tools/run_explorer2.sh /tmp/campaign_data
#
# 0. smoke test of every new piece on a few utterances; stops the run if anything fails
# 1. labels: the anchor's real candidates on LibriSpeech train-clean-100, their confusion
#    network and the reference aligned to it (tools/explorer_prep.py)
# 2. plain LoRA (control), same utterances and steps
# 3. vote LoRA: KL to the anchor where it wins the vote, expected-vote hinge where it does not
# 4. decode: anchor-only, anchor + plain, anchor + vote at K = 4 and 8 (s01 test, s00 train)
# 5. per-candidate acoustic scores
# 6. tools/explorer_eval.py
#
# Each step has a time cap; results are packed into results/explorer2_all.tar.gz after every
# step. STEPS="4 5 6" reruns only those steps.
set -uo pipefail
DATA="${1:?usage: bash tools/run_explorer2.sh <data dir>}"
UP="${UP:-$PWD/Whisfusion}"
STEPS="${STEPS:-0 1 2 3 4 5 6}"
UTTS="${UTTS:-6000}"
TRAIN_STEPS="${TRAIN_STEPS:-1000}"
DECODE_MIN="${DECODE_MIN:-170}"
DEV="ls-dev-clean ls-dev-other"
TEST="ls-test-clean ls-test-other ami earnings22 voxpopuli gigaspeech spgispeech common_voice ls-tc-babble5 ls-tc-babble0 ls-tc-white5"
ARMS="anchor-k4,mix-vote-k4,anchor-k8,mix-plain-k8,mix-vote-k8,mix-vote44-k8"
R=results/explorer2
mkdir -p "$R"
log() { echo "[$(date +%H:%M:%S)] $*"; }
want() { case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }
pack() {
  tar czf results/explorer2_all.tar.gz $(ls "$R"/*.txt "$R"/*.log "$R"/*.json "$R"/*.pt \
      "$R"/*.pkl "$R/dumps.tar" 2>/dev/null) 2>/dev/null || true
  log "packed results/explorer2_all.tar.gz"
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

if want 0; then
  log "step 0: smoke test"
  S=results/explorer2_smoke
  mkdir -p "$S"
  set -e
  python3 -u tools/explorer_prep.py --utts 16 --out "$S/labels.pkl" 2>&1 | grep -v "Loading weights"
  python3 -u tools/train_explorer.py --mode vote --labels "$S/labels.pkl" --shards 5 --bs 4 \
      --steps 4 --val_utts 8 --out "$S/vote.pt" 2>&1 | grep -v "Loading weights"
  python3 - "$S/vote.pt" "$DATA" <<'PY'
import json, sys
import data as dataio
from campaign.families import Whisfusion
f = Whisfusion({})
r = json.loads(open(f"{sys.argv[2]}/manifests/ami.jsonl").readline())
enc = f.encode(dataio.load_audio(r["audio"]), "en")
c, _ = f.decode(enc, {"K": 8, "steps": 4, "n_explorer": 2, "explorer": sys.argv[1]}, 0, "en")
print("smoke decode:", [(x["source"], x["text"][:30]) for x in c])
assert len(c) == 8 and sum(x["source"] == "explorer" for x in c) == 2
PY
  set +e
  log "smoke test passed"
fi

if want 1; then
  log "step 1: vote labels on $UTTS utterances"
  timeout 4500 python3 -u tools/explorer_prep.py --utts "$UTTS" --out "$R/labels.pkl" 2>&1 \
      | grep -v "Loading weights" | tee "$R/labels.log"
  pack
fi

if want 2; then
  log "step 2: plain LoRA (control)"
  timeout 3600 python3 -u tools/train_explorer.py --mode plain --shards 5 --steps "$TRAIN_STEPS" \
      --out "$R/plain.pt" 2>&1 | grep -v "Loading weights" | tee "$R/train_plain.log"
  pack
fi

if want 3; then
  log "step 3: vote LoRA"
  timeout 4200 python3 -u tools/train_explorer.py --mode vote --labels "$R/labels.pkl" --shards 5 \
      --steps "$TRAIN_STEPS" --out "$R/vote.pt" 2>&1 | grep -v "Loading weights" | tee "$R/train_vote.log"
  pack
fi

if want 4; then
  log "step 4: decode (s01 test first, then s00 train)"
  python3 - "$DECODE_MIN" "$R/config.json" "$PWD/$R" <<'PY'
import json, sys
dev = ["ls-dev-clean", "ls-dev-other"]
test = ["ls-test-clean", "ls-test-other", "ami", "earnings22", "voxpopuli", "gigaspeech",
        "spgispeech", "common_voice", "ls-tc-babble5", "ls-tc-babble0", "ls-tc-white5"]
r = sys.argv[3]
arms = [{"name": "anchor-k4", "K": 4, "steps": 4},
        {"name": "mix-vote-k4", "K": 4, "steps": 4, "n_explorer": 2, "explorer": f"{r}/vote.pt"},
        {"name": "anchor-k8", "K": 8, "steps": 4},
        {"name": "mix-plain-k8", "K": 8, "steps": 4, "n_explorer": 2, "explorer": f"{r}/plain.pt"},
        {"name": "mix-vote-k8", "K": 8, "steps": 4, "n_explorer": 2, "explorer": f"{r}/vote.pt"},
        {"name": "mix-vote44-k8", "K": 8, "steps": 4, "n_explorer": 4, "explorer": f"{r}/vote.pt"}]
json.dump({"plan": "explorer", "models": ["whisfusion"], "run_hours": float(sys.argv[1]) / 60,
           "tail_minutes": 10, "shard_size": 100, "explorer_shards": [1, 0],
           "explorer_train_only": dev, "tree_sets": dev + test, "explorer_arms": arms},
          open(sys.argv[2], "w"), indent=2)
PY
  timeout $(( DECODE_MIN * 60 + 900 )) python3 -u -m campaign.run --config "$R/config.json" \
      --root "$R" --data "$DATA" 2>&1 | tee "$R/decode.log"
  pack
fi

if want 5; then
  log "step 5: acoustic scores"
  # campaign.run packs the dumps into dumps.tar and removes the directory when it finishes
  [ -d "$R/dumps" ] || tar xf "$R/dumps.tar" -C "$R"
  ls -d "$R"/dumps/*explorer | head -3
  timeout 6600 python3 -u tools/cand_audio.py --data "$DATA" --dumps_root "$R/dumps" \
      --sets "$(echo $DEV $TEST | tr ' ' ',')" --per_set 1000 --arm "$ARMS" --k 8 \
      --pattern "whisfusion__{set}__s*__explorer/{arm}.jsonl*" \
      --out "$R/cand_audio.pkl" 2>&1 | tee "$R/cand_audio.log"
  pack
fi

if want 6; then
  log "step 6: evaluation"
  timeout 3000 python3 -u tools/explorer_eval.py --cand "$R/cand_audio.pkl" 2>&1 | tee "$R/eval.txt"
  pack
fi
log "done"
