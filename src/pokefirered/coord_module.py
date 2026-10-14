from collections import defaultdict
from pathlib import Path
import numpy as np
import torch


class CoordinateExplorationModule:
    """
    Count-Based Coordinate Exploration Module for Pokemon FireRed.
    Computes continuous intrinsic exploration rewards based on state visit frequency:
        r_coord(map, x, y) = 1.0 / sqrt(N(map, x, y))
    
    Provides mathematically grounded frontier expansion rewards with zero neural drift,
    and supports serialization for checkpoint persistence.
    """
    def __init__(self, beta=0.05, clip_val=1.0):
        self.beta = beta
        self.clip_val = clip_val
        # Map key: (map_bank, map_num, x, y) -> count (int)
        self.visit_counts = defaultdict(int)
        self.total_unique_tiles = 0

    def compute_intrinsic_reward(self, map_banks, map_nums, xs, ys, update_counts=True):
        """
        Compute intrinsic rewards for a batch of parallel environment steps.
        
        Args:
            map_banks: array-like of shape (N,)
            map_nums:  array-like of shape (N,)
            xs:        array-like of shape (N,)
            ys:        array-like of shape (N,)
            update_counts: bool, whether to increment visit counts
            
        Returns:
            rewards: np.ndarray of shape (N,) with rewards in [0, clip_val]
            is_new:  np.ndarray of shape (N,) bool indicating first-time visit
        """
        batch_size = len(map_banks)
        rewards = np.zeros(batch_size, dtype=np.float32)
        is_new = np.zeros(batch_size, dtype=bool)

        for i in range(batch_size):
            tile_key = (int(map_banks[i]), int(map_nums[i]), int(xs[i]), int(ys[i]))
            count = self.visit_counts[tile_key]

            if count == 0:
                is_new[i] = True
                self.total_unique_tiles += 1
                novelty = 1.0
            else:
                novelty = 1.0 / np.sqrt(count + 1)

            novelty = np.clip(novelty, 0.0, self.clip_val)
            rewards[i] = float(novelty)

            if update_counts:
                self.visit_counts[tile_key] += 1

        return rewards, is_new

    @property
    def unique_tiles_discovered(self):
        return len(self.visit_counts)

    def save(self, path):
        """Serialize visit counts to disk."""
        torch.save({
            "visit_counts": dict(self.visit_counts),
            "total_unique_tiles": self.total_unique_tiles,
            "beta": self.beta,
            "clip_val": self.clip_val,
        }, str(path))

    def load(self, path):
        """Load visit counts from disk."""
        checkpoint = torch.load(str(path), weights_only=False)
        self.visit_counts = defaultdict(int, checkpoint.get("visit_counts", {}))
        self.total_unique_tiles = checkpoint.get("total_unique_tiles", len(self.visit_counts))
        self.beta = checkpoint.get("beta", self.beta)
        self.clip_val = checkpoint.get("clip_val", self.clip_val)
