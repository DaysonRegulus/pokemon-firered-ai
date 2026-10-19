"""
Quantile Regression Deep Q-Network (QR-DQN) with Dueling Architecture and Prioritized Experience Replay (PER).
References:
- Dabney et al. (2018): 'Distributional Reinforcement Learning with Quantile Regression'
- Wang et al. (2016): 'Dueling Network Architectures for Deep Reinforcement Learning'
- Schaul et al. (2015): 'Prioritized Experience Replay'
"""
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .replay_buffer import PrioritizedReplayBuffer


class DuelingQRDQNNetwork(nn.Module):
    """
    Distributional Dueling Q-Network for Quantile Regression.
    Maps an input observation tensor (B, C, H, W) to a return distribution
    represented as N quantiles for each discrete action: (B, num_actions, num_quantiles).
    """
    def __init__(self, in_channels: int, num_actions: int, num_quantiles: int = 32):
        super().__init__()
        self.num_actions = num_actions
        self.num_quantiles = num_quantiles

        # NatureCNN convolutional backbone
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=8, stride=4),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),
            nn.ReLU(),
            nn.Flatten()
        )

        # Compute conv output dimension dynamically
        with torch.no_grad():
            dummy = torch.zeros(1, in_channels, 84, 84)
            conv_out = self.conv(dummy).shape[1]

        # Shared representation layer
        self.fc = nn.Sequential(
            nn.Linear(conv_out, 512),
            nn.ReLU()
        )

        # Dueling Streams:
        # Value Stream: V(s) -> (B, 1, num_quantiles)
        self.val_stream = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, num_quantiles)
        )

        # Advantage Stream: A(s, a) -> (B, num_actions * num_quantiles)
        self.adv_stream = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, num_actions * num_quantiles)
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Forward pass returning quantile values: (B, num_actions, num_quantiles)
        """
        feats = self.fc(self.conv(state))
        val = self.val_stream(feats).view(-1, 1, self.num_quantiles)
        adv = self.adv_stream(feats).view(-1, self.num_actions, self.num_quantiles)

        # Dueling aggregation: Z(s, a) = V(s) + (A(s, a) - mean_a(A(s, a)))
        adv_mean = adv.mean(dim=1, keepdim=True)
        quantiles = val + (adv - adv_mean)
        return quantiles

    def get_q_values(self, state: torch.Tensor) -> torch.Tensor:
        """
        Computes scalar expected Q(s, a) as the mean across all quantiles: (B, num_actions)
        """
        quantiles = self.forward(state)
        return quantiles.mean(dim=-1)


class QRDQNAgent:
    """
    Complete QR-DQN Agent with Prioritized Experience Replay (PER),
    Dueling streams, Double DQN action selection, and Quantile Huber loss.
    """
    def __init__(
        self,
        in_channels: int,
        num_actions: int,
        num_quantiles: int = 32,
        learning_rate: float = 1e-4,
        gamma: float = 0.99,
        tau: float = 0.005,
        kappa: float = 1.0,
        buffer_size: int = 50_000,
        batch_size: int = 64,
        device: str = "cpu"
    ):
        self.num_actions = num_actions
        self.num_quantiles = num_quantiles
        self.gamma = gamma
        self.tau = tau
        self.kappa = kappa
        self.batch_size = batch_size
        self.device = torch.device(device)

        # Cumulative probability midpoints: tau_i = (2i - 1) / (2N)
        tau_midpoints = torch.arange(0.5, num_quantiles, 1.0, device=self.device) / num_quantiles
        self.tau_hat = tau_midpoints.view(1, num_quantiles, 1) # Shape: (1, N, 1)

        # Policy & Target Networks
        self.online_net = DuelingQRDQNNetwork(in_channels, num_actions, num_quantiles).to(self.device)
        self.target_net = DuelingQRDQNNetwork(in_channels, num_actions, num_quantiles).to(self.device)
        self.target_net.load_state_dict(self.online_net.state_dict())
        self.target_net.eval()

        self.optimizer = torch.optim.Adam(self.online_net.parameters(), lr=learning_rate)

        # Prioritized Replay Buffer
        self.buffer = PrioritizedReplayBuffer(
            capacity=buffer_size,
            obs_shape=(in_channels, 84, 84),
            device=device,
            alpha=0.6,
            beta_start=0.4,
            beta_end=1.0
        )

        self.train_steps = 0

    def select_action(self, state: np.ndarray, epsilon: float = 0.05) -> int:
        """Epsilon-greedy action selection for a single observation."""
        if np.random.random() < epsilon:
            return int(np.random.randint(self.num_actions))

        with torch.no_grad():
            s_tensor = torch.from_numpy(state).unsqueeze(0).to(self.device).float() / 255.0
            q_values = self.online_net.get_q_values(s_tensor)
            return int(q_values.argmax(dim=-1).item())

    def select_actions(self, states: np.ndarray, epsilon: float = 0.05) -> list:
        """Batch epsilon-greedy action selection for parallel environments."""
        batch_size = states.shape[0]
        random_actions = np.random.randint(0, self.num_actions, size=batch_size)
        random_mask = np.random.random(size=batch_size) < epsilon

        if np.all(random_mask):
            return random_actions.tolist()

        with torch.no_grad():
            s_tensor = torch.as_tensor(states, dtype=torch.float32, device=self.device) / 255.0
            q_values = self.online_net.get_q_values(s_tensor)
            greedy_actions = q_values.argmax(dim=-1).cpu().numpy()

        chosen_actions = np.where(random_mask, random_actions, greedy_actions)
        return chosen_actions.tolist()

    def update(self) -> Optional[Dict[str, float]]:
        """
        Samples a prioritized mini-batch and performs a Quantile Huber Loss gradient step.
        """
        if len(self.buffer) < self.batch_size:
            return None

        # Sample prioritized mini-batch
        states, actions, rewards, next_states, dones, is_weights, indices = self.buffer.sample(self.batch_size)

        # 1. Compute target quantiles using Double DQN
        with torch.no_grad():
            # Action selection from online net: a* = argmax_a Q_online(s', a)
            next_q_values = self.online_net.get_q_values(next_states)
            next_actions = next_q_values.argmax(dim=-1) # (B,)

            # Target quantiles from target net: Z_target(s', a*)
            next_quantiles_all = self.target_net(next_states) # (B, num_actions, N)
            next_quantiles = next_quantiles_all[torch.arange(self.batch_size), next_actions] # (B, N)

            # Bellman target distribution: T = r + gamma * (1 - done) * Z_target
            target_quantiles = rewards.unsqueeze(1) + self.gamma * (1.0 - dones.unsqueeze(1)) * next_quantiles # (B, N)

        # 2. Compute current quantiles for selected actions
        current_quantiles_all = self.online_net(states) # (B, num_actions, N)
        current_quantiles = current_quantiles_all[torch.arange(self.batch_size), actions] # (B, N)

        # 3. Pairwise Quantile Huber Loss
        # Pairwise error u: (B, N, N) where u[b, i, j] = target[b, j] - current[b, i]
        u = target_quantiles.unsqueeze(1) - current_quantiles.unsqueeze(2)

        # Huber loss with threshold kappa
        huber_loss = F.huber_loss(u, torch.zeros_like(u), delta=self.kappa, reduction='none')

        # Quantile penalty weight: |tau_i - I(u < 0)|
        weight = torch.abs(self.tau_hat - (u < 0).float())

        # Quantile Huber loss per transition: sum over j (targets), mean over i (quantiles)
        loss_per_sample = (weight * huber_loss).sum(dim=2).mean(dim=1) # (B,)

        # Weighted loss by Importance Sampling weights
        loss = (is_weights * loss_per_sample).mean()

        # Optimize online network
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.online_net.parameters(), max_norm=10.0)
        self.optimizer.step()

        # 4. Update priorities in replay buffer based on TD-errors
        with torch.no_grad():
            td_errors = u.abs().mean(dim=(1, 2)).cpu().numpy()
            self.buffer.update_priorities(indices, td_errors)

        # 5. Soft Polyak update of target network
        for param, target_param in zip(self.online_net.parameters(), self.target_net.parameters()):
            target_param.data.copy_(self.tau * param.data + (1.0 - self.tau) * target_param.data)

        self.train_steps += 1

        return {
            "qr_loss": float(loss.item()),
            "mean_q": float(current_quantiles.mean().item()),
            "mean_td_error": float(td_errors.mean()),
            "beta": float(self.buffer.current_beta),
        }

    def save(self, path: Path):
        """Saves agent weights and optimizer state."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "online_net": self.online_net.state_dict(),
            "target_net": self.target_net.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "train_steps": self.train_steps,
        }, path)
        print(f"[QRDQN] Saved model checkpoint to: {path}")

    def load(self, path: Path):
        """Loads agent weights and optimizer state."""
        path = Path(path)
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        self.online_net.load_state_dict(checkpoint["online_net"])
        self.target_net.load_state_dict(checkpoint["target_net"])
        self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.train_steps = checkpoint.get("train_steps", 0)
        print(f"[QRDQN] Loaded model checkpoint from: {path}")
