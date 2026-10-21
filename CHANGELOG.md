# Changelog

All notable changes to the **Pokémon FireRed AI** project are documented in this file.

The entries in this changelog are historically reconstructed from the repository's Git history across all branches (`legacy-linux` and `master`), detailing the full progression of the codebase from its initial baseline to the modern release.

---

## 📌 Project Versioning Scheme

This repository follows a **custom commit-by-commit historical versioning convention** rather than standard SemVer:

1. **Version 0 (`0.0.0`)**: The initial development baseline commit in the repository (`9f73471`, 2025-04-10).
2. **Pre-1.0.0 Iterations (`0.0.1` – `0.0.6`)**: Early code cleanup, removal of vendored C++ emulator trees, and documentation setup on Linux.
3. **Version 1.0.0 (`1.0.0`)**: The milestone at which the Linux implementation first reached a documented, reproducible, working condition (`95f08be`, 2025-07-02), providing complete system dependency specifications (`setup.txt`), training entrypoint (`FireRedRender.py`), and verified gameplay demonstration (`demo1.gif`).
   > *Milestone Reconciliation Note*: Candidates for the Linux milestone included `e682e97` (first root README describing WSL Ubuntu execution), `95f08be` (reproducible build instructions in `setup.txt`), and `a458cc3` (the final terminal commit of the `legacy-linux` branch). Commit `95f08be` was designated `1.0.0` because it completed the end-to-end environment pipeline required to build `stable-retro` from source and run the training scripts reliably.
4. **Linux Maintenance & Pre-Migration (`1.0.1` – `1.0.11`)**: Media optimization, screenshot additions, asset normalization, legacy branch finalization, and initial Windows workspace isolation.
5. **Version 2.0.0 (`2.0.0`)**: The milestone at which the Windows-native version was created (`402c201`, 2026-10-14), introducing pre-compiled Windows `stable-retro` integration, GPU-accelerated PPO, Random Network Distillation (RND) curiosity, RAM reward managers, and the modular `src/pokefirered/` package architecture.
6. **Subsequent Commits (`2.0.1` – `2.0.23`)**: Monotonically incremented patch revisions tracking rapid architectural advances: process isolation, GPU SSIM curiosity, DMA RAM coordinate invariance, count-based exploration, distributional QR-DQN with Prioritized Experience Replay, 12-environment benchmark suites, animated Kanto swarm visualizers, 1:1 continuous world manifold topology, and the **PokéRL Studio** desktop suite.

---

## [2.0.23] - 2026-10-21 (`e70dc50`)

### Added
- **PokéRL Studio Desktop Suite**: Implemented an integrated desktop mission-control application built with **PySide6 (Qt 6.12)**:
  - `src/pokefirered/gui/theme.py`: Custom Obsidian Slate dark palette with electric cyan accents and responsive typography.
  - `src/pokefirered/gui/main_window.py`: Unified window controller featuring sidebar navigation across 6 dedicated views, status telemetry bars, and crash-resilient event dispatching.
  - `src/pokefirered/gui/views/dashboard_view.py`: Overview console with a linear 7-stage milestone breadcrumb tracker, dual 60 FPS live viewports (GBA display and continuous swarm tracking), and real-time KPI metric cards.
  - `src/pokefirered/gui/views/play_view.py`: Interactive play and calibration console with keyboard/virtual D-Pad controls, trajectory scrubbing slider, tile-level offset calibration, and single-click verification snapshots.
  - `src/pokefirered/gui/views/train_view.py`: Training management dashboard for launching PPO and QR-DQN runs with curiosity selection (NONE, RND, SSIM, COORD, Ensembles), parallel environment configuration, and auto-scrolling log terminal.
  - `src/pokefirered/gui/views/charts_view.py`: Real-time Matplotlib analytics dashboard rendering 4 live curves (Rewards Progression, Exploration Frontier, Loss Dynamics, SPS Throughput) and automated historical benchmark tables.
  - `src/pokefirered/gui/views/swarm_view.py`: Swarm compilation studio for rendering multi-agent `.mp4` videos and animated `.gif` timelapses with customizable viewport dimensions, FPS, and trajectory overlays.
  - `src/pokefirered/gui/views/settings_view.py`: Diagnostics and hardware audit panel verifying CUDA acceleration, ROM hash integrity, and asset presence.
  - `src/pokefirered/gui/workers/emu_worker.py`: Dedicated 60 FPS emulator thread preventing UI freezing during interactive play.
  - `src/pokefirered/gui/workers/train_worker.py`: Non-blocking subprocess manager streaming training logs and parsing real-time metrics.
