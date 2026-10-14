import numpy as np
import torch
import torch.nn as nn


class RunningMeanStd:
    """
    Running mean and standard deviation calculator using Welford's algorithm.
    Used for observation and intrinsic reward normalization.
    """
    def __init__(self, shape=(), epsilon=1e-4):
        self.mean = np.zeros(shape, dtype=np.float32)
        self.var = np.ones(shape, dtype=np.float32)
        self.count = epsilon

    def update(self, x):
        batch_mean = np.mean(x, axis=0)
        batch_var = np.var(x, axis=0)
        batch_count = x.shape[0] if hasattr(x, "shape") and len(x.shape) > 0 else len(x)

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


def init_weights(m):
    """Orthogonal initialization for RND layers."""
    if isinstance(m, (nn.Conv2d, nn.Linear)):
        nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
        if m.bias is not None:
            nn.init.constant_(m.bias, 0.0)


class RNDNetwork(nn.Module):
    """
    Convolutional feature extractor for Random Network Distillation.
    Takes normalized (B, C, H, W) images and outputs feature vectors of size feature_dim.
    """
    def __init__(self, input_channels=1, feature_dim=128, is_predictor=False):
        super().__init__()

        self.cnn = nn.Sequential(
            nn.Conv2d(input_channels, 32, kernel_size=8, stride=4),  # 84 -> ~20
            nn.LeakyReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),             # ~20 -> ~9
            nn.LeakyReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),             # ~9 -> ~7
            nn.LeakyReLU(),
            nn.Flatten(),
        )

        with torch.no_grad():
            dummy = torch.zeros(1, input_channels, 84, 84)
            n_flatten = self.cnn(dummy).shape[1]

        if is_predictor:
            # Predictor has extra capacity to learn the target function
            self.fc = nn.Sequential(
                nn.Linear(n_flatten, 512),
                nn.ReLU(),
                nn.Linear(512, 512),
                nn.ReLU(),
                nn.Linear(512, feature_dim),
            )
        else:
            self.fc = nn.Sequential(
                nn.Linear(n_flatten, 512),
                nn.ReLU(),
                nn.Linear(512, feature_dim),
            )

        self.apply(init_weights)

    def forward(self, x):
        x = self.cnn(x)
        return self.fc(x)


class RNDModule:
    """
    Random Network Distillation (RND) Module.
    Calculates normalized intrinsic rewards based on prediction error between
    a fixed, randomly initialized target network and a trained predictor network.
    """
    def __init__(self, device="cuda", lr=1e-4, clip_val=5.0, obs_shape=(1, 84, 84)):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.clip_val = clip_val

        # Networks
        self.target = RNDNetwork(input_channels=obs_shape[0], is_predictor=False).to(self.device)
        self.predictor = RNDNetwork(input_channels=obs_shape[0], is_predictor=True).to(self.device)

        # Freeze the target network permanently
        for param in self.target.parameters():
            param.requires_grad = False

        self.optimizer = torch.optim.Adam(self.predictor.parameters(), lr=lr)

        # Running normalizers
        self.rms_obs = RunningMeanStd(shape=obs_shape)
        self.rms_reward = RunningMeanStd(shape=())

    def normalize_obs(self, obs_tensor):
        """
        Normalize observation tensor [B, C, H, W] using running mean and std.
        Clips values to [-5, 5] for numerical stability.
        """
        mean = torch.as_tensor(self.rms_obs.mean, dtype=torch.float32, device=self.device)
        std = torch.as_tensor(self.rms_obs.std, dtype=torch.float32, device=self.device)
        norm_obs = (obs_tensor - mean) / std
        return torch.clamp(norm_obs, -5.0, 5.0)

    def compute_intrinsic_reward(self, obs_raw_np):
        """
        Compute normalized intrinsic exploration reward for a batch of observations.
        obs_raw_np: numpy array of shape [B, C, H, W] in range [0, 1]
        """
        self.rms_obs.update(obs_raw_np)

        obs_tensor = torch.as_tensor(obs_raw_np, dtype=torch.float32, device=self.device)
        obs_norm = self.normalize_obs(obs_tensor)

        with torch.no_grad():
            target_feat = self.target(obs_norm)
            pred_feat = self.predictor(obs_norm)
            # MSE per sample
            raw_error = torch.mean((pred_feat - target_feat) ** 2, dim=1).cpu().numpy()

        self.rms_reward.update(raw_error)

        # Normalize by running standard deviation
        normalized_reward = raw_error / (self.rms_reward.std + 1e-8)
        clipped_reward = np.clip(normalized_reward, 0.0, self.clip_val)

        return clipped_reward, raw_error

    def train_batch(self, obs_raw_np, epochs=4, batch_size=256):
        """
        Train predictor network on rollout observations across multiple epochs and mini-batches.
        """
        n_samples = len(obs_raw_np)
        if n_samples == 0:
            return 0.0

        obs_tensor = torch.as_tensor(obs_raw_np, dtype=torch.float32, device=self.device)
        obs_norm = self.normalize_obs(obs_tensor)

        epoch_losses = []
        indices = np.arange(n_samples)

        for _ in range(epochs):
            np.random.shuffle(indices)
            for start in range(0, n_samples, batch_size):
                end = start + batch_size
                batch_idx = indices[start:end]

                batch_obs = obs_norm[batch_idx]

                with torch.no_grad():
                    target_feat = self.target(batch_obs)

                pred_feat = self.predictor(batch_obs)
                loss = torch.mean((pred_feat - target_feat) ** 2)

                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.predictor.parameters(), max_norm=0.5)
                self.optimizer.step()

                epoch_losses.append(loss.item())

        return float(np.mean(epoch_losses)) if epoch_losses else 0.0

    def save(self, path):
        torch.save({
            "predictor_state_dict": self.predictor.state_dict(),
            "target_state_dict": self.target.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "rms_obs_mean": self.rms_obs.mean,
            "rms_obs_var": self.rms_obs.var,
            "rms_obs_count": self.rms_obs.count,
            "rms_reward_mean": self.rms_reward.mean,
            "rms_reward_var": self.rms_reward.var,
            "rms_reward_count": self.rms_reward.count,
        }, path)

    def load(self, path):
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        self.predictor.load_state_dict(checkpoint["predictor_state_dict"])
        self.target.load_state_dict(checkpoint["target_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.rms_obs.mean = checkpoint["rms_obs_mean"]
        self.rms_obs.var = checkpoint["rms_obs_var"]
        self.rms_obs.count = checkpoint["rms_obs_count"]
        self.rms_reward.mean = checkpoint["rms_reward_mean"]
        self.rms_reward.var = checkpoint["rms_reward_var"]
        self.rms_reward.count = checkpoint["rms_reward_count"]
