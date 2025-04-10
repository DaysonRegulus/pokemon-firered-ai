import sys
import retro
import torch
import numpy as np
import gymnasium as gym  # Import Gymnasium
from FireRedRewardManager import (
    RewardManager,
    ScreenshotManager,
    ActionFilterWrapper,
    CustomRewardEnv,
)
import Xlib
import Xlib.display
import subprocess
import re
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QTextEdit, QPushButton
from PyQt5.QtCore import Qt, QTimer, QMetaObject, Q_ARG
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, VecTransposeImage, DummyVecEnv, VecFrameStack
from stable_baselines3.common.callbacks import BaseCallback
from torch.profiler import profile, ProfilerActivity
from gymnasium.wrappers.common import TimeLimit
from stable_baselines3.common.atari_wrappers import WarpFrame
import time

np.random.seed(42)
torch.manual_seed(42)

# Clear GPU cache
torch.cuda.empty_cache()

env_name = "PokemonFireRed-GBA"
num_envs = 8
max_episode_steps = 8192

class FireRedRenderer:
    def __init__(self):
        self.display = Xlib.display.Display()
        self.window_id = None  # Store emulator window ID

    def get_emulator_window_id(self):
        """Find the emulator window ID using `wmctrl`."""
        try:
            output = subprocess.check_output(["wmctrl", "-l"]).decode("utf-8")
            for line in output.splitlines():
                if "mGBA" in line or "FireRed" in line:  # Adjust based on emulator title
                    match = re.match(r"(\S+)", line)
                    if match:
                        self.window_id = int(match.group(1), 16)  # Convert hex to int
                        return self.window_id
        except Exception as e:
            print(f"Error finding emulator window: {e}")
            return None
        
class MasterWindow(QMainWindow):
    """Main UI for displaying emulator and AI logs."""
    
    def __init__(self, reward_manager):
        super().__init__()
        self.setWindowTitle("FireRed AI Master Window")
        self.setGeometry(100, 100, 800, 600)

        # Main Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Emulator Display
        self.emulator_label = QLabel("Emulator Screen Here")
        self.emulator_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.emulator_label)

        # Reward Log
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)

        # Start Button
        self.start_button = QPushButton("Start AI")
        self.start_button.clicked.connect(self.start_ai)
        layout.addWidget(self.start_button)

        central_widget.setLayout(layout)

        self.reward_manager = reward_manager

        # Timer for GUI updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(500)  # Refresh every 500ms

    def start_ai(self):
        """Start AI in a separate thread."""
        self.log_message("Starting AI...")
        ai_thread = threading.Thread(target=self.run_ai, daemon=True)
        ai_thread.start()

    def run_ai(self):
        """Main AI loop to interact with emulator and update rewards."""
        while True:
            rewards = self.reward_manager.calculate_rewards()
            self.log_message(f"Rewards: {rewards}")

    def update_gui(self):
        """Update GUI elements."""
        pass  # No need for screenshots; handled by reparenting

    def log_message(self, message):
        """Append log messages to the log box in the main thread."""
        QMetaObject.invokeMethod(self.log_box, "append", Qt.QueuedConnection, Q_ARG(str, message))

class RewardTrackingCallback(BaseCallback):
    """
    Custom callback for tracking rewards during training.
    """
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.total_rewards = []

    def _on_step(self) -> bool:
        # Gather rewards from all environments
        rewards = self.locals["rewards"]
        self.total_rewards.extend(rewards)  # Append rewards for this step
        return True

    def get_total_reward(self):
        return np.sum(self.total_rewards)  # Return the sum of all rewards