- **Unified World Topology Manifold (`WorldTopology`)**:
  - `src/pokefirered/visualization/topology.py`: Created a continuous piecewise-linear overworld coordinate manifold replacing artificial corridor clamping with zero-drift physical coordinate remapping ($\Delta X = 0.00, \Delta Y = 0.00$ across Pallet Town, Route 1, Viridian City, Route 2, Pewter City, and Route 3).
  - Formally categorized map topologies into `OVERWORLD`, `INTERIOR_ROOM`, and `DUNGEON`, anchoring interior rooms (Hero's Bedroom, Oak's Lab, Pewter Gym) directly to parent overworld door coordinates to eliminate cross-map camera whipping.
- **Standalone Executable Packaging**:
  - `PokeRL_Studio.spec`: PyInstaller 6.22.3 specification configuring Windows multiprocessing hooks, runtime asset bundling, and metadata collection for PySide6, Matplotlib, imageio, and Stable-Baselines3.
  - `src/pokefirered/paths.py`: Added dynamic filesystem path resolution helper handling both development source trees and frozen `sys._MEIPASS` execution.
- **Verification Datasets**:
  - `visual_evidence/manual_verification_trajectory.json`: Captured empirical trajectory data across Pallet Town to Pewter City used for continuous visualizer regression tests.

### Changed
- `src/pokefirered/visualization/world_mapper.py`: Refactored `KantoWorldMapper` into a thin wrapper delegating directly to `WorldTopology`.
- `src/pokefirered/visualization/swarm_renderer.py`: Integrated `get_project_root()` path resolution and zero-drift coordinate transforms.
- `scripts/play_manual.py`: Upgraded into a multi-mode testing tool supporting live dual-pane OpenCV visualizer tracking, standard GBA rendering, and offline JSON trajectory playback.
- `scripts/train.py`: Added `multiprocessing.freeze_support()` to ensure clean process spawning when invoked inside frozen Windows binaries.
- `src/pokefirered/__init__.py`: Bumped package version to `2.0.0` and exported path utility functions.
- `requirements.txt`: Added `PySide6==6.12.0` and `pyinstaller==6.22.3`.
- `README.md`: Surgically updated with desktop GUI documentation, mathematical manifold proofs, and release notes.
- `RESEARCH_CHRONICLE.md`: Appended Phase 16 (PokéRL Studio Architecture) and Phase 17 (`WorldTopology` Manifold Design).

### Removed
- Cleaned up ~30 obsolete scratch scripts in `scripts/` (`test_*.py`, `walk_*.py`, `reach_*.py`, etc.) to eliminate directory bloat.

---

## [2.0.22] - 2026-10-20 (`75bc6b1`)

### Fixed
- **World Coordinate 1:1 RAM Alignment**: Corrected lateral and vertical tile offsets across Pallet Town, Route 1, and Viridian City boundaries to match authentic local GBA RAM layout coordinates (`raw_x - 7`).
- Addressed boundary snapping glitches where player sprites temporarily clipped into background tree tiles when crossing town boundaries.

### Added
- `scripts/play_and_verify_visualizer.py`: Interactive verification harness providing live side-by-side OpenCV visualization of the GBA game screen alongside the full Kanto composite map tracker with real-time HUD telemetry.

---

## [2.0.21] - 2026-10-19 (`c3d8ba4`)

