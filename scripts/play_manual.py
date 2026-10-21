"""
Interactive Manual Play & Live Swarm Visualizer Verifier for Pokemon FireRed.
Allows human play via keyboard to test controls, game events, RAM reading,
rewards, and live map tracking on the canonical Kanto composite map.

Modes:
  1. Visualizer Mode (default): Real-time side-by-side OpenCV window:
     - Left Pane: Authentic GBA Game Screen + Real-Time Telemetry HUD
     - Right Pane: Live Swarm Visualizer tracking player on kanto_firered_composite_full.png
  2. GBA Mode: Standard native emulator window (retro.render).
  3. Terminal Mode: Headless console play via terminal keyboard input.

Controls:
  W / A / S / D  : Move UP / LEFT / DOWN / RIGHT
  Z              : B Button (Run / Cancel)
  X              : A Button (Interact / Confirm)
  Space / Enter  : START / SELECT
  C              : Toggle Walkable Clamping ON / OFF (Visualizer mode)
  [ / ]          : Real-time Tile X Offset Adjustment (-1 / +1)
  ; / '          : Real-time Tile Y Offset Adjustment (-1 / +1)
  P              : Save Side-by-Side Snapshot Image
  Q / ESC        : Quit & Save Trajectory
"""
import argparse
import json
from pathlib import Path
import sys
import time
from typing import Dict, List, Tuple
import cv2
import numpy as np
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from pokefirered.env_factory import register_custom_integrations
from pokefirered.keyboard_input import KeyboardInput, key_to_action
from pokefirered.visualization import KantoWorldMapper
from pokefirered.wrappers import ActionFilterWrapper, CustomRewardEnv
import retro
import retro.data

ENV_NAME = "PokemonFireRed-GBA"


def parse_args():
    parser = argparse.ArgumentParser(description="Pokemon FireRed Manual Control & Swarm Verifier")
    parser.add_argument(
        "--render-mode",
        type=str,
        default="visualizer",
        choices=["visualizer", "gba", "terminal", "none"],
        help="Display mode: 'visualizer' (OpenCV dual-pane HUD + map tracker), 'gba' (standard retro window), 'terminal' (console only), 'none' (headless)",
    )
    parser.add_argument(
        "--state",
        type=str,
        default="BeginningPalletGotPokeballs",
        help="Starting save state (default: BeginningPalletGotPokeballs)",
    )
    parser.add_argument(
        "--clamp",
        action="store_true",
        help="Enable strict corridor clamping (default: False for authentic RAM physics)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Maximum action steps before automatic exit",
    )
    parser.add_argument(
        "--save-trajectory",
        type=str,
        default="visual_evidence/manual_verification_trajectory.json",
        help="Path to save recorded player trajectory JSON",
    )
    parser.add_argument(
        "--replay-trajectory",
        type=str,
        default=None,
        help="Path to JSON trajectory file to replay and inspect visualizer alignment",
    )
    return parser.parse_args()


