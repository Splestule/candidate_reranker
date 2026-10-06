#!/usr/bin/env bash
# Votes from distributions (docs/rb_voting.md). Kaggle, GPU T4, internet on. From the repo root:
#
#   bash tools/run_rb.sh /tmp/campaign_data
#
# 0. smoke test: tracked decode gives the same tokens as a normal decode, distributions line up
#    with the words, the evaluation runs end to end; the run stops here if anything fails
# 1. decode flat K=4, flat K=8, tree-early K=8 with the distributions kept, plus the acoustic
#    scores: s01 of the 11 test sets, s00 of all 13 sets to train on
# 2. tools/rb_eval.py
# Results in results/rb_all.tar.gz.
set -uo pipefail
DATA="${1:?usage: bash tools/run_rb.sh <data dir>}"
UP="${UP:-$PWD/Whisfusion}"
STEPS="${STEPS:-0 1 2}"
DECODE_MIN="${DECODE_MIN:-300}"
DEV="ls-dev-clean ls-dev-other"
TEST="ls-test-clean ls-test-other ami earnings22 voxpopuli gigaspeech spgispeech common_voice ls-tc-babble5 ls-tc-babble0 ls-tc-white5"
R=results/rb
mkdir -p "$R"
log() { echo "[$(date +%H:%M:%S)] $*"; }
want() { case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }
pack() { tar czf results/rb_all.tar.gz $(ls "$R"/*.txt "$R"/*.log "$R"/*.pkl 2>/dev/null) 2>/dev/null; log "packed results/rb_all.tar.gz"; }

if [ ! -d "$UP/src/lit_gpt" ]; then
  git clone -q https://github.com/taeyoun811/Whisfusion.git "$UP"
  git -C "$UP" checkout -q aa9afe3688ccd15ebf096ec9845d67925d1a3aea
fi
python3 -c "import lightning, soundfile, rapidfuzz, sklearn" 2>/dev/null || pip install -q -r requirements-kaggle.txt
export PYTHONPATH="$PWD/src:$UP/src:$PWD/tools"
MISSING=""
for s in $DEV $TEST; do [ -f "$DATA/manifests/$s.jsonl" ] || MISSING="$MISSING $s"; done
[ -z "$MISSING" ] || python3 -m campaign.prep_data --data "$DATA" --only $MISSING

if want 0; then
  log "step 0: smoke test"
  rm -f "$R/smoke.pkl"
  python3 - "$DATA" <<'PY' || { log "SMOKE FAILED: identical decode"; pack; exit 1; }
import json, sys
from pathlib import Path
import data as dataio
from campaign.families import Whisfusion
fam = Whisfusion({})
man = [json.loads(l) for l in open(Path(sys.argv[1]) / "manifests/ls-test-other.jsonl") if l.strip()][200:203]
for row in man:
    enc = fam.encode(dataio.load_audio(row["audio"]), "en")
    for arm in (dict(K=4, steps=4), dict(K=8, steps=4, branch_schedule=[1, 2, 8, 8])):
        a, _ = fam.decode(enc, arm, 11, "en")
        b, _ = fam.decode(enc, dict(arm, track_topk=8), 11, "en")
        assert [x["text"] for x in a] == [x["text"] for x in b], "tracking changed the decode"
print("identical decode: ok")
PY
  python3 -u tools/rb_run.py --data "$DATA" --jobs ls-test-other:1,ls-dev-clean:0 --limit 8 \
      --out "$R/smoke.pkl" 2>&1 | tee "$R/smoke.log"
  python3 - "$R/smoke.pkl" <<'PY' || { log "SMOKE FAILED: distributions"; pack; exit 1; }
import pickle, sys
recs = pickle.load(open(sys.argv[1], "rb"))
c = [c for r in recs for c in r["cands"]]
ok = sum(x["dist"] is not None for x in c) / max(len(c), 1)
print(f"{len(recs)} records, distributions on {100 * ok:.1f}% of candidates")
assert len(recs) == 48 and ok > 0.9
PY
  python3 tools/rb_eval.py --cand "$R/smoke.pkl" --seeds 0 --iters 50 2>&1 | tee "$R/smoke_eval.txt"
  grep -q "final + RB vs final" "$R/smoke_eval.txt" || { log "SMOKE FAILED: evaluation"; pack; exit 1; }
  log "smoke test passed"
fi

if want 1; then
  log "step 1: decode (s01 test, then s00 train)"
  J=""
  for s in $TEST; do J="$J,$s:1"; done
  for s in $DEV $TEST; do J="$J,$s:0"; done
  timeout $(( DECODE_MIN * 60 + 600 )) python3 -u tools/rb_run.py --data "$DATA" --jobs "${J#,}" \
      --minutes "$DECODE_MIN" --out "$R/cand_rb.pkl" 2>&1 | tee "$R/decode.log"
  pack
fi

if want 2; then
  log "step 2: evaluation"
  timeout 7200 python3 -u tools/rb_eval.py --cand "$R/cand_rb.pkl" 2>&1 | tee "$R/rb_eval.txt"
  pack
fi
log "done"
