"""
Optimized GPU-Accelerated Structural Similarity (SSIM) Curiosity Module.
Replaces the legacy O(N*M) CPU skimage loop with a fast hierarchical GPU filter:
  Stage 1: Coarse 16x16 perceptual thumbnail L1 distance filter (sub-millisecond).
  Stage 2: Vectorized PyTorch GPU patch-based SSIM.
  Stage 3: Continuous novelty reward calculation and dynamic anchor bank indexing.
"""
from pathlib import Path
from collections import deque
import numpy as np
import torch
import torch.nn.functional as F


class OptimizedSSIMModule:
    def __init__(
        self,
        device="cuda" if torch.cuda.is_available() else "cpu",
        max_bank_size=1000,
        novelty_threshold=0.85,
        clip_val=1.0,
    ):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.max_bank_size = max_bank_size
        self.novelty_threshold = novelty_threshold
        self.clip_val = clip_val

        # Anchor bank stored as GPU tensors
        self.bank_frames = torch.empty((0, 1, 84, 84), dtype=torch.float32, device=self.device)
        self.bank_thumbnails = torch.empty((0, 256), dtype=torch.float32, device=self.device)

        # SSIM stabilizing constants
        self.C1 = (0.01) ** 2
        self.C2 = (0.03) ** 2

    def _extract_thumbnail(self, frame_tensor):
        """Downsample (B, 1, 84, 84) to (B, 256) flattened 16x16 thumbnail."""
        thumb = F.adaptive_avg_pool2d(frame_tensor, (16, 16))
        return thumb.reshape(thumb.shape[0], -1)

    def _compute_vectorized_ssim(self, candidates, targets):
        """
        Compute patch-based structural similarity between candidates (B, 1, 84, 84)
        and targets (M, 1, 84, 84) using average-pooling convolutions on GPU.
        Returns: tensor of shape (B, M) with pairwise SSIM values.
        """
        k = 8
        stride = 4

        # Expand for pairwise broadcast: candidates (B, 1, H, W) and targets (M, 1, H, W)
        B = candidates.shape[0]
        M = targets.shape[0]

        # Process each candidate against all targets in batch
        pairwise_ssim = torch.zeros((B, M), dtype=torch.float32, device=self.device)

        # Precompute target stats
        mu_tgt = F.avg_pool2d(targets, k, stride=stride)
        mu_tgt_sq = mu_tgt.pow(2)
        sigma_tgt_sq = F.avg_pool2d(targets * targets, k, stride=stride) - mu_tgt_sq

        for b in range(B):
            cand = candidates[b:b+1]  # (1, 1, 84, 84)
            mu_cand = F.avg_pool2d(cand, k, stride=stride)
            mu_cand_sq = mu_cand.pow(2)
            sigma_cand_sq = F.avg_pool2d(cand * cand, k, stride=stride) - mu_cand_sq

            mu_cross = mu_cand * mu_tgt
            sigma_cross = F.avg_pool2d(cand * targets, k, stride=stride) - mu_cross

            ssim_map = ((2 * mu_cross + self.C1) * (2 * sigma_cross + self.C2)) / (
                (mu_cand_sq + mu_tgt_sq + self.C1) * (sigma_cand_sq + sigma_tgt_sq + self.C2)
            )
            # Spatial mean
            pairwise_ssim[b] = ssim_map.mean(dim=(1, 2, 3))

        return pairwise_ssim

    def compute_intrinsic_reward(self, obs_np):
        """
        Compute continuous novelty rewards for a batch of observations (B, 1, 84, 84).
        obs_np: numpy array of shape (B, 1, 84, 84) with values in [0, 1].
        Returns:
            rewards: numpy array of shape (B,) with continuous novelty scores.
            is_new: list of booleans indicating whether each frame was added to the anchor bank.
        """
        B = obs_np.shape[0]
        obs_tensor = torch.as_tensor(obs_np, dtype=torch.float32, device=self.device)
        thumbnails = self._extract_thumbnail(obs_tensor)

        # Base case: empty bank
        if len(self.bank_frames) == 0:
            self.bank_frames = obs_tensor[:1].clone()
            self.bank_thumbnails = thumbnails[:1].clone()
            rewards = np.ones(B, dtype=np.float32)
            is_new = [True] + [False] * (B - 1)
            return rewards, is_new

        rewards = np.zeros(B, dtype=np.float32)
        is_new = [False] * B

        for b in range(B):
            cand = obs_tensor[b:b+1]
            cand_thumb = thumbnails[b:b+1]

            # Stage 1: Coarse 16x16 L1 distance filter across entire bank
            l1_dist = torch.mean(torch.abs(self.bank_thumbnails - cand_thumb), dim=1)
            min_l1 = torch.min(l1_dist).item()

            # If thumbnail is nearly identical to an existing anchor, similarity is near 1.0
            if min_l1 < 0.015:
                max_ssim = 1.0 - min_l1
            else:
                # Stage 2: Compare against Top-K nearest candidates in bank
                k_nearest = min(30, len(self.bank_frames))
                topk_idx = torch.topk(-l1_dist, k=k_nearest).indices
                cand_targets = self.bank_frames[topk_idx]

                ssim_vals = self._compute_vectorized_ssim(cand, cand_targets)
                max_ssim = torch.max(ssim_vals).item()

            # Stage 3: Continuous Novelty Formula
            # When max_ssim == 1.0 -> novelty = 0.0
            # When max_ssim <= novelty_threshold -> novelty = 1.0
            novelty = np.clip((1.0 - max_ssim) / (1.0 - self.novelty_threshold + 1e-6), 0.0, self.clip_val)
            rewards[b] = float(novelty)

            # Dynamic Bank Insertion: If frame is sufficiently novel, add to anchor bank
            if max_ssim < self.novelty_threshold:
                is_new[b] = True
                if len(self.bank_frames) < self.max_bank_size:
                    self.bank_frames = torch.cat([self.bank_frames, cand], dim=0)
                    self.bank_thumbnails = torch.cat([self.bank_thumbnails, cand_thumb], dim=0)
                else:
                    # FIFO replacement of oldest anchor
                    self.bank_frames = torch.cat([self.bank_frames[1:], cand], dim=0)
                    self.bank_thumbnails = torch.cat([self.bank_thumbnails[1:], cand_thumb], dim=0)

        return rewards, is_new

    @property
    def bank_size(self):
        return len(self.bank_frames)

    def save(self, path):
        torch.save({
            "bank_frames": self.bank_frames.cpu(),
            "bank_thumbnails": self.bank_thumbnails.cpu(),
            "novelty_threshold": self.novelty_threshold,
            "max_bank_size": self.max_bank_size,
        }, path)

    def load(self, path):
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        self.bank_frames = checkpoint["bank_frames"].to(self.device)
        self.bank_thumbnails = checkpoint["bank_thumbnails"].to(self.device)
        self.novelty_threshold = checkpoint["novelty_threshold"]
        self.max_bank_size = checkpoint["max_bank_size"]
