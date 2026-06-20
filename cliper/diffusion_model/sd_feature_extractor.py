"""
SDFeatureExtractor
==================
Extracts spatial feature maps from Stable Diffusion's UNet decoder
at a fixed noise timestep (default 45) without any denoising loop.

Pipeline per image:
  1. VAE encode → latent z  (shape: 1, 4, H/8, W/8)
  2. q(z_t | z_0): add Gaussian noise scheduled at timestep t
  3. Single UNet forward (null-text conditioning)
  4. Return up-block feature maps, L2-normalised and upsampled to `feature_res`
"""

from typing import Dict, List, Tuple
import torch
import torch.nn.functional as F
from diffusers import AutoencoderKL, UNet2DConditionModel, DDIMScheduler
from transformers import CLIPTextModel, CLIPTokenizer

from .unet_hooks import UNetFeatureCollector


class SDFeatureExtractor:
    def __init__(
        self,
        model_id: str = "runwayml/stable-diffusion-v1-5",
        sd_timestep: int = 45,
        unet_feature_layers: List[str] = ("up_blocks.0", "up_blocks.1"),
        feature_res: int = 64,
        device: str = "cuda",
    ):
        self.timestep = sd_timestep
        self.feature_res = feature_res
        self.device = device

        # Load SD components (weights are never updated)
        self.vae = AutoencoderKL.from_pretrained(model_id, subfolder="vae").to(device).eval()
        self.unet = UNet2DConditionModel.from_pretrained(model_id, subfolder="unet").to(device).eval()
        self.scheduler = DDIMScheduler.from_pretrained(model_id, subfolder="scheduler")
        tokenizer = CLIPTokenizer.from_pretrained(model_id, subfolder="tokenizer")
        text_enc = CLIPTextModel.from_pretrained(model_id, subfolder="text_encoder").to(device).eval()

        for m in (self.vae, self.unet, text_enc):
            for p in m.parameters():
                p.requires_grad_(False)

        # Pre-compute null-text conditioning (empty string)
        with torch.no_grad():
            null_tokens = tokenizer(
                [""], padding="max_length", max_length=tokenizer.model_max_length,
                return_tensors="pt"
            ).input_ids.to(device)
            self._null_emb = text_enc(null_tokens)[0]  # (1, seq_len, 768)

        self.scheduler.set_timesteps(1000)
        self._t_tensor = torch.tensor([sd_timestep], device=device, dtype=torch.long)

        self._collector = UNetFeatureCollector(self.unet, list(unet_feature_layers))

    # ------------------------------------------------------------------

    @torch.no_grad()
    def extract(self, pixel_values: torch.Tensor) -> torch.Tensor:
        """
        Args:
            pixel_values: (1, 3, H, W)  in [-1, 1] (SD VAE normalisation)

        Returns:
            fused_feat: (1, C_fused, feature_res, feature_res) — L2-normalised
        """
        B = pixel_values.shape[0]

        # 1. Encode to latent
        latent = self.vae.encode(pixel_values).latent_dist.sample()
        latent = latent * self.vae.config.scaling_factor   # (B, 4, H/8, W/8)

        # 2. Add noise at timestep t
        noise = torch.randn_like(latent)
        t = self._t_tensor.expand(B)
        noisy_latent = self.scheduler.add_noise(latent, noise, t)

        # 3. Single UNet forward (no denoising, just feature extraction)
        self._collector.clear()
        enc_emb = self._null_emb.expand(B, -1, -1)
        self.unet(noisy_latent, t, encoder_hidden_states=enc_emb)

        # 4. Fuse up-block features
        raw_feats = self._collector.get_features()
        upsampled = []
        for name in sorted(raw_feats.keys()):
            feat = raw_feats[name].float()   # (B, C, h, w)
            feat = F.interpolate(feat, size=(self.feature_res, self.feature_res),
                                 mode="bilinear", align_corners=False)
            upsampled.append(feat)

        fused = torch.cat(upsampled, dim=1)   # (B, sum_C, feature_res, feature_res)
        fused = F.normalize(fused, dim=1)
        return fused

    def __del__(self):
        self._collector.remove()
