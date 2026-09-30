# Kaggle: GPU T4, internet ON, dataset with kaggle_patch.tar.gz added as input
import glob, os, shutil, subprocess
subprocess.run("git clone -q https://github.com/Splestule/candidate_reranker.git /kaggle/working/cr", shell=True, check=True)
os.chdir("/kaggle/working/cr")
tars = glob.glob("/kaggle/input/**/kaggle_patch.tar.gz", recursive=True)
if tars:
    subprocess.run(["tar", "xzf", tars[0]], check=True)
else:  # Kaggle sometimes unpacks archives on upload
    hit = glob.glob("/kaggle/input/**/tools/final_compare.py", recursive=True)[0]
    shutil.copytree(os.path.dirname(os.path.dirname(hit)), "../Claude outputs", dirs_exist_ok=True)
assert os.path.exists("tools/final_compare.py")
subprocess.run("bash tools/run_kaggle_all.sh /tmp/campaign_data 2>&1 | tee results/run_all.log", shell=True)
