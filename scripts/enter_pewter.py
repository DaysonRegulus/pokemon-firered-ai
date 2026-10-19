import retro
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path

BASE = 0x02000000
OVERWORLD_CB2 = 0x080565C9

PROJECT_ROOT = Path("c:/dev/Antigravity/Pokemon FireRed AI")
OUTPUT_DIR = PROJECT_ROOT / "visual_evidence" / "route_verification"

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
        'cb2': hex(cb2), 'in_battle': cb2 != OVERWORLD_CB2
    }

def annotate_and_save(screen, info, title, filename):
    img = Image.fromarray(screen).resize((screen.shape[1]*2, screen.shape[0]*2), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, img.height - 40), (img.width, img.height)], fill=(0, 0, 0))
    text = f"{title} | Map: ({info['bank']}, {info['num']}) | Pos: ({info['x']}, {info['y']}) | Trainers: {info['trainers']} | Badge1: {info['badge1']}"
    draw.text((10, img.height - 32), text, fill=(0, 255, 255))
    out_path = OUTPUT_DIR / filename
    img.save(str(out_path))
    print(f"[PROOF CAPTURED] {filename} -> {text}")
    return out_path

def step_btn(env, btn, frames=16):
    buttons = env.unwrapped.buttons
    act = np.zeros(len(buttons), dtype=np.int8)
    if btn in buttons: act[buttons.index(btn)] = 1
    for _ in range(frames): env.step(act)
    return get_telemetry(env)

env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
env.reset()
with open('data/pewter_city_arrival.state', 'rb') as f:
    env.unwrapped.em.set_state(f.read())

print("Start at tree:", get_telemetry(env))

# Move RIGHT 3 steps to dirt path (x=8)
for _ in range(3):
    info = step_btn(env, 'RIGHT', 18)
    print("Move RIGHT ->", info)

# Move UP into Pewter City
print("\n--- Moving UP into Pewter City ---")
for step in range(25):
    info = step_btn(env, 'UP', 18)
    print(f"Step {step+1}: Map ({info['bank']}, {info['num']}) Pos: ({info['x']}, {info['y']})")
    if (info['bank'], info['num']) == (3, 2):
        print(f"BINGO! Entered Pewter City! Map ({info['bank']}, {info['num']}) Pos: ({info['x']}, {info['y']})")
        break

for _ in range(40): step_btn(env, None, 1)
info = get_telemetry(env)
print("Settled in Pewter City:", info)
annotate_and_save(env.unwrapped.get_screen(), info, "Pewter City Entrance", "proof_pewter_city_clean_entrance.png")

with open('data/pewter_city_verified.state', 'wb') as f:
    f.write(env.unwrapped.em.get_state())
print("Saved data/pewter_city_verified.state")
env.close()
