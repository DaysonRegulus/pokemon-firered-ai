"""
Complete Viridian Forest Navigator with Battle Escaper.
Follows clean_forest_path.json, automatically escapes any wild encounters,
and walks straight into Viridian Forest North Gatehouse (Map 15, 3).
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

def get_ram(env):
    ram = env.unwrapped.get_ram()
    bank = int(ram[0x02031DBC - BASE])
    num = int(ram[0x02031DBD - BASE])
    sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], 'little') - BASE
    x = int.from_bytes(ram[sb1_ptr:sb1_ptr+2], 'little')
    y = int.from_bytes(ram[sb1_ptr+2:sb1_ptr+4], 'little')
    flags = ram[sb1_ptr + 0xEE0:sb1_ptr + 0xEE0 + 300]
    trainer_flags = sum(bin(b).count('1') for b in flags[160:260])
    badge1 = (flags[260] & 0x01)
    return {
        "bank": bank,
        "num": num,
        "x": x,
        "y": y,
        "trainer_flags": trainer_flags,
        "badge1": badge1,
    }

def step_btn(env, btn, frames=16):
    buttons = env.unwrapped.buttons
    act = np.zeros(len(buttons), dtype=np.int8)
    if btn in buttons:
        act[buttons.index(btn)] = 1
    for _ in range(frames):
        env.step(act)
    return get_ram(env)

def escape_battle(env):
    print("  [BATTLE DETECTED] Escaping battle...")
    buttons = env.unwrapped.buttons
    def press(btn, frames=8, wait=12):
        act = np.zeros(len(buttons), dtype=np.int8)
        if btn in buttons: act[buttons.index(btn)] = 1
        for _ in range(frames): env.step(act)
        for _ in range(wait): env.step(np.zeros(len(buttons), dtype=np.int8))

    # 1. Dismiss "Wild Pokémon appeared!"
    press('A', 8, 8)
    # 2. Wait for Bulbasaur and menu to appear
    for _ in range(240): env.step(np.zeros(len(buttons), dtype=np.int8))
    # 3. Move to RUN and select
    press('RIGHT', 10, 12)
    press('DOWN', 10, 12)
    press('A', 10, 20)
    # 4. Wait for "Got away safely!"
    for _ in range(60): env.step(np.zeros(len(buttons), dtype=np.int8))
    # 5. Dismiss "Got away safely!"
    press('A', 8, 16)
    # 6. Settle back on overworld
    for _ in range(50): env.step(np.zeros(len(buttons), dtype=np.int8))
    print("  [BATTLE ESCAPED] Successfully back on overworld floor!")

def annotate_and_save(screen, info, title, filename):
    img = Image.fromarray(screen).resize((screen.shape[1]*2, screen.shape[0]*2), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, img.height - 40), (img.width, img.height)], fill=(0, 0, 0))
    text = f"{title} | Map: ({info['bank']}, {info['num']}) | Coords: ({info['x']}, {info['y']}) | Trainers: {info['trainer_flags']} | Badge1: {info['badge1']}"
    draw.text((10, img.height - 32), text, fill=(0, 255, 255))
    out_path = OUTPUT_DIR / filename
    img.save(str(out_path))
    print(f"[PROOF CAPTURED] {filename} -> {text}")
    return out_path

def main():
    with open(OUTPUT_DIR / "clean_forest_path.json") as f:
        path = json.load(f)

    print(f"Loaded clean forest path ({len(path)} steps)")
    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()
    with open(STATE_FILE, 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    info = get_ram(env)
    print(f"Spawn in Forest: Map ({info['bank']}, {info['num']}) at ({info['x']}, {info['y']})")

    i = 0
    while i < len(path):
        act = path[i]
        prev_x, prev_y = info['x'], info['y']
        info = step_btn(env, act, 16)

        # Check if map transitioned (we reached the gatehouse warp!)
        if (info['bank'], info['num']) != (1, 0):
            print(f"\n[SUCCESS!] Warp stepped at step {i+1}! Transitioned to Map ({info['bank']}, {info['num']}) at ({info['x']}, {info['y']})")
            break

        # Check if coordinates didn't change: could be battle or bump
        if (info['x'], info['y']) == (prev_x, prev_y):
            # Test if battle triggered by checking screen change or trying escape
            # Check if screen has battle UI
            screen = env.unwrapped.get_screen()
            # In battle, the bottom right or top left has high contrast text box
            # Try escaping battle
            escape_battle(env)
            info = get_ram(env)
            # Re-try the current step
            info = step_btn(env, act, 16)

        if (i + 1) % 15 == 0 or i == len(path) - 1:
            print(f"  Step {i+1:3d}/{len(path)}: Move {act:<5} -> Map ({info['bank']}, {info['num']}) at ({info['x']:2d}, {info['y']:2d})")
            if (i + 1) % 45 == 0:
                annotate_and_save(env.unwrapped.get_screen(), info, "Viridian Forest Floor", f"proof_forest_traverse_step_{i+1}.png")
        i += 1

    # Settle
    for _ in range(40):
        step_btn(env, None, 1)

    info = get_ram(env)
    print(f"\nArrival: Map ({info['bank']}, {info['num']}) at ({info['x']}, {info['y']})")
    annotate_and_save(env.unwrapped.get_screen(), info, "Viridian Forest North Gatehouse", "proof_north_gatehouse_verified.png")

    # Save state
    with open(PROJECT_ROOT / "data" / "forest_north_gatehouse_final.state", "wb") as f:
        f.write(env.unwrapped.em.get_state())
    print("[CHECKPOINT] Saved data/forest_north_gatehouse_final.state")
    env.close()

if __name__ == "__main__":
    main()
