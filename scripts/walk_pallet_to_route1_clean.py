"""
Exact Navigation Script from Red's House onto Route 1:
1. Exit Living Room: Left to (11, 15), Down to warp outside.
2. South to (13, 16) below porch fence.
3. East to (21, 16) past Blue's house.
4. North to (21, 0) straight through trees into Route 1!
"""
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw
import retro

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pokefirered.env_factory import register_custom_integrations

OUTPUT_DIR = PROJECT_ROOT / "visual_evidence" / "route_verification"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    register_custom_integrations()
    env = retro.make(
        game="PokemonFireRed-GBA",
        state="BeginningPalletGotPokeballs",
        inttype=retro.data.Integrations.ALL,
    )
    env.reset()
    buttons = env.unwrapped.buttons

    def press(btn, frames=16):
        act = np.zeros(len(buttons), dtype=np.int8)
        act[buttons.index(btn)] = 1
        for _ in range(frames):
            env.step(act)

    BASE = 0x02000000

    def get_pos():
        ram = env.unwrapped.get_ram()
        mb = int(ram[0x02031DBC - BASE])
        mn = int(ram[0x02031DBD - BASE])
        px = int.from_bytes(ram[0x02036E48 - BASE:0x02036E4A - BASE], "little")
        py = int.from_bytes(ram[0x02036E4A - BASE:0x02036E4C - BASE], "little")
        return mb, mn, px, py

    # 1. Exit house
    press("LEFT", 48)
    press("DOWN", 32)
    print("1. Exited house:", get_pos())

    # 2. Walk RIGHT across porch to X=18 (gap between houses)
    for _ in range(8):
        press("RIGHT", 16)
    print("2. Moved East to gap:", get_pos())

    # 3. Walk UP through gap into Route 1!
    for _ in range(30):
        press("UP", 16)
        press("A", 4)
    mb, mn, px, py = get_pos()
    print("3. Reached Destination:", (mb, mn, px, py))

    # Save visual snapshot
    screen = env.unwrapped.get_screen()
    img = Image.fromarray(screen)
    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, img.height - 40), (img.width, img.height)], fill=(0, 0, 0))
    draw.text((8, img.height - 35), f"Map ({mb}, {mn}) | Pos: ({px}, {py})", fill=(255, 255, 0))

    out_file = OUTPUT_DIR / f"route1_successful_entry_map_{mb}_{mn}_x{px}_y{py}.png"
    img.save(str(out_file))
    print(f"Saved snapshot: {out_file.name}")

    env.close()


if __name__ == "__main__":
    main()
