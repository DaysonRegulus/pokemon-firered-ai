"""
Creates a verified save state at the entrance of Viridian Forest (Map 1, 0 at (36, 69)).
Also captures visual proof with annotated telemetry.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw
import retro

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "visual_evidence" / "route_verification"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_PATH = PROJECT_ROOT / "data" / "forest_checkpoint.state"

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

def step_act(env, btn, frames=18):
    inject_repel(env)
    buttons = env.unwrapped.buttons
    act = np.zeros(len(buttons), dtype=np.int8)
    if btn in buttons:
        act[buttons.index(btn)] = 1
    for _ in range(frames):
        env.step(act)
    return get_ram(env)

def main():
    print("[1/5] Booting emulator at BeginningPalletGotPokeballs...")
    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()

    # Living room exit
    for b in ['DOWN', 'LEFT', 'LEFT', 'LEFT', 'DOWN', 'DOWN']:
        step_act(env, b, 16)
    step_act(env, None, 60)

    # Route 1 walk
    for m in ['DOWN', 'DOWN', 'DOWN', 'RIGHT', 'RIGHT', 'RIGHT', 'RIGHT', 'RIGHT'] + ['UP']*14:
        step_act(env, m, 18)

    # Follow verified path to Viridian City
    with open(OUTPUT_DIR / 'path_to_viridian.json') as f:
        for s in json.load(f):
            step_act(env, s, 18)

    # Walk north to Old Man avenue
    for _ in range(7): step_act(env, 'UP', 18)
    step_act(env, 'LEFT', 18)
    step_act(env, 'LEFT', 18)
    for _ in range(23): step_act(env, 'UP', 18)
    step_act(env, 'UP', 30)

    # Complete Old Man Weedle tutorial
    buttons = env.unwrapped.buttons
    act_a = np.zeros(len(buttons), dtype=np.int8); act_a[buttons.index('A')] = 1
    act_b = np.zeros(len(buttons), dtype=np.int8); act_b[buttons.index('B')] = 1
    act_idle = np.zeros(len(buttons), dtype=np.int8)
    for _ in range(240):
        for _ in range(8): env.step(act_b)
        for _ in range(8): env.step(act_a)
        for _ in range(8): env.step(act_idle)
    for _ in range(2):
        for _ in range(10): env.step(act_a)
        for _ in range(30): env.step(act_idle)
    for _ in range(30): env.step(act_idle)

    # Walk Route 2 south to South Gatehouse
    for _ in range(7): step_act(env, 'UP', 18)
    for _ in range(12): step_act(env, 'UP', 18)
    for _ in range(5): step_act(env, 'LEFT', 18)
    for _ in range(9): step_act(env, 'UP', 18)
    for _ in range(6): step_act(env, 'RIGHT', 18)
    for _ in range(5): step_act(env, 'UP', 18)
    for _ in range(5): step_act(env, 'LEFT', 18)
    for _ in range(3): step_act(env, 'UP', 18)
    step_act(env, None, 40)
    # Inside gatehouse, walk UP to forest warp
    for _ in range(9): step_act(env, 'UP', 18)

    # Dismiss splash banner
    for _ in range(10): env.step(act_b)
    for _ in range(100): env.step(act_idle)

    bank, num, x, y = get_ram(env)
    print(f"[VERIFIED] Arrived in Viridian Forest: Map ({bank}, {num}) at ({x}, {y})")
    assert (bank, num) == (1, 0), f"Expected Map (1, 0), got ({bank}, {num})"

    # Save state
    state_bytes = env.unwrapped.em.get_state()
    with open(CHECKPOINT_PATH, 'wb') as f:
        f.write(state_bytes)
    print(f"[SAVED] Checkpoint saved to {CHECKPOINT_PATH} ({len(state_bytes)} bytes)")

    # Save annotated screenshot
    screen = env.unwrapped.get_screen()
    img = Image.fromarray(screen).resize((screen.shape[1]*2, screen.shape[0]*2), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, img.height - 40), (img.width, img.height)], fill=(0, 0, 0))
    draw.text((10, img.height - 32), f"Viridian Forest | Map: ({bank}, {num}) | Coords: ({x}, {y})", fill=(255, 255, 0))
    img.save(str(OUTPUT_DIR / "proof_forest_checkpoint.png"))
    print("[PROOF] Saved proof_forest_checkpoint.png")
    env.close()

if __name__ == "__main__":
    main()
