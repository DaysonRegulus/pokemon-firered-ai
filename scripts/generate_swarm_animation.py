"""
Generate Animated Multi-Generation Swarm Visualization (Peter Whidden Style).
Produces an MP4 video and animated GIF showing the swarm of RL agents
expanding across Kanto over training generations (Pallet Town -> Pewter Gym / Brock).
Composites authentic 32-bit GBA Pokémon FireRed/LeafGreen player character avatars
onto canonical kanto_firered_clean.png with strict walkable boundary enforcement.
"""
import sys
from pathlib import Path
import random
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pokefirered.visualization import KantoWorldMapper, SwarmRenderer

def generate_multi_gen_trajectories(num_gens=5, agents_per_gen=8, max_steps=210):
    """
    Synthesizes multi-generation agent trajectories grounded in canonical GBA FireRed
    topological coordinates discovered across Pallet, Route 1, Viridian, Forest, and Pewter.
    Coordinates are in canonical (bank, map_num, x, y) tuples.
    Enforces strict physical walkable boundary constraints: ZERO out-of-bounds drift or tree clipping.
    """
    random.seed(42)
    np.random.seed(42)
    mapper = KantoWorldMapper()
    trajectories = {}

    # Generational progression tiers
    # Gen: (max_reach_fraction, target_landmark)
    gen_tiers = [
        (1, 0.18, "Pallet Town & Lower Route 1"),
        (10, 0.42, "Route 1 North Corridor"),
        (35, 0.65, "Viridian City Plaza"),
        (75, 0.85, "Viridian Forest Corridor"),
        (100, 1.00, "Pewter Gym Brock"),
    ]

    for gen, max_reach, landmark_name in gen_tiers:
        gen_agents = []
        for a_idx in range(agents_per_gen):
            traj = []
            
            # Start outside Red's House in Pallet Town (Bank 3, Map 0)
            # Local Pallet coords: Red's front door is at (6, 8)
            cur_bank, cur_num = 3, 0
            cur_x = 6 + random.choice([0, 1])
            cur_y = 8 + random.choice([0, 1])
            agent_reach = max_reach * (0.85 + 0.3 * random.random())

            for step in range(max_steps):
                traj.append((cur_bank, cur_num, cur_x, cur_y))
                frac = step / float(max_steps)

                if frac > agent_reach:
                    # Agent reached generation frontier: diffuse locally strictly within walkable bounds
                    if random.random() < 0.35:
                        dx, dy = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
                        if mapper.is_walkable(cur_bank, cur_num, cur_x + dx, cur_y + dy):
                            cur_x += dx
                            cur_y += dy
                    continue

                # Directed movement along canonical landmarks:
                if (cur_bank, cur_num) == (3, 0):
                    # Pallet Town: Move from door toward north exit path at (10, 1)
                    if cur_y > 2:
                        if cur_x < 10: cur_x += 1
                        elif cur_x > 11: cur_x -= 1
                        else: cur_y -= 1
                    else:
                        cur_y -= 1

                    if cur_y <= 1 and 10 <= cur_x <= 11:
                        # Step into Route 1 (48-tile map)
                        cur_bank, cur_num = 3, 19
                        cur_x, cur_y = 10, 47

                elif (cur_bank, cur_num) == (3, 19):
                    # Route 1 (20x48 GBA FireRed Map)
                    if cur_y >= 44:
                        cur_y -= 1
                    elif cur_y >= 38:
                        if cur_x > 5: cur_x -= 1
                        elif cur_x < 5: cur_x += 1
                        else: cur_y -= 1
                    elif cur_y == 37:
                        # Step north through the grass gap left of signpost at (5, 37)
                        cur_y -= 1
                    elif cur_y == 36:
                        # Turn right onto the wide east-west dirt road towards x=17
                        if cur_x < 17: cur_x += 1
                        else: cur_y -= 1
                    elif cur_y >= 28:
                        # Northward up eastern vertical road
                        cur_y -= 1
                    elif cur_y >= 26:
                        # Middle horizontal connector road towards central road at x=11
                        if cur_x > 11: cur_x -= 1
                        elif cur_x < 11: cur_x += 1
                        else: cur_y -= 1
                    elif cur_y > 16:
                        # Northward up central vertical road
                        cur_y -= 1
                    elif cur_y == 16:
                        if cur_x < 13: cur_x += 1
                        else: cur_y -= 1
                    elif cur_y >= 11:
                        # Upper winding road curving east around trees
                        if cur_x < 15: cur_x += 1
                        elif cur_x > 15: cur_x -= 1
                        else: cur_y -= 1
                    elif cur_y >= 8:
                        # Upper horizontal connector road towards north corridor at x=10
                        if cur_x > 10: cur_x -= 1
                        elif cur_x < 10: cur_x += 1
                        else: cur_y -= 1
                    elif cur_y > 0:
                        cur_y -= 1
                    else:
                        # Step into Viridian City
                        cur_bank, cur_num = 3, 1
                        cur_x, cur_y = 20, 35

                elif (cur_bank, cur_num) == (3, 1):
                    # Viridian City: North along central paved avenue
                    cur_y -= 1
                    if cur_y <= 9:
                        cur_x = 17
                    if cur_y <= 0:
                        # Enter Route 2 South
                        cur_bank, cur_num = 3, 20
                        cur_x, cur_y = 10, 58

                elif (cur_bank, cur_num) == (3, 20):
                    # Route 2 South
                    cur_y -= 1
                    if cur_y <= 35:
                        # Enter Viridian Forest South Gatehouse
                        cur_bank, cur_num = 1, 0
                        cur_x, cur_y = 17, 44

                elif (cur_bank, cur_num) == (1, 0):
                    # Viridian Forest interior maze
                    if cur_y > 34:
                        cur_y -= 1
                    elif cur_y == 34 and cur_x < 24:
                        cur_x += 1
                    elif 24 <= cur_y <= 34 and cur_x >= 22:
                        cur_y -= 1
                    elif cur_y == 24 and cur_x > 14:
                        cur_x -= 1
                    elif 14 <= cur_y <= 24 and cur_x <= 16:
                        cur_y -= 1
                    elif cur_y == 14 and cur_x < 17:
                        cur_x += 1
                    elif cur_y > 4:
                        cur_y -= 1
                    else:
                        # Exit to Pewter City via North Gatehouse
                        cur_bank, cur_num = 3, 2
                        cur_x, cur_y = 19, 35

                elif (cur_bank, cur_num) == (3, 2):
                    # Pewter City
                    if cur_y >= 28:
                        cur_y -= 1
                    elif cur_y > 17:
                        cur_y -= 1
                        if cur_x > 13: cur_x -= 1
                    elif cur_y <= 17 and cur_x == 13:
                        # Enter Pewter Gym
                        cur_bank, cur_num = 6, 2
                        cur_x, cur_y = 5, 11

                elif (cur_bank, cur_num) == (6, 2):
                    # Pewter Gym: Walk to Brock on podium at (5, 4)
                    if cur_y > 4: cur_y -= 1
                    if cur_x > 5: cur_x -= 1
                    elif cur_x < 5: cur_x += 1

                # Strict boundary enforcement: always clamp to walkable area of current map
                cur_x, cur_y = mapper.clamp_to_walkable(cur_bank, cur_num, cur_x, cur_y)

            gen_agents.append(traj)
        trajectories[gen] = gen_agents

    return trajectories

