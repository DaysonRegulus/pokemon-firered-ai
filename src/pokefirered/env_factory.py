from pathlib import Path
import retro
import retro.data

from pokefirered.wrappers import ActionFilterWrapper, CustomRewardEnv, StochasticFrameSkip, WarpFrame
from pokefirered.paths import get_project_root

PROJECT_ROOT = get_project_root()
CUSTOM_INTEGRATION_DIR = PROJECT_ROOT / "data" / "custom_integrations"


def register_custom_integrations():
    """
    Ensure the custom game integration directory is known to retro.
    """
    custom_path_str = str(CUSTOM_INTEGRATION_DIR.resolve())
    retro.data.Integrations._init()
    if custom_path_str not in retro.data.Integrations.CUSTOM_PATHS:
        retro.data.Integrations.add_custom_path(custom_path_str)


def make_single_env(env_name="PokemonFireRed-GBA", state=None, idx=0, render_mode=None, exploration_mode="RND"):
    """
    Factory function to create a single wrapped environment instance.
    """
    def _init():
        register_custom_integrations()
        kwargs = {"render_mode": render_mode, "inttype": retro.data.Integrations.ALL}
        if state is not None:
            kwargs["state"] = state
        base_env = retro.make(
            env_name,
            **kwargs,
        )
        # Skip sub-frames BEFORE WarpFrame and CustomRewardEnv so 84x84 grayscale resizing
        # and pybind11 RAM extraction execute once per agent step instead of 4x per step.
        wrapped_env = StochasticFrameSkip(base_env, n=4, stickprob=0.25)
        wrapped_env = WarpFrame(wrapped_env)  # Grayscale 84x84
        wrapped_env = CustomRewardEnv(wrapped_env, env_id=idx + 1, exploration_mode=exploration_mode, reward_frame_skip=1)
        wrapped_env = ActionFilterWrapper(wrapped_env)
        return wrapped_env

    return _init


def create_vectorized_env(
    env_name="PokemonFireRed-GBA",
    state=None,
    states=None,
    num_envs=1,
    n_stack=2,
    render_mode=None,
    exploration_mode="RND",
):
    """
    Create a vectorized, frame-stacked environment.
    Uses DummyVecEnv if num_envs == 1, otherwise SubprocVecEnv.
    Optionally accepts `states` (list of save-state names) to distribute
    environments across a stepping-stone curriculum pool.
    """
    # Lazy-import SB3 VecEnvs in main process only so SubprocVecEnv workers
    # never load PyTorch/CUDA DLLs (~1.0-1.6 GB commit per worker on Windows).
    from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecFrameStack, VecTransposeImage

    register_custom_integrations()

    env_fns = []
    for i in range(num_envs):
        env_state = states[i % len(states)] if states else state
        env_fns.append(
            make_single_env(env_name, state=env_state, idx=i, render_mode=render_mode, exploration_mode=exploration_mode)
        )

    if num_envs == 1:
        vec_env = DummyVecEnv(env_fns)
    else:
        vec_env = SubprocVecEnv(env_fns)

    if n_stack > 1:
        vec_env = VecFrameStack(vec_env, n_stack=n_stack)

    vec_env = VecTransposeImage(vec_env)
    return vec_env