### Added
- **12-Environment Factorial Benchmark Execution**: Completed full 102,400-step comparative benchmark runs across 12 parallel environments evaluating PPO and QR-DQN against all curiosity paradigms (`NONE`, `SSIM`, `RND`, `COORD`).
- **Compiled Swarm Media**:
  - `media/benchmark_12env_4way_comparison.gif`: 4-way side-by-side animated swarm comparison.
  - `media/ppo_12env_rnd_vs_ssim.gif`: Direct head-to-head comparison between PPO+RND and PPO+SSIM.
  - `media/qrdqn_12env_rnd_vs_ssim.gif`: Direct head-to-head comparison between QR-DQN+RND and QR-DQN+SSIM.
  - `visual_evidence/swarm_visualizer/*.json`: Exported trajectory datasets for all 12 environments.

### Documentation
- Appended Phase 26 to `RESEARCH_CHRONICLE.md`, documenting aggregate throughput (1,150+ SPS), frontier coverage, and exploration efficiency metrics.

---

## [2.0.20] - 2026-10-19 (`183d65b`)

### Fixed
- Added missing `import json` statement in `src/pokefirered/callbacks.py` that caused runtime exceptions during episode trajectory serialization.
- Reordered checkpoint save operations in `scripts/train.py` to persist model weights prior to trajectory JSON serialization, ensuring models are safely preserved during extended I/O operations.

---

## [2.0.19] - 2026-10-19 (`a316b10`)

### Added
- `scripts/run_benchmark.py`: High-level benchmark orchestrator automating headless training of PPO and QR-DQN models across curiosity modes with automated logging and trajectory dumps.
- `scripts/visualize_12env_comparison.py`: Visualization tool compiling 12 parallel agent runs into synchronized side-by-side animated comparisons.

---

## [2.0.18] - 2026-10-19 (`1a01cbb`)

### Added
- `scripts/benchmark_qrdqn_envs.py`: Hardware scalability testing harness evaluating QR-DQN step throughput and GPU memory bandwidth across 1, 2, 4, 8, 12, and 16 vectorized environment instances.

### Documentation
- Appended Phase 25 to `RESEARCH_CHRONICLE.md`, analyzing CPU-GPU PCIe bus latency, CUDA tensor transfer overhead, and optimal environment worker allocation on RTX 4070 hardware.

---

## [2.0.17] - 2026-10-19 (`f8331b0`)

### Added
- **Zero-Overhead Trajectory Recording**: Integrated trajectory buffer logging inside `SaveTrajectoryCallback` in `src/pokefirered/callbacks.py`. Records `(step, env_id, bank, map_num, x, y)` tuples in host RAM during training, serializing to JSON upon completion with under 0.5% compute overhead.

### Documentation
- Appended Phase 24 to `RESEARCH_CHRONICLE.md`, detailing telemetry memory footprint and serialization benchmarks.

---

## [2.0.16] - 2026-10-19 (`4ae9eda`)

### Added
- `scripts/evaluate_qrdqn.py`: Dedicated evaluation script for trained PyTorch QR-DQN checkpoints (`.pth`), supporting greedy policy execution, human rendering, and headless GIF export.

### Changed
- `scripts/evaluate.py`: Refactored to universally detect and evaluate both Stable-Baselines3 `.zip` models (PPO) and PyTorch `.pth` models (QR-DQN).

---

## [2.0.15] - 2026-10-19 (`72d7ff4`)

### Added
- **4-Way QR-DQN Swarm Animation**: Compiled `media/qrdqn_swarm_comparison.gif` showcasing multi-agent swarm exploration under QR-DQN across `NONE`, `SSIM`, `RND`, and `COORD` curiosity settings.
- Exported empirical trajectory JSON datasets:
  - `visual_evidence/swarm_visualizer/benchmark_trajectories_QRDQN_NONE.json`
  - `visual_evidence/swarm_visualizer/benchmark_trajectories_QRDQN_SSIM.json`
  - `visual_evidence/swarm_visualizer/benchmark_trajectories_QRDQN_RND.json`
  - `visual_evidence/swarm_visualizer/benchmark_trajectories_QRDQN_COORD.json`

