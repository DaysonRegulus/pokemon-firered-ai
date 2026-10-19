"""
Test and verify map bank, map numbers, and event flags in GBA RAM.
Explores whether warp parameters in SaveBlock1 or overworld engine
can load Viridian City (3, 1), Viridian Forest (1, 0), and Pewter City (3, 2).
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

    # Initialize RAM
    env.step(np.zeros(len(buttons), dtype=np.int8))
    ram = env.unwrapped.get_ram()
    BASE = 0x02000000

    sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], "little") - BASE
    print(f"SaveBlock1 Base: {hex(sb1_ptr)}")

    # Print first 32 bytes of SaveBlock1 (pos + warp structures)
    header_bytes = [hex(x) for x in ram[sb1_ptr:sb1_ptr + 32]]
    print("SaveBlock1 Header:", header_bytes)

    # Let's inspect warp structure offsets:
    # Offset 0: pos (x, y, height) -> 6 bytes
    # Offset 6: location (group, mapNum, warpId, x, y) -> 8 bytes
    # Offset 14: continueGameWarp
    print(f"Current pos: ({int.from_bytes(ram[sb1_ptr:sb1_ptr+2], 'little')}, {int.from_bytes(ram[sb1_ptr+2:sb1_ptr+4], 'little')})")
    print(f"Location warp: group={ram[sb1_ptr+4]}, map={ram[sb1_ptr+5]}, warpId={ram[sb1_ptr+6]}")
    print(f"ContinueGameWarp: group={ram[sb1_ptr+12]}, map={ram[sb1_ptr+13]}, warpId={ram[sb1_ptr+14]}")

    env.close()


if __name__ == "__main__":
    main()
