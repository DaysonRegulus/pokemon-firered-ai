"""
Interactive Manual Control & Live Swarm Visualizer Verifier for Pokemon FireRed.
Enables real-time gameplay via OpenCV window with simultaneous side-by-side live map tracking:
  - Left Pane: Authentic GBA Game Screen with Real-Time Coordinate Telemetry HUD
  - Right Pane: Live Swarm Visualizer Camera tracking the player on kanto_firered_composite_full.png
Allows real-time verification of tile coordinates, map offsets, and clamping behavior.
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
from pokefirered.visualization import KantoWorldMapper, SwarmRenderer
import retro


def parse_args():
    parser = argparse.ArgumentParser(description="Manual Swarm Visualizer Verifier")
    parser.add_argument("--state", type=str, default="BeginningPalletGotPokeballs", help="Starting save state (default: BeginningPalletGotPokeballs)")
    parser.add_argument("--clamp", action="store_true", help="Enable strict corridor clamping (default: False for authentic GBA physics)")
    parser.add_argument("--save-trajectory", type=str, default="visual_evidence/manual_verification_trajectory.json", help="Trajectory save path")
    return parser.parse_args()


class LiveManualVerifier:
    def __init__(self, state: str = "BeginningPalletGotPokeballs", use_clamp: bool = False):
        register_custom_integrations()
        self.env = retro.make(
            game="PokemonFireRed-GBA",
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
        self.avatar_crop = self.sprite_sheet.crop((0, 0, 16, 32)) # Down standing frame

        self.trajectory: List[Tuple[int, int, int, int]] = []
        self.step_count = 0
        self.last_action_name = "NONE"
        self.manual_offset_x = 0
        self.manual_offset_y = 0

        # Action keybindings
        self.action_keys = {
            ord("w"): "UP",
            ord("s"): "DOWN",
            ord("a"): "LEFT",
            ord("d"): "RIGHT",
            ord("z"): "B",
            ord("x"): "A",
            32: "START",       # Space
            13: "SELECT",      # Enter
        }

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
        # 2 frames release so key inputs are cleanly registered
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

        # Clamping vs Raw
        if self.use_clamp:
            cx, cy = self.mapper.clamp_to_walkable(mb, mn, lx, ly, strict_corridor=True)
        else:
            cx, cy = lx, ly

        cx += self.manual_offset_x
        cy += self.manual_offset_y

        # 1. Left Pane: Game Boy Advance Screen (240x160 -> 480x480 with HUD)
        gba_screen = self.env.unwrapped.get_screen() # (160, 240, 3) RGB
        gba_large = cv2.resize(cv2.cvtColor(gba_screen, cv2.COLOR_RGB2BGR), (480, 320), interpolation=cv2.INTER_NEAREST)

        # Bottom HUD on Left Pane
        hud_pane = np.zeros((160, 480, 3), dtype=np.uint8)
        landmark = self.mapper.get_landmark_name(mb, mn)
        clamp_str = "ON (Strict Corridor)" if self.use_clamp else "OFF (Authentic RAM Physics)"

        cv2.putText(hud_pane, f"STEP: {self.step_count:04d} | ACTION: {self.last_action_name}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
        cv2.putText(hud_pane, f"MAP: ({mb}, {mn}) - {landmark}", (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (50, 230, 100), 1)
        cv2.putText(hud_pane, f"RAW RAM POS: X={raw_x:2d}, Y={raw_y:2d}", (10, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (200, 200, 200), 1)
        cv2.putText(hud_pane, f"LAYOUT POS : X={lx:2d}, Y={ly:2d} (raw - 7)", (10, 96), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 180, 50), 1)
        cv2.putText(hud_pane, f"CLAMP MODE : {clamp_str} | ADJ: ({self.manual_offset_x:+d}, {self.manual_offset_y:+d})", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (180, 180, 255), 1)
        cv2.putText(hud_pane, "KEYS: W/A/S/D=Move | Z=B | X=A | C=Clamp | P=Snap | Q=Quit", (10, 144), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (140, 140, 140), 1)

        left_pane = np.vstack([gba_large, hud_pane])

        # 2. Right Pane: Live Swarm Visualizer Camera (480x480)
        px, py = self.mapper.to_global_pixel_coords(mb, mn, cx, cy, clamp=self.use_clamp)

        # Center 480x480 viewport around player's canvas position
        vw, vh = 480, 480
        x1 = max(0, min(self.map_w - vw, px + 8 - vw // 2))
        y1 = max(0, min(self.map_h - vh, py + 8 - vh // 2))
        x2 = x1 + vw
        y2 = y1 + vh

        map_crop = self.composite_img.crop((x1, y1, x2, y2)).copy()
        draw = ImageDraw.Draw(map_crop)

        # Draw trajectory breadcrumbs (last 40 steps)
        for t_idx, (tb, tn, tx, ty) in enumerate(self.trajectory[-40:]):
            if self.use_clamp:
                tcx, tcy = self.mapper.clamp_to_walkable(tb, tn, tx, ty, strict_corridor=True)
            else:
                tcx, tcy = tx, ty
            tcx += self.manual_offset_x
            tcy += self.manual_offset_y
            t_px, t_py = self.mapper.to_global_pixel_coords(tb, tn, tcx, tcy, clamp=self.use_clamp)
            sx = t_px + 8 - x1
            sy = t_py + 8 - y1
            if 0 <= sx < vw and 0 <= sy < vh:
                draw.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(0, 230, 255, 180))

        # Paste player avatar sprite (16x32, feet inside tile)
        sx = px - x1
        sy = py - 16 - y1
        if -16 <= sx < vw and -32 <= sy < vh:
            map_crop.paste(self.avatar_crop, (int(sx), int(sy)), self.avatar_crop)

        # Overlay tile boundary box on player's current tile
        tx_box = px - x1
        ty_box = py - y1
        draw.rectangle([tx_box, ty_box, tx_box + 16, ty_box + 16], outline=(255, 255, 0, 255), width=1)

        # Convert to BGR for OpenCV
        right_pane = cv2.cvtColor(np.array(map_crop), cv2.COLOR_RGBA2BGR)
        cv2.putText(right_pane, f"CANVAS POS: ({px}, {py})", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
        cv2.putText(right_pane, "SWARM VISUALIZER LIVE MAP TRACKER", (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        # Combine side-by-side
        combined = np.hstack([left_pane, right_pane])
        return combined

    def run(self, save_path: Path):
        print("\n" + "=" * 70)
        print(" POKEMON FIRERED: LIVE MANUAL SWARM ALIGNMENT VERIFIER")
        print(" Controls:")
        print("   W / A / S / D  : Move UP / LEFT / DOWN / RIGHT")
        print("   Z              : B Button (Run / Cancel)")
        print("   X              : A Button (Interact / Confirm)")
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

        try:
            while True:
                # Render dual pane frame
                frame = self.render_dual_pane()
                cv2.imshow(win_name, frame)

                key = cv2.waitKey(20) & 0xFF

                if key == 255:
                    # Idle: step 1 frame with no button pressed so game animation / clock ticks
                    self.env.step(np.zeros(len(self.buttons), dtype=np.int8))
                    continue

                if key in (ord("q"), 27): # 'q' or ESC
                    print("\n[VERIFIER] Quitting manual session...")
                    break
                elif key == ord("c"):
                    self.use_clamp = not self.use_clamp
                    print(f"[VERIFIER] Walkable clamping toggled: {'ON' if self.use_clamp else 'OFF'}")
                elif key == ord("["):
                    self.manual_offset_x -= 1
                    print(f"[VERIFIER] Manual offset X: {self.manual_offset_x}")
                elif key == ord("]"):
                    self.manual_offset_x += 1
                    print(f"[VERIFIER] Manual offset X: {self.manual_offset_x}")
                elif key == ord(";"):
                    self.manual_offset_y -= 1
                    print(f"[VERIFIER] Manual offset Y: {self.manual_offset_y}")
                elif key == ord("'"):
                    self.manual_offset_y += 1
                    print(f"[VERIFIER] Manual offset Y: {self.manual_offset_y}")
                elif key == ord("p"):
                    snap_path = evidence_dir / f"manual_snap_step_{self.step_count:04d}.png"
                    cv2.imwrite(str(snap_path), frame)
                    print(f"[VERIFIER] Saved snapshot: {snap_path}")
                elif key in self.action_keys:
                    action_name = self.action_keys[key]
                    if action_name in ["UP", "DOWN", "LEFT", "RIGHT"]:
                        self.step_action(action_name, frames=16)
                    else:
                        self.step_action(action_name, frames=8)

        finally:
            cv2.destroyAllWindows()
            self.env.close()

            # Save full trajectory to JSON
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump([self.trajectory], f)
            print(f"\n[OK] Recorded {len(self.trajectory)} steps to: {save_path}")


def main():
    args = parse_args()
    save_path = PROJECT_ROOT / args.save_trajectory
    verifier = LiveManualVerifier(state=args.state, use_clamp=args.clamp)
    verifier.run(save_path)


if __name__ == "__main__":
    main()