---

## [2.0.14] - 2026-10-19 (`b1ae062`)

### Documentation
- Appended Phase 23 to `RESEARCH_CHRONICLE.md`, detailing factorial benchmark comparisons between on-policy PPO and off-policy QR-DQN with Prioritized Experience Replay, highlighting sample efficiency gains and value distribution stability.

---

## [2.0.13] - 2026-10-19 (`7b03ac9`)

### Added
- **Vectorized QR-DQN Improvements**:
  - `src/pokefirered/models/qrdqn.py`: Implemented batched $\epsilon$-greedy action selection across all parallel environments.
  - Added vectorized intrinsic curiosity reward bonuses directly inside the transition collection loop.
  - Hooked real-time RAM telemetry tracking (visited coordinates, battles, faints) into the custom replay buffer.

---

## [2.0.12] - 2026-10-19 (`7d8180c`)

### Added
- `scripts/visualize_benchmark_swarms.py`: Multi-panel swarm rendering pipeline synchronizing 4 empirical trajectories on the canonical composite map.
- Generated `media/benchmark_swarm_comparison.gif` comparing PPO baseline against curiosity variants.

---

## [2.0.11] - 2026-10-19 (`0be262c`)

### Fixed
- **Map Overwrite Elimination**: Resized and relocated interior map insets (Hero's Bedroom, Living Room, Oak's Lab, Pewter Gym) onto empty ocean canvas zones, eliminating overworld terrain occlusion.
- Scaled Viridian Forest to 0.75x and Mt. Moon to 0.5x to preserve spatial proportions without overlapping adjacent routes.

### Changed
- Standardized swarm rendering viewport to 760x480 pixels.
- Tuned animation pacing to 125ms per frame with endpoint hold frames to enhance visual clarity.

---

## [2.0.10] - 2026-10-19 (`dc26d89`)

