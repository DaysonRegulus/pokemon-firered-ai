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
ACT_LEFT = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]

# Exactly 3 tiles LEFT (from X=14 to X=11), then DOWN!
actions = [ACT_LEFT] * 48 + [ACT_DOWN] * 48

print("Walking to X=11, then stepping DOWN through the door...")
for step, act in enumerate(actions):
    obs, rew, term, trunc, info = env.step(act)
    ram = env.unwrapped.get_ram()
    cur_x = read_u16(ram, ADDR_POS_X)
    cur_y = read_u16(ram, ADDR_POS_Y)
    mb = ram[ADDR_MAP_BANK]
    mn = ram[ADDR_MAP_NUM]

    if (mb, mn) != (4, 0):
        print(f"\n=======================================================")
        print(f"!!! SUCCESS: WARPED TO OUTSIDE MAP !!!")
        print(f"Step {step:2d}: Map (Bank={mb}, Num={mn}) | Pos: (X={cur_x}, Y={cur_y})")
        print(f"=======================================================")
        screen = env.unwrapped.get_screen()
        out_path = EVIDENCE_DIR / "pallet_town_outside_verified.png"
        Image.fromarray(screen).save(out_path)
        print(f"Saved visual proof screenshot to: {out_path}")
        break

env.close()
