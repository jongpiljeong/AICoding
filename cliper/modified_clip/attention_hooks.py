"""
Forward hooks that intercept ViT transformer block outputs in open_clip.
Each block's output patch tokens (all tokens except the [CLS] token) are
stored for later retrieval by CLIPFeatureExtractor.
"""

from typing import Dict, List, Optional
import torch


class PatchFeatureCollector:
    """
    Registers hooks on a list of ViT transformer blocks and accumulates
    their patch-token outputs (post-LayerNorm or post-Attention).

    Args:
        blocks: list of nn.Module transformer blocks (model.visual.transformer.resblocks)
        layer_indices: which block indices to tap (0-indexed)
        cls_token: whether the first token is a [CLS] token (True for standard ViT)
    """

    def __init__(self, blocks: List, layer_indices: List[int], cls_token: bool = True):
        self.cls_token = cls_token
        self.layer_indices = set(layer_indices)
        self._features: Dict[int, torch.Tensor] = {}
        self._hooks = []

        for idx, block in enumerate(blocks):
            if idx in self.layer_indices:
                handle = block.register_forward_hook(self._make_hook(idx))
                self._hooks.append(handle)

    def _make_hook(self, idx: int):
        def hook(module, input, output):
            # output shape: (seq_len, batch, dim) for open_clip pre-permute
            # or (batch, seq_len, dim) depending on version
            feat = output
            if isinstance(feat, tuple):
                feat = feat[0]
            # Normalize to (batch, seq_len, dim)
            if feat.shape[0] != feat.shape[1] and feat.dim() == 3:
                if feat.shape[1] < feat.shape[0]:
                    feat = feat.permute(1, 0, 2)
            # Drop CLS token
            patch_feat = feat[:, 1:, :] if self.cls_token else feat
            self._features[idx] = patch_feat.detach()
        return hook

    def get_features(self) -> Dict[int, torch.Tensor]:
        return dict(self._features)

    def clear(self):
        self._features.clear()

    def remove(self):
        for h in self._hooks:
            h.remove()
        self._hooks.clear()