class LiveManualVerifier:
    """Real-time OpenCV dual-pane visualizer and manual test controller."""

    def __init__(self, state: str = "BeginningPalletGotPokeballs", use_clamp: bool = False):
        register_custom_integrations()
        self.env = retro.make(
            game=ENV_NAME,
            state=state,
            inttype=retro.data.Integrations.ALL,
        )
        self.obs, self.info = self.env.reset()
        self.buttons = self.env.unwrapped.buttons
        self.use_clamp = use_clamp

        self.mapper = KantoWorldMapper()
        self.composite_path = PROJECT_ROOT / "assets" / "pwhiddy" / "kanto_firered_composite_full.png"
        self.composite_img = Image.open(self.composite_path).convert("RGBA")
        self.map_w, self.map_h = self.composite_img.size

        # Player sprite
        sprite_sheet_path = PROJECT_ROOT / "assets" / "pwhiddy" / "firered_player_sprites.png"
        self.sprite_sheet = Image.open(sprite_sheet_path).convert("RGBA")
        self.avatar_crop = self.sprite_sheet.crop((0, 0, 16, 32))  # Down standing frame

        self.trajectory: List[Tuple[int, int, int, int]] = []
        self.step_count = 0
        self.last_action_name = "NONE"
        self.manual_offset_x = 0
        self.manual_offset_y = 0

    def get_ram_coords(self) -> Tuple[int, int, int, int]:
        ram = self.env.unwrapped.get_ram()
        BASE = 0x02000000
        mb = int(ram[0x02031DBC - BASE])
        mn = int(ram[0x02031DBD - BASE])
        raw_x = int.from_bytes(ram[0x02036E48 - BASE : 0x02036E4A - BASE], "little")
        raw_y = int.from_bytes(ram[0x02036E4A - BASE : 0x02036E4C - BASE], "little")
        return mb, mn, raw_x, raw_y

    def step_action(self, btn_name: str, frames: int = 16):
        act = np.zeros(len(self.buttons), dtype=np.int8)
        if btn_name in self.buttons:
            act[self.buttons.index(btn_name)] = 1
        for _ in range(frames):
            self.obs, rew, term, trunc, self.info = self.env.step(act)
        # Release frames so key presses cleanly register
        release_act = np.zeros(len(self.buttons), dtype=np.int8)
        for _ in range(2):
            self.obs, rew, term, trunc, self.info = self.env.step(release_act)
        self.step_count += 1
        self.last_action_name = btn_name

        mb, mn, raw_x, raw_y = self.get_ram_coords()
        lx = max(0, raw_x - 7) if raw_x >= 7 else raw_x
        ly = max(0, raw_y - 7) if raw_y >= 7 else raw_y
        self.trajectory.append((mb, mn, lx, ly))

    def render_dual_pane(self) -> np.ndarray:
        mb, mn, raw_x, raw_y = self.get_ram_coords()
        lx = max(0, raw_x - 7) if raw_x >= 7 else raw_x
        ly = max(0, raw_y - 7) if raw_y >= 7 else raw_y

        if self.use_clamp:
            cx, cy = self.mapper.clamp_to_walkable(mb, mn, lx, ly, strict_corridor=True)
        else:
            cx, cy = lx, ly

        cx += self.manual_offset_x
        cy += self.manual_offset_y

        # 1. Left Pane: Game Boy Advance Screen (240x160 -> 480x320) + Bottom HUD (480x160)
        gba_screen = self.env.unwrapped.get_screen()
        gba_large = cv2.resize(cv2.cvtColor(gba_screen, cv2.COLOR_RGB2BGR), (480, 320), interpolation=cv2.INTER_NEAREST)

        hud_pane = np.zeros((160, 480, 3), dtype=np.uint8)
        landmark = self.mapper.get_landmark_name(mb, mn)
        clamp_str = "ON (Strict Corridor)" if self.use_clamp else "OFF (Authentic RAM Physics)"
        ox, oy = self.mapper.CANONICAL_OFFSETS.get((mb, mn), (60, 260))

        px, py = self.mapper.to_global_pixel_coords(mb, mn, cx, cy, clamp=self.use_clamp)
        tx, ty = px // 16, py // 16

        is_border = ((mb, mn) == (3, 0) and ly <= 1) or ((mb, mn) == (3, 19) and ly >= 38)
        status_str = "BORDER: Pallet <-> Route 1 (Seamless 1:1)" if is_border else f"ADJ: ({self.manual_offset_x:+d}, {self.manual_offset_y:+d}) | R=Reset"

        cv2.putText(hud_pane, f"STEP: {self.step_count:04d} | ACTION: {self.last_action_name}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
        cv2.putText(hud_pane, f"MAP: ({mb}, {mn}) - {landmark} | OFF: ({ox}, {oy})", (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (50, 230, 100), 1)
        cv2.putText(hud_pane, f"RAM: X={raw_x:2d}, Y={raw_y:2d} | LAYOUT: X={lx:2d}, Y={ly:2d} (raw-7)", (10, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 200), 1)
        cv2.putText(hud_pane, f"CANVAS: px=({px}, {py}) | TILE=({tx}, {ty})", (10, 96), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 180, 50), 1)
        cv2.putText(hud_pane, f"CLAMP: {clamp_str} | {status_str}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (180, 180, 255), 1)
        cv2.putText(hud_pane, "KEYS: W/A/S/D=Move | Z=B | X=A | C=Clamp | P=Snap | Q=Quit", (10, 144), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (140, 140, 140), 1)

        left_pane = np.vstack([gba_large, hud_pane])

        # 2. Right Pane: Live Swarm Visualizer Camera (480x480)
        vw, vh = 480, 480
        x1 = max(0, min(self.map_w - vw, px + 8 - vw // 2))
        y1 = max(0, min(self.map_h - vh, py + 8 - vh // 2))
        x2 = x1 + vw
        y2 = y1 + vh

        map_crop = self.composite_img.crop((x1, y1, x2, y2)).copy()
        draw = ImageDraw.Draw(map_crop)

        # Draw trajectory breadcrumbs (last 40 steps)
        for t_idx, (tb, tn, tx_b, ty_b) in enumerate(self.trajectory[-40:]):
            if self.use_clamp:
                tcx, tcy = self.mapper.clamp_to_walkable(tb, tn, tx_b, ty_b, strict_corridor=True)
            else:
                tcx, tcy = tx_b, ty_b
            tcx += self.manual_offset_x
            tcy += self.manual_offset_y
            t_px, t_py = self.mapper.to_global_pixel_coords(tb, tn, tcx, tcy, clamp=self.use_clamp)
            sx = t_px + 8 - x1
            sy = t_py + 8 - y1
            if 0 <= sx < vw and 0 <= sy < vh:
                draw.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(0, 230, 255, 180))

        # Paste player avatar sprite (16x32, feet centered in tile)
        sx = px - x1
        sy = py - 16 - y1
        if -16 <= sx < vw and -32 <= sy < vh:
            map_crop.paste(self.avatar_crop, (int(sx), int(sy)), self.avatar_crop)

        # Overlay tile boundary box on player's current tile
        tx_box = px - x1
        ty_box = py - y1
        draw.rectangle([tx_box, ty_box, tx_box + 16, ty_box + 16], outline=(255, 255, 0, 255), width=1)

        # Convert right pane to BGR for OpenCV
        right_pane = cv2.cvtColor(np.array(map_crop), cv2.COLOR_RGBA2BGR)
        cv2.putText(right_pane, f"CANVAS POS: ({px}, {py}) | TILE: ({tx}, {ty})", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 255), 1)
        cv2.putText(right_pane, "SWARM VISUALIZER LIVE MAP TRACKER", (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        combined = np.hstack([left_pane, right_pane])
        return combined

    def run(self, max_steps: int = None, save_path: Path = None):
        print("\n" + "=" * 70)
        print(" POKEMON FIRERED: LIVE MANUAL PLAY & SWARM ALIGNMENT VERIFIER")
        print("=" * 70)
        print(" Controls:")
        print("   W / A / S / D  : Move UP / LEFT / DOWN / RIGHT")
        print("   Z              : B Button (Run / Cancel)")
        print("   X              : A Button (Interact / Confirm)")
        print("   Space / Enter  : START / SELECT")
        print("   C              : Toggle Walkable Clamp ON / OFF")
        print("   [  /  ]        : Adjust Tile X Offset (-1 / +1)")
        print("   ;  /  '        : Adjust Tile Y Offset (-1 / +1)")
        print("   P              : Save Side-by-Side Snapshot Image")
        print("   Q / ESC        : Quit & Save Trajectory")
        print("=" * 70 + "\n")

        win_name = "Pokemon FireRed: Live Manual Swarm Alignment Verifier"
        cv2.namedWindow(win_name, cv2.WINDOW_AUTOSIZE)

        evidence_dir = PROJECT_ROOT / "visual_evidence" / "manual_verification"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        action_keys = {
            ord("w"): "UP",
            ord("s"): "DOWN",
            ord("a"): "LEFT",
            ord("d"): "RIGHT",
            ord("z"): "B",
            ord("x"): "A",
            32: "START",
            13: "SELECT",
        }

        try:
            while True:
                frame = self.render_dual_pane()
                cv2.imshow(win_name, frame)

                key = cv2.waitKey(20) & 0xFF

                if key == 255:
                    # Idle tick
                    self.env.step(np.zeros(len(self.buttons), dtype=np.int8))
                    continue

                if key in (ord("q"), 27):
                    print("\n[MANUAL] Quitting session...")
                    break
                elif key == ord("c"):
                    self.use_clamp = not self.use_clamp
                    print(f"[MANUAL] Walkable clamping toggled: {'ON' if self.use_clamp else 'OFF'}")
                elif key == ord("["):
                    self.manual_offset_x -= 1
                    print(f"[MANUAL] Offset X adjusted: {self.manual_offset_x:+d}")
                elif key == ord("]"):
                    self.manual_offset_x += 1
                    print(f"[MANUAL] Offset X adjusted: {self.manual_offset_x:+d}")
                elif key == ord(";"):
                    self.manual_offset_y -= 1
                    print(f"[MANUAL] Offset Y adjusted: {self.manual_offset_y:+d}")
                elif key == ord("'"):
                    self.manual_offset_y += 1
                    print(f"[MANUAL] Offset Y adjusted: {self.manual_offset_y:+d}")
                elif key == ord("r"):
                    self.manual_offset_x = 0
                    self.manual_offset_y = 0
                    print("[MANUAL] Manual offsets reset to (0, 0)")
                elif key == ord("p"):
                    snap_path = evidence_dir / f"live_snap_step_{self.step_count:04d}.png"
                    cv2.imwrite(str(snap_path), frame)
                    print(f"[MANUAL] Snapshot saved to: {snap_path}")
                elif key in action_keys:
                    btn = action_keys[key]
                    self.step_action(btn, frames=16)

                if max_steps is not None and self.step_count >= max_steps:
                    print(f"\n[MANUAL] Reached max steps ({max_steps}), exiting...")
                    break

        except KeyboardInterrupt:
            print("\n[MANUAL] Interrupted by user.")
        finally:
            cv2.destroyAllWindows()
            self.env.close()

            if save_path:
                save_path = Path(save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, "w") as f:
                    json.dump(self.trajectory, f, indent=2)
                print(f"[MANUAL] Saved {len(self.trajectory)} trajectory steps to {save_path}")

    def replay_trajectory(self, traj_path: Path):
        traj_path = Path(traj_path)
        if not traj_path.exists():
            print(f"[REPLAY] Trajectory file not found: {traj_path}")
            return
        with open(traj_path) as f:
            traj_data = json.load(f)
        total_steps = len(traj_data)
        print(f"\n[REPLAY] Loaded {total_steps} trajectory steps from {traj_path}")
        print(" Controls:")
        print("   A / Left Arrow  : Previous step")
        print("   D / Right Arrow : Next step")
        print("   Space           : Toggle auto-play")
        print("   C               : Toggle walkable clamp")
        print("   P               : Save snapshot")
        print("   Q / ESC         : Quit replay\n")

        win_name = "Pokemon FireRed: Live Swarm Visualizer Replay & Verification"
        cv2.namedWindow(win_name, cv2.WINDOW_AUTOSIZE)
        evidence_dir = PROJECT_ROOT / "visual_evidence" / "manual_verification"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        step_idx = 0
        auto_play = False

        try:
            while True:
                mb, mn, lx, ly = traj_data[step_idx]
                raw_x, raw_y = lx + 7, ly + 7
                self.trajectory = traj_data[:step_idx + 1]

                cx = lx + self.manual_offset_x
                cy = ly + self.manual_offset_y
                px, py = self.mapper.to_global_pixel_coords(mb, mn, cx, cy, clamp=self.use_clamp)
                tx, ty = px // 16, py // 16

                # Render Left Pane: Replay Telemetry HUD (480x480)
                left_pane = np.zeros((480, 480, 3), dtype=np.uint8)
                landmark = self.mapper.get_landmark_name(mb, mn)
                clamp_str = "ON (Strict Corridor)" if self.use_clamp else "OFF (Authentic RAM Physics)"
                ox, oy = self.mapper.CANONICAL_OFFSETS.get((mb, mn), (60, 260))

                is_border = ((mb, mn) == (3, 0) and ly <= 1) or ((mb, mn) == (3, 19) and ly >= 38)
                status_str = "BORDER: Pallet <-> Route 1 (Seamless 1:1)" if is_border else f"ADJ: ({self.manual_offset_x:+d}, {self.manual_offset_y:+d}) | R=Reset"

                cv2.putText(left_pane, "TRAJECTORY REPLAY & ALIGNMENT INSPECTOR", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
                cv2.putText(left_pane, f"PROGRESS: Step {step_idx + 1:04d} / {total_steps:04d} [{'AUTO' if auto_play else 'PAUSED'}]", (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1)
                cv2.putText(left_pane, f"MAP: ({mb}, {mn}) - {landmark}", (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (50, 230, 100), 1)
                cv2.putText(left_pane, f"CANONICAL OFFSET: ({ox}, {oy})", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (100, 200, 255), 1)
                cv2.putText(left_pane, f"RAM: Raw=({raw_x}, {raw_y}) | Layout=({lx}, {ly})", (10, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 200), 1)
                cv2.putText(left_pane, f"GLOBAL CANVAS: px=({px}, {py}) | TILE=({tx}, {ty})", (10, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 180, 50), 1)
                cv2.putText(left_pane, f"STATUS: {status_str}", (10, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 255), 1)
                cv2.putText(left_pane, f"CLAMP: {clamp_str}", (10, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 255, 150), 1)

                cv2.line(left_pane, (10, 305), (470, 305), (80, 80, 80), 1)
                cv2.putText(left_pane, "CONTROLS:", (10, 335), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 220, 255), 1)
                cv2.putText(left_pane, "  A / D   : Step Backward / Forward", (10, 365), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)
                cv2.putText(left_pane, "  Space   : Toggle Auto-Play", (10, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)
                cv2.putText(left_pane, "  C       : Toggle Clamping", (10, 415), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)
                cv2.putText(left_pane, "  P       : Save Snapshot | Q : Quit", (10, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)

                # Render Right Pane: Live Swarm Visualizer Camera
                vw, vh = 480, 480
                x1 = max(0, min(self.map_w - vw, px + 8 - vw // 2))
                y1 = max(0, min(self.map_h - vh, py + 8 - vh // 2))
                map_crop = self.composite_img.crop((x1, y1, x1 + vw, y1 + vh)).copy()
                draw = ImageDraw.Draw(map_crop)

                for tb, tn, tx_b, ty_b in self.trajectory[max(0, step_idx - 40):step_idx]:
                    t_px, t_py = self.mapper.to_global_pixel_coords(tb, tn, tx_b, ty_b, clamp=self.use_clamp)
                    sx = t_px + 8 - x1
                    sy = t_py + 8 - y1
                    if 0 <= sx < vw and 0 <= sy < vh:
                        draw.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(0, 230, 255, 180))

                sx = px - x1
                sy = py - 16 - y1
                if -16 <= sx < vw and -32 <= sy < vh:
                    map_crop.paste(self.avatar_crop, (int(sx), int(sy)), self.avatar_crop)

                draw.rectangle([sx, py - y1, sx + 16, py - y1 + 16], outline=(255, 255, 0, 255), width=2)
                right_pane = cv2.cvtColor(np.array(map_crop), cv2.COLOR_RGBA2BGR)
                cv2.putText(right_pane, f"CANVAS POS: ({px}, {py}) | TILE: ({tx}, {ty})", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 255), 1)
                cv2.putText(right_pane, "SWARM VISUALIZER 1:1 MAP TRACKER", (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

                combined = np.hstack([left_pane, right_pane])
                cv2.imshow(win_name, combined)

                wait_time = 100 if auto_play else 0
                key = cv2.waitKey(wait_time) & 0xFF

                if key in (ord("q"), 27):
                    break
                elif key == 32:  # Space
                    auto_play = not auto_play
                elif key in (ord("d"), 83):  # D or Right Arrow
                    step_idx = min(total_steps - 1, step_idx + 1)
                elif key in (ord("a"), 81):  # A or Left Arrow
                    step_idx = max(0, step_idx - 1)
                elif key == ord("c"):
                    self.use_clamp = not self.use_clamp
                elif key == ord("r"):
                    self.manual_offset_x = 0
                    self.manual_offset_y = 0
                elif key == ord("p"):
                    snap_path = evidence_dir / f"replay_snap_step_{step_idx + 1:04d}.png"
                    cv2.imwrite(str(snap_path), combined)
                    print(f"[REPLAY] Snapshot saved to: {snap_path}")

                if auto_play:
                    if step_idx < total_steps - 1:
                        step_idx += 1
                    else:
                        auto_play = False
        finally:
            cv2.destroyAllWindows()
            self.env.close()


def run_standard_manual(render_mode: str = "human", max_steps: int = None, state: str = "BeginningPalletGotPokeballs"):
    """Standard console / GBA window interactive manual control loop."""
    print("\n" + "=" * 50)
    print(" Pokemon FireRed - Manual Console Control Mode")
    print("=" * 50)
    print("Controls:")
    print("  W A S D : Movement (UP, LEFT, DOWN, RIGHT)")
    print("  Z       : B button")
    print("  X       : A button")
    print("  Q       : Quit\n")

    register_custom_integrations()

    r_mode = "human" if render_mode == "gba" else None
    base_env = retro.make(
        ENV_NAME,
        state=state,
        render_mode=r_mode,
        inttype=retro.data.Integrations.ALL,
    )
    env = CustomRewardEnv(base_env, env_id=0, exploration_mode="NONE")
    env = ActionFilterWrapper(env)

    obs, info = env.reset()
    step_num = 0

    print("Game started. Press keys inside this console to send actions.")

    with KeyboardInput() as kbd:
        try:
            while True:
                key = kbd.get_key()
                if key == "q":
                    print("\nQuitting manual mode...")
                    break

                action = key_to_action(key)
                obs, reward, terminated, truncated, info = env.step(action)
                step_num += 1

                if max_steps is not None and step_num >= max_steps:
                    print(f"\nReached max steps ({max_steps}), exiting...")
                    break

                if reward != 0:
                    print(f"[MANUAL] Step {step_num} | Reward: {reward:+.2f}")

                if info.get("faints_this_step", 0) > 0:
                    print(f"[MANUAL] Opponent faint detected at step {step_num}!")

                if terminated or truncated:
                    print("[MANUAL] Episode reset triggered.")
                    obs, info = env.reset()

                time.sleep(0.016)

        except KeyboardInterrupt:
            print("\nStopped by user.")
        finally:
            env.close()


def main():
    args = parse_args()

    if args.replay_trajectory:
        verifier = LiveManualVerifier(state=args.state, use_clamp=args.clamp)
        verifier.replay_trajectory(Path(args.replay_trajectory))
    elif args.render_mode == "visualizer":
        verifier = LiveManualVerifier(state=args.state, use_clamp=args.clamp)
        verifier.run(max_steps=args.max_steps, save_path=Path(args.save_trajectory))
    else:
        run_standard_manual(render_mode=args.render_mode, max_steps=args.max_steps, state=args.state)


if __name__ == "__main__":
    main()
