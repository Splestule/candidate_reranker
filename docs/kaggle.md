# Kaggle notes

Quota counts session time with an accelerator attached, not compute.

- `kaggle_prepare_data.ipynb` runs once with **Accelerator: None** and downloads the
  checkpoints and LibriSpeech into its output. Other notebooks attach that output.
- `kaggle_run.ipynb` needs GPU T4 x2, internet, and that output attached. Set `REPO_URL`.
- Iterating: commit, push, rerun the `K.sync` cell.
- After starting a commit run, stop the interactive session or both burn quota.
- Changing the accelerator restarts the container and wipes `/kaggle/working`.
- Never download into `/kaggle/working`; everything there is saved as the version output.
  Data belongs in `/kaggle/input`, results in `/kaggle/working/results`.

Private repo: add a fine-grained token with Contents: Read as the Kaggle secret
`GITHUB_TOKEN`. `kaggle_env.sync` uses it when present.

CLI, once the browser gets old:

```bash
pip3 install --user kaggle      # token from Settings -> API into ~/.kaggle/kaggle.json
kaggle kernels push -p kaggle/
kaggle kernels output <user>/<slug> -p results/
```
