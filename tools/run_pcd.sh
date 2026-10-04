#!/usr/bin/env bash
# Peer-conditioned denoising (Kaggle, GPU T4 x2, internet on). From the repo root:
#
#   bash tools/run_pcd.sh /tmp/campaign_data
#
# 0. smoke test of every piece on a few utterances, including two exactness checks: the base
#    path reproduces tree-early PDD, and an adapter trained for 0 steps changes nothing
# 1. training audio disjoint from the evaluation (tools/pcd_data.py)
# 2. sibling states of the training utterances (tools/pcd_states.py), both GPUs
# 3. four variants trained identically (tools/pcd_train.py): peer, self, shuf, plain
# 4. evaluation decodes: tree-early to the last step once, the last step five ways
#    (tools/pcd_decode.py), s00 + s01 of the 13 sets, both GPUs
# 5. GPT-2 slot scores for four arms (stacking, reported separately from the method)
# 6. tools/refine_eval.py (final pipeline, set-level CV, 3 seeds, bootstrap), tools/pcd_report.py
#
# Packed into results/pcd_all.tar.gz (without adapters) every 10 minutes and after each step.
set -uo pipefail
DATA="${1:?usage: bash tools/run_pcd.sh <data dir>}"
UP="${UP:-$PWD/Whisfusion}"
STEPS="${STEPS:-0 1 2 3 4 5 6}"
CAND="${CAND:-results/cand_audio.pkl}"
TRAIN_DATA="${TRAIN_DATA:-/tmp/pcd_data}"
PER_SET="${PER_SET:-700}"
TRAIN_STEPS="${TRAIN_STEPS:-1200}"
POLL="${POLL:-600}"
DEV="ls-dev-clean ls-dev-other"
TEST="ls-test-clean ls-test-other ami earnings22 voxpopuli gigaspeech spgispeech common_voice ls-tc-babble5 ls-tc-babble0 ls-tc-white5"
R=results/pcd
mkdir -p "$R"
log() { echo "[$(date +%H:%M:%S)] $*"; }
want() { case " $STEPS " in *" $1 "*) return 0;; *) return 1;; esac; }
pack() {
  tar czf results/pcd_all.tar.gz $(ls "$R"/*.txt "$R"/*.log "$R"/*.json "$R"/dec_*.pkl "$R"/lm_*.pkl 2>/dev/null) 2>/dev/null || true
  log "packed results/pcd_all.tar.gz"
}
quiet() { grep --line-buffered -v "Loading weights"; }
both() {   # run "$1" on GPU 0 and "$2" on GPU 1, wait, report
  (export CUDA_VISIBLE_DEVICES=0; eval "$1") &
  local p0=$!
  (export CUDA_VISIBLE_DEVICES=1; eval "$2") &
  local p1=$!
  while kill -0 $p0 2>/dev/null || kill -0 $p1 2>/dev/null; do
    sleep "$POLL"
    for f in $(ls -t "$R"/*.log 2>/dev/null | head -2); do log "   $f: $(tail -n 1 "$f")"; done
    pack
  done
  wait $p0; wait $p1
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

if want 1 || want 0; then
  if [ ! -f "$TRAIN_DATA/train.jsonl" ]; then
    log "step 1: training audio"
    python3 -u tools/pcd_data.py --data "$DATA" --out "$TRAIN_DATA" --per_set "$PER_SET" 2>&1 | tee "$R/pcd_data.log"
  fi
  cp "$TRAIN_DATA/train.meta.json" "$R/train_data.json" 2>/dev/null
  [ -f "$TRAIN_DATA/train.jsonl" ] || { echo "no training data"; exit 1; }
fi

if want 0; then
  log "step 0: smoke test"
  set -e
  S=$R/smoke
  mkdir -p "$S"
  rm -f "$S"/*
  python3 -u tools/pcd_states.py --train "$TRAIN_DATA/train.jsonl" --limit 12 --out "$S/states.pkl" 2>&1 | quiet | tail -n 1
  for mode in peer self shuf plain; do
    python3 -u tools/pcd_train.py --states "$S/states.pkl" --mode $mode --steps 3 --utts 4 \
        --out "$S/$mode.pt" 2>&1 | quiet | grep -E "embedding|reaches|saved|Error"
  done
  python3 -u tools/pcd_train.py --states "$S/states.pkl" --mode peer --steps 0 --utts 4 --out "$S/zero.pt" 2>&1 | quiet | tail -n 1
  python3 -u tools/pcd_decode.py --like "$CAND" --data "$DATA" --limit 3 --check 3 \
      --adapters "peer=$S/peer.pt,self=$S/self.pt,shuf=$S/shuf.pt,plain=$S/plain.pt,zero=$S/zero.pt" \
      --out "$S/dec.pkl" 2>&1 | quiet | tee "$S/dec.log" | tail -n 3
  python3 - "$S" <<'PY'
import pickle, re, sys
S = sys.argv[1]
log = open(f"{S}/dec.log").read()
m = re.search(r"reproduces tree-early PDD on (\d+) of (\d+)", log)
assert m and m.group(1) == m.group(2) and int(m.group(2)) > 0, "base path does not reproduce tree-early PDD"
recs = pickle.loads(open(f"{S}/dec.pkl", "rb").read())
arms = sorted({r["arm"] for r in recs})
assert arms == ["pcd-peer-k8", "pcd-plain-k8", "pcd-self-k8", "pcd-shuf-k8", "pcd-zero-k8", "pcdbase-k8"], arms
by = {(r["arm"], r["id"]): [c["words"] for c in r["cands"]] for r in recs}
for (arm, uid), c in by.items():
    if arm == "pcd-zero-k8":
        assert c == by[("pcdbase-k8", uid)], "an untrained adapter changed the output: the projections are not zero"
r = next(r for r in recs if r["arm"] == "pcd-peer-k8")
ok = [c for c in r["cands"] if c["conf"] is not None]
assert len(ok) >= 2, "candidates without confidences"
print("smoke:", r["id"], "|", " ".join(r["cands"][0]["words"]), "| ref:", " ".join(r["ref"]))
PY
  set +e
  log "smoke test passed"
  pack
fi

if want 2; then
  log "step 2: sibling states of the training utterances"
  both "timeout 3600 python3 -u tools/pcd_states.py --train $TRAIN_DATA/train.jsonl --part 0/2 --out $R/states_0.pkl 2>&1 | quiet > $R/states_0.log" \
       "timeout 3600 python3 -u tools/pcd_states.py --train $TRAIN_DATA/train.jsonl --part 1/2 --out $R/states_1.pkl 2>&1 | quiet > $R/states_1.log"
  tail -n 1 "$R"/states_?.log
  pack
fi

if want 3; then
  log "step 3: four variants, trained identically"
  ST="$R/states_0.pkl,$R/states_1.pkl"
  trainc() { echo "timeout 3600 python3 -u tools/pcd_train.py --states $ST --mode $1 --steps $TRAIN_STEPS --out $R/$1.pt 2>&1 | quiet > $R/train_$1.log"; }
  both "$(trainc peer); $(trainc self)" "$(trainc shuf); $(trainc plain)"
  for m in peer self shuf plain; do echo "== $m"; grep -E "utterances|embedding|held-out|^step (300|600|900|1200):" "$R/train_$m.log"; done
  pack
fi

if want 4; then
  log "step 4: evaluation decodes"
  AD="peer=$R/peer.pt,self=$R/self.pt,shuf=$R/shuf.pt,plain=$R/plain.pt"
  both "timeout 5400 python3 -u tools/pcd_decode.py --like $CAND --data $DATA --adapters $AD --part 0/2 --out $R/dec_0.pkl 2>&1 | quiet > $R/dec_0.log" \
       "timeout 5400 python3 -u tools/pcd_decode.py --like $CAND --data $DATA --adapters $AD --part 1/2 --out $R/dec_1.pkl 2>&1 | quiet > $R/dec_1.log"
  tail -n 3 "$R"/dec_?.log
  pack
fi

DEC="$R/dec_0.pkl,$R/dec_1.pkl"
if want 5; then
  log "step 5: GPT-2 slot scores"
  lm() { echo "timeout 2400 python3 -u tools/gpt_slots.py --cand $1 --arm $2 --model gpt2 --out $R/lm_gpt2_$2.pkl 2>&1 | grep -v Warning | tail -n 2 > $R/lm_$2.log"; }
  both "$(lm $CAND anchor-k8); $(lm $DEC pcdbase-k8)" "$(lm $DEC pcd-peer-k8); $(lm $DEC pcd-plain-k8)"
  tail -n 2 "$R"/lm_*.log
  pack
fi

if want 6; then
  log "step 6: evaluation"
  G="gpt2:anchor-k8=$R/lm_gpt2_anchor-k8.pkl,pcdbase-k8=$R/lm_gpt2_pcdbase-k8.pkl,pcd-peer-k8=$R/lm_gpt2_pcd-peer-k8.pkl,pcd-plain-k8=$R/lm_gpt2_pcd-plain-k8.pkl"
  P="pcd-plain-k8@final>pcd-peer-k8@final;pcd-self-k8@final>pcd-peer-k8@final;pcd-shuf-k8@final>pcd-peer-k8@final"
  P="$P;pcdbase-k8@final>pcd-peer-k8@final;anchor-k8@final>pcd-peer-k8@final;anchor-k8@final>pcdbase-k8@final"
  P="$P;pcdbase-k8@final>pcd-plain-k8@final;pcd-plain-k8@ROVER tuned>pcd-peer-k8@ROVER tuned"
  P="$P;pcd-plain-k8@final +gpt2>pcd-peer-k8@final +gpt2;anchor-k8@final +gpt2>pcd-peer-k8@final +gpt2"
  timeout 7200 python3 -u tools/refine_eval.py --cand "$CAND,$DEC" \
      --arms anchor-k8,pcdbase-k8,pcd-plain-k8,pcd-self-k8,pcd-shuf-k8,pcd-peer-k8 --refine "" \
      --lm "$G" --pairs "$P" 2>&1 | tee "$R/eval.txt"
  python3 tools/pcd_report.py "$CAND" "$R/dec_0.pkl" "$R/dec_1.pkl" 2>&1 | tee "$R/candidates.txt"
  python3 - "$R" <<'PY' 2>&1 | tee "$R/compute.txt"
import json, sys, glob
R = sys.argv[1]
mean = lambda v: sum(v) / max(len(v), 1)
T = [json.load(open(f)) for f in sorted(glob.glob(f"{R}/dec_?.pkl.timing.json"))]
first = mean([x for t in T for x in t["first"]])
print(f"ms per utterance on a T4: tree-early to the last step {first:.1f} (11 passes)")
for arm in sorted({a for t in T for a in t["last"]}):
    last = mean([x for t in T for x in t["last"].get(arm, [])])
    print(f"  {arm}: last step {last:.1f}, total {first + last:.1f}")
for f in sorted(glob.glob(f"{R}/lm_*.log")):
    print(f, open(f).read().strip().splitlines()[0] if open(f).read().strip() else "")
print("flat K=8 (anchor-k8) measured in refine run 2: 479.5 ms; tree-early K=8: 312.1 ms")
PY
  pack
fi
log "done"
