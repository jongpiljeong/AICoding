"""
Self-contained mIoU implementation — no mmcv dependency required.

Computes per-class IoU and mean IoU from accumulated confusion matrices.
"""
from __future__ import annotations

import numpy as np
import torch


class MeanIoU:
    """
    Streaming mIoU accumulator.

    Args:
        num_classes: total number of semantic classes (including background).
        ignore_index: label value to exclude from evaluation.
    """

    def __init__(self, num_classes: int, ignore_index: int = 255) -> None:
        self.num_classes = num_classes
        self.ignore_index = ignore_index
        self._conf = np.zeros((num_classes, num_classes), dtype=np.int64)

    def update(
        self,
        pred: "np.ndarray | torch.Tensor",
        gt: "np.ndarray | torch.Tensor",
    ) -> None:
        """
        Accumulate one prediction/ground-truth pair.

        Args:
            pred: predicted class map [H, W] (int).
            gt:   ground-truth class map [H, W] (int).
        """
        if isinstance(pred, torch.Tensor):
            pred = pred.cpu().numpy()
        if isinstance(gt, torch.Tensor):
            gt = gt.cpu().numpy()

        pred = pred.astype(np.int64).ravel()
        gt = gt.astype(np.int64).ravel()

        # Mask out ignored pixels
        valid = gt != self.ignore_index
        pred = pred[valid]
        gt = gt[valid]

        # Clamp predictions to valid range
        pred = np.clip(pred, 0, self.num_classes - 1)

        # Accumulate into confusion matrix via bincount trick
        k = self.num_classes
        self._conf += np.bincount(k * gt + pred, minlength=k * k).reshape(k, k)

    def compute(self) -> dict:
        """
        Compute IoU statistics from the accumulated confusion matrix.

        Returns:
            dict with keys:
              "iou_per_class": np.ndarray [num_classes]
              "miou": float
              "acc_per_class": np.ndarray [num_classes]
              "macc": float
              "fwiou": float  (frequency-weighted IoU)
        """
        conf = self._conf.astype(np.float64)
        tp = np.diag(conf)
        sum_pred = conf.sum(axis=0)  # column sums
        sum_gt = conf.sum(axis=1)    # row sums
        denom = sum_pred + sum_gt - tp

        iou = np.where(denom > 0, tp / denom, np.nan)
        miou = float(np.nanmean(iou))

        acc = np.where(sum_gt > 0, tp / sum_gt, np.nan)
        macc = float(np.nanmean(acc))

        freq = sum_gt / sum_gt.sum()
        fwiou = float(np.nansum(freq * iou))

        return {
            "iou_per_class": iou,
            "miou": miou,
            "acc_per_class": acc,
            "macc": macc,
            "fwiou": fwiou,
        }

    def reset(self) -> None:
        self._conf[:] = 0
