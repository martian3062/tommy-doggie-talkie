# Training on Kaggle GPU

Model training for Tommy Doggie Talkie runs on Kaggle's free GPU kernels instead of the
local machine. Each trainable subtask lives under `training/kaggle/<subtask>/` as a
self-contained Kaggle script kernel: a `train.py` plus a `kernel-metadata.json` that pins
the dataset, GPU flag, and kernel slug.

The first (and currently only) subtask is the **breed classifier**: ResNet50 fine-tuned on
the Stanford Dogs dataset (120 breeds), which replaces the remote
`djhua0103/dog-breed-resnet50` Hugging Face call in the backend once its weights are
downloaded.

## One-time setup

Already done on this machine, listed for reference:

1. Generate a Kaggle API token (Settings -> API Tokens). The new `KGAT_...` token is saved at
   `~/.kaggle/access_token` (used by kagglehub) and also as the `key` in `~/.kaggle/kaggle.json`
   (used by the kaggle CLI).
2. `python -m pip install kaggle kagglehub`
3. The Kaggle account needs phone verification for GPU + internet access in kernels.

Never commit tokens; both files live outside the repository.

## Workflow

```powershell
.\training\kaggle_train.ps1 push     # upload train.py and start the GPU run
.\training\kaggle_train.ps1 status   # one-shot status check
.\training\kaggle_train.ps1 watch    # poll every 60s until complete/error
.\training\kaggle_train.ps1 output   # download outputs into backend\models\breed
```

`push` re-uploads the current `train.py` and immediately queues a fresh run on a Kaggle GPU;
pushing again while a run is active cancels-and-replaces it. Runs are also visible at
`https://www.kaggle.com/code/pardeep3062/tommy-breed-classifier-train`.

## What the run produces

| File | Purpose |
|---|---|
| `breed_model.torchscript.pt` | CPU TorchScript model; the backend loads it with plain `torch.jit.load` |
| `labels.json` | Class index -> breed display name (120 entries) |
| `metrics.json` | Config, per-epoch history, best validation top-1/top-3 |

After `output`, the files sit in `backend/models/breed/` (gitignored). The backend's breed
detection tries, in order:

1. Local Kaggle-trained TorchScript model (`BREED_MODEL_DIR`, default `./models/breed`)
2. Hugging Face `djhua0103/dog-breed-resnet50` pipeline
3. Filename/context heuristic fallback

Restart the backend after downloading new weights; the model is cached after first load.

## Training recipe

- ResNet50, ImageNet-pretrained, 85/15 stratified split per breed.
- Phase 1: head-only warmup (3 epochs, AdamW lr 1e-3).
- Phase 2: unfreeze `layer4` + head (12 epochs, cosine schedule, lr 1e-4/3e-4,
  label smoothing 0.1, early stop after 5 epochs without val top-1 gain).
- Mixed precision on GPU; uses both GPUs via DataParallel when Kaggle assigns a T4 x2.
- Best checkpoint by validation top-1 is what gets exported.

Local smoke test (needs `torch` + `torchvision`):

```powershell
python training\kaggle\breed_classifier\train.py --data-dir path\to\Images `
    --warmup-epochs 1 --epochs 1 --limit-per-class 8 --batch-size 8 --workers 0
```

## Adding the next subtask (e.g. bark/sound classifier)

1. Copy `training/kaggle/breed_classifier/` to `training/kaggle/<new_subtask>/`.
2. Point `kernel-metadata.json` at a new kernel slug and the audio dataset.
3. Extend `kaggle_train.ps1` or run the kaggle CLI directly against the new folder.

## Notes

- Kaggle free tier: ~30 GPU hours/week; the breed run takes roughly 15-30 minutes.
- The kernels-push API cannot choose the accelerator. If Kaggle assigns a P100 (sm_60),
  the preinstalled PyTorch build no longer supports it; `train.py` detects this, installs
  the cu118 torch/torchvision wheels (~3 min), and restarts itself automatically.
- Stanford Dogs is distributed for research; review dataset and base-model licenses before
  any commercial release (see README "Security and Product Boundaries").
- Model selection still follows `docs/model-subtasks.md`: validate on held-out phone
  photos/videos, not only on Stanford Dogs validation accuracy.
