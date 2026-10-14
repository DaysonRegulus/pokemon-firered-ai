import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path("c:/dev/Antigravity/Pokemon FireRed AI")
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import retro
from pokefirered.env_factory import register_custom_integrations

register_custom_integrations()

env = retro.make("PokemonFireRed-GBA", inttype=retro.data.Integrations.ALL)
obs, info = env.reset()

BASE_EWRAM = 0x02000000

ADDR_MAP_BANK = 0x02031DBC - BASE_EWRAM
ADDR_MAP_NUM  = 0x02031DBD - BASE_EWRAM
ADDR_POS_X    = 0x02036E48 - BASE_EWRAM
ADDR_POS_Y    = 0x02036E4A - BASE_EWRAM

def read_u16(ram_buf, offset):
    return ram_buf[offset] + (ram_buf[offset+1] << 8)

ACT_UP = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
ACT_DOWN = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
ACT_LEFT = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]
ACT_RIGHT = [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]

# 1. Go downstairs:
actions = [ACT_RIGHT]*40 + [ACT_UP]*80 + [ACT_RIGHT]*20 + [ACT_UP]*40
# 2. In living room, walk to door mat at (14, 15):
actions += [ACT_DOWN]*70 + [ACT_LEFT]*80 + [ACT_DOWN]*50
# 3. Walk through front door outside:
actions += [ACT_DOWN]*60 + [ACT_UP]*40

print("Stepping outside front door...")
prev_map = (-1, -1)
prev_pos = (-1, -1)

for step, act in enumerate(actions):
    obs, rew, term, trunc, info = env.step(act)
    ram = env.unwrapped.get_ram()
    cur_x = read_u16(ram, ADDR_POS_X)
    cur_y = read_u16(ram, ADDR_POS_Y)
    cur_map = (ram[ADDR_MAP_BANK], ram[ADDR_MAP_NUM])

    if cur_map != prev_map or (cur_x, cur_y) != prev_pos:
        print(f"Step {step:3d}: Map (Bank={cur_map[0]}, Num={cur_map[1]}) | Pos: (X={cur_x:2d}, Y={cur_y:2d})")
        prev_map = cur_map
        prev_pos = (cur_x, cur_y)

env.close()
