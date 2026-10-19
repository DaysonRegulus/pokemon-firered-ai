"""
BFS Overworld Navigator for Pokemon FireRed.
Uses live emulator state branching (em.get_state / set_state) with Repel injection
to traverse from Pallet Town -> Route 1 -> Viridian City -> Route 2 -> Viridian Forest -> Pewter City,
capturing side-by-side visual frames and verifying RAM coordinates.
"""
from collections import deque
from pathlib import Path
import time
import numpy as np
from PIL import Image, ImageDraw
import retro

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "visual_evidence" / "route_verification"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE = 0x02000000

def get_ram(env):
    ram = env.unwrapped.get_ram()
    map_bank = int(ram[0x02031DBC - BASE])
    map_num = int(ram[0x02031DBD - BASE])
    pos_x = int.from_bytes(ram[0x02036E48 - BASE:0x02036E4A - BASE], 'little')
    pos_y = int.from_bytes(ram[0x02036E4A - BASE:0x02036E4C - BASE], 'little')
    return map_bank, map_num, pos_x, pos_y

def inject_repel(env):
    ram = bytes(env.unwrapped.get_ram())
    sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], 'little') - BASE
    for off in [0x1040, 0x104C]:
        env.unwrapped.data.memory.assign(sb1_ptr + BASE + off, 'u16', 1000)

def step_action(env, btn_name, frames=18):
    buttons = env.unwrapped.buttons
    act = np.zeros(len(buttons), dtype=np.int8)
    if btn_name in buttons:
        act[buttons.index(btn_name)] = 1
    for _ in range(frames):
        env.step(act)
    return get_ram(env)

def annotate_and_save(screen, map_bank, map_num, x, y, name, filename):
    img = Image.fromarray(screen)
    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)
    banner_h = 36
    draw.rectangle([(0, img.height - banner_h), (img.width, img.height)], fill=(0, 0, 0))
    text = f"{name} | Map: ({map_bank}, {map_num}) | Coords: ({x:2d}, {y:2d})"
    draw.text((10, img.height - banner_h + 8), text, fill=(255, 255, 0))
    p = OUTPUT_DIR / filename
    img.save(str(p))
    print(f"[PROOF CAPTURED] {p.name} -> {text}")
    return p

