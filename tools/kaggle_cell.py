# Kaggle: GPU T4 x2, internet ON, no input dataset needed -- everything comes from GitHub.
# Runs the confirmation run (tools/run_confirm.sh); results in results/confirm_all.tar.gz.
import os, subprocess

if not os.path.isdir("/kaggle/working/cr"):
    subprocess.run("git clone -q https://github.com/Splestule/candidate_reranker.git /kaggle/working/cr",
                   shell=True, check=True)
os.chdir("/kaggle/working/cr")
for f in ("tools/run_confirm.sh", "tools/confirm_eval.py", "tools/whisper_ref.py",
          "tools/cand_audio.py", "docs/confirm_prereg.md"):
    assert os.path.exists(f), f"missing {f}: is it pushed to GitHub?"
assert "treek_shards" in open("src/campaign/config.py").read(), "config.py without treek_shards"
print("repo OK, starting the run", flush=True)
subprocess.run("bash tools/run_confirm.sh /tmp/campaign_data 2>&1 | tee results/run_confirm.log", shell=True)
