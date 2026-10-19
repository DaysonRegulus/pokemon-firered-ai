"""
Navigate from BeginningPalletGotPokeballs out of the house and directly onto Route 1.
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

    # 1. Exit Living Room: Walk LEFT to door mat at (11, 15) then DOWN
    # Spawn is (14, 14)
    press("LEFT", 48)  # 3 tiles left -> (11, 14)
    press("DOWN", 32)  # 2 tiles down onto mat -> (11, 15) -> Warps to outside!

    ram = env.unwrapped.get_ram()
    BASE = 0x02000000
    map_bank = int(ram[0x02031DBC - BASE])
    map_num = int(ram[0x02031DBD - BASE])
    pos_x = int.from_bytes(ram[0x02036E48 - BASE:0x02036E4A - BASE], "little")
    pos_y = int.from_bytes(ram[0x02036E4A - BASE:0x02036E4C - BASE], "little")
    print(f"Step 1 (Outside Porch): Map ({map_bank}, {map_num}) Pos: ({pos_x}, {pos_y})")

    # 2. Walk East towards path: (10, 6) -> (20, 6)
    for _ in range(10):
        press("RIGHT", 16)

    # 3. Walk North onto Route 1!
    for step in range(25):
        press("UP", 16)
        press("A", 4)  # mash A to bypass any text

    ram = env.unwrapped.get_ram()
    map_bank = int(ram[0x02031DBC - BASE])
    map_num = int(ram[0x02031DBD - BASE])
    pos_x = int.from_bytes(ram[0x02036E48 - BASE:0x02036E4A - BASE], "little")
    pos_y = int.from_bytes(ram[0x02036E4A - BASE:0x02036E4C - BASE], "little")
    print(f"Step 2 (Route 1 Entrance): Map ({map_bank}, {map_num}) Pos: ({pos_x}, {pos_y})")

    img = Image.fromarray(env.unwrapped.get_screen())
    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, img.height - 40), (img.width, img.height)], fill=(0, 0, 0))
    draw.text((8, img.height - 35), f"Map ({map_bank}, {map_num}) | Pos: ({pos_x}, {pos_y})", fill=(255, 255, 0))

    out_file = OUTPUT_DIR / f"route1_entry_map_{map_bank}_{map_num}_x{pos_x}_y{pos_y}.png"
    img.save(str(out_file))
    print(f"Saved: {out_file.name}")

    # 4. Walk further North along Route 1 towards Viridian City
    for _ in range(50):
        press("UP", 16)
        press("A", 4)

    ram = env.unwrapped.get_ram()
    map_bank = int(ram[0x02031DBC - BASE])
    map_num = int(ram[0x02031DBD - BASE])
    pos_x = int.from_bytes(ram[0x02036E48 - BASE:0x02036E4A - BASE], "little")
    pos_y = int.from_bytes(ram[0x02036E4A - BASE:0x02036E4C - BASE], "little")
    print(f"Step 3 (North Route 1): Map ({map_bank}, {map_num}) Pos: ({pos_x}, {pos_y})")

    img2 = Image.fromarray(env.unwrapped.get_screen())
    img2 = img2.resize((img2.width * 2, img2.height * 2), Image.Resampling.NEAREST)
    draw2 = ImageDraw.Draw(img2)
    draw2.rectangle([(0, img2.height - 40), (img2.width, img2.height)], fill=(0, 0, 0))
    draw2.text((8, img2.height - 35), f"Map ({map_bank}, {map_num}) | Pos: ({pos_x}, {pos_y})", fill=(255, 255, 0))

    out_file2 = OUTPUT_DIR / f"route1_north_map_{map_bank}_{map_num}_x{pos_x}_y{pos_y}.png"
    img2.save(str(out_file2))
    print(f"Saved: {out_file2.name}")

    env.close()


if __name__ == "__main__":
    main()
