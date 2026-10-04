# Kaggle: GPU T4 x2, internet ON, no input dataset needed -- everything comes from GitHub.
# Runs peer-conditioned denoising (tools/run_pcd.sh); results in pcd_all.tar.gz (Output tab).
import os, subprocess

BRANCH = "claude/busy-johnson-2cglu7"
if not os.path.isdir("/kaggle/working/cr"):
    subprocess.run(f"git clone -q -b {BRANCH} https://github.com/Splestule/candidate_reranker.git /kaggle/working/cr",
                   shell=True, check=True)
os.chdir("/kaggle/working/cr")
for f in ("tools/run_pcd.sh", "tools/pcd.py", "tools/pcd_data.py", "tools/pcd_states.py", "tools/pcd_train.py",
          "tools/pcd_decode.py", "tools/pcd_report.py", "tools/refine_eval.py", "tools/gpt_slots.py",
          "results/cand_audio.pkl"):
    assert os.path.exists(f), f"missing {f}: is it pushed to GitHub?"
print("repo OK, starting the run", flush=True)
subprocess.run("bash tools/run_pcd.sh /tmp/campaign_data 2>&1 | tee results/run_pcd.log", shell=True)
# the results Kaggle's Output tab shows; small enough to push (no adapters, no states)
subprocess.run("cp results/pcd_all.tar.gz /kaggle/working/ 2>/dev/null; ls -la /kaggle/working", shell=True)
