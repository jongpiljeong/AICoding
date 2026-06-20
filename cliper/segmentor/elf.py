"""
ELF — Edge-guided Local Feature enhancement
============================================
Computes Sobel edge maps from the input image and uses them as
spatial attention weights to sharpen the fused CLIP patch features
near object boundaries.

High-gradient regions → amplify local patch features.
Low-gradient regions  → suppress (smooth background tokens).
"""

import torch
import torch.nn.functional as F


def _sobel_edges(gray: torch.Tensor) -> torch.Tensor:
    """
    Args:
        gray: (B, 1, H, W)  values in [0, 1]

    Returns:
        edge_map: (B, 1, H, W)  in [0, 1]
    """
    kx = torch.tensor([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
                      dtype=gray.dtype, device=gray.device).view(1, 1, 3, 3)
    ky = kx.transpose(-1, -2)
    gx = F.conv2d(gray, kx, padding=1)
    gy = F.conv2d(gray, ky, padding=1)
    mag = (gx ** 2 + gy ** 2).sqrt()
    # normalise per image
    B = mag.shape[0]
    mag_flat = mag.view(B, -1)
    mn = mag_flat.min(dim=1).values.view(B, 1, 1, 1)
    mx = mag_flat.max(dim=1).values.view(B, 1, 1, 1)
    return (mag - mn) / (mx - mn + 1e-6)


def enhance_local_features(
    clip_feats: torch.Tensor,       # (B, D, Hp, Wp)
    image_rgb: torch.Tensor,        # (B, 3, H, W)   in [0, 1]
    edge_weight: float = 1.5,
) -> torch.Tensor:
    """
    Amplify CLIP patch features at edge positions.

    Returns:
        enhanced: (B, D, Hp, Wp)  L2-normalised
    """
    B, D, Hp, Wp = clip_feats.shape

    # grayscale from RGB
    gray = (image_rgb * torch.tensor([0.2989, 0.5870, 0.1140],
                                      device=image_rgb.device).view(1, 3, 1, 1)).sum(dim=1, keepdim=True)
    edge_map = _sobel_edges(gray)   # (B, 1, H, W)

    # Downsample edge map to patch grid
    edge_patch = F.adaptive_avg_pool2d(edge_map, (Hp, Wp))   # (B, 1, Hp, Wp)

    # Spatial weighting: w ∈ [1, edge_weight]
    w = 1.0 + (edge_weight - 1.0) * edge_patch
    enhanced = clip_feats * w

    enhanced = F.normalize(enhanced, dim=1)
    return enhanced
