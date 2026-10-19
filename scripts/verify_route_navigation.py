"""
Navigator and RAM Discovery Verification:
Step from Pallet Town into Route 1, capturing side-by-side visual frames
and reading real-time RAM map codes and coordinates.
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


def get_telemetry(ram):
    BASE = 0x02000000
    map_bank = int(ram[0x02031DBC - BASE])
    map_num = int(ram[0x02031DBD - BASE])
    pos_x = int.from_bytes(ram[0x02036E48 - BASE:0x02036E4A - BASE], byteorder="little")
    pos_y = int.from_bytes(ram[0x02036E4A - BASE:0x02036E4C - BASE], byteorder="little")
    
    # SaveBlock pointers
    sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], byteorder="little")
    sb2_ptr = int.from_bytes(ram[0x4500C:0x45010], byteorder="little")
    return {
        "map_bank": map_bank,
        "map_num": map_num,
        "pos_x": pos_x,
        "pos_y": pos_y,
        "sb1_ptr": hex(sb1_ptr),
        "sb2_ptr": hex(sb2_ptr),
    }


def save_annotated(screen_np, info, label, filename):
    img = Image.fromarray(screen_np)
    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)
    banner_h = 50
    draw.rectangle([(0, img.height - banner_h), (img.width, img.height)], fill=(0, 0, 0))
    line1 = f"{label} | Map ({info['map_bank']}, {info['map_num']}) Pos: ({info['pos_x']}, {info['pos_y']})"
    line2 = f"SB1: {info['sb1_ptr']} | SB2: {info['sb2_ptr']}"
    draw.text((8, img.height - banner_h + 4), line1, fill=(255, 255, 0))
    draw.text((8, img.height - banner_h + 26), line2, fill=(100, 255, 255))
    out_path = OUTPUT_DIR / filename
    img.save(str(out_path))
    print(f"Saved: {out_path.name} | {line1}")
    return out_path


def main():
    register_custom_integrations()
    env = retro.make(
        game="PokemonFireRed-GBA",
        state="BeginningPallet",
        inttype=retro.data.Integrations.ALL,
    )
    env.reset()
    buttons = env.unwrapped.buttons

    def step_action(btn_name, frames=8):
        act = np.zeros(len(buttons), dtype=np.int8)
        if btn_name in buttons:
            act[buttons.index(btn_name)] = 1
        for _ in range(frames):
            env.step(act)

    # Initialize RAM
    env.step(np.zeros(len(buttons), dtype=np.int8))
    ram = env.unwrapped.get_ram()
    info = get_telemetry(ram)
    save_annotated(env.unwrapped.get_screen(), info, "Spawn Pallet Town", "01_pallet_town_spawn.png")

    # Navigate North towards Route 1
    # Move West to path, then North
    for _ in range(8):
        step_action("LEFT", frames=8)
    for _ in range(16):
        step_action("UP", frames=8)

    ram = env.unwrapped.get_ram()
    info = get_telemetry(ram)
    save_annotated(env.unwrapped.get_screen(), info, "Pallet Town North Exit", "02_pallet_town_north_exit.png")

    # Continue stepping North onto Route 1
    for _ in range(20):
        step_action("UP", frames=8)

    ram = env.unwrapped.get_ram()
    info = get_telemetry(ram)
    save_annotated(env.unwrapped.get_screen(), info, "Route 1 Entry", "03_route1_entry.png")

    # Walk further North in Route 1
    for _ in range(30):
        step_action("UP", frames=8)
        # Mash A in case of text / wild encounter
        step_action("A", frames=4)

    ram = env.unwrapped.get_ram()
    info = get_telemetry(ram)
    save_annotated(env.unwrapped.get_screen(), info, "Route 1 Navigation", "04_route1_navigation.png")

    env.close()


if __name__ == "__main__":
    main()