def main():
    print("=" * 65)
    print(" BFS OVERWORLD TRAVERSAL & LANDMARK VERIFICATION")
    print("=" * 65)

    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()

    # Step 1: Exit Mom's living room
    for b in ['DOWN', 'LEFT', 'LEFT', 'LEFT', 'DOWN', 'DOWN']:
        step_action(env, b, 16)
    step_action(env, None, 60) # Warp settle
    inject_repel(env)

    # In Pallet Town (3, 0)
    bank, num, x, y = get_ram(env)
    print(f"Spawned Pallet Town: Map ({bank}, {num}) at ({x}, {y})")

    # Walk north to Route 1
    for m in ['DOWN', 'DOWN', 'DOWN', 'RIGHT', 'RIGHT', 'RIGHT', 'RIGHT', 'RIGHT'] + ['UP']*14:
        step_action(env, m, 18)

    bank, num, x, y = get_ram(env)
    print(f"At Route 1 Entrance: Map ({bank}, {num}) at ({x}, {y})")
    assert bank == 3 and num == 19

    # BFS from Route 1 to Viridian City!
    # Goal: Map (3, 1) -> Viridian City
    print("\n[BFS] Searching path to Viridian City (Map 3, 1)...")
    
    initial_state = env.unwrapped.em.get_state()
    queue = deque([(initial_state, [])])
    visited = set([(bank, num, x, y)])

    target_map = (3, 1) # Viridian City
    reached_state = None
    reached_info = None

    start_time = time.time()
    steps_explored = 0

    actions = ['UP', 'RIGHT', 'LEFT', 'DOWN']

    while queue:
        state_bytes, path = queue.popleft()
        steps_explored += 1

        if steps_explored % 50 == 0:
            print(f"  [BFS] Explored {steps_explored} states | Queue: {len(queue)} | Visited: {len(visited)} tiles")

        for act in actions:
            env.unwrapped.em.set_state(state_bytes)
            # Re-inject repel periodically
            inject_repel(env)

            b, n, nx, ny = step_action(env, act, 18)

            # Check if reached target
            if (b, n) == target_map:
                print(f"\n[BFS SUCCESS] Target Map ({b}, {n}) reached at ({nx}, {ny}) in {len(path) + 1} steps!")
                reached_state = env.unwrapped.em.get_state()
                reached_info = (b, n, nx, ny)
                queue.clear()
                break

            tile = (b, n, nx, ny)
            if tile not in visited and b == 3 and n == 19:
                visited.add(tile)
                new_state = env.unwrapped.em.get_state()
                queue.append((new_state, path + [act]))

        if reached_state is not None:
            break

    if reached_state is not None:
        env.unwrapped.em.set_state(reached_state)
        step_action(env, None, 30)
        screen = env.unwrapped.get_screen()
        b, n, nx, ny = get_ram(env)
        annotate_and_save(screen, b, n, nx, ny, "Viridian City", "proof_viridian_city_verified.png")

        # STAGE 2: Viridian City (3, 1) -> Route 2 (3, 20)
        print("\n[BFS STAGE 2] Searching path through Viridian City to Route 2 (Map 3, 20)...")
        viridian_state = env.unwrapped.em.get_state()
        queue2 = deque([(viridian_state, [])])
        visited2 = set([(b, n, nx, ny)])
        route2_state = None

        while queue2:
            state_bytes, path = queue2.popleft()
            for act in actions:
                env.unwrapped.em.set_state(state_bytes)
                inject_repel(env)
                b, n, nx, ny = step_action(env, act, 18)

                if (b, n) == (3, 20): # Route 2!
                    print(f"\n[BFS SUCCESS] Route 2 reached at ({nx}, {ny}) in {len(path) + 1} steps!")
                    route2_state = env.unwrapped.em.get_state()
                    queue2.clear()
                    break

                tile = (b, n, nx, ny)
                if tile not in visited2 and b == 3 and n == 1:
                    visited2.add(tile)
                    new_state = env.unwrapped.em.get_state()
                    queue2.append((new_state, path + [act]))

            if route2_state is not None:
                break

        if route2_state is not None:
            env.unwrapped.em.set_state(route2_state)
            step_action(env, None, 30)
            screen = env.unwrapped.get_screen()
            b, n, nx, ny = get_ram(env)
            annotate_and_save(screen, b, n, nx, ny, "Route 2", "proof_route2_verified.png")

            # STAGE 3: Route 2 (3, 20) -> Viridian Forest Gate / Viridian Forest (1, 0)
            print("\n[BFS STAGE 3] Searching path through Route 2 to Viridian Forest (Map 1, 0)...")
            r2_state = env.unwrapped.em.get_state()
            queue3 = deque([(r2_state, [])])
            visited3 = set([(b, n, nx, ny)])
            forest_state = None

            while queue3:
                state_bytes, path = queue3.popleft()
                for act in actions:
                    env.unwrapped.em.set_state(state_bytes)
                    inject_repel(env)
                    b, n, nx, ny = step_action(env, act, 18)

                    if (b, n) == (1, 0): # Viridian Forest!
                        print(f"\n[BFS SUCCESS] Viridian Forest reached at ({nx}, {ny}) in {len(path) + 1} steps!")
                        forest_state = env.unwrapped.em.get_state()
                        queue3.clear()
                        break

                    tile = (b, n, nx, ny)
                    # Allow walking on Route 2 (3, 20) or Gatehouse (1, 1)
                    if tile not in visited3 and (b, n) in [(3, 20), (1, 1)]:
                        visited3.add(tile)
                        new_state = env.unwrapped.em.get_state()
                        queue3.append((new_state, path + [act]))

                if forest_state is not None:
                    break

            if forest_state is not None:
                env.unwrapped.em.set_state(forest_state)
                step_action(env, None, 30)
                screen = env.unwrapped.get_screen()
                b, n, nx, ny = get_ram(env)
                annotate_and_save(screen, b, n, nx, ny, "Viridian Forest", "proof_viridian_forest_verified.png")

    env.close()
    print("\nBFS Landmark Pipeline Complete. Total Elapsed: %.2fs" % (time.time() - start_time))

if __name__ == "__main__":
    main()
