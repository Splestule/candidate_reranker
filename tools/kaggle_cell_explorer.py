# Kaggle: GPU T4 x2, internet ON, no input dataset needed -- everything comes from GitHub.
# Runs the explorer proof of concept (tools/run_explorer.sh); results in results/explorer_all.tar.gz.
import os, subprocess

if not os.path.isdir("/kaggle/working/cr"):
    subprocess.run("git clone -q https://github.com/Splestule/candidate_reranker.git /kaggle/working/cr",
                   shell=True, check=True)
os.chdir("/kaggle/working/cr")
for f in ("tools/run_explorer.sh", "tools/train_explorer.py", "tools/explorer_eval.py", "src/lora.py",
          "docs/explorer_poc.md"):
    assert os.path.exists(f), f"missing {f}: is it pushed to GitHub?"
assert "_decode_mixed" in open("src/campaign/families.py").read(), "families.py without the explorer arms"
print("repo OK, starting the run", flush=True)
subprocess.run("bash tools/run_explorer.sh /tmp/campaign_data 2>&1 | tee results/run_explorer.log", shell=True)
