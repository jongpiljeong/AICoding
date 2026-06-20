from __future__ import annotations
import os
from typing import Tuple

import numpy as np
from PIL import Image

from .base_dataset import BaseSegDataset


class VOCDataset(BaseSegDataset):
    """PASCAL VOC 2012 segmentation dataset (val split)."""

    def _load_file_list(self) -> list:
        split_file = os.path.join(
            self.root, "ImageSets", "Segmentation", f"{self.split}.txt"
        )
        with open(split_file) as f:
            names = [l.strip() for l in f if l.strip()]
        pairs = []
        for n in names:
            img = os.path.join(self.root, "JPEGImages", f"{n}.jpg")
            gt = os.path.join(self.root, "SegmentationClass", f"{n}.png")
            pairs.append((img, gt))
        return pairs

    def __getitem__(self, idx: int) -> Tuple[Image.Image, np.ndarray, dict]:
        img_path, gt_path = self.file_list[idx]
        image = Image.open(img_path).convert("RGB")
        gt = np.array(Image.open(gt_path))  # palette PNG; values are class IDs
        # VOC palette PNG: void class = 255; keep as-is
        return image, gt, {"img_path": img_path}
