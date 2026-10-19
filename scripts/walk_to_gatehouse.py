import retro
import numpy as np
from PIL import Image

BASE = 0x02000000

def get_telemetry(env):
    ram = env.unwrapped.get_ram()
    bank = int(ram[0x02031DBC - BASE])
    num = int(ram[0x02031DBD - BASE])
    sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], 'little') - BASE
    x = int.from_bytes(ram[sb1_ptr:sb1_ptr+2], 'little')
    y = int.from_bytes(ram[sb1_ptr+2:sb1_ptr+4], 'little')
    cb2 = int.from_bytes(ram[0x430F4:0x430F8], 'little')
    return {'bank': bank, 'num': num, 'x': x, 'y': y, 'cb2': hex(cb2)}

env = retro.make('PokemonFireRed-GBA', state='BeginningPalletGotPokeballs', inttype=retro.data.Integrations.ALL)
env.reset()
with open('data/forest_post_trainer_verified.state', 'rb') as f:
    env.unwrapped.em.set_state(f.read())

buttons = env.unwrapped.buttons
def step_up(frames=16):
    act = np.zeros(len(buttons), dtype=np.int8)
    act[buttons.index('UP')] = 1
    for _ in range(frames): env.step(act)
    return get_telemetry(env)

print('Post-trainer start:', get_telemetry(env))
for step in range(30):
    info = step_up()
    print(f"Step {step+1}: Map ({info['bank']}, {info['num']}) Pos: ({info['x']}, {info['y']})")
    if (info['bank'], info['num']) != (1, 0):
        print(f"Warp stepped! Entered Map ({info['bank']}, {info['num']}) at ({info['x']}, {info['y']})")
        break

for _ in range(40):
    env.step(np.zeros(len(buttons), dtype=np.int8))

info = get_telemetry(env)
print(f"Settled: Map ({info['bank']}, {info['num']}) Pos: ({info['x']}, {info['y']})")
Image.fromarray(env.unwrapped.get_screen()).save('visual_evidence/route_verification/proof_north_gatehouse_interior.png')
print("Saved proof_north_gatehouse_interior.png")
with open('data/forest_north_gatehouse_interior.state', 'wb') as f:
    f.write(env.unwrapped.em.get_state())
print("Saved data/forest_north_gatehouse_interior.state")
env.close()
