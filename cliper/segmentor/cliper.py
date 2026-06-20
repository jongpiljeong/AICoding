"""
CLIPer — Main inference pipeline
=================================
Orchestrates the four-stage pipeline:

  Stage 1 – ELF  : extract multi-layer CLIP patch features, enhance with
                    edge guidance
  Stage 2 – Coarse map : cosine-similarity patch-text matching
  Stage 3 – FGC  : diffusion-feature-guided non-local correction (optional)
  Stage 4 – Output: upsample to original resolution, argmax

Reference: arXiv 2411.13836
"""

from typing import List, Optional, Tuple
import torch
import torch.nn.functional as F
from PIL import Image

from modified_clip import CLIPFeatureExtractor
from diffusion_model import SDFeatureExtractor
from segmentor.elf import enhance_local_features
from segmentor.coarse_map import compute_coarse_map, apply_background_threshold
from segmentor.fgc import fine_grained_correction
from utils.image_utils import (
    resize_short_side, pad_to_multiple, sliding_window_tiles, to_tensor
)
from utils.mask_utils import combine_window_preds, crop_to_original, upsample_mask


class CLIPer:
    def __init__(self, cfg: dict, device: str = "cuda"):
        self.cfg = cfg
        self.device = device

        m_cfg = cfg["model"]
        c_cfg = cfg["clip"]
        d_cfg = cfg["diffusion"]
        s_cfg = cfg["segmentor"]

        self.clip = CLIPFeatureExtractor(
            backbone=m_cfg["backbone"],
            pretrained=m_cfg["clip_pretrained"],
            fuse_layer_start=c_cfg["fuse_layer_start"],
            device=device,
        )

        self.use_fgc: bool = s_cfg["use_fgc"]
        if self.use_fgc:
            self.sd = SDFeatureExtractor(
                model_id=m_cfg["sd_model_id"],
                sd_timestep=d_cfg["sd_timestep"],
                unet_feature_layers=d_cfg["unet_feature_layers"],
                feature_res=d_cfg["feature_res"],
                device=device,
            )

        self.input_short_side: int = c_cfg["input_short_side"]
        self.patch_size: int = self.clip.patch_size
        self.use_sliding_window: bool = c_cfg["use_sliding_window"]
        self.sw_stride: int = c_cfg.get("sliding_window_stride", 224)

        self.temperature: float = s_cfg["temperature"]
        self.bg_threshold: float = s_cfg["bg_threshold"]
        self.fgc_alpha: float = s_cfg.get("fgc_alpha", 0.4)

        self._text_embs: Optional[torch.Tensor] = None
        self._categories: Optional[List[str]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_categories(self, categories: List[str]) -> None:
        """Pre-compute and cache text embeddings."""
        self._categories = categories
        self._text_embs = self.clip.encode_text(categories)

    @torch.no_grad()
    def predict(self, image: Image.Image) -> torch.Tensor:
        """
        Args:
            image: PIL RGB image (any resolution)

        Returns:
            pred_mask: (H_orig, W_orig)  int64 label map
                       0 = background, 1..n = category indices
        """
        assert self._text_embs is not None, "Call set_categories() first."

        orig_w, orig_h = image.size
        image_rs = resize_short_side(image, self.input_short_side)
        image_pad, pad_hw = pad_to_multiple(image_rs, self.patch_size)
        padded_w, padded_h = image_pad.size

        if self.use_sliding_window:
            logits = self._sliding_window_inference(image_pad, padded_h, padded_w)
        else:
            logits = self._single_pass(image_pad)   # (1, n_cls+1, Hp, Wp)

        # Upsample to padded size, then crop padding
        logits = upsample_mask(logits.squeeze(0), (padded_h, padded_w))   # (C, padded_h, padded_w)
        logits = crop_to_original(logits, pad_hw)                          # (C, H_rs, W_rs)

        # Upsample to original size
        logits = upsample_mask(logits.unsqueeze(0), (orig_h, orig_w)).squeeze(0)

        pred = logits.argmax(dim=0).cpu()   # (H, W)  int64
        return pred

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _single_pass(self, image: Image.Image) -> torch.Tensor:
        """Run one full pipeline pass. Returns (1, n_cls+1, Hp, Wp)."""
        w, h = image.size
        Hp, Wp = h // self.patch_size, w // self.patch_size

        # --- Stage 1: ELF ---
        pv_clip = to_tensor(image).unsqueeze(0).to(self.device)
        _, layer_feats = self.clip.encode_image(pv_clip)
        fused = self.clip.fuse_patch_features(layer_feats, (Hp, Wp))  # (1, D, Hp, Wp)

        # RGB in [0,1] for edge computation
        rgb_01 = pv_clip * torch.tensor([0.26862954, 0.26130258, 0.27577711],
                                         device=self.device).view(1, 3, 1, 1)
        rgb_01 = rgb_01 + torch.tensor([0.48145466, 0.4578275, 0.40821073],
                                        device=self.device).view(1, 3, 1, 1)
        rgb_01 = rgb_01.clamp(0, 1)
        elf_feats = enhance_local_features(fused, rgb_01)              # (1, D, Hp, Wp)

        # --- Stage 2: Coarse map ---
        sim = compute_coarse_map(elf_feats, self._text_embs, self.temperature)
        sim_with_bg = apply_background_threshold(sim, self.bg_threshold)  # (1, C+1, Hp, Wp)

        # --- Stage 3: FGC ---
        if self.use_fgc:
            # SD expects [-1, 1]
            pv_sd = (rgb_01 * 2.0 - 1.0)
            sd_feats = self.sd.extract(pv_sd)
            sim_with_bg = fine_grained_correction(sim_with_bg, sd_feats, self.fgc_alpha)

        return sim_with_bg   # (1, n_cls+1, Hp, Wp)

    def _sliding_window_inference(
        self, image: Image.Image, H: int, W: int
    ) -> torch.Tensor:
        n_cls = len(self._categories) + 1
        canvas = torch.zeros(1, n_cls, H, W, device=self.device)
        count = torch.zeros(1, 1, H, W, device=self.device)

        tiles = sliding_window_tiles(image, self.input_short_side, self.sw_stride)
        for tile, bbox in tiles:
            tile_logits = self._single_pass(tile)           # (1, C, Ht/ps, Wt/ps)
            y0, x0, y1, x1 = bbox
            ph, pw = y1 - y0, x1 - x0
            upsampled = upsample_mask(tile_logits.squeeze(0), (ph, pw)).unsqueeze(0)
            canvas[:, :, y0:y1, x0:x1] += upsampled
            count[:, :, y0:y1, x0:x1] += 1

        canvas = canvas / count.clamp(min=1)
        # Downsample back to patch grid for consistency
        Hp, Wp = H // self.patch_size, W // self.patch_size
        return F.interpolate(canvas, size=(Hp, Wp), mode="bilinear", align_corners=False)
