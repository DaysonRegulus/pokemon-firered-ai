import sys
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path("c:/dev/Antigravity/Pokemon FireRed AI")
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import retro
from pokefirered.env_factory import register_custom_integrations

register_custom_integrations()

EVIDENCE_DIR = PROJECT_ROOT / "visual_evidence"

env = retro.make("PokemonFireRed-GBA", inttype=retro.data.Integrations.ALL)
obs, info = env.reset()

ACT_DOWN = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
ACT_LEFT = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]

actions = [ACT_LEFT] * 64 + [ACT_DOWN] * 20
for act in actions:
    env.step(act)

screen = env.unwrapped.get_screen()
Image.fromarray(screen).save(EVIDENCE_DIR / "red_at_10_15.png")
print("Saved red_at_10_15.png")
env.close()
