"""
Wraps open_clip to expose:
  - per-layer ViT patch features (for ELF)
  - global image / text embeddings
"""
from __future__ import annotations
from typing import Dict, List, Tuple

import torch
import torch.nn.functional as F
import open_clip

from .attention_hooks import MultiLayerHookManager


class CLIPExtractor:
    """
    Loads an open_clip model and wires up hooks for dense feature extraction.

    Args:
        backbone: open_clip model name, e.g. "ViT-B-16" or "ViT-L-14".
        pretrained: open_clip pretrained tag, e.g. "openai".
        fuse_layer_start: first layer index (0-based) to capture.
        device: torch device string.
    """

    def __init__(
        self,
        backbone: str = "ViT-B-16",
        pretrained: str = "openai",
        fuse_layer_start: int = 6,
        device: str = "cuda",
    ) -> None:
        self.device = torch.device(device)
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            backbone, pretrained=pretrained
        )
        self.model = self.model.eval().to(self.device)
        self.tokenizer = open_clip.get_tokenizer(backbone)

        # ViT transformer blocks
        visual = self.model.visual
        # open_clip stores blocks at visual.transformer.resblocks
        blocks = visual.transformer.resblocks
        self.num_layers = len(blocks)
        self.hook_manager = MultiLayerHookManager(blocks, start=fuse_layer_start)
        self.fuse_layer_start = fuse_layer_start

    # ── image features ───────────────────────────────────────────────────────

    @torch.no_grad()
    def encode_image_dense(
        self, image: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[int, torch.Tensor]]:
        """
        Run image through CLIP visual encoder, collecting intermediate patch
        features from each hooked layer.

        Args:
            image: preprocessed image tensor [B, 3, H, W].

        Returns:
            global_feat: L2-normalised CLS embedding [B, D].
            layer_feats: {layer_idx: patch_features [B, N_patches, D]}.
        """
        self.hook_manager.clear()
        global_feat = self.model.encode_image(image.to(self.device))
        global_feat = F.normalize(global_feat, dim=-1)

        raw = self.hook_manager.collect()
        # raw tensors are [seq, B, D] (seq = 1 CLS + N_patches)
        layer_feats: Dict[int, torch.Tensor] = {}
        for idx, feat in raw.items():
            if feat is None:
                continue
            # drop CLS token; transpose to [B, N_patches, D]
            patch = feat[1:].permute(1, 0, 2)  # [B, N, D]
            patch = F.normalize(patch, dim=-1)
            layer_feats[idx] = patch

        return global_feat, layer_feats

    # ── text features ────────────────────────────────────────────────────────

    @torch.no_grad()
    def encode_text(self, classnames: List[str]) -> torch.Tensor:
        """
        Encode class names with prompt ensembling (80 ImageNet templates).

        Returns:
            text_feats: [num_classes, D] L2-normalised.
        """
        templates = _IMAGENET_TEMPLATES
        all_feats: List[torch.Tensor] = []
        for name in classnames:
            prompts = [t.format(name) for t in templates]
            tokens = self.tokenizer(prompts).to(self.device)
            feats = self.model.encode_text(tokens)   # [T, D]
            feats = F.normalize(feats, dim=-1).mean(0)
            feats = F.normalize(feats, dim=-1)
            all_feats.append(feats)
        return torch.stack(all_feats)  # [C, D]

    def close(self) -> None:
        self.hook_manager.remove()


# 80 ImageNet zero-shot prompt templates (same as original CLIP paper)
_IMAGENET_TEMPLATES = [
    "a photo of a {}.",
    "a bad photo of a {}.",
    "a origami {}.",
    "a photo of the large {}.",
    "a {} in a video game.",
    "art of the {}.",
    "a photo of the small {}.",
    "a photo of a {} in nature.",
    "a rendering of a {}.",
    "a cropped photo of the {}.",
    "the photo of a {}.",
    "a photo of a clean {}.",
    "a photo of a dirty {}.",
    "a dark photo of the {}.",
    "a photo of my {}.",
    "a photo of the cool {}.",
    "a close-up photo of a {}.",
    "a bright photo of the {}.",
    "a cropped photo of a {}.",
    "a photo of the {}.",
    "a good photo of the {}.",
    "a photo of one {}.",
    "a close-up photo of the {}.",
    "a rendition of the {}.",
    "a photo of the clean {}.",
    "a rendition of a {}.",
    "a photo of a nice {}.",
    "a good photo of a {}.",
    "a photo of the nice {}.",
    "a photo of the weird {}.",
    "a blurry photo of the {}.",
    "a cartoon {}.",
    "art of a {}.",
    "a sketch of the {}.",
    "a embroidered {}.",
    "a pixelated photo of a {}.",
    "itap of the {}.",
    "a jpeg corrupted photo of the {}.",
    "a good photo of the {}.",
    "a plushie {}.",
    "a photo of the nice {}.",
    "a photo of the small {}.",
    "a photo of the weird {}.",
    "the cartoon {}.",
    "art of the {}.",
    "a drawing of the {}.",
    "a photo of the large {}.",
    "a black and white photo of a {}.",
    "the plushie {}.",
    "a dark photo of a {}.",
    "itap of a {}.",
    "graffiti of the {}.",
    "a toy {}.",
    "itap of my {}.",
    "a photo of a cool {}.",
    "a photo of a small {}.",
    "a tattoo of the {}.",
]
