# Kaggle: GPU T4 x2, internet ON, no input dataset needed -- everything comes from GitHub
import os, subprocess

if not os.path.isdir("/kaggle/working/cr"):
    subprocess.run("git clone -q https://github.com/Splestule/candidate_reranker.git /kaggle/working/cr",
                   shell=True, check=True)
os.chdir("/kaggle/working/cr")
for f in ("tools/run_kaggle_all.sh", "tools/treek_eval.py", "tools/cand_audio.py", "tools/final_compare.py"):
    assert os.path.exists(f), f"missing {f}: is it pushed to GitHub?"
assert "treek" in open("src/campaign/run.py").read(), "src/campaign/run.py without the treek plan"
print("repo OK, starting the run", flush=True)
subprocess.run("bash tools/run_kaggle_all.sh /tmp/campaign_data 2>&1 | tee results/run_all.log", shell=True)
