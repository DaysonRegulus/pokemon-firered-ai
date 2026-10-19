import json
from pathlib import Path
import retro
import numpy as np
from PIL import Image

BASE = 0x02000000
OVERWORLD_CB2 = 0x080565C9

def get_telemetry(env):
    ram = env.unwrapped.get_ram()
    bank = int(ram[0x02031DBC - BASE])
    num = int(ram[0x02031DBD - BASE])
    sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], 'little') - BASE
    x = int.from_bytes(ram[sb1_ptr:sb1_ptr+2], 'little')
    y = int.from_bytes(ram[sb1_ptr+2:sb1_ptr+4], 'little')
    cb2 = int.from_bytes(ram[0x430F4:0x430F8], 'little')
    return {'bank': bank, 'num': num, 'x': x, 'y': y, 'cb2': hex(cb2), 'in_battle': cb2 != OVERWORLD_CB2}

def step_btn(env, btn, frames=16):
    buttons = env.unwrapped.buttons
    act = np.zeros(len(buttons), dtype=np.int8)
    if btn in buttons: act[buttons.index(btn)] = 1
    for _ in range(frames): env.step(act)
    return get_telemetry(env)

def escape_battle(env):
    buttons = env.unwrapped.buttons
    def press(btn, frames=8, wait=12):
        act = np.zeros(len(buttons), dtype=np.int8)
        if btn in buttons: act[buttons.index(btn)] = 1
        for _ in range(frames): env.step(act)
        for _ in range(wait): env.step(np.zeros(len(buttons), dtype=np.int8))
    press('A', 8, 8)
    for _ in range(240): env.step(np.zeros(len(buttons), dtype=np.int8))
    press('RIGHT', 10, 12)
    press('DOWN', 10, 12)
    press('A', 10, 20)
    for _ in range(60): env.step(np.zeros(len(buttons), dtype=np.int8))
    press('A', 8, 16)
    for _ in range(40): env.step(np.zeros(len(buttons), dtype=np.int8))

with open('visual_evidence/route_verification/exact_warp_path.json') as f:
    rem_path = json.load(f)

env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
env.reset()
with open('data/forest_north_gatehouse_verified.state', 'rb') as f:
    env.unwrapped.em.set_state(f.read())

print('Initial:', get_telemetry(env))

for i, act in enumerate(rem_path):
    prev = get_telemetry(env)
    info = step_btn(env, act, 16)
    if (info['bank'], info['num']) != (1, 0):
        print(f"Warp stepped at step {i+1}: Map ({info['bank']}, {info['num']}) at ({info['x']}, {info['y']})")
        break
    if info['in_battle']:
        escape_battle(env)
        info = get_telemetry(env)
        info = step_btn(env, act, 16)
    if (info['x'], info['y']) == (prev['x'], prev['y']) and not info['in_battle']:
        info = step_btn(env, act, 6)
    if i >= 170:
        print(f"Step {i+1:3d}: {act:<5} -> ({info['x']:2d}, {info['y']:2d}) in_battle={info['in_battle']}")

Image.fromarray(env.unwrapped.get_screen()).save('visual_evidence/route_verification/debug_step197.png')
print('Debug screen saved to visual_evidence/route_verification/debug_step197.png')
env.close()
