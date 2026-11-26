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
3. **Dynamic Curriculum Scaling Formula**:
   - Generation horizon scales dynamically with agent lifetime:
     $$T_g = \max\left(2048, \text{round}\left(\frac{4096 + 0.05 \times \text{lifetime}}{2048}\right) \times 2048\right)$$
4. **Empirical Hardware Throughput Baselines (CUDA)**:
   - Steady-state rollout throughput on CUDA: **$260\text{--}295$ SPS** for QR-DQN vs **$114\text{--}120$ SPS** for PPO.
   - *Note*: Initial short generations (< 10k steps) have lower average SPS (~160 QR-DQN / ~72 PPO) due to fixed Python interpreter and GBA environment initialization overhead.

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

---

## 6. Benchmark Orchestration, Resumption & Symmetry Invariants

1. **The Symmetrical Step Invariant**:
   - In alternating comparative benchmarks (e.g., QR-DQN vs PPO), **never leave or resume the benchmark in an asymmetrical step state**. Both models must hold identical cumulative environment experience before pausing or concluding.
2. **Safe Generation Boundary Interception**:
   - When pausing or stopping runs, **never terminate processes mid-rollout**. Always intercept cleanly after Phase 2 (PPO) and Phase 3 (visual rendering) have finalized and flushed checkpoints and state ledgers to disk.
3. **Fast-Resume & Zero-Redundancy Principle**:
   - When resuming a multi-generation run, the orchestrator must skip historical generation replay and skip redundant chronological re-stitching (`is_new_render = False`), avoiding the $\mathcal{O}(G^2)$ video re-encoding bottleneck.
4. **Benchmark CLI Invocation Semantics**:
   - `--generations N`: Relative incremental execution (runs $N$ additional generations from current state).
   - `--target-generation N`: Absolute cumulative milestone targeting (runs until generation $N$ is reached).
5. **Visual Artifact & Rendering Invariant**:
   - Visual swarm evidence must always be exported exclusively as compressed MP4 video (GIF export is permanently deprecated to prevent file bloat).
   - Trajectory recordings must never be truncated (recording full generation trajectories to the final step) and rendered at **60 FPS** representing **4x real-time game speed** (with 4-frame skip, 0 intro/outro hold frames).

---

## 7. AGENTS.md Governance & Project Conventions

1. **Prompt-Injection Filtering Standard**:
   - `AGENTS.md` MUST strictly contain only invariants, operational constraints, and technical ground truths that make sense to inject before every prompt (i.e. invariants the agent tends to forget or must strictly abide by). It must never become a changelog or narrative research essay.
2. **Strictly Surgical Edits**:
   - Only minimal, surgical edits must be performed on `AGENTS.md`. Every addition, cut, or modification requires careful consideration of context budget and necessity.
3. **Feature & Architecture Naming Protocol**:
   - When introducing major new architectural paradigms, algorithms, curriculum designs, or significant features, the agent MUST explicitly ask the user for their preferred naming convention rather than inventing names unilaterally.

---

## 8. Calibrated Milestone Reward Invariants

1. **Anti-Handholding Invariant (Zero-Reward Trivial Interiors)**:
   - Trivial interior rooms (Hero's Bedroom `(4, 1)`, Rival's House `(4, 3)`, Oak's Lab `(4, 2)`, Gatehouses `(15, X)`, and random NPC homes) award **strictly 0.0 extrinsic reward** to prevent indoor exploitation traps.
2. **Mathematically Calibrated Geographic Milestones**:
   - **Pallet Town Overworld `(3, 0)`**: **+10.0** (Outdoor breakthrough).
   - **Overland Routes**: **+20.0** (Route 1 `(3, 19)`, Route 22 `(3, 40)`), **+30.0** (Route 2 `(3, 20)`), **+40.0** (Route 3/4).
   - **Dungeons & Complexes**: **+30.0** (Viridian Forest `(1, 0)`, Diglett's Cave `(1, 22)`), **+40.0** (Mt. Moon `(1, 1..3)`).
   - **Major Hub Cities**: **+50.0** (Viridian City `(3, 1)`), **+100.0** (Pewter City `(3, 2)`), **+120.0** (Cerulean City `(3, 3)`), scaling up to **+300.0** (Indigo Plateau `(3, 9)`).
   - **Gym Arenas**: **+25.0** (Pewter Gym Arena `(6, 2)`).
3. **Gym Leader Defeat Badges**:
   - Defeating Gym Leaders awards calibrated bonuses: **+250.0** (Boulder Badge / Brock), scaling up to **+600.0** (Earth Badge / Giovanni), awarded upon acquisition in `SaveBlock1` flags byte `0xEE0 + 260`.
4. **Anti-Farming / Episode Invariant**:
   - Every geographic milestone and gym badge reward is awarded **strictly once per episode** upon initial trigger to prevent boundary oscillation or cyclic reward exploitation.
