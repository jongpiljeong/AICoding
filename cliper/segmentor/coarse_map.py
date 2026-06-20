"""
Coarse segmentation map generation
====================================
Computes patch-level cosine similarity between ELF-enhanced CLIP patch
features and text embeddings to produce a per-class score map.

Output: (B, n_classes, Hp, Wp)  — raw logits before final upsampling.
"""

import torch
import torch.nn.functional as F


def compute_coarse_map(
    patch_feats: torch.Tensor,      # (B, D, Hp, Wp)  L2-normed
    text_embs: torch.Tensor,        # (n_classes, D)  L2-normed
    temperature: float = 0.07,
) -> torch.Tensor:
    """
    Returns:
        sim_map: (B, n_classes, Hp, Wp)
    """
    B, D, Hp, Wp = patch_feats.shape
    n_cls = text_embs.shape[0]

    # (B, D, N_patches)
    patches = patch_feats.view(B, D, -1)                      # (B, D, N)
    text = text_embs.unsqueeze(0).expand(B, -1, -1)           # (B, C, D)

    # cosine sim: (B, C, N)
    sim = torch.bmm(text, patches) / temperature
    sim = sim.view(B, n_cls, Hp, Wp)
    return sim


def apply_background_threshold(
    sim_map: torch.Tensor,         # (B, n_classes, Hp, Wp)
    bg_threshold: float = 0.45,
) -> torch.Tensor:
    """
    Prepend a background channel whose score is a constant bg_threshold.
    Argmax then naturally assigns patches below threshold to background.

    Returns:
        (B, n_classes + 1, Hp, Wp)
    """
    B, C, Hp, Wp = sim_map.shape
    bg = torch.full((B, 1, Hp, Wp), bg_threshold, device=sim_map.device, dtype=sim_map.dtype)
    return torch.cat([bg, sim_map], dim=1)
