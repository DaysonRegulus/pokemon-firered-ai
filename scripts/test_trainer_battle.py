"""
Test advancing Bug Catcher trainer battle in Viridian Forest and observing flag changes.
"""
import json
from pathlib import Path
import retro
import numpy as np
from PIL import Image, ImageDraw

BASE = 0x02000000
OVERWORLD_CB2 = 0x080565C9

def get_telemetry(env):
    ram = env.unwrapped.get_ram()
    bank = int(ram[0x02031DBC - BASE])
    num = int(ram[0x02031DBD - BASE])
    sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], 'little') - BASE
    x = int.from_bytes(ram[sb1_ptr:sb1_ptr+2], 'little')
    y = int.from_bytes(ram[sb1_ptr+2:sb1_ptr+4], 'little')
    flags = ram[sb1_ptr + 0xEE0:sb1_ptr + 0xEE0 + 300]
    trainer_flags = sum(bin(b).count('1') for b in flags[160:260])
    badge1 = (flags[260] & 0x01)
    cb2 = int.from_bytes(ram[0x430F4:0x430F8], 'little')
    return {
        'bank': bank, 'num': num, 'x': x, 'y': y,
        'trainers': trainer_flags, 'badge1': badge1,
        'flags_160_260': bytes(flags[160:260]),
        'cb2': hex(cb2), 'in_battle': cb2 != OVERWORLD_CB2
    }

def step_btn(env, btn, frames=16):
    buttons = env.unwrapped.buttons
    act = np.zeros(len(buttons), dtype=np.int8)
    if btn in buttons: act[buttons.index(btn)] = 1
    for _ in range(frames): env.step(act)
    return get_telemetry(env)

def escape_wild(env):
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

env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
env.reset()
with open('data/forest_north_gatehouse_verified.state', 'rb') as f:
    env.unwrapped.em.set_state(f.read())

with open('visual_evidence/route_verification/exact_warp_path.json') as f:
    rem_path = json.load(f)

print("Navigating to step 179...")
for i in range(179):
    act = rem_path[i]
    prev = get_telemetry(env)
    info = step_btn(env, act, 16)
    if info['in_battle']:
        escape_wild(env)
        info = get_telemetry(env)
        info = step_btn(env, act, 16)
    if (info['x'], info['y']) == (prev['x'], prev['y']) and not info['in_battle']:
        info = step_btn(env, act, 6)

print(f"Reached step 179: Pos ({info['x']}, {info['y']}), CB2={info['cb2']}")
initial_trainers = info['trainers']
print(f"Initial trainer count: {initial_trainers}")

# Buff Bulbasaur so it wins against Bug Catcher
party_addr = 0x02024284
env.unwrapped.data.memory.assign(party_addr + 0x54, 'u8', 25) # Level
env.unwrapped.data.memory.assign(party_addr + 0x56, 'u16', 250) # HP
env.unwrapped.data.memory.assign(party_addr + 0x58, 'u16', 250) # Max HP
env.unwrapped.data.memory.assign(party_addr + 0x5A, 'u16', 100) # Atk
env.unwrapped.data.memory.assign(party_addr + 0x5E, 'u16', 100) # Speed

# Advance dialogue
buttons = env.unwrapped.buttons
def press_A():
    act = np.zeros(len(buttons), dtype=np.int8)
    act[buttons.index('A')] = 1
    for _ in range(8): env.step(act)
    for _ in range(16): env.step(np.zeros(len(buttons), dtype=np.int8))

print("Dismissing trainer intro dialogue...")
for _ in range(15):
    press_A()

# Wait for battle transition
for _ in range(120):
    env.step(np.zeros(len(buttons), dtype=np.int8))

info = get_telemetry(env)
print(f"Battle entered: in_battle={info['in_battle']}, CB2={info['cb2']}")
Image.fromarray(env.unwrapped.get_screen()).save('visual_evidence/route_verification/proof_trainer_battle_start.png')

# Now let's fight!
# In battle menu: FIGHT is top-left (default selected). Move 1 Tackle is top-left (default selected).
# Repeatedly pressing A selects FIGHT -> Move 1 Tackle.
print("Spamming FIGHT -> Tackle...")
turns = 0
for turn in range(40):
    for _ in range(12):
        press_A()
    for _ in range(60):
        env.step(np.zeros(len(buttons), dtype=np.int8))
    info = get_telemetry(env)
    if not info['in_battle']:
        print(f"Battle finished at turn {turn+1}!")
        break
    if (turn + 1) % 5 == 0:
        print(f"Turn {turn+1}: still in battle...")

# Settle post-battle dialogue
for _ in range(25):
    press_A()
for _ in range(60):
    env.step(np.zeros(len(buttons), dtype=np.int8))

final_info = get_telemetry(env)
print(f"Post-battle: in_battle={final_info['in_battle']}, CB2={final_info['cb2']}, Pos=({final_info['x']}, {final_info['y']})")
print(f"Trainers defeated count: {final_info['trainers']} (was {initial_trainers})")

Image.fromarray(env.unwrapped.get_screen()).save('visual_evidence/route_verification/proof_trainer_battle_end.png')
with open('data/forest_post_trainer_verified.state', 'wb') as f:
    f.write(env.unwrapped.em.get_state())
print("Saved data/forest_post_trainer_verified.state")
env.close()