### Added
- **Authentic Player Sprites & Insets**:
  - `assets/pwhiddy/firered_player_sprites.png`: Extracted authentic GBA Red/Leaf walking sprites with 4-directional movement cycles (North, South, East, West).
  - Integrated high-resolution interior room insets (Pallet Town houses, Oak's Lab, Pewter Gym, Mt. Moon).
  - Monotonic milestone tracking recording progression timestamps across Pallet Town, Route 1, Viridian City, Viridian Forest, and Pewter City.

---

## [2.0.9] - 2026-10-19 (`e21c808`)

### Added
- **Distributional Reinforcement Learning (QR-DQN)**:
  - `src/pokefirered/models/qrdqn.py`: Implemented Quantile Regression Deep Q-Network with Huber quantile regression loss, polyak target synchronization, and Prioritized Experience Replay (PER).
- **Canonical 32-bit GBA Swarm Visualizer**:
  - `src/pokefirered/visualization/world_mapper.py`: First iteration of global coordinate mapper translating local GBA coordinates onto the 32-bit composite overworld map.
  - `src/pokefirered/visualization/swarm_renderer.py`: Trajectory rendering engine compositing agent markers onto the overworld map.
  - Added Peter Whidden's composite overworld map asset `assets/pwhiddy/kanto_firered_composite_full.png`.

---

## [2.0.8] - 2026-10-15 (`cdcfc34`)

### Added
- Integrated legacy demonstration media (`media/demo1.gif`, `media/AIPlays.PNG`, `media/Screenshot1.PNG`) and historical documentation (`doc/README.md`) from the legacy Linux branch.

### Changed
- Major overhaul of root `README.md`, introducing technical architecture diagrams, hardware requirements, curiosity formulations, and dual-branch structure documentation.

### Removed
- Untracked `data/custom_integrations/PokemonFireRed-GBA/rom.gba` from Git tracking to ensure copyright compliance, replacing it with `rom.sha` verification.

---

## [2.0.7] - 2026-10-14 (`c63edd7`)

### Added
- **Count-Based Coordinate Exploration**:
  - `src/pokefirered/coord_module.py`: Count-based intrinsic curiosity module providing reward bonuses inverse to visited coordinate frequency:
    $$r_{\text{coord}}(x, y) = \frac{\alpha}{\sqrt{N(x, y)} + 1}$$
- **Hybrid Curiosity Ensembles**:
  - Extended `scripts/train.py` to support runtime composition: `RND+COORD`, `SSIM+COORD`, `RND+SSIM`, and `RND+SSIM+COORD`.

---

## [2.0.6] - 2026-10-14 (`c0c3d8d`)

### Added
- **Empirical GBA RAM DMA Invariance Resolution**:
  - Resolved dynamic memory allocation (DMA) pointer shifting in GBA `SaveBlock1` and `SaveBlock2` by discovering static EWRAM overworld object event tables (`gObjectEvents[0]` at `0x02036E48`).
  - Added empirical test scripts and image proofs in `visual_evidence/ram_verification/` verifying identical coordinate tracking across room transitions and door warps.

---

## [2.0.5] - 2026-10-14 (`0933f1e`)

### Documentation
- Appended Phase 8 to `RESEARCH_CHRONICLE.md`, formalizing the Scientific Integrity Protocol, empirical reproducibility criteria, and explicit research boundaries.

---

## [2.0.4] - 2026-10-14 (`bee9d39`)

### Documentation
- Appended Phase 7 to `RESEARCH_CHRONICLE.md`, mathematically formulating the "Backtracking Paradox" where agents oscillate between familiar maps once local curiosity saturates, and deriving sample efficiency bounds for reaching Pewter City.

---

## [2.0.3] - 2026-10-14 (`8607f58`)

### Added
- **GPU-Accelerated Structural Similarity (SSIM) Curiosity**:
  - `src/pokefirered/ssim_module.py`: Visual curiosity exploration module calculating PyTorch-accelerated SSIM differences between consecutive observations and historical memory buffers.
  - Integrated SSIM curiosity rewards into the PPO training pipeline.

### Documentation
- Appended Phase 6 to `RESEARCH_CHRONICLE.md` analyzing SSIM sensitivity to non-navigational visual dynamics (grass rustle, text boxes).

---

## [2.0.2] - 2026-10-14 (`bf16106`)

### Added
- `scripts/benchmark_envs.py`: Hardware benchmarking utility sweeping parallel environment configurations (1 to 16) to identify optimal step-per-second (SPS) throughput.
- Added RAM exploration tile tracking and automated evaluation GIF export in `src/pokefirered/callbacks.py`.

### Changed
- Optimized Random Network Distillation (RND) network architecture in `src/pokefirered/rnd.py` with normalized running observation statistics and adaptive reward scaling.

---

## [2.0.1] - 2026-10-14 (`c952764`)

### Fixed
- **Multi-Environment Process Isolation**: Replaced `DummyVecEnv` with `SubprocVecEnv` in `src/pokefirered/env_factory.py` for multi-environment training runs, resolving shared-memory state corruption and emulator collisions across parallel processes.

---

## [2.0.0] - 2026-10-14 (`402c201`)

### 🌟 Milestone: Windows Platform Creation

This milestone marks the creation of the modern **Windows-native** reinforcement learning workspace, migrating away from the monolithic Linux/WSL2 setup into a structured, modular Python package.

> [!NOTE]
> Based on repository evidence, this milestone established the initial working Windows implementation with GPU-accelerated PPO, RND curiosity, and manual control. Further optimizations for process isolation (`SubprocVecEnv`), DMA memory invariance, and multi-agent visualization were completed in subsequent commits.

### Platform Support
- **Windows-Native Integration**: Compiled and linked `stable-retro` under Windows Python 3.10 with MinGW and MSVC compatibility, removing Linux ELF binary dependencies.

### Added
- **Modular Package Structure (`src/pokefirered/`)**:
  - `env_factory.py`: Vectorized environment factory supporting custom integrations, WarpFrame downsampling (84x84 grayscale), StochasticFrameSkip, and Atari wrappers.
  - `wrappers.py`: Action filtering wrapper reducing GBA gamepad to 6 discrete actions (`DOWN`, `LEFT`, `RIGHT`, `UP`, `A`, `B`) and custom RAM reward hooks.
  - `rewards.py`: Memory-mapped reward engine calculating rewards from HP, badge counts, party levels, and exploration events.
  - `rnd.py`: PyTorch GPU implementation of Random Network Distillation (target and predictor CNN networks).
  - `callbacks.py`: TensorBoard telemetry logging for policy entropy, value loss, intrinsic reward loss, and SPS.
  - `keyboard_input.py`: Windows-native interactive keyboard capture using `msvcrt`.
- **Command-Line Entrypoints (`scripts/`)**:
  - `scripts/train.py`: Unified PPO training CLI supporting configurable parallel environments, learning rates, and RND hyperparameters.
  - `scripts/evaluate.py`: Policy evaluation runner supporting real-time rendering and headless GIF recording.
  - `scripts/play_manual.py`: Interactive manual control script for testing game physics, RAM offsets, and rewards.
- **Custom Integration Files**:
  - `data/custom_integrations/PokemonFireRed-GBA/`: ROM integration directory containing `rom.sha`, `metadata.json`, and initial save states (`BeginningPallet.state`, `BeginningPalletGotPokeballs.state`, `BeginningPalletReceivedBulbasaur.state`).
- **Dependencies & Environment**:
  - `requirements.txt`: Standardized Windows dependency manifest (`torch`, `stable-baselines3`, `gymnasium`, `opencv-python`).

---

## [1.0.11] - 2026-10-14 (`51912f8`)

### Build / Infrastructure
- Initialized clean Git repository on Windows development workstation.
- Added root `.gitignore` isolating legacy Linux source code (`original_src/`), virtual environments (`.venv/`), checkpoints, logs, and sensitive ROM binaries.

---

## [1.0.10] - 2025-08-11 (`a458cc3`)

### Build / Infrastructure
- Modified filesystem permissions for `gym-retro-integration` binary (mode `100755` to `100644`).
- Serves as the final historical commit on the `legacy-linux` branch prior to migration.

---

## [1.0.9] - 2025-08-11 (`7f24c77`)

### Changed
- Merge commit uniting parallel documentation updates (`9260aa0`) with screenshot additions (`bf2f15e`).

---

## [1.0.8] - 2025-08-11 (`9260aa0`)

### Documentation
- Updated `README.md` to reference `media/Screenshot1.PNG` in the media showcase section.

---

## [1.0.7] - 2025-08-11 (`bf2f15e`)

### Added
- `media/Screenshot1.PNG`: Added high-resolution gameplay screenshot showcasing battle interface and text box rendering under Linux.

---

## [1.0.6] - 2025-08-11 (`6101419`)

### Documentation
- Updated `README.md` with explicit Python 3.10+ virtual environment requirements and CUDA GPU acceleration notes.

---

## [1.0.5] - 2025-08-11 (`7eeaf71`)

### Changed
- Merge commit integrating optimized `demo1.gif` asset (`fc4e0fb`) with upstream documentation additions (`187c299`).

---

## [1.0.4] - 2025-08-11 (`fc4e0fb`)

### Changed
- Re-encoded `media/demo1.gif`, compressing asset size from 79.8 MB to 24.9 MB to improve repository cloning performance.

---

## [1.0.3] - 2025-07-02 (`187c299`)

### Documentation
- Updated `README.md` with additional notes on training workflows and checkpoint management.

---

## [1.0.2] - 2025-07-02 (`303c7d9`)

### Refactored
- Renamed `media/AI Plays.PNG` to `media/AIPlays.PNG` to eliminate whitespace and ensure cross-platform URI compatibility.

---

## [1.0.1] - 2025-07-02 (`d5ec5ba`)

### Added
- `media/AI Plays.PNG`: Added initial gameplay screenshot demonstrating agent movement in the starting area.

### Changed
- Updated `README.md` to display the gameplay screenshot.

---

## [1.0.0] - 2025-07-02 (`95f08be`)

### 🌟 Milestone: Linux Working Release

This milestone marks the point at which the initial Linux/WSL2 version reached a verified, reproducible working condition.

> [!NOTE]
> In this milestone, the project operated as a collection of monolithic scripts (`FireRedRender.py`, `FireRedRewardManager.py`) driven by an upstream build of `stable-retro`. It was functional for training and evaluation on Linux, but lacked modern modular packaging, DMA-invariant RAM hooks, multi-paradigm curiosity modules, and Windows support.

### Platform Support
- **Linux / WSL2 Functional Baseline**: First complete set of instructions enabling external developers to build and execute the RL agent on Ubuntu / WSL2.

### Added
- `setup.txt`: Complete bash setup and compilation script documenting:
  - System package prerequisites: `sudo apt-get install python3.10 python3-pip git zlib1g-dev libopenmpi-dev ffmpeg libqt5opengl5-dev qtbase5-dev cmake`
  - Virtual environment creation (`~/vretro`)
  - Source build and compilation of Farama Foundation `stable-retro`: `cmake . -DBUILD_UI=ON -UPYLIB_DIRECTORY && make -j$(nproc)`
  - Python package installation: `pip3 install stable_baselines3[extra]`
- Operational verification: Combined with `FireRedRender.py`, `FireRedRewardManager.py`, and `PokemonFireRed-GBA_ppo_model_8penv.zip`, users could execute `python FireRedRender.py` to train or run the model under WSL Ubuntu.

---

## [0.0.6] - 2025-07-02 (`e682e97`)

### Added
- `README.md`: Created initial root-level project README for GitHub display, defining the agent goals, CNN policy overview, RAM-derived reward signals, WSL Ubuntu environment requirements, and basic execution instructions (`python FireRedRender.py`).

---

## [0.0.5] - 2025-07-02 (`b68822a`)

### Added
- `media/demo1.gif`: Added 79.8 MB animated GIF recording demonstrating the PPO agent navigating the Pokémon FireRed overworld and interacting with NPCs on Linux.

---

## [0.0.4] - 2025-07-02 (`f7f52ad`)

### Added
- `PokemonFireRed-GBA_ppo_model_8penv.zip`: Updated 21.6 MB pretrained Stable-Baselines3 PPO model checkpoint trained across 8 parallel emulator environments.

---

## [0.0.3] - 2025-07-02 (`917f353`)

### Added
- `doc/README.md`: Created preliminary technical documentation detailing the reward engineering architecture:
  - Visual exploration signals (discovering new areas)
  - Level-up events
  - Self and opponent fainting rewards
  - Real-time HP and battle telemetry derived from direct emulator RAM reads

---

## [0.0.2] - 2025-07-02 (`9541a92`)

### Removed
- Cleaned up obsolete upstream documentation files from `docs/` (`conf.py`, `developing.md`, `getting_started.md`, `integration.md`, `python.md`, `release_notes.md`) to focus repository on Pokémon FireRed.

---

## [0.0.1] - 2025-07-02 (`a8e5a7e`)

### Removed
- Removed 6,405 vendored third-party C++ source files, build scripts, and emulator cores (`cores/32x`, `third-party/pybind11`, etc.) from the initial commit dump to isolate project-specific Python code.

---

## [0.0.0] - 2025-04-10 (`9f73471`)

### 🚀 Initial Development Baseline

The initial baseline commit of the repository.

### Added
- **Monolithic Linux Scripts**:
  - `FireRedRender.py`: Initial monolithic script handling environment initialization, reward calculation, and policy training/rendering.
  - `FireRedRewardManager.py`: Early emulator RAM reward manager extracting player battle statistics and map coordinates.
  - `FireRed_MasterView.py`: Multi-environment visualization prototype.
  - `FireRed_RenderWindow.py`: Rendering window display logic.
  - `PokemonFireRed-GBA_ppo_model_8penv.zip`: Initial baseline pretrained PPO model weights (21.6 MB).
- **Upstream Snapshot**:
  - Full source tree snapshot of `gym-retro` and associated emulation libraries.
