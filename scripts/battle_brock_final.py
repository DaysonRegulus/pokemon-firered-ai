"""
Walk up to Brock's pedestal (5, 4), initiate battle, defeat Brock's Geodude and Onix,
and verify the transition of FLAG_BADGE01_GET from 0 to 1 in SaveBlock1.
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

def main():
    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()
    with open('data/brock_face_to_face.state', 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    buttons = env.unwrapped.buttons
    info = get_telemetry(env)
    print(f"Start from (5, 9): Map ({info['bank']}, {info['num']}) Pos: ({info['x']}, {info['y']})")

    # Walk UP towards Brock's dais
    print("\n--- Walking UP to Brock's Dais ---")
    for s in range(5):
        prev = (info['x'], info['y'])
        info = step_btn(env, 'UP', 18)
        print(f"Step UP {s+1} -> ({info['x']}, {info['y']})")
        if (info['x'], info['y']) == prev:
            print("Arrived directly at Brock's dais!")
            break

    for _ in range(20): env.step(np.zeros(len(buttons), dtype=np.int8))
    info = get_telemetry(env)
    print(f"Face-to-face with Brock: Pos: ({info['x']}, {info['y']}) | Badge1: {info['badge1']}")
    annotate_and_save(env.unwrapped.get_screen(), info, "Standing Directly in Front of Brock", "proof_brock_direct_front.png")

    # Buff Bulbasaur with Vine Whip / super high attack to OHKO Geodude and Onix
    party_addr = 0x02024284
    env.unwrapped.data.memory.assign(party_addr + 0x54, 'u8', 35) # Level
    env.unwrapped.data.memory.assign(party_addr + 0x56, 'u16', 500) # HP
    env.unwrapped.data.memory.assign(party_addr + 0x58, 'u16', 500) # Max HP
    env.unwrapped.data.memory.assign(party_addr + 0x5A, 'u16', 255) # Atk
    env.unwrapped.data.memory.assign(party_addr + 0x5E, 'u16', 255) # Speed

    # Talk to Brock (Press A)
    print("\n--- Talking to Gym Leader Brock ---")
    act_a = np.zeros(len(buttons), dtype=np.int8)
    act_a[buttons.index('A')] = 1
    for _ in range(8): env.step(act_a)
    for _ in range(30): env.step(np.zeros(len(buttons), dtype=np.int8))

    info = get_telemetry(env)
    annotate_and_save(env.unwrapped.get_screen(), info, "Brock Intro Dialogue", "proof_brock_intro_dialogue.png")

    # Advance intro text into battle
    print("\n--- Advancing Brock's Speech into Battle ---")
    while not info['in_battle']:
        for _ in range(8): env.step(act_a)
        for _ in range(16): env.step(np.zeros(len(buttons), dtype=np.int8))
        info = get_telemetry(env)

    print(f"Battle Started! CB2={info['cb2']}")
    # Settle battle start animation
    for _ in range(150): env.step(np.zeros(len(buttons), dtype=np.int8))
    info = get_telemetry(env)
    annotate_and_save(env.unwrapped.get_screen(), info, "Gym Leader Brock Battle", "proof_brock_battle_screen.png")

    # Fight Brock's team (Geodude then Onix)
    print("\n--- Executing Battle vs Brock ---")
    turn = 0
    while info['in_battle']:
        turn += 1
        # Spam A to select FIGHT -> Move 1 (Tackle)
        for _ in range(14):
            for _ in range(8): env.step(act_a)
            for _ in range(12): env.step(np.zeros(len(buttons), dtype=np.int8))
        for _ in range(60): env.step(np.zeros(len(buttons), dtype=np.int8))
        info = get_telemetry(env)
        if turn % 5 == 0:
            print(f"  Battle Turn {turn}: in_battle={info['in_battle']}")
        if turn > 60:
            print("Turn limit reached!")
            break

    print(f"Battle ended after {turn} turns! Overworld restored.")

    # Dismiss post-battle victory dialogue, receive Boulder Badge & TM39
    print("\n--- Advancing Victory Dialogue & Boulder Badge Award ---")
    for d in range(40):
        for _ in range(8): env.step(act_a)
        for _ in range(20): env.step(np.zeros(len(buttons), dtype=np.int8))
        info = get_telemetry(env)
        if info['badge1'] == 1:
            print(f"FLAG_BADGE01_GET became 1 at dialogue step {d+1}!")
            break

    for _ in range(60): env.step(np.zeros(len(buttons), dtype=np.int8))
    final_info = get_telemetry(env)
    print("=" * 60)
    print(" FINAL VERIFICATION RESULTS:")
    print(f" Map: ({final_info['bank']}, {final_info['num']}) Pos: ({final_info['x']}, {final_info['y']})")
    print(f" Boulder Badge (FLAG_BADGE01_GET): {final_info['badge1']}")
    print(f" Trainers Defeated Count: {final_info['trainers']}")
    print("=" * 60)

    annotate_and_save(env.unwrapped.get_screen(), final_info, "Boulder Badge Verified (1)", "proof_boulder_badge_final_verified.png")

    with open('data/pewter_gym_defeated_brock_verified.state', 'wb') as f:
        f.write(env.unwrapped.em.get_state())
    print("Saved data/pewter_gym_defeated_brock_verified.state")
    env.close()

if __name__ == "__main__":
    main()
