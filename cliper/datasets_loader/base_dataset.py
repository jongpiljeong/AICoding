from abc import ABC, abstractmethod
from typing import List, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
from torch.utils.data import Dataset


class BaseSegDataset(ABC, Dataset):
    """
    Returns (image: PIL.Image, gt_mask: np.ndarray H×W int32, img_id: str).
    gt_mask uses the dataset's native label encoding; 255 is ignored.
    """

    def __init__(self, cfg: dict):
        self.root = Path(cfg["root"])
        self.split = cfg.get("split", "validation")
        self.categories = self._load_categories(cfg["category_file"])
        self.samples: List[Tuple[Path, Path]] = []  # (image_path, mask_path)
        self._build_sample_list()

    @property
    def num_classes(self) -> int:
        return len(self.categories)

    def _load_categories(self, cat_file: str) -> List[str]:
        with open(cat_file) as f:
            return [line.strip() for line in f if line.strip()]

    @abstractmethod
    def _build_sample_list(self) -> None: ...

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        img_path, mask_path = self.samples[idx]
        image = Image.open(img_path).convert("RGB")
        gt_mask = self._load_mask(mask_path)
        return image, gt_mask, img_path.stem

    def _load_mask(self, path: Path) -> np.ndarray:
        return np.array(Image.open(path)).astype(np.int32)
