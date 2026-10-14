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

BASE_EWRAM = 0x02000000
ADDR_MAP_BANK = 0x02031DBC - BASE_EWRAM
ADDR_MAP_NUM  = 0x02031DBD - BASE_EWRAM
ADDR_POS_X    = 0x02036E48 - BASE_EWRAM
ADDR_POS_Y    = 0x02036E4A - BASE_EWRAM

def read_u16(ram_buf, offset):
    return ram_buf[offset] + (ram_buf[offset+1] << 8)

ACT_DOWN = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
ACT_UP   = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
ACT_LEFT = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]
ACT_RIGHT= [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]

# 1. Exit house:
actions = [ACT_LEFT] * 48 + [ACT_DOWN] * 70
# 2. In Pallet Town: walk down past house, then right towards Oak's Lab:
actions += [ACT_DOWN] * 80 + [ACT_RIGHT] * 80 + [ACT_DOWN] * 60

print("Tracking movement in Pallet Town overworld...")
prev_pos = (-1, -1)
overworld_steps = []

for step, act in enumerate(actions):
    obs, rew, term, trunc, info = env.step(act)
    ram = env.unwrapped.get_ram()
    cur_x = read_u16(ram, ADDR_POS_X)
    cur_y = read_u16(ram, ADDR_POS_Y)
    mb = ram[ADDR_MAP_BANK]
    mn = ram[ADDR_MAP_NUM]

    if (mb, mn) == (3, 0) and (cur_x, cur_y) != prev_pos:
        entry = f"Overworld Step {step:3d}: Map ({mb}, {mn}) | Pos: (X={cur_x:2d}, Y={cur_y:2d})"
        print(entry)
        overworld_steps.append(entry)
        prev_pos = (cur_x, cur_y)

screen = env.unwrapped.get_screen()
Image.fromarray(screen).save(EVIDENCE_DIR / "pallet_town_oaks_lab_path.png")
print("Saved pallet_town_oaks_lab_path.png")
print(f"Total overworld tile transitions: {len(overworld_steps)}")

env.close()
