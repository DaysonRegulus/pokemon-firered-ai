"""
Automated Navigator & Battle-Handling Walker from Pallet Town to Viridian City.
Empirically verifies Route 1 (3, 19) and Viridian City (3, 1) in RAM and visual frames.
"""
from pathlib import Path
import time
import numpy as np
import imageio
import retro

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "visual_evidence" / "route_verification"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE = 0x02000000

def get_ram_info(env):
    ram = env.unwrapped.get_ram()
    map_bank = int(ram[0x02031DBC - BASE])
    map_num = int(ram[0x02031DBD - BASE])
    pos_x = int.from_bytes(ram[0x02036E48 - BASE:0x02036E4A - BASE], 'little')
    pos_y = int.from_bytes(ram[0x02036E4A - BASE:0x02036E4C - BASE], 'little')
    b_flags = int.from_bytes(ram[0x22B4C:0x22B50], 'little')
    return {
        "map_bank": map_bank,
        "map_num": map_num,
        "pos_x": pos_x,
        "pos_y": pos_y,
        "in_battle": b_flags != 0,
    }

def make_step(env, btn_name, frames=16):
    buttons = env.unwrapped.buttons
    act = np.zeros(len(buttons), dtype=np.int8)
    if btn_name in buttons:
        act[buttons.index(btn_name)] = 1
    for _ in range(frames):
        env.step(act)
    return get_ram_info(env)

def escape_battle(env):
    print("[NAVIGATOR] Wild battle detected! Escaping...")
    # Advance battle entry text
    for _ in range(12):
        make_step(env, 'A', 16)
        info = get_ram_info(env)
        if not info["in_battle"]:
            return
    # Select RUN: Down, Right, A
    make_step(env, 'DOWN', 8)
    make_step(env, 'RIGHT', 8)
    make_step(env, 'A', 16)
    # Clear escape text
    for _ in range(12):
        make_step(env, 'B', 16)
        info = get_ram_info(env)
        if not info["in_battle"]:
            break
    print("[NAVIGATOR] Escaped battle! Back on overworld.")

def main():
    print("=" * 60)
    print(" EMPIRICAL VERIFICATION: PALLET -> ROUTE 1 -> VIRIDIAN")
    print("=" * 60)

    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()

    # Step 1: Exit Mom's living room
    for b in ['DOWN', 'LEFT', 'LEFT', 'LEFT', 'DOWN', 'DOWN']:
        make_step(env, b)
    make_step(env, None, 60) # Warp settle

    info = get_ram_info(env)
    print(f"Spawned Outside: Map ({info['map_bank']},{info['map_num']}) Pos: ({info['pos_x']},{info['pos_y']})")

    # Step 2: Navigate Pallet Town north path
    for m in ['DOWN', 'DOWN', 'DOWN', 'RIGHT', 'RIGHT', 'RIGHT', 'RIGHT', 'RIGHT'] + ['UP'] * 14:
        make_step(env, m, 18)

    info = get_ram_info(env)
    print(f"Entered Route 1: Map ({info['map_bank']},{info['map_num']}) Pos: ({info['pos_x']},{info['pos_y']})")
    assert info['map_bank'] == 3 and info['map_num'] == 19, "Must be on Route 1"

    # Step 3: Walk north past first ledge
    for _ in range(4): make_step(env, 'UP', 18)
    for _ in range(4): make_step(env, 'LEFT', 18)
    for _ in range(3): make_step(env, 'UP', 18)
    for _ in range(9): make_step(env, 'RIGHT', 18)

    info = get_ram_info(env)
    print(f"Past First Ledge: Map ({info['map_bank']},{info['map_num']}) Pos: ({info['pos_x']},{info['pos_y']})")

    # Step 4: Step north along Route 1 towards Viridian City
    step_count = 0
    while step_count < 150:
        info = get_ram_info(env)
        if info['in_battle']:
            escape_battle(env)
            continue

        if info['map_bank'] == 3 and info['map_num'] == 1:
            print(f"\n[SUCCESS] REACHED VIRIDIAN CITY! Map ({info['map_bank']},{info['map_num']}) Pos: ({info['pos_x']},{info['pos_y']})")
            screen = env.unwrapped.get_screen()
            p = OUTPUT_DIR / "proof_viridian_city_entry.png"
            imageio.imwrite(str(p), screen)
            print(f"Saved visual proof to: {p.name}")
            break

        prev_y = info['pos_y']
        info = make_step(env, 'UP', 18)
        step_count += 1

        # If blocked by obstacle, try sidestepping
        if info['pos_y'] == prev_y and not info['in_battle']:
            # Try RIGHT then UP, or LEFT then UP
            info_r = make_step(env, 'RIGHT', 18)
            if info_r['pos_x'] == info['pos_x']:
                make_step(env, 'LEFT', 18)
                make_step(env, 'LEFT', 18)

        if step_count % 10 == 0:
            print(f"  Step {step_count:3d}: Map ({info['map_bank']},{info['map_num']}) Pos: ({info['pos_x']:2d},{info['pos_y']:2d})")

    env.close()

if __name__ == "__main__":
    main()
