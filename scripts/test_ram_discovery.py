"""
Empirical Verification Script for GBA RAM Discoveries:
Validates sCurrentMap, gObjectEvents[0], gSaveBlock1Ptr, and gSaveBlock2Ptr,
and captures side-by-side visual frames with annotated RAM values.
"""
from pathlib import Path
import sys
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import retro

# Ensure src/ is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pokefirered.env_factory import register_custom_integrations

OUTPUT_DIR = PROJECT_ROOT / "visual_evidence" / "ram_verification"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# GBA Character Map Decoder for Gen 3 English
GEN3_CHARMAP = {
    0x00: " ", 0x01: "À", 0x02: "Á", 0x03: "Â", 0x04: "Ç", 0x05: "È", 0x06: "É",
    0xBB: "A", 0xBC: "B", 0xBD: "C", 0xBE: "D", 0xBF: "E", 0xC0: "F", 0xC1: "G",
    0xC2: "H", 0xC3: "I", 0xC4: "J", 0xC5: "K", 0xC6: "L", 0xC7: "M", 0xC8: "N",
    0xC9: "O", 0xCA: "P", 0xCB: "Q", 0xCC: "R", 0xCD: "S", 0xCE: "T", 0xCF: "U",
    0xD0: "V", 0xD1: "W", 0xD2: "X", 0xD3: "Y", 0xD4: "Z",
    0xD5: "a", 0xD6: "b", 0xD7: "c", 0xD8: "d", 0xD9: "e", 0xDA: "f", 0xDB: "g",
    0xDC: "h", 0xDD: "i", 0xDE: "j", 0xDF: "k", 0xE0: "l", 0xE1: "m", 0xE2: "n",
    0xE3: "o", 0xE4: "p", 0xE5: "q", 0xE6: "r", 0xE7: "s", 0xE8: "t", 0xE9: "u",
    0xEA: "v", 0xEB: "w", 0xEC: "x", 0xED: "y", 0xEE: "z",
    0xFF: "",  # Terminator
}


def decode_gen3_string(byte_list):
    res = []
    for b in byte_list:
        if b == 0xFF:
            break
        res.append(GEN3_CHARMAP.get(b, f"[{hex(b)}]"))
    return "".join(res)


def inspect_pointers(env):
    ram = env.unwrapped.get_ram()
    BASE = 0x02000000

    # 1. Static Overworld Engine Addresses in EWRAM
    map_bank = int(ram[0x02031DBC - BASE])
    map_num = int(ram[0x02031DBD - BASE])
    player_x = int.from_bytes(ram[0x02036E48 - BASE:0x02036E4A - BASE], byteorder="little")
    player_y = int.from_bytes(ram[0x02036E4A - BASE:0x02036E4C - BASE], byteorder="little")

    # 2. IWRAM Master Pointers at offset 0x45000 in ram buffer
    # 0x45008 is gSaveBlock1Ptr; 0x4500C is gSaveBlock2Ptr; 0x45010 is gPokemonStoragePtr
    sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], byteorder="little")
    sb2_ptr = int.from_bytes(ram[0x4500C:0x45010], byteorder="little")

    sb1_valid = (0x02000000 <= sb1_ptr < 0x02040000)
    sb2_valid = (0x02000000 <= sb2_ptr < 0x02040000)

    # 3. Decode Trainer Name from SaveBlock2
    trainer_name = "UNKNOWN"
    if sb2_valid:
        sb2_offset = sb2_ptr - BASE
        name_bytes = list(ram[sb2_offset:sb2_offset + 8])
        trainer_name = decode_gen3_string(name_bytes)

    # 4. Read Saved Coords from SaveBlock1
    sb1_x, sb1_y = -1, -1
    if sb1_valid:
        sb1_offset = sb1_ptr - BASE
        sb1_x = int.from_bytes(ram[sb1_offset:sb1_offset + 2], byteorder="little")
        sb1_y = int.from_bytes(ram[sb1_offset + 2:sb1_offset + 4], byteorder="little")

    return {
        "map_bank": map_bank,
        "map_num": map_num,
        "pos_x": player_x,
        "pos_y": player_y,
        "sb1_ptr": hex(sb1_ptr),
        "sb2_ptr": hex(sb2_ptr),
        "sb1_valid": sb1_valid,
        "sb2_valid": sb2_valid,
        "trainer_name": trainer_name,
        "sb1_pos": (sb1_x, sb1_y),
    }


