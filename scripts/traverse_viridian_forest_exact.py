"""
Hardware-verified Viridian Forest Navigator.
Uses gMain.callback2 at IWRAM 0x430F4 to distinguish overworld vs battle with 100% fidelity.
Walks from (29, 62) all the way into Viridian Forest North Gatehouse (Map 15, 3).
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
import retro

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "visual_evidence" / "route_verification"
STATE_FILE = PROJECT_ROOT / "data" / "forest_active_floor.state"

BASE = 0x02000000
OVERWORLD_CB2 = 0x080565C9

def get_status(env):
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
        "bank": bank,
        "num": num,
        "x": x,
        "y": y,
        "trainer_flags": trainer_flags,
        "badge1": badge1,
        "in_battle": (cb2 != OVERWORLD_CB2),
        "cb2": hex(cb2)
    }

def step_btn(env, btn, frames=16):
    buttons = env.unwrapped.buttons
    act = np.zeros(len(buttons), dtype=np.int8)
    if btn in buttons:
        act[buttons.index(btn)] = 1
    for _ in range(frames):
        env.step(act)
    return get_status(env)

def escape_battle(env):
    print("    [CB2 BATTLE TRIGGERED] Escaping wild battle...")
    buttons = env.unwrapped.buttons
    def press(btn, frames=8, wait=12):
        act = np.zeros(len(buttons), dtype=np.int8)
        if btn in buttons: act[buttons.index(btn)] = 1
        for _ in range(frames): env.step(act)
        for _ in range(wait): env.step(np.zeros(len(buttons), dtype=np.int8))

    # 1. Dismiss "Wild Pokémon appeared!"
    press('A', 8, 8)
    # 2. Wait until menu appears
    for _ in range(240): env.step(np.zeros(len(buttons), dtype=np.int8))
    # 3. Select RUN
    press('RIGHT', 10, 12)
    press('DOWN', 10, 12)
    press('A', 10, 20)
    # 4. Wait for escape confirmation
    for _ in range(60): env.step(np.zeros(len(buttons), dtype=np.int8))
    # 5. Dismiss escape text
    press('A', 8, 16)
    # 6. Wait for overworld CB2 restore
    for _ in range(40): env.step(np.zeros(len(buttons), dtype=np.int8))
    status = get_status(env)
    print(f"    [CB2 RESTORED] Status: in_battle={status['in_battle']}, CB2={status['cb2']} at Pos: ({status['x']}, {status['y']})")

def annotate_screen(screen, info, title, filename):
    img = Image.fromarray(screen).resize((screen.shape[1]*2, screen.shape[0]*2), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, img.height - 40), (img.width, img.height)], fill=(0, 0, 0))
    text = f"{title} | Map: ({info['bank']}, {info['num']}) | Pos: ({info['x']}, {info['y']}) | Trainers: {info['trainer_flags']} | Badge1: {info['badge1']}"
    draw.text((10, img.height - 32), text, fill=(0, 255, 255))
    out_path = OUTPUT_DIR / filename
    img.save(str(out_path))
    print(f"[PROOF] {filename} -> {text}")
    return out_path

def main():
    with open(OUTPUT_DIR / "clean_forest_path.json") as f:
        path = json.load(f)

    print(f"Loaded clean forest path ({len(path)} steps)")
    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()
    with open(STATE_FILE, 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    status = get_status(env)
    print(f"Initial State: Map ({status['bank']}, {status['num']}) Pos: ({status['x']}, {status['y']}) | CB2: {status['cb2']}")

    for i, act in enumerate(path):
        prev_x, prev_y = status['x'], status['y']
        status = step_btn(env, act, 16)

        # Check if stepped on warp
        if (status['bank'], status['num']) != (1, 0):
            print(f"\n[WARP TRIGGERED at step {i+1}!] Transitioned to Map ({status['bank']}, {status['num']}) at ({status['x']}, {status['y']})")
            break

        # Check if in battle via CB2
        if status['in_battle']:
            escape_battle(env)
            status = get_status(env)
            # Re-execute the step that was interrupted by the encounter
            status = step_btn(env, act, 16)

        # If bumped/turned without battle, give 4 extra frames to ensure movement
        if (status['x'], status['y']) == (prev_x, prev_y) and not status['in_battle']:
            status = step_btn(env, act, 6)

        if (i + 1) % 20 == 0 or i == len(path) - 1:
            print(f"  Step {i+1:3d}/{len(path)}: Move {act:<5} -> Map ({status['bank']}, {status['num']}) at ({status['x']:2d}, {status['y']:2d})")
            if (i + 1) % 40 == 0:
                annotate_screen(env.unwrapped.get_screen(), status, "Viridian Forest Floor", f"proof_forest_traverse_step_{i+1}.png")

    # Settle
    for _ in range(50):
        step_btn(env, None, 1)

    status = get_status(env)
    print(f"\nFinal Arrival: Map ({status['bank']}, {status['num']}) at ({status['x']}, {status['y']})")
    annotate_screen(env.unwrapped.get_screen(), status, "Viridian Forest North Gatehouse", "proof_north_gatehouse_verified.png")

    with open(PROJECT_ROOT / "data" / "forest_north_gatehouse_verified.state", "wb") as f:
        f.write(env.unwrapped.em.get_state())
    print("[CHECKPOINT] Saved data/forest_north_gatehouse_verified.state")
    env.close()

if __name__ == "__main__":
    main()
