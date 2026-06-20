# CLIPer — Training-Free Open-Vocabulary Semantic Segmentation

Inference-only reproduction of **CLIPer** (arXiv 2411.13836).

---

## Pipeline

```
Input Image
    │
    ▼
┌──────────────────────────────────────────────────────┐
│  Step 1 – ELF (Enhanced Local Features)              │
│                                                      │
│  Modified CLIP ViT extracts patch features from      │
│  layers [fuse_layer_start, last].  Per-layer feats   │
│  are L2-normalised and averaged → dense feature map  │
│  [B, H_p, W_p, D].  Cosine similarity with text      │
│  embeddings produces a coarse logit map               │
│  [B, C, H_p, W_p].                                   │
└──────────────────────────────────────────────────────┘
    │
    ▼  bilinear upsample → [B, C, H, W]
    │
┌──────────────────────────────────────────────────────┐
│  Step 2 – Coarse Segmentation Map                    │
│                                                      │
│  Argmax of upsampled ELF logits gives a per-pixel    │
│  class assignment.  This map captures global         │
│  structure but lacks fine boundary detail.           │
└──────────────────────────────────────────────────────┘
    │
    ▼  (only when use_fgc: true)
    │
┌──────────────────────────────────────────────────────┐
│  Step 3 – FGC (Fine-Grained Calibration)             │
│                                                      │
│  Stable Diffusion UNet is run once with the image    │
│  noised to timestep t=45.  Cross-attention maps      │
│  (text→spatial) are harvested from decoder blocks    │
│  and averaged across heads.  The FGC module blends   │
│  coarse CLIP logits with SD attention maps:          │
│                                                      │
│    refined = (1-α)·coarse_prob + α·sd_attn_norm      │
│                                                      │
│  This sharpens object boundaries and recovers fine-  │
│  grained regions under-represented by CLIP patches.  │
└──────────────────────────────────────────────────────┘
    │
    ▼  argmax → pred_mask [H, W]
    │
┌──────────────────────────────────────────────────────┐
│  Step 4 – Evaluation                                 │
│                                                      │
│  Streaming confusion-matrix accumulation over the    │
│  validation set → per-class IoU, mIoU, mAcc, fwIoU. │
│  No mmcv required; self-contained in eval/miou.py.   │
└──────────────────────────────────────────────────────┘
```

---

## Project Structure

```
CLIPer/
├── modified_clip/
│   ├── clip_extractor.py      # open_clip wrapper; dense feature extraction
│   └── attention_hooks.py     # per-block forward hooks for ELF
├── diffusion_model/
│   ├── sd_feature_extractor.py  # SD UNet single-step query at t=45
│   └── fgc.py                   # Fine-Grained Calibration (training-free)
├── datasets_loader/
│   ├── voc_dataset.py
│   ├── coco_stuff_dataset.py
│   └── ade20k_dataset.py
├── segmentor/
│   ├── elf.py                 # multi-layer feature aggregation
│   ├── cliper.py              # full pipeline orchestration
│   └── sliding_window.py      # tiled inference for hi-res images
├── eval/
│   ├── miou.py                # self-contained mIoU (no mmcv)
│   └── evaluator.py
├── configs/
│   ├── base.yaml              # shared defaults
│   ├── voc21_vitb16.yaml
│   ├── coco_stuff164k_vitl14.yaml
│   └── ade20k_vitl14.yaml
├── scripts/
│   ├── run_inference.sh
│   └── eval_all.sh
├── utils/
│   ├── config.py              # YAML loader with _base_ inheritance
│   └── visualize.py
└── infer.py                   # main entry point
```

---

## Setup

```bash
# 1. Create environment (Python 3.9, CUDA 11.8+)
conda create -n cliper python=3.9 -y
conda activate cliper

# 2. Install PyTorch 2.x (match your CUDA version)
pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cu118

# 3. Install remaining dependencies
pip install -r requirements.txt
```

---

## Data Preparation

| Dataset | Expected path |
|---|---|
| PASCAL VOC 2012 | `data/VOCdevkit/VOC2012/` |
| COCO-Stuff 164k | `data/coco_stuff164k/` |
| ADE20K | `data/ADEChallengeData2016/` |

---

## Inference

```bash
# Single dataset
bash scripts/run_inference.sh configs/voc21_vitb16.yaml

# With colourised prediction PNGs
bash scripts/run_inference.sh configs/ade20k_vitl14.yaml --save-vis

# All benchmarks
bash scripts/eval_all.sh
```

---

## Config Schema

Key fields in `configs/base.yaml`:

| Field | Type | Description |
|---|---|---|
| `backbone` | str | `"ViT-B-16"` or `"ViT-L-14"` |
| `fuse_layer_start` | int | First layer to fuse for ELF (0-based) |
| `sd_timestep` | int | SD noise timestep for FGC feature query (default 45) |
| `input_short_side` | int | Resize shorter image side before inference (default 336) |
| `use_fgc` | bool | Enable Fine-Grained Calibration |
| `use_sliding_window` | bool | Enable tiled inference |
| `dataset.name` | str | `voc2012` / `coco_stuff164k` / `ade20k` |

---

## Reference

```
@article{cliper2024,
  title  = {CLIPer: Hierarchically Improving Spatial Representation of
             CLIP for Open-Vocabulary Semantic Segmentation},
  author = {...},
  journal = {arXiv preprint arXiv:2411.13836},
  year   = {2024}
}
```
