from pathlib import Path
import numpy as np
from .base_dataset import BaseSegDataset


class PascalVOCDataset(BaseSegDataset):
    """
    Pascal VOC 2012 segmentation val split.
    Expected layout:
      root/
        JPEGImages/*.jpg
        SegmentationClass/*.png
        ImageSets/Segmentation/val.txt
    """

    def _build_sample_list(self):
        split_file = self.root / "ImageSets" / "Segmentation" / f"{self.split}.txt"
        img_dir = self.root / "JPEGImages"
        ann_dir = self.root / "SegmentationClass"
        with open(split_file) as f:
            ids = [l.strip() for l in f if l.strip()]
        for id_ in ids:
            img_path = img_dir / f"{id_}.jpg"
            ann_path = ann_dir / f"{id_}.png"
            if img_path.exists() and ann_path.exists():
                self.samples.append((img_path, ann_path))

    def _load_mask(self, path) -> np.ndarray:
        import numpy as np
        mask = np.array(__import__("PIL").Image.open(path)).astype(np.int32)
        # 255 = void/border → keep as-is (handled by evaluator)
        return mask