class StochasticFrameSkip(gym.Wrapper):
    """
    A wrapper for stochastic frame skipping.
    """
    def __init__(self, env, n, stickprob):
        super().__init__(env)
        self.n = n
        self.stickprob = stickprob
        self.curac = None
        self.rng = np.random.default_rng()

    def reset(self, **kwargs):
        self.curac = None
        return self.env.reset(**kwargs)

    def step(self, action):
        totrew = 0
        terminated, truncated = False, False
        for i in range(self.n):
            if self.curac is None or (i == 0 and self.rng.random() > self.stickprob):
                self.curac = action
            obs, rew, terminated, truncated, info = self.env.step(self.curac)
            totrew += rew
            if terminated or truncated:
                break
        return obs, totrew, terminated, truncated, info


def make_env(env_name, idx):
    """
    Factory function to create a single environment instance.
    """
    def _init():
        base_env = retro.make(env_name)  # Create the Retro environment
        wrapped_env = WarpFrame(base_env)  # Preprocess frames to grayscale
        wrapped_env = CustomRewardEnv(wrapped_env, env_id=idx + 1)  # Wrap with custom reward logic and Pass env ID
        wrapped_env = StochasticFrameSkip(wrapped_env, n=4, stickprob=0.25)  # Add frame skip
        wrapped_env = ActionFilterWrapper(wrapped_env)  # Filter out unnecessary buttons
        wrapped_env = TimeLimit(wrapped_env, max_episode_steps=max_episode_steps)  # Add time limit
        return wrapped_env
    return _init


def display_gpu_details():
    """
    Display details of the GPU being used.
    """
    if torch.cuda.is_available():
        device = torch.device("cuda:0")
        gpu_name = torch.cuda.get_device_name(device)
        gpu_memory_allocated = torch.cuda.memory_allocated(device) / 1e9  # GB
        gpu_memory_reserved = torch.cuda.memory_reserved(device) / 1e9  # GB
        print(f"Using GPU: {gpu_name}")
        print(f"Memory Allocated: {gpu_memory_allocated:.2f} GB")
        print(f"Memory Reserved: {gpu_memory_reserved:.2f} GB")
    else:
        print("CUDA is not available. Running on CPU.")


if __name__ == "__main__":
    print("Setting up the environment...")
    try:
        # Create multiple parallel environments
        train_env = SubprocVecEnv([make_env(env_name, i) for i in range(num_envs)])
        train_env = VecFrameStack(train_env, n_stack=10)  # Stack 10 frames
        train_env = VecTransposeImage(train_env)  # Adjust image input format
        print(f"{num_envs} parallel environments set up successfully!")
    except Exception as e:
        print(f"Error creating environment: {e}")
        exit()

    # Display GPU details
    display_gpu_details()

    # Load or create a new model
    model_path = f"{env_name}_ppo_model_{num_envs}penv"
    try:
        print("Attempting to load existing model...")
        model = PPO.load(model_path, env=train_env, device="cuda")
        print("Model loaded successfully!")
    except FileNotFoundError:
        print("No pre-trained model found. Creating a new model...")
        model = PPO(
            policy="CnnPolicy",
            env=train_env,
            learning_rate=2.5e-4,
            n_steps=512,
            batch_size=256,
            n_epochs=4,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.1,
            ent_coef=0.01,
            verbose=1,
        )
        
     # Start GUI
    app = QApplication(sys.argv)
    screenshot_manager = ScreenshotManager()
    reward_manager = RewardManager(env=train_env, screenshot_manager=screenshot_manager)
    window = MasterWindow(reward_manager)
    window.show()

    # Train the model
    continue_training = 'y'
    if continue_training == "y":
        print("Training the model...")
        try:
            reward_callback = RewardTrackingCallback()
            model.learn(total_timesteps=81920, callback=reward_callback)
            total_reward = reward_callback.get_total_reward()
            print(f"Total reward after training: {total_reward:.2f}")
            model.save(model_path)
            print(f"Model training completed and saved as '{model_path}'!")
        except Exception as e:
            print(f"Error during training: {e}")
            exit()
            
    '''

    # Profile performance (optional)
    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
        model.learn(total_timesteps=4096)
    print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))
    '''
    # Cleanup
    train_env.close()
