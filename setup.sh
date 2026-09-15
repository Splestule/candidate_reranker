#!/usr/bin/env bash
# Local/standalone setup. On Kaggle use notebooks/kaggle_prepare_data.ipynb instead.
#   bash setup.sh [WORKDIR]
set -euo pipefail

WORK="${1:-$(pwd)}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$WORK/ckpt" "$WORK/results"

echo "== deps"
pip install -q -r "$HERE/requirements-kaggle.txt"
python -c "import torch; print('   torch', torch.__version__, 'cuda', torch.cuda.is_available())"

echo "== upstream Whisfusion"
[ -d "$WORK/Whisfusion" ] || git clone --depth 1 \
  https://github.com/taeyoun811/Whisfusion.git "$WORK/Whisfusion"

echo "== checkpoints (~1.9 GB)"
python - "$WORK" <<'PY'
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download
work = Path(sys.argv[1])
print("  ", hf_hub_download("nieshen/SMDM",
      "mdm_safetensors/mdm-170M-100e18-rsl-0.01.safetensors", local_dir=str(work / "ckpt")))
print("  ", hf_hub_download("taeyoun811/whisfusion",
      "whisfusion_stage2_decoder.pt", local_dir=str(work / "ckpt")))
PY

echo "== LibriSpeech test-clean (~331 MB)"
if [ ! -d "$WORK/data/LibriSpeech/test-clean" ]; then
  mkdir -p "$WORK/data"
  curl -L --retry 3 -o "$WORK/data/test-clean.tar.gz" \
      https://www.openslr.org/resources/12/test-clean.tar.gz
  tar -xzf "$WORK/data/test-clean.tar.gz" -C "$WORK/data"
  rm -f "$WORK/data/test-clean.tar.gz"
fi
find "$WORK/data/LibriSpeech/test-clean" -name '*.flac' | wc -l | xargs echo "   flac files:"

cat <<MSG

Next:
  export PYTHONPATH=$HERE/src:$WORK/Whisfusion/src
  python $HERE/src/selftest.py --work $WORK
MSG
