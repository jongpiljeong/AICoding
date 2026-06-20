"""
CLIPFeatureExtractor
====================
Wraps an open_clip ViT model to expose:
  - Hierarchical patch features from intermediate transformer blocks
    (fused from fuse_layer_start to the final block)
  - Frozen text embeddings for a list of category names

The fused feature tensor F ∈ R^(B, N_patches, D) is the key input for
coarse map generation and ELF.
"""

from typing import Dict, List, Optional, Tuple
import torch
import torch.nn.functional as F
import open_clip

from .attention_hooks import PatchFeatureCollector


_BACKBONE_SPECS = {
    "vit-b-16": {"arch": "ViT-B-16", "patch_size": 16, "n_layers": 12},
    "vit-l-14": {"arch": "ViT-L-14", "patch_size": 14, "n_layers": 24},
}


class CLIPFeatureExtractor:
    def __init__(
        self,
        backbone: str = "vit-b-16",
        pretrained: str = "laion2b_s34b_b88k",
        fuse_layer_start: int = 6,
        device: str = "cuda",
    ):
        spec = _BACKBONE_SPECS[backbone]
        self.patch_size = spec["patch_size"]
        self.n_layers = spec["n_layers"]
        self.fuse_layer_start = fuse_layer_start
        self.device = device

        model, _, _ = open_clip.create_model_and_transforms(spec["arch"], pretrained=pretrained)
        model = model.eval().to(device)
        for p in model.parameters():
            p.requires_grad_(False)
        self.model = model
        self.tokenizer = open_clip.get_tokenizer(spec["arch"])

        # tap every block from fuse_layer_start to n_layers-1
        blocks = list(model.visual.transformer.resblocks)
        self._collector = PatchFeatureCollector(
            blocks=blocks,
            layer_indices=list(range(fuse_layer_start, self.n_layers)),
        )

    # ------------------------------------------------------------------
    # Text
    # ------------------------------------------------------------------

    @torch.no_grad()
    def encode_text(self, categories: List[str]) -> torch.Tensor:
        """
        Returns L2-normalised text embeddings (n_classes, D).
        Uses prompt ensemble: 'a photo of a {cls}.' etc.
        """
        templates = [
            "a photo of a {}.",
            "a photo of the {}.",
            "a {} in the scene.",
        ]
        all_embs = []
        for tmpl in templates:
            prompts = [tmpl.format(c) for c in categories]
            tokens = self.tokenizer(prompts).to(self.device)
            emb = self.model.encode_text(tokens)
            emb = F.normalize(emb, dim=-1)
            all_embs.append(emb)
        # average across templates
        text_embs = torch.stack(all_embs, dim=0).mean(dim=0)
        return F.normalize(text_embs, dim=-1)

    # ------------------------------------------------------------------
    # Visual
    # ------------------------------------------------------------------

    @torch.no_grad()
    def encode_image(self, pixel_values: torch.Tensor) -> Tuple[torch.Tensor, Dict[int, torch.Tensor]]:
        """
        Args:
            pixel_values: (B, 3, H, W) normalised tensor

        Returns:
            global_feat : (B, D)  – CLS-based global embedding (L2-normed)
            layer_feats : dict {layer_idx: (B, N_patches, D)}
        """
        self._collector.clear()
        global_feat = self.model.encode_image(pixel_values)
        global_feat = F.normalize(global_feat, dim=-1)
        layer_feats = self._collector.get_features()
        return global_feat, layer_feats

    # ------------------------------------------------------------------
    # Fused patch feature
    # ------------------------------------------------------------------

    def fuse_patch_features(
        self,
        layer_feats: Dict[int, torch.Tensor],
        spatial_hw: Optional[Tuple[int, int]] = None,
    ) -> torch.Tensor:
        """
        Average-fuse patch features from all tapped layers.

        Args:
            layer_feats : output of encode_image
            spatial_hw  : (H_patches, W_patches) for reshaping; inferred if None

        Returns:
            fused : (B, D, H_patches, W_patches)  — spatial feature map
        """
        tensors = [layer_feats[k] for k in sorted(layer_feats.keys())]
        # each tensor: (B, N, D) — project to common dim if needed
        stacked = torch.stack(tensors, dim=0)          # (L, B, N, D)
        fused = stacked.mean(dim=0)                    # (B, N, D)
        fused = F.normalize(fused, dim=-1)

        B, N, D = fused.shape
        if spatial_hw is None:
            hw = int(N ** 0.5)
            spatial_hw = (hw, hw)
        fused = fused.permute(0, 2, 1).reshape(B, D, *spatial_hw)
        return fused

    def __del__(self):
        self._collector.remove()