def annotate_frame(screen_np, data, step):
    img = Image.fromarray(screen_np)
    # Upscale 2x for sharp presentation
    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(img)

    banner_h = 52
    draw.rectangle([(0, img.height - banner_h), (img.width, img.height)], fill=(0, 0, 0))

    line1 = f"Step {step:03d} | Map ({data['map_bank']},{data['map_num']}) Pos: ({data['pos_x']:2d},{data['pos_y']:2d}) | Trainer: '{data['trainer_name']}'"
    line2 = f"SB1: {data['sb1_ptr']} (EntryPos: {data['sb1_pos']}) | SB2: {data['sb2_ptr']}"

    draw.text((8, img.height - banner_h + 4), line1, fill=(255, 255, 0))
    draw.text((8, img.height - banner_h + 26), line2, fill=(100, 255, 255))
    return img


def main():
    print("=" * 65)
    print(" EMPIRICAL GBA RAM DISCOVERY & POINTER VERIFICATION")
    print("=" * 65)

    register_custom_integrations()
    env = retro.make(
        game="PokemonFireRed-GBA",
        state="BeginningPallet",
        inttype=retro.data.Integrations.ALL,
    )
    env.reset()
    # Step 1 frame to initialize RAM buffers
    env.step(np.zeros(env.action_space.shape[0], dtype=np.int8))

    data = inspect_pointers(env)
    print("\n[VERIFIED INITIAL STATE]")
    for k, v in data.items():
        print(f"  {k:18s} : {v}")

    # Buttons in retro action space
    buttons = env.unwrapped.buttons
    
    def step_button(btn_name, frames=8):
        act = np.zeros(len(buttons), dtype=np.int8)
        if btn_name in buttons:
            act[buttons.index(btn_name)] = 1
        for _ in range(frames):
            env.step(act)

    captured_snapshots = []
    
    # Snapshot 0: Initial State
    screen = env.unwrapped.get_screen()
    img = annotate_frame(screen, data, step=0)
    p0 = OUTPUT_DIR / "ram_proof_step000_spawn.png"
    img.save(str(p0))
    captured_snapshots.append(p0)
    print(f"\n[SNAPSHOT 1] Saved: {p0.name}")

    # Step through scripted movements in Pallet Town
    moves = [
        ("DOWN", 16),
        ("DOWN", 16),
        ("LEFT", 16),
        ("LEFT", 16),
        ("UP", 16),
        ("RIGHT", 16),
        ("UP", 16),
    ]

    total_steps = 0
    for move_idx, (btn, frames) in enumerate(moves, 1):
        step_button(btn, frames=frames)
        total_steps += frames
        cur_data = inspect_pointers(env)
        screen = env.unwrapped.get_screen()
        img = annotate_frame(screen, cur_data, step=total_steps)
        p = OUTPUT_DIR / f"ram_proof_step{total_steps:03d}_{btn}_x{cur_data['pos_x']}_y{cur_data['pos_y']}.png"
        img.save(str(p))
        captured_snapshots.append(p)
        print(f"[SNAPSHOT {move_idx + 1}] Step {total_steps:3d} ({btn:5s}) -> Map ({cur_data['map_bank']},{cur_data['map_num']}) Pos: ({cur_data['pos_x']:2d},{cur_data['pos_y']:2d}) -> {p.name}")

    env.close()

    print("\n" + "=" * 65)
    print(" RAM VERIFICATION COMPLETE")
    print(f" Total Visual Snapshots Saved: {len(captured_snapshots)}")
    print(f" Destination Directory:        {OUTPUT_DIR}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
