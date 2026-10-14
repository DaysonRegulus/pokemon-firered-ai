import numpy as np
import torch
import torch.nn as nn


class RunningMeanStd:
    """
    Running mean and standard deviation calculator using Welford's algorithm.
    Used to normalize intrinsic curiosity rewards.
    """
    def __init__(self, epsilon=1e-4):
        self.mean = 0.0
        self.var = 1.0
        self.count = epsilon

    def update(self, x):
        batch_mean = np.mean(x)
        batch_var = np.var(x)
        batch_count = len(x)

        delta = batch_mean - self.mean
        total_count = self.count + batch_count

        new_mean = self.mean + delta * batch_count / total_count

        m_a = self.var * self.count
        m_b = batch_var * batch_count
        m2 = m_a + m_b + delta**2 * self.count * batch_count / total_count
        new_var = m2 / total_count

        self.mean = new_mean
        self.var = new_var
        self.count = total_count

    @property
    def std(self):
        return np.sqrt(self.var + 1e-8)


class RNDNetwork(nn.Module):
    """
    Convolutional feature extractor for Random Network Distillation.
    Takes (B, C, H, W) images and outputs feature vectors of size feature_dim.
    """
    def __init__(self, input_channels=1, feature_dim=128):
        super().__init__()

        self.cnn = nn.Sequential(
            nn.Conv2d(input_channels, 32, kernel_size=8, stride=4),  # 84 -> ~20
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),             # ~20 -> ~9
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),             # ~9 -> ~7
            nn.ReLU(),
            nn.Flatten(),
        )

        with torch.no_grad():
            dummy = torch.zeros(1, input_channels, 84, 84)
            n_flatten = self.cnn(dummy).shape[1]

        self.fc = nn.Sequential(
            nn.Linear(n_flatten, 256),
            nn.ReLU(),
            nn.Linear(256, feature_dim),
        )

    def forward(self, x):
        x = self.cnn(x)
        return self.fc(x)


class RNDModule:
    """
    Random Network Distillation (RND) module.
    Calculates intrinsic rewards based on prediction error between
    a fixed, randomly initialized target network and a trained predictor network.
    """
    def __init__(self, device="cuda", lr=5e-5, clip_val=5.0):
        self.device = device
        self.clip_val = clip_val

        self.target = RNDNetwork().to(device)
        self.predictor = RNDNetwork().to(device)

        # Freeze the target network
        for param in self.target.parameters():
            param.requires_grad = False

        self.optimizer = torch.optim.Adam(self.predictor.parameters(), lr=lr)
        self.rms = RunningMeanStd()

    def compute_intrinsic_reward(self, obs):
        """
        Compute intrinsic exploration reward for a batch of observations.
        obs: torch tensor [N, C, H, W]
        """
        with torch.no_grad():
            target_feat = self.target(obs)
            pred_feat = self.predictor(obs)
            error = torch.mean((pred_feat - target_feat) ** 2, dim=1)

        error_np = error.cpu().numpy()
        self.rms.update(error_np)
        return error_np

    def train(self, obs):
        """
        Train the predictor network to minimize MSE against the target network.
        """
        target_feat = self.target(obs).detach()
        pred_feat = self.predictor(obs)

        loss = torch.mean((pred_feat - target_feat) ** 2)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()

    def save(self, path):
        torch.save({
            "predictor_state_dict": self.predictor.state_dict(),
            "target_state_dict": self.target.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "rms_mean": self.rms.mean,
            "rms_var": self.rms.var,
            "rms_count": self.rms.count,
        }, path)

    def load(self, path):
        checkpoint = torch.load(path, map_location=self.device)
        self.predictor.load_state_dict(checkpoint["predictor_state_dict"])
        self.target.load_state_dict(checkpoint["target_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.rms.mean = checkpoint["rms_mean"]
        self.rms.var = checkpoint["rms_var"]
        self.rms.count = checkpoint["rms_count"]
