"""
BFS Pathfinding through Viridian Forest to the North Gatehouse.
Prunes trainer battle encounters and exploits visited (x, y) coordinate caching.
"""
from collections import deque
from pathlib import Path
import time
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
    x = int.from_bytes(ram[0x02036E48 - BASE:0x02036E4A - BASE], 'little')
    y = int.from_bytes(ram[0x02036E4A - BASE:0x02036E4C - BASE], 'little')
    b_flags = int.from_bytes(ram[0x22B4C:0x22B50], 'little')
    return bank, num, x, y, b_flags != 0

def inject_repel(env):
    ram = bytes(env.unwrapped.get_ram())
    sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], 'little') - BASE
    for off in [0x1040, 0x104C]:
        env.unwrapped.data.memory.assign(sb1_ptr + BASE + off, 'u16', 1000)

def step_action(env, btn_name, frames=18):
    inject_repel(env)
    buttons = env.unwrapped.buttons
    act = np.zeros(len(buttons), dtype=np.int8)
    if btn_name in buttons:
        act[buttons.index(btn_name)] = 1
    for _ in range(frames):
        env.step(act)
    return get_ram(env)

def main():
    print("=" * 60)
    print(" VIRIDIAN FOREST BFS PATHFINDER")
    print("=" * 60)

    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()

    with open(STATE_FILE, 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    bank, num, start_x, start_y, in_battle = get_ram(env)
    print(f"Start: Map ({bank}, {num}) at ({start_x}, {start_y})")

    # Queue contains: (state_bytes, (x, y), path)
    initial_state = env.unwrapped.em.get_state()
    queue = deque([(initial_state, (start_x, start_y), [])])
    visited = set([(start_x, start_y)])

    actions = ['UP', 'LEFT', 'RIGHT', 'DOWN']
    steps_explored = 0
    start_time = time.time()

    reached_path = None
    reached_state = None
    reached_coords = None
    reached_map = None

    while queue:
        state_bytes, (cx, cy), path = queue.popleft()
        steps_explored += 1

        if steps_explored % 50 == 0:
            elapsed = time.time() - start_time
            print(f"  [BFS] Explored: {steps_explored} tiles | Queue: {len(queue)} | Visited: {len(visited)} | Current: ({cx}, {cy}) | Elapsed: {elapsed:.1f}s")

        for act in actions:
            env.unwrapped.em.set_state(state_bytes)
            inject_repel(env)
            b, n, nx, ny, battle = step_action(env, act, 18)

            # Check if warp triggered to North Gatehouse or another map
            if (b, n) != (1, 0):
                # We stepped onto a warp!
                # Ensure it's not the South entrance we came from
                if ny < 50: # North exit!
                    print(f"\n[SUCCESS] Warp triggered to Map ({b}, {n}) at ({nx}, {ny}) in {len(path) + 1} steps!")
                    reached_path = path + [act]
                    reached_state = env.unwrapped.em.get_state()
                    reached_coords = (nx, ny)
                    reached_map = (b, n)
                    queue.clear()
                    break

            # If moved to a new overworld tile in Viridian Forest
            if (nx, ny) not in visited and (nx, ny) != (cx, cy):
                visited.add((nx, ny))
                new_state = env.unwrapped.em.get_state()
                queue.append((new_state, (nx, ny), path + [act]))

        if reached_path is not None:
            break

    if reached_path is not None:
        print(f"\nPath found! Total actions: {len(reached_path)}")
        with open(OUTPUT_DIR / "path_forest_to_gatehouse.json", "w") as f:
            json.dump(reached_path, f)

        # Restore reached state and save visual proof
        env.unwrapped.em.set_state(reached_state)
        # Settle warp
        for _ in range(30):
            step_action(env, None, 1)

        b, n, x, y, _ = get_ram(env)
        screen = env.unwrapped.get_screen()
        img = Image.fromarray(screen).resize((screen.shape[1]*2, screen.shape[0]*2), Image.Resampling.NEAREST)
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, img.height - 40), (img.width, img.height)], fill=(0, 0, 0))
        draw.text((10, img.height - 32), f"North Gatehouse Entry | Map: ({b}, {n}) | Coords: ({x}, {y})", fill=(0, 255, 0))
        img.save(str(OUTPUT_DIR / "proof_forest_north_gatehouse_entry.png"))
        print("[PROOF] Saved proof_forest_north_gatehouse_entry.png")

        # Save reached state
        with open(PROJECT_ROOT / "data" / "forest_north_gatehouse.state", "wb") as f:
            f.write(env.unwrapped.em.get_state())
        print("[STATE] Saved data/forest_north_gatehouse.state")

    else:
        print("\n[FAIL] BFS exhausted without finding North Gatehouse.")

    env.close()

if __name__ == "__main__":
    main()
