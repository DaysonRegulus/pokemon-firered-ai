"""
Tests dismissing the Viridian Forest splash screen and inspecting the live overworld.
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import retro

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "visual_evidence" / "route_verification"
STATE_FILE = PROJECT_ROOT / "data" / "forest_checkpoint.state"

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

def main():
    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()

    with open(STATE_FILE, 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    buttons = env.unwrapped.buttons
    act_a = np.zeros(len(buttons), dtype=np.int8); act_a[buttons.index('A')] = 1
    act_idle = np.zeros(len(buttons), dtype=np.int8)

    # Press A to dismiss banner
    for _ in range(16): env.step(act_a)
    for _ in range(60): env.step(act_idle)

    bank, num, x, y, in_battle = get_ram(env)
    print(f"Overworld ready: Map ({bank}, {num}) at ({x}, {y}) | battle: {in_battle}")

    screen = env.unwrapped.get_screen()
    img = Image.fromarray(screen).resize((screen.shape[1]*2, screen.shape[0]*2), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, img.height - 40), (img.width, img.height)], fill=(0, 0, 0))
    draw.text((10, img.height - 32), f"Viridian Forest Floor | Map: ({bank}, {num}) | Coords: ({x}, {y})", fill=(0, 255, 255))
    img.save(str(OUTPUT_DIR / "proof_forest_floor_active.png"))
    print("Saved proof_forest_floor_active.png")

    # Update state file so it starts directly with banner dismissed!
    clean_state = env.unwrapped.em.get_state()
    with open(STATE_FILE, 'wb') as f:
        f.write(clean_state)
    print("Updated forest_checkpoint.state with dismissed banner!")
    env.close()

if __name__ == "__main__":
    main()
