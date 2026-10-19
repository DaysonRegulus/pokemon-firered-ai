from pathlib import Path
import retro
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE = 0x02000000

def get_pos(env):
    ram = env.unwrapped.get_ram()
    x = int.from_bytes(ram[0x02036E48 - BASE:0x02036E4A - BASE], 'little')
    y = int.from_bytes(ram[0x02036E4A - BASE:0x02036E4C - BASE], 'little')
    return x, y

def main():
    env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
    env.reset()
    with open(PROJECT_ROOT / 'data' / 'forest_active_floor.state', 'rb') as f:
        env.unwrapped.em.set_state(f.read())

    buttons = env.unwrapped.buttons
    print("Initial pos:", get_pos(env))

    # Let's test stepping UP (facing UP already)
    act_up = np.zeros(len(buttons), dtype=np.int8)
    act_up[buttons.index('UP')] = 1
    for _ in range(16): env.step(act_up)
    print("After UP 16 frames:", get_pos(env))
    for _ in range(16): env.step(act_up)
    print("After second UP 16 frames:", get_pos(env))

    # Now test turning LEFT
    act_left = np.zeros(len(buttons), dtype=np.int8)
    act_left[buttons.index('LEFT')] = 1
    for _ in range(16): env.step(act_left)
    print("After LEFT 16 frames:", get_pos(env))
    for _ in range(16): env.step(act_left)
    print("After second LEFT 16 frames:", get_pos(env))

    env.close()

if __name__ == "__main__":
    main()
