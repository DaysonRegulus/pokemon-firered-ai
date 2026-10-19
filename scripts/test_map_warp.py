"""
Test Map Warping in GBA RAM:
Attempts to set location.mapGroup and location.mapNum in SaveBlock1,
triggers overworld warp/reload, and checks if Viridian Forest,
Viridian City, and Pewter City can be rendered and verified.
"""
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw
import retro

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pokefirered.env_factory import register_custom_integrations

OUTPUT_DIR = PROJECT_ROOT / "visual_evidence" / "map_verification"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_warp(env, target_bank, target_map, target_x, target_y, label):
    ram = env.unwrapped.get_ram()
    BASE = 0x02000000

    sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], "little") - BASE
    
    # Set pos in SaveBlock1
    ram[sb1_ptr] = target_x & 0xFF
    ram[sb1_ptr + 1] = (target_x >> 8) & 0xFF
    ram[sb1_ptr + 2] = target_y & 0xFF
    ram[sb1_ptr + 3] = (target_y >> 8) & 0xFF
    
    # Set location warp: offset 4 is group, offset 5 is map
    ram[sb1_ptr + 4] = target_bank
    ram[sb1_ptr + 5] = target_map
    ram[sb1_ptr + 6] = 0xFF  # warpId
    ram[sb1_ptr + 8] = target_x & 0xFF
    ram[sb1_ptr + 9] = (target_x >> 8) & 0xFF
    ram[sb1_ptr + 10] = target_y & 0xFF
    ram[sb1_ptr + 11] = (target_y >> 8) & 0xFF

    # Also set continueGameWarp and dynamicWarp
    for off in [12, 20, 28]:
        ram[sb1_ptr + off] = target_bank
        ram[sb1_ptr + off + 1] = target_map
        ram[sb1_ptr + off + 2] = 0xFF
        ram[sb1_ptr + off + 4] = target_x & 0xFF
        ram[sb1_ptr + off + 5] = (target_x >> 8) & 0xFF
        ram[sb1_ptr + off + 6] = target_y & 0xFF
        ram[sb1_ptr + off + 7] = (target_y >> 8) & 0xFF

    # Also test setting sCurrentMap directly
    ram[0x02031DBC - BASE] = target_bank
    ram[0x02031DBD - BASE] = target_map

    # Step environment for 16 frames with empty action to allow engine to reload
    buttons = env.unwrapped.buttons
    act = np.zeros(len(buttons), dtype=np.int8)
    for _ in range(16):
        env.step(act)

    cur_bank = int(ram[0x02031DBC - BASE])
    cur_map = int(ram[0x02031DBD - BASE])
    cur_x = int.from_bytes(ram[0x02036E48 - BASE:0x02036E4A - BASE], "little")
    cur_y = int.from_bytes(ram[0x02036E4A - BASE:0x02036E4C - BASE], "little")

    screen = env.unwrapped.get_screen()
    img = Image.fromarray(screen)
    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, img.height - 42), (img.width, img.height)], fill=(0, 0, 0))
    draw.text((8, img.height - 38), f"Target: {label} ({target_bank}, {target_map})", fill=(255, 255, 0))
    draw.text((8, img.height - 18), f"Actual RAM: Map ({cur_bank}, {cur_map}) Pos: ({cur_x}, {cur_y})", fill=(100, 255, 255))

    out_path = OUTPUT_DIR / f"warp_test_{label.replace(' ', '_')}.png"
    img.save(str(out_path))
    print(f"[{label}] Target: ({target_bank}, {target_map}) -> RAM Reads: Map ({cur_bank}, {cur_map}) Pos: ({cur_x}, {cur_y}) -> Saved: {out_path.name}")
    return cur_bank, cur_map


def main():
    register_custom_integrations()
    env = retro.make(
        game="PokemonFireRed-GBA",
        state="BeginningPallet",
        inttype=retro.data.Integrations.ALL,
    )
    env.reset()
    buttons = env.unwrapped.buttons
    env.step(np.zeros(len(buttons), dtype=np.int8))

    targets = [
        (3, 19, 10, 20, "Route 1"),
        (3, 1, 15, 15, "Viridian City"),
        (3, 20, 10, 20, "Route 2"),
        (1, 0, 15, 20, "Viridian Forest"),
        (3, 2, 15, 15, "Pewter City"),
    ]

    for bank, map_num, x, y, label in targets:
        test_warp(env, bank, map_num, x, y, label)

    env.close()


if __name__ == "__main__":
    main()
