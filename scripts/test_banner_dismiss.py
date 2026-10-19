"""
Tests stepping frames with various inputs to determine exact banner dismissal timing.
"""
from pathlib import Path
import numpy as np
from PIL import Image
import retro

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "visual_evidence" / "route_verification"
STATE_FILE = PROJECT_ROOT / "data" / "forest_checkpoint.state"

def main():
    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()
    with open(STATE_FILE, 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    buttons = env.unwrapped.buttons
    act_a = np.zeros(len(buttons), dtype=np.int8); act_a[buttons.index('A')] = 1
    act_b = np.zeros(len(buttons), dtype=np.int8); act_b[buttons.index('B')] = 1
    act_idle = np.zeros(len(buttons), dtype=np.int8)

    # Let's try stepping 60 frames at a time up to 300 frames
    for i in range(1, 8):
        for _ in range(60):
            env.step(act_b)
        screen = env.unwrapped.get_screen()
        # Save a thumbnail
        Image.fromarray(screen).save(str(OUTPUT_DIR / f"banner_test_step_{i*60}.png"))
        print(f"Frame {i*60}: screen shape {screen.shape}")

    env.close()

if __name__ == "__main__":
    main()
