"""
Orchestrates evaluation: loops over a dataset, runs CLIPer, accumulates mIoU.
"""
from __future__ import annotations
from typing import List

import torch
from tqdm import tqdm

from .miou import MeanIoU


class Evaluator:
    def __init__(
        self,
        model,          # CLIPer instance
        dataloader,     # torch DataLoader yielding (image_pil, gt_mask, meta)
        num_classes: int,
        ignore_index: int = 255,
        classnames: List[str] = None,
    ) -> None:
        self.model = model
        self.dataloader = dataloader
        self.metric = MeanIoU(num_classes=num_classes, ignore_index=ignore_index)
        if classnames is not None:
            self.model.set_classnames(classnames)

    def run(self) -> dict:
        self.metric.reset()
        for batch in tqdm(self.dataloader, desc="Evaluating"):
            image, gt_mask, _ = batch
            # image is a single PIL Image (batch_size=1 expected)
            pred = self.model.predict(image)   # [H, W] int64
            self.metric.update(pred, gt_mask)

        results = self.metric.compute()
        self._print_results(results)
        return results

    @staticmethod
    def _print_results(results: dict) -> None:
        print(f"mIoU  : {results['miou']*100:.2f}%")
        print(f"mAcc  : {results['macc']*100:.2f}%")
        print(f"fwIoU : {results['fwiou']*100:.2f}%")
