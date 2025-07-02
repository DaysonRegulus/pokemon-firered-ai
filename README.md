# Pokémon FireRed AI Agent

An AI agent trained to play **Pokémon FireRed** using the **Stable-Baselines3** reinforcement learning framework.

## 🎯 Project Goal

Train reinforcement learning (RL) agents capable of playing Pokémon FireRed effectively, using visual feedback and emulator RAM values as reward signals.

## 🧠 Agent Overview

This project uses a CNN-based policy to train the agent, with reward signals engineered from:

* Visual exploration (new areas discovered)
* Pokémon leveling up
* Fainting events (self and opponent)
* Real-time battle statistics (HP, level, etc.)

These signals are derived from direct memory (RAM) reads of the emulator.

## 🚀 Getting Started

To run the project, simply execute:

```bash
python FireRedRender.py
```

This will start the training process (or load an existing pre-trained model if available).

All environment setup (gym, stable-retro, reward manager) is handled internally. The script runs in a compact form, assuming dependencies are already installed.

## 🖥️ Environment

* WSL Ubuntu
* Virtual Environment (venv)
* Python 3.10+
* GPU Acceleration (CUDA supported)

## 🔁 Workflow

* Parallelized environments for faster training
* Reward management via RAM data
* Model checkpoints for resuming training

## 📁 File Structure

```
├── FireRedRender.py         # Main training loop
├── FireRedRewardManager.py # Custom reward logic from emulator RAM
├── model/                   # Stores checkpoints of trained models
├── README.md
```

## 📽️ Media Showcase

<!-- TODO: Add GIFs or YouTube link demonstrating training progress or gameplay -->

## 🙌 Acknowledgements

* [Farama Foundation](https://farama.org) for **stable-retro**
* [MatPoliquin](https://github.com/MatPoliquin) for foundational work on RAM mapping and wrappers
* [Peter Whidden](https://github.com/peterwhidden) for key contributions to retro gaming AI environments

## 📄 License

<!-- TODO: Add license later -->
