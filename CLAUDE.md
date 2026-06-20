# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workspace Overview

This is a multi-project Claude Code workspace. The root (`C:\AICoding`) holds installed agent skills and several independent subprojects — each subdirectory is a separate project with its own purpose and stack. There is no shared build system or test runner at the root level.

## Installed Skills

Skills live in `.agents/skills/` and are driven by their `SKILL.md` files. They are invoked via slash commands or automatically when their trigger condition is met. `skills-lock.json` records installed versions and source hashes.

| Skill | Trigger |
|---|---|
| `research-paper-writer` | User asks to write a research/academic/conference paper |
| `manufacturing-expert` | Questions about MES, OEE, Industry 4.0, SPC, predictive maintenance |
| `proposal-writer` | User asks to write a business or research proposal |
| `agent-browser` | Browser automation tasks |
| `autoresearch` | Automated deep learning research exploration |
| `nxp-semiconductors-skill` | NXP MCU/MPU, i.MX, MCUXpresso, FlexCAN questions |

**research-paper-writer** details:
- Default format: IEEE; ACM on request
- Workflow: clarify scope → outline → methodology first, abstract last → references
- Reference specs: `.agents/skills/research-paper-writer/references/` (writing style, IEEE/ACM formatting)
- Layout templates: `.agents/skills/research-paper-writer/assets/`

## Subprojects

### `cliper/` — Training-Free Semantic Segmentation (Python/PyTorch)
Inference-only reproduction of CLIPer (arXiv 2411.13836): open-vocabulary semantic segmentation combining CLIP ViT and Stable Diffusion.

**Setup:**
```bash
conda create -n cliper python=3.9 -y && conda activate cliper
pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cu118
pip install -r cliper/requirements.txt
```

**Run inference:**
```bash
bash cliper/scripts/run_inference.sh cliper/configs/voc21_vitb16.yaml
bash cliper/scripts/eval_all.sh   # all benchmarks
```

**Pipeline:** ELF (multi-layer CLIP patch features) → coarse segmentation → FGC (SD UNet cross-attention calibration, optional) → mIoU evaluation. Key modules: `segmentor/cliper.py` (orchestration), `segmentor/elf.py` (feature fusion), `diffusion_model/fgc.py` (fine-grained calibration), `eval/miou.py` (self-contained, no mmcv). Config inheritance via `configs/base.yaml` + dataset-specific overrides.

### `Jinseol/` — MES Lite Dashboard (Python/Streamlit)
Streamlit-based manufacturing execution system dashboard for a filling line (`㈜진설초해`). Displays OEE, SPC (X̄-R charts, Cpk), UPH, lot traceability, and Pareto charts.

**Run:**
```bash
streamlit run Jinseol/app.py
```

Core logic split across `mes_core.py` (data loading, lot execution, traceability) and `run.py` (SPC/OEE calculations). Data lives in `Jinseol/data/*.csv`.

### `Study-04/fridge-recipe/` — Next.js Recipe App
Next.js app that recommends recipes from fridge contents. Runs with standard Next.js commands from within `Study-04/fridge-recipe/`.

### `AMSE/` — Separate Claude Code Workspace
Standalone workspace with its own `CLAUDE.md` and `.agents/skills/` (research-paper-writing, figure-generation, paper-reading, etc.). Treat as an independent project.

### `VibeCoding/claude-code-blog-builder/` — Blog Builder
Node.js project with its own `CLAUDE.md`, `.claude/` config, and git history.

## Root-Level Scripts

- `generate_ieee_paper.py` — Generates an IEEE-formatted `.docx` via `python-docx`; run with `python generate_ieee_paper.py`
- `generate_proposal.py` — Generates a research proposal `.docx`; run with `python generate_proposal.py`
- `oee_test.py` — Standalone OEE calculation test script

## Skill Management

To add or update skills: use the `/prompts.chat:skill-manager` skill or manually edit `skills-lock.json` and place the skill directory under `.agents/skills/`.
