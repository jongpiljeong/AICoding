from typing import List, Tuple
import torch
import torch.nn.functional as F


def upsample_mask(logits: torch.Tensor, target_hw: Tuple[int, int]) -> torch.Tensor:
    """Bilinearly upsample (C, H, W) or (N, C, H, W) logits to target_hw."""
    if logits.dim() == 3:
        logits = logits.unsqueeze(0)
        return F.interpolate(logits, size=target_hw, mode="bilinear", align_corners=False).squeeze(0)
    return F.interpolate(logits, size=target_hw, mode="bilinear", align_corners=False)


def combine_window_preds(
    canvas: torch.Tensor,
    count: torch.Tensor,
    tile_pred: torch.Tensor,
    bbox: Tuple[int, int, int, int],
) -> None:
    """Accumulate tile_pred (C, Ht, Wt) into canvas (C, H, W) in-place."""
    y0, x0, y1, x1 = bbox
    ph, pw = y1 - y0, x1 - x0
    upsampled = upsample_mask(tile_pred, (ph, pw))
    canvas[:, y0:y1, x0:x1] += upsampled
    count[:, y0:y1, x0:x1] += 1


def crop_to_original(tensor: torch.Tensor, pad_hw: Tuple[int, int]) -> torch.Tensor:
    """Remove reflect-padding added by pad_to_multiple."""
    pad_h, pad_w = pad_hw
    h, w = tensor.shape[-2], tensor.shape[-1]
    return tensor[..., : h - pad_h, : w - pad_w] if (pad_h or pad_w) else tensor
