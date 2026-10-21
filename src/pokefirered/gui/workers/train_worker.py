"""
Training Worker Thread for PySide6.
Spawns scripts/train.py as a managed subprocess, parses stdout in real time,
and emits Qt signals for timesteps, SPS, rewards, loss, and exploration metrics.
"""
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal, QThread

from pokefirered.paths import get_project_root

PROJECT_ROOT = get_project_root()


class TrainWorker(QThread):
    """
    Background worker that runs training subprocess and streams real-time telemetry.
    """
    sig_log = Signal(str)
    sig_progress = Signal(int, int, float)  # (current_steps, total_steps, sps)
    sig_metrics = Signal(dict)              # parsed key metrics
    sig_status = Signal(str)
    sig_finished = Signal(int, str)         # (exit_code, summary_text)
    sig_error = Signal(str)

    def __init__(
        self,
        algo: str = "PPO",
        exploration: str = "RND",
        num_envs: int = 8,
        timesteps: int = 102400,
        device: str = "auto",
        fresh: bool = False,
        record_trajectories: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.algo = algo
        self.exploration = exploration
        self.num_envs = num_envs
        self.timesteps = timesteps
        self.device = device
        self.fresh = fresh
        self.record_trajectories = record_trajectories

        self.process: Optional[subprocess.Popen] = None
        self._is_cancelled = False

        # Regex patterns for stdout telemetry parsing
        self.re_sb3_step = re.compile(r"\|\s*total_timesteps\s*\|\s*(\d+)\s*\|")
        self.re_sb3_fps = re.compile(r"\|\s*fps\s*\|\s*([\d\.]+)\s*\|")
        self.re_sb3_loss = re.compile(r"\|\s*loss\s*\|\s*([-\d\.]+)\s*\|")
        self.re_sb3_entropy = re.compile(r"\|\s*entropy_loss\s*\|\s*([-\d\.]+)\s*\|")
        self.re_sb3_value_loss = re.compile(r"\|\s*value_loss\s*\|\s*([-\d\.]+)\s*\|")
        self.re_sb3_policy_loss = re.compile(r"\|\s*policy_loss\s*\|\s*([-\d\.]+)\s*\|")
        self.re_sb3_mean_reward = re.compile(r"\|\s*ep_rew_mean\s*\|\s*([-\d\.]+)\s*\|")
        self.re_milestone = re.compile(
            r"\[EXPLORATION MILESTONE\]\s*Total unique tiles visited:\s*(\d+)\s*\|\s*Maps:\s*(\d+)"
        )
        self.re_qrdqn_step = re.compile(
            r"Step\s+(\d+)\s*\|\s*Loss:\s*([-\d\.]+)\s*\|\s*Reward\s*\(Ext/Int\):\s*([-\d\.]+)\s*/\s*([-\d\.]+)\s*\|\s*Tiles:\s*(\d+)\s*\|\s*Maps:\s*(\d+)\s*\|\s*SPS:\s*([\d\.]+)"
        )

    def cancel(self):
        """Requests graceful cancellation of training subprocess."""
        self._is_cancelled = True
        if self.process and self.process.poll() is None:
            self.sig_status.emit("Cancelling training subprocess...")
            try:
                self.process.terminate()
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

    def run(self):
        self._is_cancelled = False

        if getattr(sys, "frozen", False):
            cmd = [
                sys.executable,
                "--train",
                "--algo", self.algo,
                "--exploration", self.exploration,
                "--num-envs", str(self.num_envs),
                "--timesteps", str(self.timesteps),
            ]
        else:
            python_exe = sys.executable
            cmd = [
                python_exe,
                str(PROJECT_ROOT / "scripts" / "train.py"),
                "--algo", self.algo,
                "--exploration", self.exploration,
                "--num-envs", str(self.num_envs),
                "--timesteps", str(self.timesteps),
            ]
        if self.device != "auto":
            cmd.extend(["--device", self.device])
        if self.fresh:
            cmd.append("--fresh")
        if not self.record_trajectories:
            cmd.append("--no-record-trajectories")

        self.sig_status.emit(f"Launching: {' '.join(cmd)}")
        self.sig_log.emit(f"[TRAIN] Spawning: {self.algo} ({self.exploration}) for {self.timesteps:,} steps...\n")

        current_metrics: Dict[str, float] = {
            "current_step": 0,
            "total_steps": self.timesteps,
            "sps": 0.0,
            "loss": 0.0,
            "unique_tiles": 0,
            "unique_maps": 0,
            "reward_ext": 0.0,
            "reward_int": 0.0,
            "reward_total": 0.0,
        }

        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            # Read line by line
            for line in self.process.stdout:
                if self._is_cancelled:
                    break
                line_str = line.rstrip()
                self.sig_log.emit(line_str)

                # Parse SB3 tabular logger
                m_step = self.re_sb3_step.search(line_str)
                if m_step:
                    step = int(m_step.group(1))
                    current_metrics["current_step"] = step

                m_fps = self.re_sb3_fps.search(line_str)
                if m_fps:
                    fps = float(m_fps.group(1))
                    current_metrics["sps"] = fps

                m_loss = self.re_sb3_loss.search(line_str)
                if m_loss:
                    current_metrics["loss"] = float(m_loss.group(1))

                m_ent = self.re_sb3_entropy.search(line_str)
                if m_ent:
                    current_metrics["entropy"] = float(m_ent.group(1))

                m_vloss = self.re_sb3_value_loss.search(line_str)
                if m_vloss:
                    current_metrics["value_loss"] = float(m_vloss.group(1))

                m_ploss = self.re_sb3_policy_loss.search(line_str)
                if m_ploss:
                    current_metrics["policy_loss"] = float(m_ploss.group(1))

                m_rew = self.re_sb3_mean_reward.search(line_str)
                if m_rew:
                    current_metrics["reward_total"] = float(m_rew.group(1))

                # Parse exploration milestone
                m_mile = self.re_milestone.search(line_str)
                if m_mile:
                    tiles = int(m_mile.group(1))
                    maps = int(m_mile.group(2))
                    current_metrics["unique_tiles"] = tiles
                    current_metrics["unique_maps"] = maps

                # Parse QR-DQN line
                m_qrdqn = self.re_qrdqn_step.search(line_str)
                if m_qrdqn:
                    current_metrics["current_step"] = int(m_qrdqn.group(1))
                    current_metrics["loss"] = float(m_qrdqn.group(2))
                    current_metrics["reward_ext"] = float(m_qrdqn.group(3))
                    current_metrics["reward_int"] = float(m_qrdqn.group(4))
                    current_metrics["reward_total"] = current_metrics["reward_ext"] + current_metrics["reward_int"]
                    current_metrics["unique_tiles"] = int(m_qrdqn.group(5))
                    current_metrics["unique_maps"] = int(m_qrdqn.group(6))
                    current_metrics["sps"] = float(m_qrdqn.group(7))

                # Emit updates
                if current_metrics["current_step"] > 0:
                    self.sig_progress.emit(
                        int(current_metrics["current_step"]),
                        self.timesteps,
                        float(current_metrics["sps"]),
                    )
                    self.sig_metrics.emit(dict(current_metrics))

            self.process.wait()
            ret_code = self.process.returncode

            if self._is_cancelled:
                self.sig_status.emit("Training was cancelled.")
                self.sig_finished.emit(-1, "Training cancelled by user.")
            elif ret_code == 0:
                self.sig_status.emit("Training completed successfully.")
                self.sig_finished.emit(0, "Training finished successfully.")
            else:
                err_msg = f"Training exited with code {ret_code}."
                self.sig_status.emit(err_msg)
                self.sig_finished.emit(ret_code, err_msg)

        except Exception as e:
            self.sig_error.emit(str(e))
            self.sig_finished.emit(-1, str(e))
