"""
Sliding-window inference for high-resolution images.

Tiles the image into overlapping windows, runs the inner forward function on
each tile, and averages the logit maps in the overlap regions.
"""
from __future__ import annotations
from typing import Callable

import math
import torch
import torch.nn.functional as F
from PIL import Image


class SlidingWindowInference:
    """
    Args:
        window_size: square tile side length in pixels.
        stride: step between tile centres.
    """

    def __init__(self, window_size: int = 336, stride: int = 224) -> None:
        self.window_size = window_size
        self.stride = stride

    def infer(
        self,
        image: Image.Image,
        forward_fn: Callable[[torch.Tensor], torch.Tensor],
    ) -> torch.Tensor:
        """
        Args:
            image: full-resolution PIL image.
            forward_fn: callable that accepts a preprocessed [1,3,ws,ws]
                        tensor and returns [C, ws, ws] logits.

        Returns:
            logits: [C, H_orig, W_orig] accumulated logit map.
        """
        from modified_clip.clip_extractor import CLIPExtractor  # local import

        W, H = image.size
        ws = self.window_size
        s = self.stride

        # Pad image so it's divisible into windows
        pad_h = max(0, math.ceil((H - ws) / s) * s + ws - H)
        pad_w = max(0, math.ceil((W - ws) / s) * s + ws - W)
        padded_w = W + pad_w
        padded_h = H + pad_h

        import torchvision.transforms.functional as TF
        img_t = TF.to_tensor(image)  # [3, H, W]
        if pad_h > 0 or pad_w > 0:
            img_t = F.pad(img_t, (0, pad_w, 0, pad_h), mode="reflect")

        # Pre-run to get C
        sample_crop = TF.to_pil_image(img_t[:, :ws, :ws])
        from modified_clip import CLIPExtractor as _CE  # noqa: F811
        # Forward fn handles preprocessing; we pass crops as PIL
        sample_logits = forward_fn(self._crop_to_tensor(img_t, 0, 0, ws))
        C = sample_logits.shape[0]
        device = sample_logits.device
        dtype = sample_logits.dtype

        acc = torch.zeros(C, padded_h, padded_w, device=device, dtype=dtype)
        cnt = torch.zeros(1, padded_h, padded_w, device=device, dtype=dtype)

        ys = list(range(0, padded_h - ws + 1, s))
        xs = list(range(0, padded_w - ws + 1, s))
        for y in ys:
            for x in xs:
                tile = self._crop_to_tensor(img_t, y, x, ws)
                logits = forward_fn(tile)  # [C, ws, ws]
                acc[:, y: y + ws, x: x + ws] += logits
                cnt[:, y: y + ws, x: x + ws] += 1.0

        acc = acc / cnt.clamp(min=1)
        return acc[:, :H, :W]  # trim padding

    @staticmethod
    def _crop_to_tensor(img_t: torch.Tensor, y: int, x: int, ws: int) -> torch.Tensor:
        """Return [1, 3, ws, ws] crop as a float tensor."""
        crop = img_t[:, y: y + ws, x: x + ws]
        return crop.unsqueeze(0)
