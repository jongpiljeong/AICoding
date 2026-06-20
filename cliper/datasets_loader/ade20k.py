from pathlib import Path
from .base_dataset import BaseSegDataset


class ADE20KDataset(BaseSegDataset):
    """
    ADE20K validation split.
    Expected layout:
      root/
        images/validation/*.jpg
        annotations/validation/*.png   (1-indexed labels; 0 = background)
    """

    def _build_sample_list(self):
        img_dir = self.root / "images" / self.split
        ann_dir = self.root / "annotations" / self.split
        for img_path in sorted(img_dir.glob("*.jpg")):
            ann_path = ann_dir / (img_path.stem + ".png")
            if ann_path.exists():
                self.samples.append((img_path, ann_path))
