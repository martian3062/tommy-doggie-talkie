"""Fine-tune the Tommy Doggie Talkie breed classifier on a Kaggle GPU.

Designed to run as a Kaggle script kernel with the Stanford Dogs dataset
attached (jessicali9530/stanford-dogs-dataset). The kernel is pushed and
monitored from the repo with training/kaggle_train.ps1.

Local smoke test (needs torch + torchvision installed):

    python train.py --data-dir path/to/Images --warmup-epochs 1 --epochs 1 \
        --limit-per-class 8 --batch-size 8 --workers 0

Outputs written to /kaggle/working (or --output-dir):
    breed_model.torchscript.pt  CPU TorchScript model loaded by the Litestar backend
    labels.json                 class index -> breed display name
    metrics.json                config, per-epoch history, best validation scores
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

import torch


def ensure_torch_supports_gpu() -> None:
    """Kaggle sometimes assigns a P100 (sm_60) that the image's torch build dropped.

    The cu118 wheels still ship sm_60 kernels, so install them once and re-exec.
    """
    if not torch.cuda.is_available():
        return
    major, minor = torch.cuda.get_device_capability(0)
    if f"sm_{major}{minor}" in torch.cuda.get_arch_list():
        return
    if os.environ.get("TOMMY_TORCH_REINSTALLED") == "1":
        print(f"WARNING: GPU sm_{major}{minor} still unsupported after reinstall; continuing anyway.")
        return
    print(
        f"GPU sm_{major}{minor} not in torch {torch.__version__} arch list "
        f"{torch.cuda.get_arch_list()}; installing cu118 wheels..."
    )
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "--quiet",
            "torch==2.6.0+cu118", "torchvision==0.21.0+cu118",
            "--index-url", "https://download.pytorch.org/whl/cu118",
        ],
        check=True,
    )
    os.environ["TOMMY_TORCH_REINSTALLED"] = "1"
    print("Reinstalled torch for this GPU; restarting the script.")
    sys.stdout.flush()
    os.execv(sys.executable, [sys.executable, *sys.argv])


ensure_torch_supports_gpu()

import numpy as np
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

SEED = 42
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune a dog breed classifier.")
    parser.add_argument("--data-dir", type=str, default=None, help="Directory of per-breed image folders")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--warmup-epochs", type=int, default=3, help="Head-only warmup epochs")
    parser.add_argument("--epochs", type=int, default=12, help="Fine-tune epochs (layer4 + head)")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--img-size", type=int, default=224)
    parser.add_argument("--val-fraction", type=float, default=0.15)
    parser.add_argument("--head-lr", type=float, default=1e-3)
    parser.add_argument("--fine-lr", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--label-smoothing", type=float, default=0.1)
    parser.add_argument("--patience", type=int, default=5, help="Early-stop patience on val top-1")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit-per-class", type=int, default=0, help="Debug: cap images per class")
    return parser.parse_args()


def resolve_data_dir(cli_value: str | None) -> Path:
    if cli_value:
        path = Path(cli_value)
        if path.exists():
            return path
        raise SystemExit(f"--data-dir does not exist: {path}")
    known = Path("/kaggle/input/stanford-dogs-dataset/images/Images")
    if known.exists():
        return known
    kaggle_input = Path("/kaggle/input")
    if kaggle_input.exists():
        for images_dir in kaggle_input.rglob("Images"):
            if images_dir.is_dir() and any(child.is_dir() for child in images_dir.iterdir()):
                return images_dir
    raise SystemExit("Dataset not found. Attach stanford-dogs-dataset or pass --data-dir.")


def display_name(class_dir_name: str) -> str:
    # Stanford Dogs folders look like "n02106662-German_shepherd".
    name = class_dir_name.split("-", 1)[1] if "-" in class_dir_name else class_dir_name
    return name.replace("_", " ").strip().title()


def build_samples(
    data_dir: Path, val_fraction: float, limit_per_class: int
) -> tuple[list[tuple[Path, int]], list[tuple[Path, int]], list[str]]:
    class_dirs = sorted(d for d in data_dir.iterdir() if d.is_dir())
    if not class_dirs:
        raise SystemExit(f"No class folders found under {data_dir}")
    labels = [display_name(d.name) for d in class_dirs]
    rng = random.Random(SEED)
    train_samples: list[tuple[Path, int]] = []
    val_samples: list[tuple[Path, int]] = []
    for class_index, class_dir in enumerate(class_dirs):
        files = sorted(
            f for f in class_dir.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS
        )
        if limit_per_class > 0:
            files = files[:limit_per_class]
        rng.shuffle(files)
        val_count = max(1, int(len(files) * val_fraction)) if len(files) > 1 else 0
        val_samples.extend((f, class_index) for f in files[:val_count])
        train_samples.extend((f, class_index) for f in files[val_count:])
    rng.shuffle(train_samples)
    return train_samples, val_samples, labels


class BreedDataset(Dataset):
    def __init__(self, samples: list[tuple[Path, int]], transform) -> None:
        self.samples = samples
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int):
        path, label = self.samples[index]
        image = Image.open(path).convert("RGB")
        return self.transform(image), label


def build_model(num_classes: int) -> tuple[nn.Module, bool]:
    try:
        model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
        pretrained = True
    except Exception as exc:  # no internet in the kernel, still train
        print(f"WARNING: pretrained weights unavailable ({exc}); training from scratch.")
        model = models.resnet50(weights=None)
        pretrained = False
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model, pretrained


def set_trainable(model: nn.Module, head_only: bool) -> None:
    for name, param in model.named_parameters():
        if head_only:
            param.requires_grad = name.startswith("fc.")
        else:
            param.requires_grad = name.startswith("fc.") or name.startswith("layer4.")


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, criterion, device: torch.device, use_amp: bool):
    model.eval()
    total = 0
    top1 = 0
    top3 = 0
    loss_sum = 0.0
    for images, targets in loader:
        images = images.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)
        with torch.amp.autocast("cuda", enabled=use_amp):
            outputs = model(images)
            loss = criterion(outputs, targets)
        loss_sum += float(loss) * targets.size(0)
        total += targets.size(0)
        top_indices = outputs.topk(min(3, outputs.size(1)), dim=1).indices
        hits = top_indices.eq(targets.unsqueeze(1))
        top1 += int(hits[:, 0].sum())
        top3 += int(hits.any(dim=1).sum())
    return loss_sum / max(total, 1), top1 / max(total, 1), top3 / max(total, 1)


def train_one_epoch(model, loader, criterion, optimizer, scaler, device, use_amp) -> float:
    model.train()
    loss_sum = 0.0
    total = 0
    for images, targets in loader:
        images = images.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)
        optimizer.zero_grad(set_to_none=True)
        with torch.amp.autocast("cuda", enabled=use_amp):
            outputs = model(images)
            loss = criterion(outputs, targets)
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        loss_sum += float(loss) * targets.size(0)
        total += targets.size(0)
    return loss_sum / max(total, 1)


def main() -> None:
    args = parse_args()
    set_seed()
    torch.backends.cudnn.benchmark = True

    data_dir = resolve_data_dir(args.data_dir)
    output_dir = Path(args.output_dir) if args.output_dir else (
        Path("/kaggle/working") if Path("/kaggle/working").exists() else Path("./outputs")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = device.type == "cuda"
    gpu_count = torch.cuda.device_count() if use_amp else 0
    print(f"data: {data_dir}")
    print(f"device: {device} (gpus={gpu_count})")

    train_samples, val_samples, labels = build_samples(
        data_dir, args.val_fraction, args.limit_per_class
    )
    print(f"classes: {len(labels)}, train images: {len(train_samples)}, val images: {len(val_samples)}")

    train_transform = transforms.Compose(
        [
            transforms.RandomResizedCrop(args.img_size, scale=(0.6, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.15),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
    val_transform = transforms.Compose(
        [
            transforms.Resize(int(args.img_size * 256 / 224)),
            transforms.CenterCrop(args.img_size),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
    loader_kwargs = dict(
        num_workers=args.workers,
        pin_memory=use_amp,
        persistent_workers=args.workers > 0,
    )
    train_loader = DataLoader(
        BreedDataset(train_samples, train_transform),
        batch_size=args.batch_size,
        shuffle=True,
        drop_last=False,
        **loader_kwargs,
    )
    val_loader = DataLoader(
        BreedDataset(val_samples, val_transform),
        batch_size=args.batch_size,
        shuffle=False,
        **loader_kwargs,
    )

    raw_model, pretrained = build_model(len(labels))
    raw_model.to(device)
    model: nn.Module = nn.DataParallel(raw_model) if gpu_count > 1 else raw_model

    criterion = nn.CrossEntropyLoss(label_smoothing=args.label_smoothing)
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    history: list[dict] = []
    best = {"val_top1": 0.0, "val_top3": 0.0, "epoch": 0, "phase": ""}
    best_state: dict | None = None
    epochs_without_improvement = 0

    def run_phase(phase: str, epochs: int, optimizer, scheduler=None) -> bool:
        nonlocal best, best_state, epochs_without_improvement
        for epoch in range(1, epochs + 1):
            started = time.time()
            train_loss = train_one_epoch(
                model, train_loader, criterion, optimizer, scaler, device, use_amp
            )
            val_loss, val_top1, val_top3 = evaluate(model, val_loader, criterion, device, use_amp)
            if scheduler is not None:
                scheduler.step()
            lr = optimizer.param_groups[0]["lr"]
            seconds = round(time.time() - started, 1)
            record = {
                "phase": phase,
                "epoch": epoch,
                "train_loss": round(train_loss, 4),
                "val_loss": round(val_loss, 4),
                "val_top1": round(val_top1, 4),
                "val_top3": round(val_top3, 4),
                "lr": lr,
                "seconds": seconds,
            }
            history.append(record)
            print(
                f"[{phase} {epoch}/{epochs}] train_loss={train_loss:.4f} "
                f"val_loss={val_loss:.4f} top1={val_top1:.4f} top3={val_top3:.4f} "
                f"lr={lr:.2e} ({seconds}s)"
            )
            if val_top1 > best["val_top1"]:
                best = {
                    "val_top1": round(val_top1, 4),
                    "val_top3": round(val_top3, 4),
                    "epoch": epoch,
                    "phase": phase,
                }
                best_state = copy.deepcopy(raw_model.state_dict())
                epochs_without_improvement = 0
            else:
                epochs_without_improvement += 1
                if phase == "finetune" and epochs_without_improvement >= args.patience:
                    print(f"Early stop: no val top-1 gain for {args.patience} epochs.")
                    return False
        return True

    if args.warmup_epochs > 0:
        set_trainable(raw_model, head_only=True)
        head_params = [p for p in raw_model.parameters() if p.requires_grad]
        warmup_optimizer = torch.optim.AdamW(
            head_params, lr=args.head_lr, weight_decay=args.weight_decay
        )
        run_phase("warmup", args.warmup_epochs, warmup_optimizer)

    set_trainable(raw_model, head_only=False)
    epochs_without_improvement = 0
    fine_optimizer = torch.optim.AdamW(
        [
            {"params": raw_model.layer4.parameters(), "lr": args.fine_lr},
            {"params": raw_model.fc.parameters(), "lr": args.fine_lr * 3},
        ],
        weight_decay=args.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(fine_optimizer, T_max=args.epochs)
    run_phase("finetune", args.epochs, fine_optimizer, scheduler)

    if best_state is not None:
        raw_model.load_state_dict(best_state)
    raw_model.cpu().eval()

    with torch.no_grad():
        traced = torch.jit.trace(raw_model, torch.zeros(1, 3, args.img_size, args.img_size))
    traced.save(str(output_dir / "breed_model.torchscript.pt"))
    (output_dir / "labels.json").write_text(json.dumps(labels, indent=2), encoding="utf-8")
    metrics = {
        "dataset": str(data_dir),
        "num_classes": len(labels),
        "train_images": len(train_samples),
        "val_images": len(val_samples),
        "pretrained_backbone": pretrained,
        "img_size": args.img_size,
        "normalization": {"mean": IMAGENET_MEAN, "std": IMAGENET_STD},
        "best": best,
        "history": history,
        "config": vars(args),
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved TorchScript model, labels.json, metrics.json to {output_dir}")
    print(f"Best: top1={best['val_top1']} top3={best['val_top3']} ({best['phase']} epoch {best['epoch']})")


if __name__ == "__main__":
    main()
