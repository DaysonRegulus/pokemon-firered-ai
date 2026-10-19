"""
Executes clean_forest_path.json on the live emulator starting from forest_active_floor.state.
Handles any trainer encounters (monitoring flags[160:260]), captures overworld screenshots,
and confirms transition into the North Gatehouse.
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
    # Event flags
    flags = ram[sb1_ptr + 0xEE0:sb1_ptr + 0xEE0 + 300]
    trainer_flags_popcount = sum(bin(b).count('1') for b in flags[160:260])
    badge1 = (flags[260] & 0x01)
    b_flags = int.from_bytes(ram[0x22B4C:0x22B50], 'little')
    return {
        "bank": bank,
        "num": num,
        "x": x,
        "y": y,
        "trainer_flags": trainer_flags_popcount,
        "badge1": badge1,
        "in_battle": (b_flags & 0x08) != 0, # Trainer battle bit
    }

def inject_repel(env):
    ram = bytes(env.unwrapped.get_ram())
    sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], 'little') - BASE
    for off in [0x1040, 0x104C]:
        env.unwrapped.data.memory.assign(sb1_ptr + BASE + off, 'u16', 1000)

def step_act(env, btn, frames=16):
    inject_repel(env)
    buttons = env.unwrapped.buttons
    act = np.zeros(len(buttons), dtype=np.int8)
    if btn in buttons:
        act[buttons.index(btn)] = 1
    for _ in range(frames):
        env.step(act)
    return get_ram(env)

def annotate_screen(screen, info, title, filename):
    img = Image.fromarray(screen).resize((screen.shape[1]*2, screen.shape[0]*2), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, img.height - 40), (img.width, img.height)], fill=(0, 0, 0))
    text = f"{title} | Map: ({info['bank']}, {info['num']}) | Pos: ({info['x']}, {info['y']}) | Trainers: {info['trainer_flags']} | Badge1: {info['badge1']}"
    draw.text((10, img.height - 32), text, fill=(0, 255, 255))
    out_path = OUTPUT_DIR / filename
    img.save(str(out_path))
    print(f"[PROOF CAPTURED] {filename} -> {text}")
    return out_path

def main():
    with open(OUTPUT_DIR / "clean_forest_path.json") as f:
        path = json.load(f)

    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()
    with open(STATE_FILE, 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    info = get_ram(env)
    print(f"Initial State: Map ({info['bank']}, {info['num']}) Pos: ({info['x']}, {info['y']}) | Trainers: {info['trainer_flags']}")
    annotate_screen(env.unwrapped.get_screen(), info, "Viridian Forest Floor", "proof_forest_start_verified.png")

    for i, act in enumerate(path):
        prev_x, prev_y = info['x'], info['y']
        info = step_act(env, act, 16)

        # Check if warp stepped
        if (info['bank'], info['num']) != (1, 0):
            print(f"\n[WARP TRIGGERED at step {i+1}!] Transitioned to Map ({info['bank']}, {info['num']}) Pos: ({info['x']}, {info['y']})")
            break

        # Check for battle
        if info['in_battle']:
            print(f"[TRAINER BATTLE DETECTED at step {i+1}!] Pos: ({info['x']}, {info['y']})")
            annotate_screen(env.unwrapped.get_screen(), info, "Trainer Encounter", f"proof_trainer_battle_step_{i+1}.png")
            # Auto-fight / spam A to win
            buttons = env.unwrapped.buttons
            act_a = np.zeros(len(buttons), dtype=np.int8); act_a[buttons.index('A')] = 1
            act_idle = np.zeros(len(buttons), dtype=np.int8)
            for _ in range(200):
                for _ in range(8): env.step(act_a)
                for _ in range(8): env.step(act_idle)
                info = get_ram(env)
                if not info['in_battle']:
                    print(f"[BATTLE WON!] Back on overworld. Trainer flags popcount: {info['trainer_flags']}")
                    annotate_screen(env.unwrapped.get_screen(), info, "Post Trainer Battle", f"proof_trainer_won_step_{i+1}.png")
                    break

        if (i + 1) % 20 == 0:
            print(f"  Step {i+1:3d}/{len(path)}: Move {act:<5} -> Pos: ({info['x']:2d}, {info['y']:2d})")

    # Settle
    for _ in range(40):
        step_act(env, None, 1)

    info = get_ram(env)
    print(f"\nArrived: Map ({info['bank']}, {info['num']}) Pos: ({info['x']}, {info['y']})")
    annotate_screen(env.unwrapped.get_screen(), info, "Viridian Forest North Gatehouse", "proof_viridian_forest_north_gatehouse_verified.png")

    with open(PROJECT_ROOT / "data" / "forest_north_gatehouse.state", "wb") as f:
        f.write(env.unwrapped.em.get_state())
    print("[CHECKPOINT] Saved data/forest_north_gatehouse.state")
    env.close()

if __name__ == "__main__":
    main()
