# Pokémon FireRed AI — Core Architectural Invariants & Project Rules

This document establishes the ground-truth technical invariants and architectural constraints for the Pokémon FireRed AI reinforcement learning project. These rules must be preserved across all analysis, training runs, evaluations, and chronicle entries.

---

## 1. Active Save State & Environmental Invariants

1. **Active Save State**:
   - Environment instances MUST exclusively load **`BeginningPalletGotPokeballs.state`** (configured as `default_state` in `data/custom_integrations/PokemonFireRed-GBA/metadata.json`).
2. **Initial Spawn Location**:
   - The agent spawns on **`Map (4, 0)`: Hero's Living Room (1F)** downstairs where Mom is.
   - The agent does **NOT** spawn in the bedroom 2F (`Map (4, 1)`).
3. **Narrative / Quest Progress**:
   - **Party Count**: $1$ (Bulbasaur is already in party; level 5).
   - **Key Items**: Oak's parcel delivery and initial Pokéballs quest are **already completed**.
   - **Oak Grass Trigger**: The scripted intro cutscene where Professor Oak stops the player from entering tall grass is **already passed and cleared**. Agents can step directly into the tall grass at the north exit of Pallet Town without triggering an Oak cutscene.

---

## 2. In-Game Map Coordinate Reference (RAM Ground Truth)

| Bank & Map ID | Map Name | Description |
| :---: | :--- | :--- |
| **`(4, 0)`** | **Hero's Living Room (1F)** | Initial spawn location with Mom |
| **`(4, 1)`** | **Hero's Bedroom (2F)** | Upstairs room with PC and SNES |
| **`(3, 0)`** | **Pallet Town Overworld** | Town square, yard perimeters, front door exit |
| **`(4, 2)`** | **Oak's Laboratory** | Professor Oak's research lab |
| **`(4, 3)`** | **Rival's House** | Daisy and Rival's house |
| **`(3, 19)`** | **Route 1** | Northern overland route to Viridian City |
| **`(3, 1)`** | **Viridian City** | City hub with Gym, Mart, and Pokémon Center |
| **`(3, 20)`** | **Route 2** | Overland route between Viridian and Pewter |
| **`(3, 2)`** | **Pewter City** | Pewter Gym (Brock) |

> [!IMPORTANT]
> A run visiting maps `(4, 0)`, `(4, 1)`, `(3, 0)`, and `(4, 2)` records `unique_maps: 4`, but all 4 maps are entirely within **Pallet Town**. Never confuse multi-room interior visits with cross-city travel.

---

## 3. Exploration Paradigms & The "Roomba Fallacy"

1. **Rejection of `COORD` Novelty**:
   - Count-based coordinate exploration (`COORD`, $1/\sqrt{N}$) is **permanently rejected** (Phases 12 & 24).
   - *Reason*: The **"Roomba Fallacy"** (Exhaustive Area Mowing Trap). Coordinate density bonuses strongly incentivize agents to systematically vacuum every corner and perimeter tile of familiar rooms and lawns rather than pursuing macro-milestones or transitioning through narrow doorway bottlenecks.
   - Furthermore, $1/\sqrt{N}$ variance causes severe Bellman target non-stationarity in off-policy replay buffers.
2. **Approved Curiosity Paradigm**:
   - Primary curiosity is visual prediction error via **Random Network Distillation (`RND`)**, optionally augmented by perceptual structural similarity (`SSIM`).

---

## 4. Long-Horizon Training Paradigm (Peter Whidden Standard)

1. **Horizon Scale**:
   - Navigating, battling, leveling up, and traveling to Pewter City requires **tens to hundreds of millions of environment steps**. Short horizon benchmarks (< 1M steps) represent the extreme early phase of policy initialization.
2. **Exploration Entropy Preservation**:
   - **QR-DQN Epsilon Schedule**:
     - `--epsilon-decay-steps`: Scaled to **`5,000,000`** steps (100x longer decay).
     - `--epsilon-end` ($\epsilon$-floor): Minimum floor of **`0.20`** (ensuring 20% random action injection even after millions of steps to prevent deterministic wall-locking).
   - **PPO Policy Entropy**:
     - `--ent-coef`: Set to **`0.08`** (preventing policy collapse into local attractor loops).

---

## 5. Research Chronicle Maintenance Protocol

1. **Periodic Manual Synchronization**:
   - The agent MUST periodically update [`RESEARCH_CHRONICLE.md`](file:///c:/dev/Antigravity/Pokemon%20FireRed%20AI/RESEARCH_CHRONICLE.md) manually at logical research checkpoints:
     - Upon completion of a training run, multi-generation benchmark, or experimental phase.
     - Following major architectural changes, hyperparameter overhauls, or algorithmic pivots.
     - Whenever empirical findings reveal unexpected behaviors, pathologies, or critical corrections.
2. **Strictly Non-Automated (Manual Review Standard)**:
   - Updates must **NEVER** be delegated to unattended background cron daemons, automated OS schedules, or headless script hooks.
   - The agent must personally inspect and verify the empirical data (RAM coordinates, loss curves, reward distributions, trajectory files) before logging entries, ensuring rigorous academic analysis and preventing erroneous assertions.
3. **Immutability & Non-Destructive Standard**:
   - Updates must strictly append new numbered phases to the end of the document without modifying, renumbering, or deleting historical phases.
   - Maintain the IEEE/NeurIPS formal academic tone, complete telemetry tables, and KaTeX mathematical notation.
