from .ade20k import ADE20KDataset
from .pascal_voc import PascalVOCDataset
from .coco_stuff import COCOStuffDataset


def build_dataset(cfg: dict):
    name = cfg["dataset"]["name"]
    if name == "ade20k":
        return ADE20KDataset(cfg["dataset"])
    elif name == "pascal_voc":
        return PascalVOCDataset(cfg["dataset"])
    elif name == "coco_stuff164k":
        return COCOStuffDataset(cfg["dataset"])
    else:
        raise ValueError(f"Unknown dataset: {name}")
