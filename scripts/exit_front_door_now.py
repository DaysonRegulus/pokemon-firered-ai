import sys
from pathlib import Path
import numpy as np
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

# From start (14, 14):
# Red door mat is at bottom-left:
# Walk left 2 tiles (32 frames)
# Walk down 3 tiles (48 frames)
actions = [ACT_LEFT] * 35 + [ACT_DOWN] * 50

print("Stepping directly from start onto the red door mat...")
for step, act in enumerate(actions):
    obs, rew, term, trunc, info = env.step(act)
    ram = env.unwrapped.get_ram()
    cur_x = read_u16(ram, ADDR_POS_X)
    cur_y = read_u16(ram, ADDR_POS_Y)
    mb = ram[ADDR_MAP_BANK]
    mn = ram[ADDR_MAP_NUM]

    if step % 8 == 0 or (mb, mn) != (4, 0):
        print(f"Step {step:2d}: Map ({mb}, {mn}) | Pos: ({cur_x:2d}, {cur_y:2d})")
        if (mb, mn) != (4, 0):
            print(f"--> OUTSIDE PALLET TOWN REACHED AT STEP {step}! Map: ({mb}, {mn})")
            screen = env.unwrapped.get_screen()
            Image.fromarray(screen).save(EVIDENCE_DIR / "visual_proof_pallet_town_outside.png")
            print(f"--> Saved visual proof screenshot: visual_proof_pallet_town_outside.png")
            break

env.close()
