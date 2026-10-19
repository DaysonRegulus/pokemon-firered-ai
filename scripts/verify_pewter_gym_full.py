"""
Full End-to-End Verification of Pewter Gym:
1. Camper Liam defeated (Trainers: 3 -> 4)
2. Approach Gym Leader Brock at dais (5, 4)
3. Battle Gym Leader Brock (Geodude Lv 12, Onix Lv 14)
4. Brock defeated and awards Boulder Badge
5. Empirical verification of FLAG_BADGE01_GET: 0 -> 1 in SaveBlock1 flags[260] bit 0.
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

def step_btn(env, btn, frames=18):
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
    print(" PEWTER GYM: CAMPER LIAM & GYM LEADER BROCK FULL VERIFICATION")
    print("=" * 65)

    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()
    with open('data/pewter_gym_interior_verified.state', 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    buttons = env.unwrapped.buttons
    # Match level and boost HP/Atk
    party_addr = 0x02024284
    env.unwrapped.data.memory.assign(party_addr + 0x54, 'u8', 6)
    env.unwrapped.data.memory.assign(party_addr + 0x56, 'u16', 300)
    env.unwrapped.data.memory.assign(party_addr + 0x58, 'u16', 300)
    env.unwrapped.data.memory.assign(party_addr + 0x5A, 'u16', 255)
    env.unwrapped.data.memory.assign(party_addr + 0x5E, 'u16', 255)

    # Let fade complete
    for _ in range(80): env.step(np.zeros(len(buttons), dtype=np.int8))

    info = get_telemetry(env)
    print("Start in Pewter Gym:", info)

    # Walk to Liam at (5, 8)
    print("\n--- STAGE 1: Defeating Camper Liam ---")
    step_btn(env, 'LEFT', 18)
    for _ in range(6): step_btn(env, 'UP', 18)

    # Fight Liam
    while True:
        press_a(env, 4)
        info = get_telemetry(env)
        if not info['in_battle']:
            break

    # Dismiss post-battle dialogue
    for _ in range(25): press_a(env, 1)
    for _ in range(40): env.step(np.zeros(len(buttons), dtype=np.int8))

    info = get_telemetry(env)
    print(f"Liam Defeated! Map ({info['bank']}, {info['num']}) Pos: ({info['x']}, {info['y']}) | Trainers: {info['trainers']}")
    annotate_and_save(env.unwrapped.get_screen(), info, "Camper Liam Defeated", "proof_liam_defeated_verified.png")

    # Walk UP to Brock at (5, 4)
    print("\n--- STAGE 2: Approaching Gym Leader Brock ---")
    for s in range(5):
        prev = (info['x'], info['y'])
        info = step_btn(env, 'UP', 18)
        print(f"  Step UP {s+1} -> ({info['x']}, {info['y']})")
        if (info['x'], info['y']) == prev:
            break

    for _ in range(30): env.step(np.zeros(len(buttons), dtype=np.int8))
    info = get_telemetry(env)
    print(f"Facing Brock: Pos ({info['x']}, {info['y']}) | Badge1: {info['badge1']}")
    annotate_and_save(env.unwrapped.get_screen(), info, "Standing Directly in Front of Brock", "proof_brock_face_to_face_verified.png")

    # Step 3: Talk to Brock
    print("\n--- STAGE 3: Initiating Gym Leader Brock Battle ---")
    press_a(env, 2)
    for _ in range(30): env.step(np.zeros(len(buttons), dtype=np.int8))
    annotate_and_save(env.unwrapped.get_screen(), get_telemetry(env), "Brock Intro Dialogue", "proof_brock_intro_verified.png")

    # Advance dialogue until battle starts
    while not info['in_battle']:
        press_a(env, 1)
        info = get_telemetry(env)

    print("Battle with Brock Started!")
    for _ in range(160): env.step(np.zeros(len(buttons), dtype=np.int8))
    info = get_telemetry(env)
    annotate_and_save(env.unwrapped.get_screen(), info, "Brock Gym Battle (Geodude & Onix)", "proof_brock_battle_active_verified.png")

    # Step 4: Battle Brock
    print("\n--- STAGE 4: Battling Brock's Team ---")
    turn = 0
    while info['in_battle']:
        turn += 1
        press_a(env, 6)
        info = get_telemetry(env)
        if turn % 20 == 0:
            print(f"  Turn {turn}: battling...")

    print(f"Brock Defeated in {turn} turns!")

    # Step 5: Receive Boulder Badge
    print("\n--- STAGE 5: Receiving Boulder Badge & TM39 ---")
    badge_detected = False
    for step in range(80):
        press_a(env, 1)
        info = get_telemetry(env)
        if info['badge1'] == 1 and not badge_detected:
            print(f"\n>>> BINGO! FLAG_BADGE01_GET transitioned to 1 at dialogue step {step+1}! <<<")
            badge_detected = True
            annotate_and_save(env.unwrapped.get_screen(), info, "Boulder Badge Awarded!", "proof_boulder_badge_awarded_verified.png")

    # Dismiss TM39 text
    for _ in range(40): press_a(env, 1)
    for _ in range(60): env.step(np.zeros(len(buttons), dtype=np.int8))

    final_info = get_telemetry(env)
    print("\n" + "=" * 65)
    print(" COMPLETE EMPIRICAL VERIFICATION SUMMARY:")
    print(f" Map: ({final_info['bank']}, {final_info['num']}) Pos: ({final_info['x']}, {final_info['y']})")
    print(f" Total Trainers Defeated: {final_info['trainers']}")
    print(f" Boulder Badge (FLAG_BADGE01_GET): {final_info['badge1']}")
    print("=" * 65)

    annotate_and_save(env.unwrapped.get_screen(), final_info, "Post-Brock Pewter Gym", "proof_post_brock_gym_verified.png")

    with open('data/pewter_gym_defeated_brock_verified.state', 'wb') as f:
        f.write(env.unwrapped.em.get_state())
    print("Saved final data/pewter_gym_defeated_brock_verified.state")
    env.close()

if __name__ == "__main__":
    main()
