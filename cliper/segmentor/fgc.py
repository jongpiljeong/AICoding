"""
FGC — Fine-Grained Correction
==============================
Uses Stable Diffusion UNet decoder features (extracted at a fixed noise
timestep) to correct the coarse CLIP-based segmentation map.

Mechanism:
  For each patch position, we compute the affinity between the SD feature
  at that position and all other positions (non-local means style).  The
  resulting affinity matrix propagates high-confidence coarse predictions
  to neighboring patches that share similar SD features, effectively
  correcting boundary errors and filling holes.

  coarse_map_refined = (1 - alpha) * coarse_map + alpha * affinity @ coarse_map
"""

import torch
import torch.nn.functional as F


def fine_grained_correction(
    coarse_map: torch.Tensor,      # (B, n_classes+1, Hp, Wp)
    sd_feats: torch.Tensor,        # (B, C_sd, Hf, Wf)
    alpha: float = 0.4,
    softmax_temp: float = 0.1,
) -> torch.Tensor:
    """
    Args:
        coarse_map : output of apply_background_threshold, upsampled if needed
        sd_feats   : L2-normalised diffusion UNet features
        alpha      : interpolation weight; 0 = no correction, 1 = full correction

    Returns:
        refined_map: (B, n_classes+1, Hp, Wp)
    """
    B, C_cls, Hp, Wp = coarse_map.shape

    # Align SD feature resolution to coarse map
    if sd_feats.shape[-2:] != (Hp, Wp):
        sd_feats = F.interpolate(sd_feats, size=(Hp, Wp), mode="bilinear", align_corners=False)
        sd_feats = F.normalize(sd_feats, dim=1)

    N = Hp * Wp
    # (B, C_sd, N)
    f = sd_feats.view(B, -1, N)

    # Pairwise cosine affinity (B, N, N)
    f_t = f.permute(0, 2, 1)                           # (B, N, C_sd)
    affinity = torch.bmm(f_t, f) / softmax_temp        # (B, N, N)
    affinity = affinity.softmax(dim=-1)

    # Propagate coarse scores
    cm_flat = coarse_map.view(B, C_cls, N)             # (B, C_cls, N)
    propagated = torch.bmm(cm_flat, affinity)          # (B, C_cls, N)
    propagated = propagated.view(B, C_cls, Hp, Wp)

    refined = (1 - alpha) * coarse_map + alpha * propagated
    return refined
