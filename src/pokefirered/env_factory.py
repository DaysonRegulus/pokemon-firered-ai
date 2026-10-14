from pathlib import Path
import retro
import retro.data
from stable_baselines3.common.atari_wrappers import WarpFrame
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecFrameStack, VecTransposeImage

from pokefirered.wrappers import ActionFilterWrapper, CustomRewardEnv, StochasticFrameSkip

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
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
        wrapped_env = WarpFrame(base_env)  # Grayscale 84x84
        wrapped_env = CustomRewardEnv(wrapped_env, env_id=idx + 1, exploration_mode=exploration_mode)
        wrapped_env = StochasticFrameSkip(wrapped_env, n=4, stickprob=0.25)
        wrapped_env = ActionFilterWrapper(wrapped_env)
        return wrapped_env

    return _init


def create_vectorized_env(
    env_name="PokemonFireRed-GBA",
    state=None,
    num_envs=1,
    n_stack=2,
    render_mode=None,
    exploration_mode="RND",
):
    """
    Create a vectorized, frame-stacked environment.
    Uses DummyVecEnv if num_envs == 1 or render_mode is set, otherwise SubprocVecEnv.
    """
    register_custom_integrations()

    env_fns = [
        make_single_env(env_name, state=state, idx=i, render_mode=render_mode, exploration_mode=exploration_mode)
        for i in range(num_envs)
    ]

    if num_envs == 1 or render_mode == "human":
        vec_env = DummyVecEnv(env_fns)
    else:
        vec_env = SubprocVecEnv(env_fns)

    if n_stack > 1:
        vec_env = VecFrameStack(vec_env, n_stack=n_stack)

    vec_env = VecTransposeImage(vec_env)
    return vec_env
