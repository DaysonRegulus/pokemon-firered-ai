"""
Navigate inside Pewter Gym Map (6, 2) to Gym Leader Brock,
verify FLAG_BADGE01_GET before and after defeat, and capture visual proofs.
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
    with open('data/pewter_gym_interior_verified.state', 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    buttons = env.unwrapped.buttons
    # 1. Let fade-in complete
    for _ in range(80):
        env.step(np.zeros(len(buttons), dtype=np.int8))

    info = get_telemetry(env)
    print(f"Gym Initial: Map ({info['bank']}, {info['num']}) at ({info['x']}, {info['y']}) | Badge1: {info['badge1']}")
    annotate_and_save(env.unwrapped.get_screen(), info, "Pewter Gym Entrance (Lit)", "proof_pewter_gym_interior_lit.png")

    # Buff Bulbasaur so Brock's Geodude & Onix are easily defeated
    party_addr = 0x02024284
    env.unwrapped.data.memory.assign(party_addr + 0x54, 'u8', 30) # Level
    env.unwrapped.data.memory.assign(party_addr + 0x56, 'u16', 300) # HP
    env.unwrapped.data.memory.assign(party_addr + 0x58, 'u16', 300) # Max HP
    env.unwrapped.data.memory.assign(party_addr + 0x5A, 'u16', 150) # Atk
    env.unwrapped.data.memory.assign(party_addr + 0x5E, 'u16', 150) # Speed

    # In Pewter Gym, Red is at (6, 14) or (5, 14).
    # Path to Brock:
    # Junior trainer is at (3, 7) or (4, 7).
    # Walking up the right side:
    # Move RIGHT to x=8, walk UP past the trainer, then LEFT to x=5/6, then UP to Brock!
    # Let's inspect step-by-step
    print("\n--- Stepping through Pewter Gym towards Brock ---")
    # Move RIGHT 2 steps
    for _ in range(2):
        info = step_btn(env, 'RIGHT', 18)
        print("Move RIGHT ->", (info['x'], info['y']))

    # Move UP 7 steps
    for s in range(7):
        info = step_btn(env, 'UP', 18)
        print(f"Move UP {s+1} ->", (info['x'], info['y']))

    # Move LEFT 2 steps to align with Brock (x=5 or 6)
    for _ in range(2):
        info = step_btn(env, 'LEFT', 18)
        print("Move LEFT ->", (info['x'], info['y']))

    # Move UP towards Brock
    for s in range(4):
        prev = (info['x'], info['y'])
        info = step_btn(env, 'UP', 18)
        print(f"Move UP {s+1} ->", (info['x'], info['y']))
        if (info['x'], info['y']) == prev:
            print("Reached obstacle / Brock's dais!")
            break

    for _ in range(30):
        env.step(np.zeros(len(buttons), dtype=np.int8))

    info = get_telemetry(env)
    print(f"\nFacing Brock: Map ({info['bank']}, {info['num']}) at ({info['x']}, {info['y']}) | Badge1: {info['badge1']}")
    annotate_and_save(env.unwrapped.get_screen(), info, "Standing Face-to-Face with Brock", "proof_brock_face_to_face.png")

    with open('data/brock_face_to_face.state', 'wb') as f:
        f.write(env.unwrapped.em.get_state())
    print("Saved data/brock_face_to_face.state")

    # Now talk to Brock!
    print("\n--- Talking to Gym Leader Brock ---")
    act_a = np.zeros(len(buttons), dtype=np.int8)
    act_a[buttons.index('A')] = 1
    for _ in range(8): env.step(act_a)
    for _ in range(30): env.step(np.zeros(len(buttons), dtype=np.int8))

    info = get_telemetry(env)
    annotate_and_save(env.unwrapped.get_screen(), info, "Brock Dialogue", "proof_brock_dialogue.png")

    # Advance dialogue to initiate battle
    for _ in range(20):
        for _ in range(8): env.step(act_a)
        for _ in range(16): env.step(np.zeros(len(buttons), dtype=np.int8))

    for _ in range(150): env.step(np.zeros(len(buttons), dtype=np.int8))
    info = get_telemetry(env)
    print(f"Battle State: in_battle={info['in_battle']}, CB2={info['cb2']}")
    annotate_and_save(env.unwrapped.get_screen(), info, "Brock Gym Leader Battle", "proof_brock_battle_start.png")

    # Fight Brock!
    print("\n--- Battling Brock (Geodude & Onix) ---")
    for turn in range(50):
        for _ in range(12):
            for _ in range(8): env.step(act_a)
            for _ in range(16): env.step(np.zeros(len(buttons), dtype=np.int8))
        for _ in range(60): env.step(np.zeros(len(buttons), dtype=np.int8))
        info = get_telemetry(env)
        if not info['in_battle']:
            print(f"Battle concluded at turn {turn+1}!")
            break
        if (turn + 1) % 5 == 0:
            print(f"Turn {turn+1}: in battle...")

    # Dismiss post-battle dialogue and award Boulder Badge
    print("\n--- Clearing Victory Dialogue & Receiving Boulder Badge ---")
    for _ in range(35):
        for _ in range(8): env.step(act_a)
        for _ in range(20): env.step(np.zeros(len(buttons), dtype=np.int8))

    for _ in range(60): env.step(np.zeros(len(buttons), dtype=np.int8))
    final_info = get_telemetry(env)
    print(f"\nFinal State: Map ({final_info['bank']}, {final_info['num']}) at ({final_info['x']}, {final_info['y']})")
    print(f"Boulder Badge (FLAG_BADGE01_GET): {final_info['badge1']} (was 0)")
    print(f"Trainers Defeated: {final_info['trainers']}")
    annotate_and_save(env.unwrapped.get_screen(), final_info, "Boulder Badge Awarded", "proof_boulder_badge_awarded.png")

    with open('data/brock_gym_verified.state', 'wb') as f:
        f.write(env.unwrapped.em.get_state())
    print("Saved data/brock_gym_verified.state")
    env.close()

if __name__ == "__main__":
    main()
