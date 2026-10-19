"""
BFS pathfinder through Pewter City to the Pewter Gym entrance Map (6, 2).
"""
import collections
from pathlib import Path
import json
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
    print("=" * 60)
    print(" NAVIGATING PEWTER CITY -> PEWTER GYM MAP (6, 2)")
    print("=" * 60)

    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()
    with open('data/pewter_city_verified.state', 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    # Dismiss banner
    buttons = env.unwrapped.buttons
    for _ in range(60):
        env.step(np.zeros(len(buttons), dtype=np.int8))

    start_info = get_telemetry(env)
    print(f"Start: Map ({start_info['bank']}, {start_info['num']}) at ({start_info['x']}, {start_info['y']})")

    # Queue: (state_bytes, (x, y), path)
    queue = collections.deque([(env.unwrapped.em.get_state(), (start_info['x'], start_info['y']), [])])
    visited = {(start_info['x'], start_info['y'])}

    actions = ['UP', 'LEFT', 'RIGHT', 'DOWN']
    found_path = None
    found_state = None
    final_info = None

    steps_explored = 0
    while queue:
        state_bytes, (cx, cy), path = queue.popleft()
        steps_explored += 1

        if steps_explored % 50 == 0:
            print(f"  [BFS] Explored {steps_explored} nodes | Current pos: ({cx}, {cy}) | Path len: {len(path)}")

        for act in actions:
            env.unwrapped.em.set_state(state_bytes)
            info = step_btn(env, act, 16)

            # Check if warp entered Pewter Gym Map (6, 2)
            if (info['bank'], info['num']) == (6, 2):
                print(f"\n[SUCCESS!] Entered Pewter Gym Map (6, 2) at ({info['x']}, {info['y']}) in {len(path)+1} steps!")
                found_path = path + [act]
                found_state = env.unwrapped.em.get_state()
                final_info = info
                queue.clear()
                break

            # If still in Pewter City and moved to an unvisited tile
            if (info['bank'], info['num']) == (3, 2):
                nx, ny = info['x'], info['y']
                if (nx, ny) != (cx, cy) and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((env.unwrapped.em.get_state(), (nx, ny), path + [act]))

    if found_path is not None:
        print(f"Path to Gym found: {len(found_path)} steps")
        print("Path:", found_path)
        with open(OUTPUT_DIR / "pewter_gym_path.json", "w") as f:
            json.dump(found_path, f)

        # Restore found state and settle
        env.unwrapped.em.set_state(found_state)
        for _ in range(30):
            env.step(np.zeros(len(buttons), dtype=np.int8))
        settled_info = get_telemetry(env)
        print("Settled Gym Telemetry:", settled_info)

        annotate_and_save(env.unwrapped.get_screen(), settled_info, "Pewter Gym Entrance", "proof_pewter_gym_interior_verified.png")
        with open('data/pewter_gym_interior_verified.state', 'wb') as f:
            f.write(env.unwrapped.em.get_state())
        print("Saved data/pewter_gym_interior_verified.state")
    else:
        print("No path found!")

    env.close()

if __name__ == "__main__":
    main()
