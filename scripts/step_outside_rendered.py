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

# Walk to X=11, step through door, and keep stepping down in Pallet Town:
actions = [ACT_LEFT] * 48 + [ACT_DOWN] * 80

print("Stepping all the way outside into Pallet Town overworld...")
for step, act in enumerate(actions):
    obs, rew, term, trunc, info = env.step(act)
    ram = env.unwrapped.get_ram()
    cur_x = read_u16(ram, ADDR_POS_X)
    cur_y = read_u16(ram, ADDR_POS_Y)
    mb = ram[ADDR_MAP_BANK]
    mn = ram[ADDR_MAP_NUM]

    if step % 10 == 0 or (mb, mn) == (3, 0):
        print(f"Step {step:2d}: Map ({mb}, {mn}) | Pos: ({cur_x:2d}, {cur_y:2d})")

screen = env.unwrapped.get_screen()
out_path = EVIDENCE_DIR / "pallet_town_outside_fully_rendered.png"
Image.fromarray(screen).save(out_path)
print(f"--> Saved visual proof screenshot: {out_path}")
env.close()
