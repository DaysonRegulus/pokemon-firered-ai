# Pokémon FireRed AI Agent 🎮🤖

An advanced Reinforcement Learning framework and research testbed for **Pokémon FireRed (Game Boy Advance)** using **Stable-Baselines3 (PPO)**, emulator RAM telemetry, and multi-paradigm curiosity-driven exploration.

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Framework: Stable-Baselines3](https://img.shields.io/badge/framework-Stable--Baselines3-orange.svg)](https://github.com/DLR-RM/stable-baselines3)
[![Platform: Windows & Linux](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📽️ Media Showcase

| Autonomous Gameplay | Battle & RAM Telemetry | Live Policy Execution |
| :---: | :---: | :---: |
| ![Autonomous Gameplay](media/demo1.gif) | ![Battle Telemetry](media/AIPlays.PNG) | ![Agent Play](media/Screenshot1.PNG) |

---

## 🔬 Research & Exploration Paradigms

This repository serves as an empirical research platform comparing intrinsic curiosity and exploration architectures within sparse-reward video games. The engine supports standalone evaluation as well as arbitrary multi-method hybrid composition:

1. **Neural Curiosity (RND - Random Network Distillation)**:
   - A fixed, randomly initialized Target Network paired with a trainable Predictor Network.
   - Rewards observation novelty via predictor MSE loss, calibrated with online running observation normalization.
2. **Perceptual Visual Metric (SSIM - Structural Similarity)**:
   - GPU-accelerated structural similarity evaluation across sliding temporal frame buffers.
   - Computes spatial luminance, contrast, and structural variance to reward visual transitions.
3. **Ground-Truth Spatial Frequency (COORD - Memory Coordinate Novelty)**:
   - Real-time tracking of map coordinates `(map_id, x, y)` extracted directly from DMA-invariant GBA overworld RAM structures.
   - Computes non-parametric curiosity decay via $r_{\text{coord}} = \beta \cdot \frac{1}{\sqrt{N(m, x, y)}}$.
4. **Hybrid Ensembles**:
   - Arbitrary runtime composition: `RND+COORD`, `SSIM+COORD`, `RND+SSIM`, `RND+SSIM+COORD`.

> [!NOTE]
> For in-depth research chronicles, mathematical formulations, empirical benchmarks, and DMA memory invariance proofs, see [RESEARCH_CHRONICLE.md](RESEARCH_CHRONICLE.md).

---

## 🌿 Repository Branch Structure

- **`master`** (Current): The modernized, modular v2 engine. Features cross-platform Windows native and Linux support, vectorized multi-processing, memory-invariant RAM wrappers, plug-and-play curiosity modules, and automated evaluation suites.
- **`legacy-linux`**: The historical baseline repository branch containing the original Linux/WSL2 monolithic training scripts (`FireRedRender.py`, `FireRedRewardManager.py`) and legacy model checkpoints.

---

## 📁 Architecture & File Structure

```
Pokemon FireRed AI/
├── .venv/                              # Python 3.10 virtual environment
├── data/
│   └── custom_integrations/
│       └── PokemonFireRed-GBA/         # Integration metadata, rom.sha, custom save states
├── doc/
│   └── README.md                       # Legacy project documentation
├── media/
│   ├── demo1.gif                       # Showcase gameplay GIF
│   ├── AIPlays.PNG                     # Battle state & RAM visual
│   └── Screenshot1.PNG                 # Agent overworld visual
├── src/
│   └── pokefirered/
│       ├── __init__.py
│       ├── env_factory.py              # Vectorized environment factory
│       ├── wrappers.py                 # Action filtering (12->6 buttons), frame skipping, rewards
│       ├── rewards.py                  # Direct RAM inspection, HP/level tracking, faint multipliers
│       ├── rnd.py                      # Random Network Distillation (RND) neural architecture
│       ├── ssim_module.py              # GPU-accelerated SSIM perceptual curiosity module
│       ├── coord_module.py             # Ground-truth count-based coordinate novelty module
│       ├── callbacks.py                # Telemetry, speed (SPS), faint, and action distribution logging
│       └── keyboard_input.py           # Cross-platform non-blocking keyboard controller
├── scripts/
│   ├── train.py                        # Unified training pipeline with dynamic curriculum & CLI
│   ├── evaluate.py                     # Rendered policy evaluation & GIF recording
│   ├── benchmark_envs.py               # Hardware scalability & throughput benchmarking
│   └── play_manual.py                  # Real-time manual playtest tool (WASD + Z/X)
├── visual_evidence/                    # Empirical keyframes verifying DMA coordinate invariance
├── RESEARCH_CHRONICLE.md               # Append-only empirical research document
├── requirements.txt                    # Project dependencies
└── README.md
```

---

## ⚡ Quickstart

### 1. Prerequisites & Virtual Environment

Clone the repository and set up a Python 3.10 virtual environment:

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / WSL2 (Bash):**
```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> [!IMPORTANT]
> **Legal Notice & ROM Setup**: This repository does NOT distribute commercial Nintendo ROMs. You must supply your own legally dumped `rom.gba` (Pokémon FireRed - Squirrels version or compatible v1.0 English GBA ROM) and place it inside:
> `data/custom_integrations/PokemonFireRed-GBA/rom.gba`
> Validate your dump matches the expected SHA-1 hash in `rom.sha`.

---

### 2. Manual Playtesting (RAM & Control Verification)

Verify your ROM integration, action bindings, and real-time RAM reward triggers with keyboard controls:

```powershell
python scripts/play_manual.py
```

**Keybindings:**
- `W` / `A` / `S` / `D` : Move (Up / Left / Down / Right)
- `Z` : B Button (Run / Cancel / Fast Text)
- `X` : A Button (Confirm / Interact)
- `Q` : Quit

---

### 3. Hardware Scalability Benchmarking

Measure throughput (Steps Per Second - SPS) and RAM footprint across varying parallel environments:

```powershell
python scripts/benchmark_envs.py --envs 2 4 8 12 16 --steps 1024
```

**Empirical Benchmarks (RTX 3050 Ti Laptop GPU / 8-Core Intel i7):**
- **8 Envs**: ~335 SPS | 2.2 GB RAM (Rock-solid stability)
- **12 Envs**: ~440 SPS | 2.6 GB RAM (**Optimal throughput-to-memory sweet spot**)
- **16 Envs**: ~500 SPS | 4.6 GB RAM (Maximum throughput)

---

### 4. Training the Agent

Launch PPO training with your chosen curiosity exploration paradigm:

```powershell
# 1. Pure Coordinate Novelty Exploration (Ground-Truth Spatial Frequency)
python scripts/train.py --num-envs 8 --exploration COORD --beta-coord 0.05

# 2. Pure Random Network Distillation (RND Neural Curiosity)
python scripts/train.py --num-envs 8 --exploration RND --beta-rnd 1.0

# 3. Pure Structural Similarity (SSIM Perceptual Frame Novelty)
python scripts/train.py --num-envs 8 --exploration SSIM --beta-ssim 0.5

# 4. Multi-Method Hybrid (Neural RND + Ground-Truth Spatial Coordinates)
python scripts/train.py --num-envs 8 --exploration RND+COORD --beta-rnd 1.0 --beta-coord 0.05

# 5. Baseline (Extrinsic Game Rewards Only - Leveling & Battle)
python scripts/train.py --num-envs 8 --exploration NONE
```

**Optional Training Flags:**
- `--visual-eval`: Periodically spawns an isolated evaluation environment and writes out gameplay GIFs to `eval_recordings/`.
- `--eval-freq <STEPS>`: Interval of environment steps between visual evaluation recordings (default: 20480).
- `--total-timesteps <N>`: Explicitly set training duration (defaults to automatic curriculum scaling).

---

### 5. Evaluating Checkpoints & Recording Play

Render a trained agent in real-time or export policy recordings:

```powershell
# Human rendered interactive window
python scripts/evaluate.py --model-path checkpoints/PokemonFireRed-GBA-COORD-8env.zip --render-mode human

# Headless evaluation with GIF recording
python scripts/evaluate.py --model-path checkpoints/PokemonFireRed-GBA-RND+COORD-8env.zip --record-gif --output-gif eval_demo.gif
```

---

### 6. Live Telemetry with TensorBoard

Monitor learning rate, value loss, policy entropy, intrinsic curiosity loss, coordinates discovered, and opponent faints:

```powershell
tensorboard --logdir ./logs --host 0.0.0.0 --port 6006
```

---

## 🧩 Technical Details: GBA DMA Memory Invariance

Prior approaches to GBA RAM hacking suffered from dynamic memory allocation (DMA), where pointers inside `SaveBlock1` and `SaveBlock2` shift across gameplay sessions. 

Our engine interfaces directly with static engine addresses in overworld VRAM/EWRAM:
- **`sCurrentMap` (`0x02031DBC`)**: Current Map Bank (`0x02031DBC`) and Map Number (`0x02031DBD`). Completely static and invariant across all game states.
- **`gObjectEvents[0]` (`0x02036E48`)**: Player avatar overworld event object containing local map coordinates $(x, y)$ at byte offsets `+0x10` and `+0x12`.
- **Warp Invariance**: Verified across transitions: Pallet Town 1F Living Room `(14, 14)` $\rightarrow$ Exit Door Mat `(11, 15)` $\rightarrow$ Pallet Town Overworld `(10, 6)`.

Empirical proof and keyframe captures are documented in [visual_evidence/](visual_evidence/) and [RESEARCH_CHRONICLE.md](RESEARCH_CHRONICLE.md).

---

## 🙌 Acknowledgements

* [Farama Foundation](https://farama.org) for **stable-retro**
* [DLR-RM](https://github.com/DLR-RM/stable-baselines3) for **Stable-Baselines3**
* [MatPoliquin](https://github.com/MatPoliquin) for foundational work on RAM mapping and wrappers
* [Peter Whidden](https://github.com/peterwhidden) for pioneer research on retro gaming reinforcement learning environments

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
