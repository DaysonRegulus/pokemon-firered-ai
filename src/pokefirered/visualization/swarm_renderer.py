"""
Swarm Renderer: Generates animated video/GIF visualizations of RL agent swarms
expanding across the Kanto map across training generations (Peter Whidden style).
Composites authentic 32-bit GBA Pokémon FireRed/LeafGreen player character avatars (Red & Leaf)
onto the canonical kanto_firered_clean.png overworld map with boundary enforcement,
dynamic camera tracking, and scientific HUD.
"""
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from .world_mapper import KantoWorldMapper

class SwarmRenderer:
    """
    Renders multi-generation agent trajectories onto the canonical 32-bit GBA FireRed overworld map.
    Renders official GBA Red/Leaf walking avatar sprites, breadcrumb exploration trails,
    strict boundary enforcement (no out-of-bounds wandering), and a research HUD.
    """
    # Generation color palette (RGB)
    GEN_PALETTE: Dict[int, Tuple[int, int, int]] = {
        1: (240, 60, 60),      # Crimson Red (Gen 1 baseline)
        10: (255, 140, 0),     # Bright Orange (Gen 10 Route 1)
        35: (255, 215, 0),     # Amber Gold (Gen 35 Viridian City)
        75: (40, 220, 60),     # Lime Green (Gen 75 Viridian Forest)
        100: (0, 220, 255),    # Cyan / Sky Blue (Gen 100 Brock / Pewter Gym)
    }

    def __init__(
        self,
        mapper: Optional[KantoWorldMapper] = None,
        assets_dir: Optional[Path] = None,
        viewport_w: int = 760,
        viewport_h: int = 480
    ):
        self.mapper = mapper or KantoWorldMapper(tile_size=16)
        
        # Locate assets
        if assets_dir is None:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            assets_dir = project_root / "assets" / "pwhiddy"
        self.assets_dir = Path(assets_dir)

        kanto_path = self.assets_dir / "kanto_firered_composite_full.png"
        if not kanto_path.exists():
            kanto_path = self.assets_dir / "kanto_firered_clean.png"

        red_path = self.assets_dir / "red_normal.png"
        green_path = self.assets_dir / "green_normal.png"

        if not kanto_path.exists() or not red_path.exists():
            raise FileNotFoundError(f"Missing required FireRed GBA assets in {self.assets_dir}")

        # Load canonical FireRed overworld & interior composite map
        print(f"[SWARM RENDERER] Loading 32-bit GBA FireRed composite map: {kanto_path.name}...")
        self.kanto_img = Image.open(kanto_path).convert("RGBA")
        if kanto_path.name != "kanto_firered_composite_full.png":
            # Seamlessly replace unmapped white void pixels with authentic GBA forest canopy green
            arr = np.array(self.kanto_img)
            white_mask = (arr[:, :, 0] > 245) & (arr[:, :, 1] > 245) & (arr[:, :, 2] > 245)
            arr[white_mask] = [56, 88, 16, 255]
            self.kanto_img = Image.fromarray(arr)
        self.map_w, self.map_h = self.kanto_img.size

        # Load official GBA player sprite sheets (indexed 16-color)
        print(f"[SWARM RENDERER] Loading official GBA FireRed player sprites...")
        self.red_img = Image.open(red_path)
        self.green_img = Image.open(green_path) if green_path.exists() else None

        self.viewport_w = viewport_w
        self.viewport_h = viewport_h
        self.sprite_cache: Dict[Tuple[int, str, int, bool], Image.Image] = {}

    def _get_gen_color(self, generation: int) -> Tuple[int, int, int]:
        """Returns RGB color keyed or interpolated by generation."""
        if generation in self.GEN_PALETTE:
            return self.GEN_PALETTE[generation]
        for g in sorted(self.GEN_PALETTE.keys()):
            if generation <= g:
                return self.GEN_PALETTE[g]
        return (0, 220, 255)

    def _generate_tinted_sheet(self, base_img: Image.Image, color: Tuple[int, int, int]) -> Image.Image:
        """Applies generation tinting to Red's jacket and cap while preserving linework and skin."""
        pal = np.array(base_img.getpalette()).reshape(-1, 3)[:16]
        arr = np.array(base_img)

        c_pal = pal.copy()
        # In GBA Red: Index 11 is light red cap/jacket, Index 12 is darker red shadow
        c_pal[11] = np.clip(np.array(color) * 1.0, 0, 255).astype(np.uint8)
        c_pal[12] = np.clip(np.array(color) * 0.72, 0, 255).astype(np.uint8)

        rgba_arr = np.zeros((32, 144, 4), dtype=np.uint8)
        for i in range(16):
            mask = (arr == i)
            if i == 0:
                rgba_arr[mask] = [0, 0, 0, 0] # Background transparent
            else:
                rgba_arr[mask] = [c_pal[i][0], c_pal[i][1], c_pal[i][2], 255]

        return Image.fromarray(rgba_arr, mode="RGBA")

    def _get_avatar_sprite(self, gen: int, direction: str, walk_frame: int, is_leaf: bool = False, scale: float = 1.0) -> Image.Image:
        """
        Retrieves or generates a tinted, directional GBA walking sprite.
        direction: 'down', 'up', 'left', 'right'
        walk_frame: 0 (walk left), 1 (stand), 2 (walk right)
        scale: scale factor for resized interior maps (e.g. 0.75 for Viridian Forest)
        """
        cache_key = (gen, direction, walk_frame, is_leaf, scale)
        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]

        color = self._get_gen_color(gen)
        base = self.green_img if (is_leaf and self.green_img) else self.red_img
        sheet = self._generate_tinted_sheet(base, color)

        # GBA Frame mapping in 144x32 sheet (each frame 16x32):
        # 0: Down stand, 1: Up stand, 2: Left stand
        # 3: Down walk1, 4: Down walk2
        # 5: Up walk1, 6: Up walk2
        # 7: Left walk1, 8: Left walk2
        # Right is horizontally flipped from Left
        flip_h = False
        if direction == 'down':
            f_idx = 0 if walk_frame == 1 else (3 if walk_frame == 0 else 4)
        elif direction == 'up':
            f_idx = 1 if walk_frame == 1 else (5 if walk_frame == 0 else 6)
        elif direction == 'left':
            f_idx = 2 if walk_frame == 1 else (7 if walk_frame == 0 else 8)
        elif direction == 'right':
            f_idx = 2 if walk_frame == 1 else (7 if walk_frame == 0 else 8)
            flip_h = True
        else:
            f_idx = 0

        crop = sheet.crop((f_idx * 16, 0, (f_idx + 1) * 16, 32))
        if flip_h:
            crop = crop.transpose(Image.FLIP_LEFT_RIGHT)

        if scale != 1.0:
            tw = max(4, int(crop.width * scale))
            th = max(8, int(crop.height * scale))
            crop = crop.resize((tw, th), Image.Resampling.NEAREST)

        self.sprite_cache[cache_key] = crop
        return crop

    def _draw_hud(
        self,
        frame: Image.Image,
        step_idx: int,
        total_steps: int,
        unique_tiles: int,
        max_gen: int,
        frontier_landmark: str,
        boulder_badge: bool
    ):
        """Draws a semi-transparent HUD overlay with research telemetry."""
        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Top-Left Telemetry Card
        hud_x, hud_y = 12, 12
        hud_w, hud_h = 295, 110
        draw.rectangle([hud_x, hud_y, hud_x + hud_w, hud_y + hud_h], fill=(10, 16, 24, 220), outline=(0, 200, 255, 230), width=1)

        draw.text((hud_x + 10, hud_y + 8), "POKEMON FIRERED GBA: SWARM VIZ", fill=(0, 230, 255, 255))
        draw.line([hud_x + 10, hud_y + 24, hud_x + hud_w - 10, hud_y + 24], fill=(0, 140, 180, 180), width=1)

        draw.text((hud_x + 10, hud_y + 28), f"Step: {step_idx:,} / {total_steps:,} | Gens 1-{max_gen}", fill=(225, 225, 225, 255))
        draw.text((hud_x + 10, hud_y + 44), f"Unique Tiles Discovered: {unique_tiles:,}", fill=(50, 240, 120, 255))
        draw.text((hud_x + 10, hud_y + 60), f"Frontier: {frontier_landmark.upper()}", fill=(255, 190, 40, 255))

        badge_txt = "BOULDER BADGE: ACQUIRED [1/8]" if boulder_badge else "BOULDER BADGE: LOCKED [0/8]"
        badge_col = (40, 240, 60, 255) if boulder_badge else (120, 140, 240, 255)
        draw.text((hud_x + 10, hud_y + 78), badge_txt, fill=badge_col)

        # Bottom-Right Generation Legend
        leg_w, leg_h = 165, 96
        leg_x = frame.width - leg_w - 12
        leg_y = frame.height - leg_h - 12
        draw.rectangle([leg_x, leg_y, leg_x + leg_w, leg_y + leg_h], fill=(10, 16, 24, 220), outline=(80, 80, 90, 200), width=1)
        draw.text((leg_x + 8, leg_y + 6), "GENERATION PALETTE", fill=(200, 200, 200, 255))

        legend_items = [
            (1, "Gen 1 (Pallet)"),
            (10, "Gen 10 (Route 1)"),
            (35, "Gen 35 (Viridian)"),
            (75, "Gen 75 (Forest)"),
            (100, "Gen 100 (Brock)"),
        ]
        for i, (g, lbl) in enumerate(legend_items):
            c = self._get_gen_color(g)
            cy = leg_y + 22 + i * 14
            draw.ellipse([leg_x + 10, cy, leg_x + 16, cy + 6], fill=(*c, 255))
            draw.text((leg_x + 22, cy - 2), lbl, fill=(210, 210, 210, 255))

        frame.alpha_composite(overlay)

    def generate_timelapse(
        self,
        trajectories_by_gen: Dict[int, List[List[Tuple[int, int, int, int]]]],
        output_video_path: Path,
        output_gif_path: Optional[Path] = None,
        fps: int = 15,
        trail_length: int = 14,
        gif_duration_ms: int = 125,
        gif_frame_skip: int = 2,
        intro_hold_frames: int = 15,
        outro_hold_frames: int = 30
    ):
        """
        Renders multi-generation agent trajectories onto the canonical 32-bit GBA FireRed map.
        Each agent is rendered as an authentic GBA animated walking sprite with strict
        walkable boundary enforcement, dynamic camera tracking, and research HUD.
        """
        output_video_path = Path(output_video_path)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        all_agents = []
        for gen, traj_list in sorted(trajectories_by_gen.items()):
            for a_idx, traj in enumerate(traj_list):
                all_agents.append({
                    'gen': gen,
                    'agent_id': f"g{gen}_a{a_idx}",
                    'is_leaf': (a_idx % 2 == 1), # Alternate between Red and Leaf avatars
                    'traj': traj,
                    'last_dir': 'down',
                })

        max_steps = max(len(a['traj']) for a in all_agents) if all_agents else 0
        print(f"[SWARM RENDERER] Total GBA agents: {len(all_agents)} | Max steps: {max_steps}")

        LANDMARK_RANKS = [
            ("Pallet Town", 0, "Pallet Town"),
            ("Hero's House", 0, "Pallet Town (Home)"),
            ("Route 1", 1, "Route 1"),
            ("Viridian City", 2, "Viridian City"),
            ("Route 2", 3, "Route 2"),
            ("Forest", 4, "Viridian Forest"),
            ("Pewter City", 5, "Pewter City"),
            ("Gym", 6, "Pewter Gym (Brock)"),
            ("Brock", 6, "Pewter Gym (Brock)"),
            ("Mt. Moon", 7, "Mt. Moon"),
        ]
        visited_tiles = set()
        max_rank = 0
        frontier_landmark = "Pallet Town"
        boulder_badge = False

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_writer = cv2.VideoWriter(str(output_video_path), fourcc, fps, (self.viewport_w, self.viewport_h))

        gif_frames = []

        # Smooth camera state centered on Pallet Town (px=1152, py=4336)
        cam_x, cam_y = 1152.0, 4336.0

        for step in range(max_steps):
            active_heads = []

            for agent in all_agents:
                traj = agent['traj']
                if step < len(traj):
                    raw_bank, raw_num, raw_x, raw_y = traj[step]
                    # Strict boundary enforcement: clamp to walkable map area
                    bank, num = raw_bank, raw_num
                    x, y = self.mapper.clamp_to_walkable(bank, num, raw_x, raw_y)
                    visited_tiles.add((bank, num, x, y))
                    px, py = self.mapper.to_global_pixel_coords(bank, num, x, y)

                    # Update frontier landmark monotonically based on highest milestone reached
                    name = self.mapper.get_landmark_name(bank, num)
                    for key, r, display_name in LANDMARK_RANKS:
                        if key in name and r > max_rank:
                            max_rank = r
                            frontier_landmark = display_name
                            if r >= 6:
                                boulder_badge = True

                    # Calculate movement direction
                    if step > 0 and step - 1 < len(traj):
                        p_bank, p_num, p_raw_x, p_raw_y = traj[step - 1]
                        px_prev, py_prev = self.mapper.clamp_to_walkable(p_bank, p_num, p_raw_x, p_raw_y)
                        if (p_bank, p_num) == (bank, num):
                            dx = x - px_prev
                            dy = y - py_prev
                            if abs(dx) > abs(dy):
                                direction = 'right' if dx > 0 else ('left' if dx < 0 else agent['last_dir'])
                            elif abs(dy) > 0:
                                direction = 'down' if dy > 0 else 'up'
                            else:
                                direction = agent['last_dir']
                        else:
                            direction = agent['last_dir']
                    else:
                        direction = 'down'

                    agent['last_dir'] = direction

                    # Walk cycle: alternates 0 (step left) -> 1 (stand) -> 2 (step right) -> 1 (stand)
                    cycle = (step + int(agent['gen'])) % 4
                    wf = 0 if cycle == 0 else (2 if cycle == 2 else 1)

                    # Trail history
                    trail_pts = []
                    for t_back in range(1, min(step + 1, trail_length)):
                        tb_b, tb_n, tb_x, tb_y = traj[step - t_back]
                        c_tbx, c_tby = self.mapper.clamp_to_walkable(tb_b, tb_n, tb_x, tb_y)
                        t_px, t_py = self.mapper.to_global_pixel_coords(tb_b, tb_n, c_tbx, c_tby)
                        alpha = max(0.2, 1.0 - (t_back / trail_length))
                        trail_pts.append((t_px + 8, t_py + 8, alpha))

                    scale = self.mapper.get_map_scale(bank, num)

                    active_heads.append({
                        'gen': agent['gen'],
                        'is_leaf': agent['is_leaf'],
                        'px': px,
                        'py': py,
                        'direction': direction,
                        'walk_frame': wf,
                        'trail_pts': trail_pts,
                        'scale': scale,
                    })

            # Calculate target camera position (focused dynamically on the exploration frontier)
            if active_heads:
                max_active_gen = max(h['gen'] for h in active_heads)
                frontier_heads = [h for h in active_heads if h['gen'] == max_active_gen]
                
                f_target_x = float(np.mean([h['px'] + 8 for h in frontier_heads]))
                f_target_y = float(np.mean([h['py'] + 8 for h in frontier_heads]))
                all_mean_x = float(np.mean([h['px'] + 8 for h in active_heads]))
                
                target_x = 0.85 * f_target_x + 0.15 * all_mean_x
                target_y = f_target_y

                # Gentle, cinematic camera smoothing (eliminates rapid whip-pans)
                cam_x = 0.94 * cam_x + 0.06 * target_x
                cam_y = 0.94 * cam_y + 0.06 * target_y

            # Clamp viewport within map
            crop_x1 = int(max(0, min(self.map_w - self.viewport_w, cam_x - self.viewport_w / 2)))
            crop_y1 = int(max(0, min(self.map_h - self.viewport_h, cam_y - self.viewport_h / 2)))
            crop_x2 = crop_x1 + self.viewport_w
            crop_y2 = crop_y1 + self.viewport_h

            # Crop viewport from base GBA FireRed map
            frame = self.kanto_img.crop((crop_x1, crop_y1, crop_x2, crop_y2)).copy()
            draw = ImageDraw.Draw(frame)

            # Draw breadcrumb trails
            for head in active_heads:
                color = self._get_gen_color(head['gen'])
                for t_px, t_py, alpha in head['trail_pts']:
                    sx = t_px - crop_x1
                    sy = t_py - crop_y1
                    if 0 <= sx < self.viewport_w and 0 <= sy < self.viewport_h:
                        draw.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(*color, int(alpha * 210)))

            # Draw GBA Red / Leaf avatar sprites
            for head in active_heads:
                sx = head['px'] - crop_x1
                sc = head.get('scale', 1.0)
                # Offset by -16 * scale vertically so feet land naturally on tile
                sy = head['py'] - int(16 * sc) - crop_y1
                if -16 <= sx < self.viewport_w and -32 <= sy < self.viewport_h:
                    sprite = self._get_avatar_sprite(
                        head['gen'],
                        head['direction'],
                        head['walk_frame'],
                        is_leaf=head['is_leaf'],
                        scale=sc
                    )
                    frame.paste(sprite, (int(sx), int(sy)), sprite)

            # Draw HUD
            self._draw_hud(
                frame=frame,
                step_idx=step + 1,
                total_steps=max_steps,
                unique_tiles=len(visited_tiles),
                max_gen=max(trajectories_by_gen.keys()) if trajectories_by_gen else 1,
                frontier_landmark=frontier_landmark,
                boulder_badge=boulder_badge
            )

            # Write to video
            rgb_arr = np.array(frame.convert("RGB"))
            bgr_arr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)

            # Intro hold: hold frame at step 0 so viewer can register the initial setup
            if step == 0:
                for _ in range(intro_hold_frames):
                    out_writer.write(bgr_arr)
                    if output_gif_path:
                        gif_frames.append(frame.convert("RGB"))

            out_writer.write(bgr_arr)

            # Capture GIF frames
            if output_gif_path and (step % gif_frame_skip == 0):
                gif_frames.append(frame.convert("RGB"))

            # Outro hold: hold final frame on Brock & Boulder badge victory
            if step == max_steps - 1:
                for _ in range(outro_hold_frames):
                    out_writer.write(bgr_arr)
                    if output_gif_path:
                        gif_frames.append(frame.convert("RGB"))

            if (step + 1) % 50 == 0 or step == max_steps - 1:
                print(f"  [RENDER PROGRESS] Step {step+1:3d}/{max_steps:3d} | Cam: ({int(cam_x)}, {int(cam_y)}) | Frontier: {frontier_landmark}")

        out_writer.release()
        print(f"[SUCCESS] Exported 32-bit GBA FireRed swarm video: {output_video_path}")

        if output_gif_path and gif_frames:
            print(f"[SWARM RENDERER] Compiling animated GIF ({len(gif_frames)} frames @ {gif_duration_ms}ms/frame)...")
            gif_frames[0].save(
                str(output_gif_path),
                save_all=True,
                append_images=gif_frames[1:],
                duration=gif_duration_ms,
                loop=0,
                optimize=True
            )
            print(f"[SUCCESS] Exported authentic GBA FireRed showcase GIF: {output_gif_path}")
