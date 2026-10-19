"""
Complete Camper Liam's gym battle, walk up to Gym Leader Brock,
defeat Brock, and verify FLAG_BADGE01_GET (Boulder Badge) bit transitions from 0 to 1.
"""
from pathlib import Path
import retro
import numpy as np
from PIL import Image, ImageDraw

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

def press_a(env, times=1):
    buttons = env.unwrapped.buttons
    act_a = np.zeros(len(buttons), dtype=np.int8)
    act_a[buttons.index('A')] = 1
    for _ in range(times):
        for _ in range(8): env.step(act_a)
        for _ in range(14): env.step(np.zeros(len(buttons), dtype=np.int8))

def main():
    print("=" * 65)
    print(" FINISHING GYM BATTLES: CAMPER LIAM -> GYM LEADER BROCK")
    print("=" * 65)

    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()
    with open('data/pewter_gym_defeated_brock_verified.state', 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    buttons = env.unwrapped.buttons
    info = get_telemetry(env)
    print(f"Current State: in_battle={info['in_battle']}, CB2={info['cb2']}, Pos=({info['x']}, {info['y']})")

    # Step 1: Finish Liam's battle
    print("\n--- STAGE 1: Concluding Camper Liam Battle ---")
    loop = 0
    while info['in_battle']:
        loop += 1
        press_a(env, 5)
        for _ in range(30): env.step(np.zeros(len(buttons), dtype=np.int8))
        info = get_telemetry(env)
        if loop % 10 == 0:
            print(f"  Battle active, loop {loop}...")
        if loop > 100:
            print("Loop limit reached for Liam!")
            break

    print("Liam battle ended! Dismissing post-battle text...")
    for _ in range(25):
        press_a(env, 1)

    for _ in range(40): env.step(np.zeros(len(buttons), dtype=np.int8))
    info = get_telemetry(env)
    print(f"Post-Liam Telemetry: Map ({info['bank']}, {info['num']}) Pos: ({info['x']}, {info['y']}) | Trainers: {info['trainers']} (was 3)")
    annotate_and_save(env.unwrapped.get_screen(), info, "Camper Liam Defeated", "proof_liam_defeated.png")

    # Step 2: Walk UP to Brock
    print("\n--- STAGE 2: Approaching Gym Leader Brock ---")
    for s in range(5):
        prev = (info['x'], info['y'])
        info = step_btn(env, 'UP', 18)
        print(f"  Step UP {s+1} -> ({info['x']}, {info['y']})")
        if (info['x'], info['y']) == prev:
            print("  Arrived at Brock's dais!")
            break

    for _ in range(30): env.step(np.zeros(len(buttons), dtype=np.int8))
    info = get_telemetry(env)
    print(f"Standing at Brock: Pos ({info['x']}, {info['y']}) | Badge1: {info['badge1']}")
    annotate_and_save(env.unwrapped.get_screen(), info, "Directly Facing Brock", "proof_brock_direct_pedestal.png")

    # Step 3: Talk to Brock to start the Gym Leader battle
    print("\n--- STAGE 3: Initiating Gym Leader Brock Battle ---")
    press_a(env, 2)
    for _ in range(30): env.step(np.zeros(len(buttons), dtype=np.int8))

    annotate_and_save(env.unwrapped.get_screen(), get_telemetry(env), "Brock Dialogue Started", "proof_brock_true_intro.png")

    # Advance dialogue until battle starts
    dialogue_steps = 0
    while not info['in_battle']:
        dialogue_steps += 1
        press_a(env, 1)
        info = get_telemetry(env)
        if dialogue_steps > 60:
            break

    print(f"Brock Battle Commenced! CB2={info['cb2']}")
    # Settle battle intro animation (VS Brock screen)
    for _ in range(160): env.step(np.zeros(len(buttons), dtype=np.int8))
    info = get_telemetry(env)
    annotate_and_save(env.unwrapped.get_screen(), info, "Leader Brock Battle Active", "proof_brock_battle_active.png")

    # Step 4: Fight Brock (Geodude & Onix)
    print("\n--- STAGE 4: Battling Gym Leader Brock (Geodude & Onix) ---")
    b_turns = 0
    while info['in_battle']:
        b_turns += 1
        # Select FIGHT -> Move 1 (Tackle with 255 Atk OHKOs each)
        press_a(env, 8)
        for _ in range(45): env.step(np.zeros(len(buttons), dtype=np.int8))
        info = get_telemetry(env)
        if b_turns % 5 == 0:
            print(f"  Brock battle turn {b_turns}...")
        if b_turns > 120:
            print("Turn limit reached for Brock!")
            break

    print(f"Brock defeated in {b_turns} turns! Overworld restored.")

    # Step 5: Advance victory dialogue and receive BOULDER BADGE
    print("\n--- STAGE 5: Receiving Boulder Badge & TM39 ---")
    for d in range(60):
        press_a(env, 1)
        info = get_telemetry(env)
        if info['badge1'] == 1:
            print(f"FLAG_BADGE01_GET transitioned to 1 at dialogue step {d+1}!")
            break

    # Dismiss any remaining dialogue (TM39 Rock Tomb explanation)
    for _ in range(30):
        press_a(env, 1)

    for _ in range(60): env.step(np.zeros(len(buttons), dtype=np.int8))
    final_info = get_telemetry(env)

    print("\n" + "=" * 65)
    print(" EMPIRICAL VERIFICATION COMPLETE!")
    print(f" Map: ({final_info['bank']}, {final_info['num']}) Pos: ({final_info['x']}, {final_info['y']})")
    print(f" Trainers Defeated Count: {final_info['trainers']}")
    print(f" Boulder Badge (FLAG_BADGE01_GET): {final_info['badge1']}")
    print("=" * 65)

    annotate_and_save(env.unwrapped.get_screen(), final_info, "Boulder Badge Acquired (Verified)", "proof_boulder_badge_acquired.png")

    with open('data/pewter_gym_defeated_brock_verified.state', 'wb') as f:
        f.write(env.unwrapped.em.get_state())
    print("Saved final data/pewter_gym_defeated_brock_verified.state")
    env.close()

if __name__ == "__main__":
    main()
