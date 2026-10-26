"""
Prioritized Experience Replay (PER) Buffer with Binary SumTree.
Provides O(log N) priority updates and prefix-sum sampling for off-policy RL.
Based on Schaul et al. (2015) 'Prioritized Experience Replay'.
"""
from typing import Tuple, List, Optional
import numpy as np
import torch

class SumTree:
    """
    Binary SumTree and MinTree data structure for O(log N) prioritized sampling.
    Tree structure:
    - Root at index 1
    - Total tree size: 2 * capacity
    - Leaf nodes (data priorities): indices [capacity ... 2*capacity - 1]
    """
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.tree = np.zeros(2 * capacity, dtype=np.float32)
        self.min_tree = np.full(2 * capacity, float('inf'), dtype=np.float32)

    def update(self, data_idx: int, priority: float):
        tree_idx = data_idx + self.capacity
        self.tree[tree_idx] = priority
        self.min_tree[tree_idx] = priority

        parent = tree_idx // 2
        while parent > 0:
            self.tree[parent] = self.tree[2 * parent] + self.tree[2 * parent + 1]
            self.min_tree[parent] = min(self.min_tree[2 * parent], self.min_tree[2 * parent + 1])
            parent //= 2

    def get_leaf(self, val: float) -> Tuple[int, float]:
        idx = 1
        while idx < self.capacity:
            left = 2 * idx
            right = left + 1
            if val <= self.tree[left]:
                idx = left
            else:
                val -= self.tree[left]
                idx = right
        data_idx = idx - self.capacity
        return data_idx, self.tree[idx]

    @property
    def total_priority(self) -> float:
        return float(self.tree[1])

    @property
    def min_priority(self) -> float:
        return float(self.min_tree[1])


class PrioritizedReplayBuffer:
    """
    Circular Prioritized Experience Replay buffer supporting multi-step transitions,
    importance sampling (IS) correction, and dynamic priority updates via TD-errors.
    """
    def __init__(
        self,
        capacity: int,
        obs_shape: Tuple[int, ...],
        device: str = "cpu",
        alpha: float = 0.6,
        beta_start: float = 0.4,
        beta_end: float = 1.0,
        beta_steps: int = 100_000,
        eps: float = 1e-5
    ):
        self.capacity = capacity
        self.obs_shape = obs_shape
        self.device = torch.device(device)
        self.alpha = alpha
        self.beta_start = beta_start
        self.beta_end = beta_end
        self.beta_steps = beta_steps
        self.eps = eps

        self.tree = SumTree(capacity)
        self.max_priority = 1.0
        self.ptr = 0
        self.size = 0
        self.step_count = 0

        # Memory allocations (uint8 for image observations to conserve RAM)
        self.states = np.zeros((capacity, *obs_shape), dtype=np.uint8)
        self.actions = np.zeros((capacity,), dtype=np.int64)
        self.rewards = np.zeros((capacity,), dtype=np.float32)
        self.next_states = np.zeros((capacity, *obs_shape), dtype=np.uint8)
        self.dones = np.zeros((capacity,), dtype=np.float32)

    @property
    def current_beta(self) -> float:
        fraction = min(1.0, self.step_count / max(1, self.beta_steps))
        return self.beta_start + fraction * (self.beta_end - self.beta_start)

    def add(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """Adds a single transition with initial max priority."""
        self.states[self.ptr] = state
        self.actions[self.ptr] = action
        self.rewards[self.ptr] = reward
        self.next_states[self.ptr] = next_state
        self.dones[self.ptr] = 1.0 if done else 0.0

        # Assign maximum priority so new transitions are sampled at least once
        self.tree.update(self.ptr, self.max_priority ** self.alpha)

        self.ptr = (self.ptr + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)
        self.step_count += 1

    def sample(self, batch_size: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, np.ndarray]:
        """
        Samples a prioritized mini-batch and computes Importance Sampling weights.
        Returns: (states, actions, rewards, next_states, dones, weights, indices)
        """
        indices = []
        priorities = []
        segment = self.tree.total_priority / batch_size

        for i in range(batch_size):
            a = segment * i
            b = segment * (i + 1)
            val = np.random.uniform(a, b)
            data_idx, priority = self.tree.get_leaf(val)
            # Guard against edge-case uninitialized leaves
            data_idx = min(data_idx, self.size - 1)
            indices.append(data_idx)
            priorities.append(priority)

        indices = np.array(indices, dtype=np.int64)
        probs = np.array(priorities, dtype=np.float32) / max(1e-8, self.tree.total_priority)

        # Importance sampling weights: w_i = (N * P(i)) ^ (-beta)
        beta = self.current_beta
        weights = (self.size * probs) ** (-beta)
        # Normalize weights by max weight for stability
        weights /= max(1e-8, weights.max())

        # Convert to PyTorch tensors
        s_tensor = torch.from_numpy(self.states[indices]).to(self.device).float() / 255.0
        a_tensor = torch.from_numpy(self.actions[indices]).to(self.device).long()
        r_tensor = torch.from_numpy(self.rewards[indices]).to(self.device).float()
        ns_tensor = torch.from_numpy(self.next_states[indices]).to(self.device).float() / 255.0
        d_tensor = torch.from_numpy(self.dones[indices]).to(self.device).float()
        w_tensor = torch.from_numpy(weights).to(self.device).float()

        return s_tensor, a_tensor, r_tensor, ns_tensor, d_tensor, w_tensor, indices

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        """Updates priorities in SumTree based on observed absolute TD-errors."""
        for idx, error in zip(indices, td_errors):
            priority = (float(np.abs(error)) + self.eps) ** self.alpha
            self.max_priority = max(self.max_priority, float(np.abs(error)) + self.eps)
            self.tree.update(int(idx), priority)

    def save(self, path):
        """Serializes replay buffer states, transitions, and SumTree priorities."""
        from pathlib import Path
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            states=self.states,
            actions=self.actions,
            rewards=self.rewards,
            next_states=self.next_states,
            dones=self.dones,
            tree=self.tree.tree,
            min_tree=self.tree.min_tree,
            meta=np.array([self.ptr, self.size, self.step_count, self.max_priority], dtype=np.float64)
        )

    def load(self, path):
        """Loads serialized replay buffer states, transitions, and SumTree priorities."""
        from pathlib import Path
        path = Path(path)
        data = np.load(path)
        self.states[:] = data["states"]
        self.actions[:] = data["actions"]
        self.rewards[:] = data["rewards"]
        self.next_states[:] = data["next_states"]
        self.dones[:] = data["dones"]
        self.tree.tree[:] = data["tree"]
        self.tree.min_tree[:] = data["min_tree"]
        meta = data["meta"]
        self.ptr = int(meta[0])
        self.size = int(meta[1])
        self.step_count = int(meta[2])
        self.max_priority = float(meta[3])

    def __len__(self) -> int:
        return self.size
