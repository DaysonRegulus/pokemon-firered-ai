import sys
from pathlib import Path
import numpy as np
import imageio
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path("c:/dev/Antigravity/Pokemon FireRed AI")
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import retro
from pokefirered.env_factory import register_custom_integrations

register_custom_integrations()

EVIDENCE_DIR = PROJECT_ROOT / "visual_evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

env = retro.make("PokemonFireRed-GBA", inttype=retro.data.Integrations.ALL)
obs, info = env.reset()

BASE_EWRAM = 0x02000000
ADDR_MAP_BANK = 0x02031DBC - BASE_EWRAM
ADDR_MAP_NUM  = 0x02031DBD - BASE_EWRAM
ADDR_POS_X    = 0x02036E48 - BASE_EWRAM
ADDR_POS_Y    = 0x02036E4A - BASE_EWRAM

def read_u16(ram_buf, offset):
    return ram_buf[offset] + (ram_buf[offset+1] << 8)

def save_annotated_frame(frame, step, map_bank, map_num, x, y, label=""):
    img = Image.fromarray(frame)
    # Scale up for readability (GBA native 240x160 -> 480x320)
    img_large = img.resize((480, 320), Image.NEAREST)
    draw = ImageDraw.Draw(img_large)
    
    # Overlay black box
    draw.rectangle([(0, 0), (480, 40)], fill=(0, 0, 0))
    text = f"Step {step:03d} | Map: ({map_bank}, {map_num}) | Pos: ({x}, {y}) | {label}"
    draw.text((10, 10), text, fill=(255, 255, 0))
    return np.array(img_large)

ACT_UP = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
ACT_DOWN = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
ACT_LEFT = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]
ACT_RIGHT = [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
ACT_A = [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
ACT_B = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# Plan:
# 1. Start in bedroom: walk to stairs
# 2. Downstairs: walk around table to Mom, face Mom, inspect visual
# 3. Walk to exit door
actions = []
actions += [ACT_RIGHT]*40 + [ACT_UP]*80 + [ACT_RIGHT]*20 + [ACT_UP]*40 # Bedroom to stairs
actions += [ACT_DOWN]*120 # Down to bottom wall
actions += [ACT_LEFT]*80  # Walk left along bottom
actions += [ACT_UP]*40    # Walk up towards Mom/TV
actions += [ACT_LEFT]*60  # Walk left past table
actions += [ACT_DOWN]*80  # Walk down to exit door mat

recorded_frames = []
keyframe_saved = {}

print("Starting visual proof recording...")

for step, act in enumerate(actions):
    obs, rew, term, trunc, info = env.step(act)
    ram = env.unwrapped.get_ram()
    cur_x = read_u16(ram, ADDR_POS_X)
    cur_y = read_u16(ram, ADDR_POS_Y)
    mb = ram[ADDR_MAP_BANK]
    mn = ram[ADDR_MAP_NUM]
    
    screen = env.unwrapped.get_screen()
    
    # Save keyframes at milestones
    label = ""
    if step == 0:
        label = "Bedroom Start"
    elif mb == 4 and mn == 0 and cur_x == 17 and cur_y == 9:
        label = "Bedroom Stairs"
    elif mb == 4 and mn == 1 and cur_x == 17 and cur_y == 9:
        label = "Living Room Arrival"
    elif mb == 4 and mn == 1 and cur_x == 13 and cur_y == 15:
        label = "Living Room Bottom Carpet"
    elif mb == 3 or (mb != 4):
        label = f"Warped Out to Map ({mb}, {mn})"

    if label and label not in keyframe_saved:
        keyframe_saved[label] = True
        annotated = save_annotated_frame(screen, step, mb, mn, cur_x, cur_y, label)
        Image.fromarray(annotated).save(EVIDENCE_DIR / f"keyframe_{step:04d}_{label.replace(' ', '_')}.png")
        print(f"[KEYFRAME] Saved: {label} at Step {step} | Pos: ({cur_x}, {cur_y})")

    if step % 4 == 0:
        annotated = save_annotated_frame(screen, step, mb, mn, cur_x, cur_y, label)
        recorded_frames.append(annotated)

env.close()

gif_path = EVIDENCE_DIR / "visual_proof_navigation.gif"
print(f"Compiling animated GIF to {gif_path} ({len(recorded_frames)} frames)...")
imageio.mimsave(str(gif_path), recorded_frames, fps=15, loop=0)
print("Visual proof recording complete!")
