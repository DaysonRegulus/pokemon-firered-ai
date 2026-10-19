"""
Walk directly up the Pallet Town exit path at X=21 and verify Route 1 transition.
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
        state="BeginningPallet",
        inttype=retro.data.Integrations.ALL,
    )
    env.reset()
    buttons = env.unwrapped.buttons

    def press(btn, frames=16):
        act = np.zeros(len(buttons), dtype=np.int8)
        act[buttons.index(btn)] = 1
        for _ in range(frames):
            env.step(act)

    # 1. Walk UP from (18, 17) to (18, 11)
    for _ in range(6):
        press("UP", 16)

    # 2. Walk RIGHT to align with the open path at X=21
    for _ in range(3):
        press("RIGHT", 16)

    # 3. Walk straight UP through the path into the tall grass at the top of Pallet Town
    for step in range(25):
        press("UP", 16)
        press("A", 4)  # Mash A in case of text box or encounter

    ram = env.unwrapped.get_ram()
    BASE = 0x02000000
    map_bank = int(ram[0x02031DBC - BASE])
    map_num = int(ram[0x02031DBD - BASE])
    pos_x = int.from_bytes(ram[0x02036E48 - BASE:0x02036E4A - BASE], "little")
    pos_y = int.from_bytes(ram[0x02036E4A - BASE:0x02036E4C - BASE], "little")

    print(f"Final Destination: Map ({map_bank}, {map_num}) | Pos: ({pos_x}, {pos_y})")

    img = Image.fromarray(env.unwrapped.get_screen())
    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, img.height - 40), (img.width, img.height)], fill=(0, 0, 0))
    draw.text((8, img.height - 35), f"Map ({map_bank}, {map_num}) | Pos: ({pos_x}, {pos_y})", fill=(255, 255, 0))

    out_file = OUTPUT_DIR / f"route1_path_x{pos_x}_y{pos_y}.png"
    img.save(str(out_file))
    print(f"Saved: {out_file.name}")

    env.close()


if __name__ == "__main__":
    main()
