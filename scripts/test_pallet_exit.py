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

# 1. Bedroom to stairs (17, 9)
actions = [ACT_RIGHT]*40 + [ACT_UP]*80 + [ACT_RIGHT]*20 + [ACT_UP]*40
# 2. Living room: walk down along right wall to (17, 15)
actions += [ACT_DOWN]*120
# 3. Walk left exactly 5 tiles from 17 to 12 (16 frames per tile):
actions += [ACT_LEFT]*80
# 4. Step down through the door!
actions += [ACT_DOWN]*100
# 5. In Pallet Town overworld: walk down then right
actions += [ACT_DOWN]*80 + [ACT_RIGHT]*80

print("Stepping onto door mat and through to Pallet Town...")
prev_map = (-1, -1)
prev_pos = (-1, -1)
events = []

for step, act in enumerate(actions):
    obs, rew, term, trunc, info = env.step(act)
    ram = env.unwrapped.get_ram()
    cur_x = read_u16(ram, ADDR_POS_X)
    cur_y = read_u16(ram, ADDR_POS_Y)
    cur_map = (ram[ADDR_MAP_BANK], ram[ADDR_MAP_NUM])

    if cur_map != prev_map or (cur_x, cur_y) != prev_pos:
        entry = f"Step {step:3d}: Map (Bank={cur_map[0]}, Num={cur_map[1]}) | Pos: (X={cur_x:2d}, Y={cur_y:2d})"
        print(entry)
        events.append(entry)
        prev_map = cur_map
        prev_pos = (cur_x, cur_y)

env.close()
print(f"\nDone! Total events: {len(events)}")
