"""
CLIPer inference entry point.

Usage:
    python infer.py --config configs/voc21_vitb16.yaml
    python infer.py --config configs/ade20k_vitl14.yaml --save-vis
"""
import argparse
import os
import sys

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from utils.config import load_config
from utils import save_prediction
from segmentor import CLIPer
from datasets_loader import build_dataset
from eval import MeanIoU


def parse_args():
    p = argparse.ArgumentParser(description="CLIPer inference")
    p.add_argument("--config", required=True, help="Path to YAML config file")
    p.add_argument("--save-vis", action="store_true", help="Save colourised predictions")
    p.add_argument(
        "--classnames",
        default=None,
        help="Path to classnames txt (overrides config)",
    )
    return p.parse_args()


def load_classnames(path: str):
    with open(path) as f:
        return [l.strip() for l in f if l.strip()]


def main():
    args = parse_args()
    cfg = load_config(args.config)

    # Load class names
    cn_path = args.classnames or cfg["dataset"]["classnames_file"]
    classnames = load_classnames(cn_path)
    num_classes = cfg["dataset"]["num_classes"]
    assert len(classnames) == num_classes, (
        f"classnames count {len(classnames)} != num_classes {num_classes}"
    )

    # Dataset & loader
    dataset = build_dataset(cfg)
    loader = DataLoader(
        dataset,
        batch_size=1,
        num_workers=cfg.get("num_workers", 4),
        collate_fn=lambda x: x[0],  # return single (image, gt, meta) tuple
    )

    # Model
    model = CLIPer(cfg)
    model.set_classnames(classnames)

    # Metric
    metric = MeanIoU(
        num_classes=num_classes,
        ignore_index=cfg["dataset"].get("ignore_index", 255),
    )

    output_dir = cfg.get("output_dir", "outputs")
    save_vis = args.save_vis or cfg.get("save_vis", False)

    for image, gt_mask, meta in tqdm(loader, desc="Inference"):
        pred = model.predict(image)  # [H, W] int64 tensor

        metric.update(pred, gt_mask)

        if save_vis:
            stem = os.path.splitext(os.path.basename(meta["img_path"]))[0]
            out_path = os.path.join(output_dir, "vis", f"{stem}.png")
            save_prediction(pred, out_path)

    results = metric.compute()
    print(f"\n=== Results ({cfg['dataset']['name']}) ===")
    print(f"mIoU  : {results['miou']*100:.2f}%")
    print(f"mAcc  : {results['macc']*100:.2f}%")
    print(f"fwIoU : {results['fwiou']*100:.2f}%")

    # Per-class table
    print("\nPer-class IoU:")
    for i, (name, iou) in enumerate(zip(classnames, results["iou_per_class"])):
        if not (iou != iou):  # skip NaN
            print(f"  [{i:3d}] {name:<30s} {iou*100:.2f}%")

    model.close()


if __name__ == "__main__":
    main()
