from __future__ import annotations
import os
from typing import Tuple

import numpy as np
from PIL import Image

from .base_dataset import BaseSegDataset


class ADE20KDataset(BaseSegDataset):
    """ADE20K dataset.

    Expected layout:
        root/
          images/validation/
          annotations/validation/  (*.png, uint8; 0=void, 1..150=classes)

    The ignore_index for ADE20K is 0 (void), not 255.
    Class IDs in GT are 1-indexed; shift by -1 before mIoU to get 0-indexed.
    """

    def _load_file_list(self) -> list:
        img_dir = os.path.join(self.root, "images", self.split)
        ann_dir = os.path.join(self.root, "annotations", self.split)
        pairs = []
        for fname in sorted(os.listdir(img_dir)):
            if not fname.endswith(".jpg"):
                continue
            stem = fname[:-4]
            img = os.path.join(img_dir, fname)
            gt = os.path.join(ann_dir, f"{stem}.png")
            if os.path.exists(gt):
                pairs.append((img, gt))
        return pairs

    def __getitem__(self, idx: int) -> Tuple[Image.Image, np.ndarray, dict]:
        img_path, gt_path = self.file_list[idx]
        image = Image.open(img_path).convert("RGB")
        # ADE20K GT: 0=void, 1..150=semantic classes
        gt = np.array(Image.open(gt_path)).astype(np.int32) - 1
        # After shift: -1=void (→ set to ignore_index), 0..149=classes
        gt[gt == -1] = self.ignore_index
        return image, gt, {"img_path": img_path}
