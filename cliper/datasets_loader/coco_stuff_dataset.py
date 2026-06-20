from __future__ import annotations
import os
from typing import Tuple

import numpy as np
from PIL import Image

from .base_dataset import BaseSegDataset


class COCOStuffDataset(BaseSegDataset):
    """COCO-Stuff 164k dataset.

    Expected layout:
        root/
          images/val2017/
          annotations/val2017/   (*.png, uint8, 0-based class IDs, 255=void)
    """

    def _load_file_list(self) -> list:
        img_dir = os.path.join(self.root, "images", f"{self.split}2017")
        ann_dir = os.path.join(self.root, "annotations", f"{self.split}2017")
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
        gt = np.array(Image.open(gt_path)).astype(np.int32)
        return image, gt, {"img_path": img_path}
