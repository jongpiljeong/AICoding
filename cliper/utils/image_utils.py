from typing import List, Tuple
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image


def resize_short_side(image: Image.Image, short_side: int) -> Image.Image:
    w, h = image.size
    scale = short_side / min(h, w)
    new_h, new_w = round(h * scale), round(w * scale)
    return image.resize((new_w, new_h), Image.BICUBIC)


def pad_to_multiple(image: Image.Image, multiple: int) -> Tuple[Image.Image, Tuple[int, int]]:
    """Pad image so H and W are multiples of `multiple`. Returns (padded_image, (pad_h, pad_w))."""
    w, h = image.size
    pad_h = (multiple - h % multiple) % multiple
    pad_w = (multiple - w % multiple) % multiple
    if pad_h == 0 and pad_w == 0:
        return image, (0, 0)
    arr = np.array(image)
    arr = np.pad(arr, ((0, pad_h), (0, pad_w), (0, 0)), mode="reflect")
    return Image.fromarray(arr), (pad_h, pad_w)


def sliding_window_tiles(
    image: Image.Image,
    window_size: int,
    stride: int,
) -> List[Tuple[Image.Image, Tuple[int, int, int, int]]]:
    """
    Yield (tile, (y0, x0, y1, x1)) pairs covering the image.
    Coordinates are in the padded image's pixel space.
    """
    w, h = image.size
    arr = np.array(image)
    tiles = []
    for y0 in range(0, h - window_size + 1, stride):
        for x0 in range(0, w - window_size + 1, stride):
            y1, x1 = y0 + window_size, x0 + window_size
            tile = Image.fromarray(arr[y0:y1, x0:x1])
            tiles.append((tile, (y0, x0, y1, x1)))
    # always include the bottom-right corner tile
    if tiles and (h - window_size, w - window_size) != (tiles[-1][1][0], tiles[-1][1][1]):
        y0, x0 = h - window_size, w - window_size
        tile = Image.fromarray(arr[y0:h, x0:w])
        tiles.append((tile, (y0, x0, h, w)))
    return tiles


def to_tensor(image: Image.Image, mean=(0.48145466, 0.4578275, 0.40821073),
              std=(0.26862954, 0.26130258, 0.27577711)) -> torch.Tensor:
    arr = np.array(image).astype(np.float32) / 255.0
    arr = (arr - np.array(mean)) / np.array(std)
    return torch.from_numpy(arr).permute(2, 0, 1).float()
