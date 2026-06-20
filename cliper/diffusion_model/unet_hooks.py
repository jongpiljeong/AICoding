"""
UNet decoder block hooks for Stable Diffusion feature extraction.

At inference time we:
  1. Encode the image to latent z via the VAE encoder.
  2. Add noise at timestep t (sd_timestep=45 by default).
  3. Run one forward pass of the UNet with an empty-string conditioning.
  4. Collect spatial feature maps from the specified up-blocks.

The hook captures the *output* of each up-block's resnets (before attention),
which carries rich semantic and geometric information.
"""

from typing import Dict, List
import torch


class UNetFeatureCollector:
    """
    Args:
        unet        : diffusers UNet2DConditionModel
        block_names : e.g. ["up_blocks.0", "up_blocks.1"]
    """

    def __init__(self, unet, block_names: List[str]):
        self._features: Dict[str, torch.Tensor] = {}
        self._hooks = []

        for name in block_names:
            module = self._get_submodule(unet, name)
            handle = module.register_forward_hook(self._make_hook(name))
            self._hooks.append(handle)

    @staticmethod
    def _get_submodule(model, dotted_path: str):
        parts = dotted_path.split(".")
        m = model
        for p in parts:
            m = getattr(m, p)
        return m

    def _make_hook(self, name: str):
        def hook(module, input, output):
            feat = output
            if isinstance(feat, tuple):
                feat = feat[0]
            self._features[name] = feat.detach()
        return hook

    def get_features(self) -> Dict[str, torch.Tensor]:
        return dict(self._features)

    def clear(self):
        self._features.clear()

    def remove(self):
        for h in self._hooks:
            h.remove()
        self._hooks.clear()
