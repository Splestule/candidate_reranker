# Kaggle: GPU T4 x2, internet ON, no input dataset needed -- everything comes from GitHub.
# Runs consensus re-denoising (tools/run_refine.sh); results in results/refine_all.tar.gz.
import os, subprocess

BRANCH = "claude/busy-johnson-2cglu7"
if not os.path.isdir("/kaggle/working/cr"):
    subprocess.run(f"git clone -q -b {BRANCH} https://github.com/Splestule/candidate_reranker.git /kaggle/working/cr",
                   shell=True, check=True)
os.chdir("/kaggle/working/cr")
for f in ("tools/run_refine.sh", "tools/refine.py", "tools/refine_eval.py", "results/cand_audio.pkl"):
    assert os.path.exists(f), f"missing {f}: is it pushed to GitHub?"
print("repo OK, starting the run", flush=True)
subprocess.run("bash tools/run_refine.sh /tmp/campaign_data 2>&1 | tee results/run_refine.log", shell=True)
