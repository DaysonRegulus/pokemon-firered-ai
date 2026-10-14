import sys
from pathlib import Path

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

# 1. Go downstairs
actions = [ACT_RIGHT]*40 + [ACT_UP]*80 + [ACT_RIGHT]*20 + [ACT_UP]*40
# 2. Downstairs to bottom wall
actions += [ACT_DOWN]*120

# Walk all the way left to X=8
actions += [ACT_LEFT]*180

# Now scan from X=8 down to X=0 trying DOWN!
test_actions = list(actions)
for tile in range(9): # try 9 more tiles to the left
    test_actions += [ACT_DOWN]*30 + [ACT_UP]*5 + [ACT_LEFT]*20

print("Scanning from X=8 down to X=0...")
warped = False
for step, act in enumerate(test_actions):
    obs, rew, term, trunc, info = env.step(act)
    ram = env.unwrapped.get_ram()
    cur_x = read_u16(ram, ADDR_POS_X)
    cur_y = read_u16(ram, ADDR_POS_Y)
    cur_map = (ram[ADDR_MAP_BANK], ram[ADDR_MAP_NUM])

    if cur_map != (4, 0) and cur_map != (4, 1):
        print(f"!!! WARPED TO NEW MAP !!! Step {step:3d}: Map {cur_map} | Coordinates: X={cur_x}, Y={cur_y}")
        warped = True
        break
    if step % 25 == 0:
        print(f"Step {step:3d}: Map {cur_map} | Pos: ({cur_x:2d}, {cur_y:2d})")

if not warped:
    print(f"Final Pos before end: Map {cur_map} | Pos: ({cur_x}, {cur_y})")

env.close()
