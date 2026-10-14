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
BASE_IWRAM = 0x03000000

# Let's inspect where EWRAM and IWRAM are in retro's get_ram()
ram = env.unwrapped.get_ram()
# Retro GBA RAM is typically 256KB EWRAM + 32KB IWRAM + ...
print(f"Total Retro RAM buffer length: {len(ram)} bytes")

# Address definitions:
# Overworld active buffers (sCurrentMap / gObjectEvents[0])
ADDR_MAP_BANK = 0x02031DBC - BASE_EWRAM
ADDR_MAP_NUM  = 0x02031DBD - BASE_EWRAM
ADDR_POS_X    = 0x02036E48 - BASE_EWRAM
ADDR_POS_Y    = 0x02036E4A - BASE_EWRAM

def read_u16(ram_buf, offset):
    return ram_buf[offset] + (ram_buf[offset+1] << 8)

def read_u32(ram_buf, offset):
    return ram_buf[offset] + (ram_buf[offset+1] << 8) + (ram_buf[offset+2] << 16) + (ram_buf[offset+3] << 24)

# In GBA pokefirered:
# gSaveBlock1Ptr is at IWRAM 0x03005008 (or 0x03005018)
# If len(ram) > 262144, IWRAM starts at 262144:
IWRAM_OFFSET = 0x40000 # 262,144 bytes

def get_saveblock1_pos(ram_buf):
    # Search for gSaveBlock1Ptr in IWRAM (0x03005000 - 0x03005100)
    # IWRAM is 32KB
    if len(ram_buf) >= IWRAM_OFFSET + 0x8000:
        for ptr_addr in [0x5008, 0x5018, 0x5000, 0x5010, 0x5020, 0x5024]:
            iwram_idx = IWRAM_OFFSET + ptr_addr
            ptr = read_u32(ram_buf, iwram_idx)
            if 0x02000000 <= ptr < 0x02040000:
                ewram_offset = ptr - BASE_EWRAM
                sb_x = read_u16(ram_buf, ewram_offset)
                sb_y = read_u16(ram_buf, ewram_offset + 2)
                return ptr, sb_x, sb_y
    return None, None, None

print("\n--- INITIAL STATE VERIFICATION ---")
sb_ptr, sb_x, sb_y = get_saveblock1_pos(ram)
print(f"Active ObjectEvent Pos: X={read_u16(ram, ADDR_POS_X)}, Y={read_u16(ram, ADDR_POS_Y)}")
print(f"Active Map Buffer: Bank={ram[ADDR_MAP_BANK]}, Num={ram[ADDR_MAP_NUM]}")
if sb_ptr:
    print(f"SaveBlock1 Pointer: {hex(sb_ptr)} -> Pos: X={sb_x}, Y={sb_y}")
else:
    print("SaveBlock1 Pointer: searching dynamically...")

# Walk sequence from Red's bedroom to stairs (downstairs warp):
# Red starts at (14, 14) in room.
# Stairs in Red's room are at the top right (around X=16, Y=10).
# Let's execute movement and monitor every single step for DMA relocation or changes!

# Actions: [B, null, SELECT, START, UP, DOWN, LEFT, RIGHT, A, null, L, R]
ACT_UP = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
ACT_DOWN = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
ACT_LEFT = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]
ACT_RIGHT = [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
ACT_A = [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]

print("\n--- STEPPING AND TRACKING COORDINATES THROUGH TIME ---")
# Walk right then up towards the stairs
walk_plan = [ACT_RIGHT]*40 + [ACT_UP]*60 + [ACT_RIGHT]*30 + [ACT_UP]*30

prev_x = -1
prev_y = -1
prev_map = (-1, -1)
transitions = []

for step, act in enumerate(walk_plan):
    obs, rew, term, trunc, info = env.step(act)
    ram = env.unwrapped.get_ram()
    cur_x = read_u16(ram, ADDR_POS_X)
    cur_y = read_u16(ram, ADDR_POS_Y)
    cur_map = (ram[ADDR_MAP_BANK], ram[ADDR_MAP_NUM])

    if cur_x != prev_x or cur_y != prev_y or cur_map != prev_map:
        sb_ptr, sb_x, sb_y = get_saveblock1_pos(ram)
        sb_info = f" | SB1 ({hex(sb_ptr) if sb_ptr else 'N/A'}): X={sb_x}, Y={sb_y}" if sb_ptr else ""
        print(f"Step {step:3d}: Map {cur_map} | ObjPos: ({cur_x:2d}, {cur_y:2d}){sb_info}")
        transitions.append((step, cur_map, (cur_x, cur_y), sb_ptr))
        prev_x, prev_y, prev_map = cur_x, cur_y, cur_map

env.close()
print(f"\nTotal coordinate transitions detected: {len(transitions)}")
