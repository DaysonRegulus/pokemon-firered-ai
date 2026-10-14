# Pokemon FireRed AI - Reinforcement Learning (Windows Native)

A high-performance Reinforcement Learning environment and training pipeline for **Pokemon FireRed (GBA)** using Proximal Policy Optimization (**PPO**) and Curiosity-Driven Exploration (**RND / SSIM**).

---

## Architecture Overview

```
Pokemon FireRed AI/
├── .venv/                              # Isolated Python 3.10 virtual environment
├── data/
│   └── custom_integrations/
│       └── PokemonFireRed-GBA/         # ROM, SHA hash, metadata, and custom save states
├── src/
│   └── pokefirered/
│       ├── __init__.py
│       ├── env_factory.py              # Environment factory and vectorization
│       ├── wrappers.py                 # Action space reduction, frame skipping, reward wrapper
│       ├── rewards.py                  # RAM inspection, HP/level tracking, faint multipliers
│       ├── rnd.py                      # Random Network Distillation (curiosity exploration)
│       ├── callbacks.py                # Hardware, speed, faint, and action distribution logging
│       └── keyboard_input.py           # Cross-platform non-blocking keyboard controller
├── scripts/
│   ├── train.py                        # Training pipeline with dynamic curriculum & CLI
│   ├── evaluate.py                     # Rendered policy evaluation & victory lap
│   └── play_manual.py                  # Real-time manual testing (WASD + Z/X)
├── checkpoints/                        # Model weights (.zip) and RND checkpoints (.pth)
├── logs/                               # TensorBoard telemetry
├── requirements.txt                    # Project dependencies
└── README.md
```

---

## Key Features

1. **Reduced Action Space**: Maps the 12-button GBA pad down to 6 gameplay-critical buttons (`B`, `UP`, `DOWN`, `LEFT`, `RIGHT`, `A`) via `ActionFilterWrapper`.
2. **Direct Memory Inspection**: `RewardManager` monitors GBA RAM addresses for party HP, party levels, opponent HP, and opponent levels.
3. **Dynamic Faint Multipliers**: Scales opponent faint rewards based on level differentials between the player and opponent teams.
4. **Exploration Systems**:
   - **RND (Random Network Distillation)**: Neural intrinsic curiosity network rewarding visits to novel visual states.
   - **SSIM (Structural Similarity Index Measure)**: Frame difference buffer for visual discovery bonuses.
5. **Dynamic Curriculum**: Automatically scales training steps per run based on cumulative model lifetime.
6. **Cross-Platform Manual Test**: `scripts/play_manual.py` supports Windows native console input (`msvcrt`) as well as Linux POSIX (`termios`).

---

## Quickstart (Windows)

### 1. Environment Setup
The project uses an isolated Python 3.10 virtual environment:

```powershell
# Activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

### 2. Manual Testing (Play with Keyboard)
Test the game, ROM state, and live RAM reward triggers:
```powershell
python scripts/play_manual.py
```
**Controls:**
- `W` / `A` / `S` / `D` : Move (Up / Left / Down / Right)
- `Z` : B button (Run / Cancel)
- `X` : A button (Confirm / Interact)
- `Q` : Quit

### 3. Training the Agent
Run PPO training with RND curiosity:
```powershell
# Default: 2 parallel environments with RND exploration on GPU
python scripts/train.py --num-envs 2 --exploration RND

# Benchmark with 8 environments
python scripts/train.py --num-envs 8 --exploration RND

# Watch training with rendering enabled
python scripts/train.py --num-envs 1 --render-mode human
```

### 4. Evaluating a Checkpoint
Run a trained model with human rendering:
```powershell
python scripts/evaluate.py --model-path checkpoints/PokemonFireRed-GBA-RND-2env.zip
```

### 5. Monitoring with TensorBoard
View hardware utilization, environment steps per second, cumulative opponent faints, and intrinsic curiosity rewards:
```powershell
tensorboard --logdir ./logs --host 0.0.0.0 --port 6006
```
