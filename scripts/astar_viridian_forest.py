"""
A* / Best-First Overworld Navigator through Viridian Forest.
Uses Manhattan distance heuristic to (5, 9) and priority queue to find the exit in seconds.
"""
import heapq
import json
from pathlib import Path
import time
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
    return bank, num, x, y

def inject_repel(env):
    ram = bytes(env.unwrapped.get_ram())
    sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], 'little') - BASE
    for off in [0x1040, 0x104C]:
        env.unwrapped.data.memory.assign(sb1_ptr + BASE + off, 'u16', 1000)

def step_action(env, btn_name, frames=16):
    inject_repel(env)
    buttons = env.unwrapped.buttons
    act = np.zeros(len(buttons), dtype=np.int8)
    if btn_name in buttons:
        act[buttons.index(btn_name)] = 1
    for _ in range(frames):
        env.step(act)
    return get_ram(env)

def heuristic(x, y, tx=5, ty=9):
    return abs(x - tx) + abs(y - ty)

def main():
    print("=" * 60)
    print(" A* PATHFINDING: VIRIDIAN FOREST -> NORTH GATEHOUSE")
    print("=" * 60)

    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()
    with open(STATE_FILE, 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    bank, num, sx, sy = get_ram(env)
    print(f"Spawn: Map ({bank}, {num}) at ({sx}, {sy})")

    # Priority queue: (f_score, tie_breaker, g_score, state_bytes, (x, y), path)
    counter = 0
    h0 = heuristic(sx, sy)
    pq = [(h0, counter, 0, env.unwrapped.em.get_state(), (sx, sy), [])]
    visited = {(sx, sy): 0}

    actions = ['UP', 'LEFT', 'RIGHT', 'DOWN']
    start_time = time.time()
    nodes_explored = 0

    reached_path = None
    reached_state = None
    reached_coords = None
    reached_map = None

    while pq:
        f_score, _, g, state_bytes, (cx, cy), path = heapq.heappop(pq)
        nodes_explored += 1

        if nodes_explored % 25 == 0:
            elapsed = time.time() - start_time
            print(f"  [A*] Nodes: {nodes_explored:4d} | Pos: ({cx:2d}, {cy:2d}) | Path Len: {len(path):3d} | Dist to Exit: {heuristic(cx, cy):2d} | Elapsed: {elapsed:.1f}s")

        # Try actions
        for act in actions:
            env.unwrapped.em.set_state(state_bytes)
            b, n, nx, ny = step_action(env, act, 16)

            # Check if map transitioned (warp stepped)
            if (b, n) != (1, 0):
                if ny < 50: # North exit gatehouse!
                    print(f"\n[A* SUCCESS] North Gatehouse reached! Map ({b}, {n}) at ({nx}, {ny}) in {len(path)+1} steps!")
                    reached_path = path + [act]
                    reached_state = env.unwrapped.em.get_state()
                    reached_coords = (nx, ny)
                    reached_map = (b, n)
                    pq.clear()
                    break

            # If valid movement
            if (nx, ny) != (cx, cy):
                new_g = g + 1
                if (nx, ny) not in visited or new_g < visited[(nx, ny)]:
                    visited[(nx, ny)] = new_g
                    counter += 1
                    h = heuristic(nx, ny)
                    # Priority is f = g + 2 * h (greedy search bias towards goal)
                    new_state = env.unwrapped.em.get_state()
                    heapq.heappush(pq, (new_g + 2 * h, counter, new_g, new_state, (nx, ny), path + [act]))

        if reached_path is not None:
            break

    if reached_path is not None:
        total_time = time.time() - start_time
        print(f"\nTraversal Complete in {total_time:.2f}s! Steps: {len(reached_path)}")
        with open(OUTPUT_DIR / "path_forest_to_north_gatehouse.json", "w") as f:
            json.dump(reached_path, f)

        # Restore reached state
        env.unwrapped.em.set_state(reached_state)
        # Settle 30 frames
        for _ in range(30):
            step_action(env, None, 1)

        b, n, x, y = get_ram(env)
        screen = env.unwrapped.get_screen()
        img = Image.fromarray(screen).resize((screen.shape[1]*2, screen.shape[0]*2), Image.Resampling.NEAREST)
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, img.height - 40), (img.width, img.height)], fill=(0, 0, 0))
        draw.text((10, img.height - 32), f"Viridian Forest North Gatehouse | Map: ({b}, {n}) | Coords: ({x}, {y})", fill=(0, 255, 255))
        img.save(str(OUTPUT_DIR / "proof_viridian_forest_north_gatehouse.png"))
        print("[PROOF] Saved proof_viridian_forest_north_gatehouse.png")

        # Save checkpoint state for North Gatehouse
        with open(PROJECT_ROOT / "data" / "forest_north_gatehouse.state", "wb") as f:
            f.write(env.unwrapped.em.get_state())
        print("[CHECKPOINT] Saved data/forest_north_gatehouse.state")

    else:
        print("\n[A* FAILED] Priority queue exhausted.")

    env.close()

if __name__ == "__main__":
    main()
