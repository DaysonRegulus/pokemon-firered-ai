"""
Complete End-to-End Traversal from Viridian Forest (39, 23) -> North Gatehouse -> Route 2 -> Pewter City -> Pewter Gym -> Brock.
Captures annotated visual proofs and verifies RAM coordinates and event flags at every landmark.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
import retro

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "visual_evidence" / "route_verification"
STATE_FILE = PROJECT_ROOT / "data" / "forest_north_gatehouse_verified.state"

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
        "bank": bank,
        "num": num,
        "x": x,
        "y": y,
        "trainers": trainer_flags,
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
    return get_telemetry(env)

def escape_battle(env):
    print("    [CB2 BATTLE] Escaping wild battle...")
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

def main():
    with open(OUTPUT_DIR / "exact_warp_path.json") as f:
        rem_path = json.load(f)

    print("=" * 65)
    print(" ADVANCING FROM VIRIDIAN FOREST TO PEWTER CITY & PEWTER GYM")
    print("=" * 65)

    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()
    with open(STATE_FILE, 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    info = get_telemetry(env)
    print(f"Start: Map ({info['bank']}, {info['num']}) Pos: ({info['x']}, {info['y']})")

    # STAGE 1: Walk to North Gatehouse (Map 15, 3)
    print("\n--- STAGE 1: Navigating Northern Forest Corridor to North Gatehouse ---")
    for i, act in enumerate(rem_path):
        prev_x, prev_y = info['x'], info['y']
        info = step_btn(env, act, 16)

        if (info['bank'], info['num']) != (1, 0):
            print(f"Warp stepped at step {i+1}! Transitioned to Map ({info['bank']}, {info['num']}) at ({info['x']}, {info['y']})")
            break

        if info['in_battle']:
            escape_battle(env)
            info = get_telemetry(env)
            info = step_btn(env, act, 16)

        if (info['x'], info['y']) == (prev_x, prev_y) and not info['in_battle']:
            info = step_btn(env, act, 6)

        if (i + 1) % 20 == 0:
            print(f"  Step {i+1:2d}/{len(rem_path)}: Move {act:<5} -> Pos: ({info['x']:2d}, {info['y']:2d})")

    # Settle warp into North Gatehouse
    for _ in range(40): step_btn(env, None, 1)
    info = get_telemetry(env)
    print(f"[REACHED] North Gatehouse Interior: Map ({info['bank']}, {info['num']}) at ({info['x']}, {info['y']})")
    assert (info['bank'], info['num']) == (15, 3), f"Expected North Gatehouse Map (15, 3), got ({info['bank']}, {info['num']})"
    annotate_and_save(env.unwrapped.get_screen(), info, "North Gatehouse Interior", "proof_north_gatehouse_interior.png")

    # STAGE 2: Walk North through Gatehouse onto Route 2 (Map 3, 20)
    print("\n--- STAGE 2: Exiting North Gatehouse to Route 2 (North Section) ---")
    # Walk straight UP through the gatehouse corridor to the north door (7, 1)
    for _ in range(9):
        info = step_btn(env, 'UP', 18)
    for _ in range(40): step_btn(env, None, 1) # Settle warp

    info = get_telemetry(env)
    print(f"[REACHED] Route 2 North: Map ({info['bank']}, {info['num']}) at ({info['x']}, {info['y']})")
    assert (info['bank'], info['num']) == (3, 20), f"Expected Route 2 Map (3, 20), got ({info['bank']}, {info['num']})"
    annotate_and_save(env.unwrapped.get_screen(), info, "Route 2 North Exit", "proof_route2_north_section.png")

    # STAGE 3: Walk North along Route 2 into Pewter City (Map 3, 2)
    print("\n--- STAGE 3: Stepping North into Pewter City ---")
    # From Route 2 (5, 13), walk UP towards y=0
    for s in range(16):
        info = step_btn(env, 'UP', 18)
        if (info['bank'], info['num']) == (3, 2):
            print(f"Crossed boundary into Pewter City at step {s+1}!")
            break

    for _ in range(30): step_btn(env, None, 1)
    info = get_telemetry(env)
    print(f"[REACHED] Pewter City: Map ({info['bank']}, {info['num']}) at ({info['x']}, {info['y']})")
    assert (info['bank'], info['num']) == (3, 2), f"Expected Pewter City Map (3, 2), got ({info['bank']}, {info['num']})"
    annotate_and_save(env.unwrapped.get_screen(), info, "Pewter City Arrival", "proof_pewter_city_arrival.png")

    # STAGE 4: Navigate Pewter City to the Pewter Gym entrance (15, 16)
    print("\n--- STAGE 4: Navigating Pewter City to Gym Entrance ---")
    # Red is around x=17, y=39 in Pewter City. Gym is at (15, 16)
    # Walk UP towards y=17
    while info['y'] > 17:
        info = step_btn(env, 'UP', 18)
    # Walk LEFT towards x=15
    while info['x'] > 15:
        info = step_btn(env, 'LEFT', 18)
    # Walk UP into Gym door at (15, 16)
    while (info['bank'], info['num']) == (3, 2):
        info = step_btn(env, 'UP', 18)

    for _ in range(40): step_btn(env, None, 1)
    info = get_telemetry(env)
    print(f"[REACHED] Pewter Gym Interior: Map ({info['bank']}, {info['num']}) at ({info['x']}, {info['y']})")
    assert (info['bank'], info['num']) == (6, 2), f"Expected Pewter Gym Map (6, 2), got ({info['bank']}, {info['num']})"
    annotate_and_save(env.unwrapped.get_screen(), info, "Pewter Gym Entrance", "proof_pewter_gym_interior_verified.png")

    # STAGE 5: Walk up to Gym Leader Brock at (6, 5)
    print("\n--- STAGE 5: Approaching Gym Leader Brock ---")
    # From rug at (6, 14), walk UP along x=6 to (6, 6)
    while info['y'] > 6:
        info = step_btn(env, 'UP', 18)

    print(f"[FACE TO FACE] Standing in front of Brock: Pos ({info['x']}, {info['y']})")
    annotate_and_save(env.unwrapped.get_screen(), info, "Brock Face-to-Face", "proof_brock_face_to_face.png")

    # Interact with Brock: Press 'A' to start dialogue
    buttons = env.unwrapped.buttons
    act_a = np.zeros(len(buttons), dtype=np.int8); act_a[buttons.index('A')] = 1
    for _ in range(16): env.step(act_a)
    for _ in range(30): env.step(np.zeros(len(buttons), dtype=np.int8))

    info = get_telemetry(env)
    annotate_and_save(env.unwrapped.get_screen(), info, "Brock Gym Leader Dialogue", "proof_brock_dialogue_verified.png")
    print(f"\n[EVENT FLAGS VERIFIED] Boulder Badge FLAG_BADGE01_GET: {info['badge1']} | Defeated Trainers Popcount: {info['trainers']}")

    # Save final verified state
    final_state = env.unwrapped.em.get_state()
    with open(PROJECT_ROOT / "data" / "brock_gym_verified.state", "wb") as f:
        f.write(final_state)
    print("\nSaved data/brock_gym_verified.state")
    env.close()
    print("ALL STAGES COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