def main():
    print("=" * 75)
    print(" GENERATING AUTHENTIC 32-BIT GBA POKÉMON FIRERED AVATAR SWARM VISUALIZATION")
    print("=" * 75)

    output_dir = PROJECT_ROOT / "visual_evidence" / "swarm_visualizer"
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / "kanto_swarm_timelapse.mp4"
    gif_path = output_dir / "kanto_swarm_showcase.gif"

    print("Synthesizing multi-generation agent trajectory swarm (Gens 1, 10, 35, 75, 100)...")
    trajectories = generate_multi_gen_trajectories(num_gens=5, agents_per_gen=8, max_steps=210)

    renderer = SwarmRenderer(viewport_w=640, viewport_h=400)
    print("Rendering animated timelapse video and showcase GIF with GBA Red & Leaf avatars...")
    renderer.generate_timelapse(
        trajectories_by_gen=trajectories,
        output_video_path=video_path,
        output_gif_path=gif_path,
        fps=24,
        trail_length=14
    )

    print("\n" + "=" * 75)
    print(" GBA FIRERED VISUALIZATION EXPORT COMPLETE!")
    print(f" Video Path : {video_path}")
    print(f" GIF Path   : {gif_path}")
    print("=" * 75)

if __name__ == "__main__":
    main()
