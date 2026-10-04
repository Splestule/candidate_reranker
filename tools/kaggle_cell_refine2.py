# Kaggle: GPU T4 x2, internet ON, no input dataset needed -- everything comes from GitHub.
# Runs refine run 2 (tools/run_refine2.sh); results in results/refine2_all.tar.gz (Output tab).
import os, subprocess

BRANCH = "claude/busy-johnson-2cglu7"
if not os.path.isdir("/kaggle/working/cr"):
    subprocess.run(f"git clone -q -b {BRANCH} https://github.com/Splestule/candidate_reranker.git /kaggle/working/cr",
                   shell=True, check=True)
os.chdir("/kaggle/working/cr")
for f in ("tools/run_refine2.sh", "tools/refine.py", "tools/refine_eval.py", "tools/loop_decode.py",
          "tools/train_refiner.py", "tools/gpt_slots.py", "results/cand_audio.pkl"):
    assert os.path.exists(f), f"missing {f}: is it pushed to GitHub?"
print("repo OK, starting the run", flush=True)
subprocess.run("bash tools/run_refine2.sh /tmp/campaign_data 2>&1 | tee results/run_refine2.log", shell=True)
# keep the results where Kaggle's Output tab shows them
subprocess.run("cp results/refine2_all.tar.gz /kaggle/working/ 2>/dev/null; ls -la /kaggle/working", shell=True)
