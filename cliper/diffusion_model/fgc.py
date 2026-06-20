"""
Fine-Grained Calibration (FGC).

Takes the coarse segmentation logit map from ELF and refines it by blending
with SD cross-attention features.  The calibration is purely multiplicative /
additive — no learned weights — keeping the pipeline training-free.
"""
from __future__ import annotations

import torch
import torch.nn.functional as F


class FineGrainedCalibration:
    """
    Args:
        alpha: weight for SD attention contribution in the blending formula.
               CLIPer paper uses alpha=0.5 as default.
        temperature: softmax temperature applied to coarse logits before blend.
    """

    def __init__(self, alpha: float = 0.5, temperature: float = 1.0) -> None:
        self.alpha = alpha
        self.temperature = temperature

    def calibrate(
        self,
        coarse_logits: torch.Tensor,
        sd_attn: torch.Tensor,
    ) -> torch.Tensor:
        """
        Blend coarse CLIP logits with SD cross-attention maps.

        Args:
            coarse_logits: [C, H, W]  (raw cosine similarity per class).
            sd_attn:        [C, H, W]  (normalised SD cross-attention maps).

        Returns:
            refined_logits: [C, H, W]
        """
        assert coarse_logits.shape == sd_attn.shape, (
            f"Shape mismatch: {coarse_logits.shape} vs {sd_attn.shape}"
        )

        # Normalise SD maps to [0,1] per-class
        sd_norm = self._minmax_norm(sd_attn)

        # Soft coarse probabilities
        coarse_prob = F.softmax(coarse_logits / self.temperature, dim=0)

        # Blend: refined = (1-α)·coarse_prob + α·sd_norm, then re-weight
        blended = (1.0 - self.alpha) * coarse_prob + self.alpha * sd_norm

        # Convert back to log-space for consistent downstream argmax
        refined = torch.log(blended.clamp(min=1e-8))
        return refined

    @staticmethod
    def _minmax_norm(x: torch.Tensor) -> torch.Tensor:
        """Per-class min-max normalisation → [0, 1]."""
        C = x.shape[0]
        flat = x.reshape(C, -1)
        mn = flat.min(dim=1).values[:, None, None]
        mx = flat.max(dim=1).values[:, None, None]
        return (x - mn) / (mx - mn + 1e-8)
