"""
Background Emulator Worker Thread for PySide6.
Handles live Retro environment stepping, manual keyboard input, trajectory replay,
and 1:1 composite map camera tracking without blocking the Qt GUI thread.
"""
from pathlib import Path
from queue import Queue, Empty
import time
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageDraw
from PySide6.QtCore import QThread, Signal

from pokefirered.env_factory import register_custom_integrations
from pokefirered.visualization import KantoWorldMapper
import retro
import retro.data

from pokefirered.paths import get_project_root

PROJECT_ROOT = get_project_root()


class EmulatorWorker(QThread):
    """
    Background worker thread running Pokemon FireRed GBA emulation.
    Emits 60 FPS video frames, swarm tracker crops, and real-time telemetry.
    """
    sig_frame = Signal(np.ndarray, np.ndarray, dict)  # (gba_screen, swarm_crop, telemetry)
    sig_log = Signal(str)
    sig_status = Signal(str)

    def __init__(
        self,
        state: str = "BeginningPalletGotPokeballs",
        use_clamp: bool = False,
        parent=None
    ):
        super().__init__(parent)
        self.state_name = state
        self.use_clamp = use_clamp
        self._running = False
        self._paused = False

        # Mode: 'manual' (live play) or 'replay' (scrubbing recorded trajectory)
        self.mode = "manual"
        self.action_queue: Queue = Queue()

        # Replay state
        self.replay_trajectory: List[Tuple[int, int, int, int]] = []
        self.replay_idx = 0
        self.replay_auto = False

        # Offsets
        self.manual_offset_x = 0
        self.manual_offset_y = 0

        # Resources
        self.env = None
        self.mapper = KantoWorldMapper(tile_size=16)

        # Composite map
        comp_path = PROJECT_ROOT / "assets" / "pwhiddy" / "kanto_firered_composite_full.png"
        self.comp_img = Image.open(comp_path).convert("RGBA")
        self.map_w, self.map_h = self.comp_img.size

        # Player sprite
        sprite_sheet_path = PROJECT_ROOT / "assets" / "pwhiddy" / "firered_player_sprites.png"
        self.sprite_sheet = Image.open(sprite_sheet_path).convert("RGBA")
        self.avatar_crop = self.sprite_sheet.crop((0, 0, 16, 32))

        self.recorded_trajectory: List[Tuple[int, int, int, int]] = []
        self.step_count = 0
        self.last_action = "IDLE"

    def set_mode_manual(self, state: Optional[str] = None):
        """Switches to live manual play mode."""
        self.mode = "manual"
        if state and state != self.state_name:
            self.state_name = state
            self._reinit_env()

    def set_mode_replay(self, traj_path: Path):
        """Loads trajectory JSON and enters replay mode."""
        import json
        with open(traj_path) as f:
            self.replay_trajectory = json.load(f)
        self.replay_idx = 0
        self.mode = "replay"
        self.replay_auto = False
        self.sig_status.emit(f"Loaded {len(self.replay_trajectory)} trajectory steps for replay.")

    def send_action(self, btn_name: str):
        """Queues an action button press for the emulator."""
        self.action_queue.put(btn_name)

    def set_replay_index(self, idx: int):
        """Jumps directly to a step in replay mode."""
        if self.replay_trajectory:
            self.replay_idx = max(0, min(len(self.replay_trajectory) - 1, idx))

    def toggle_replay_auto(self):
        """Toggles auto-play in replay mode."""
        self.replay_auto = not self.replay_auto

    def reset_offsets(self):
        self.manual_offset_x = 0
        self.manual_offset_y = 0

    def adjust_offsets(self, dx: int, dy: int):
        self.manual_offset_x += dx
        self.manual_offset_y += dy

    def stop(self):
        self._running = False
        self.wait(1000)

    def _reinit_env(self):
        if self.env is not None:
            try:
                self.env.close()
            except Exception:
                pass
        register_custom_integrations()
        self.env = retro.make("PokemonFireRed-GBA", state=self.state_name, inttype=retro.data.Integrations.ALL)
        self.obs = self.env.reset()
        self.buttons = self.env.unwrapped.buttons
        self.recorded_trajectory.clear()
        self.step_count = 0

    def _get_ram_telemetry(self) -> dict:
        ram = self.env.unwrapped.get_ram()
        BASE = 0x02000000
        mb = int(ram[0x02031DBC - BASE])
        mn = int(ram[0x02031DBD - BASE])
        raw_x = int.from_bytes(ram[0x02036E48 - BASE : 0x02036E4A - BASE], "little")
        raw_y = int.from_bytes(ram[0x02036E4A - BASE : 0x02036E4C - BASE], "little")

        lx = max(0, raw_x - 7) if raw_x >= 7 else raw_x
        ly = max(0, raw_y - 7) if raw_y >= 7 else raw_y

        # Badge and HP
        sb1_ptr = int.from_bytes(ram[0x45008:0x4500C], "little") - BASE
        boulder_badge = False
        hp, max_hp = 20, 20
        if 0 <= sb1_ptr < len(ram) - 0x1000:
            badge1 = ram[sb1_ptr + 0xEE0 + 260] & 0x01
            boulder_badge = bool(badge1)

        return {
            "map_bank": mb,
            "map_num": mn,
            "raw_x": raw_x,
            "raw_y": raw_y,
            "layout_x": lx,
            "layout_y": ly,
            "boulder_badge": boulder_badge,
            "landmark": self.mapper.get_landmark_name(mb, mn),
        }

    def _render_swarm_crop(self, mb: int, mn: int, lx: int, ly: int, traj_history: List) -> Tuple[np.ndarray, dict]:
        cx = lx + self.manual_offset_x
        cy = ly + self.manual_offset_y

        px, py = self.mapper.to_global_pixel_coords(mb, mn, cx, cy, clamp=self.use_clamp)
        tx, ty = px // 16, py // 16

        vw, vh = 480, 480
        x1 = max(0, min(self.map_w - vw, px + 8 - vw // 2))
        y1 = max(0, min(self.map_h - vh, py + 8 - vh // 2))

        map_crop = self.comp_img.crop((x1, y1, x1 + vw, y1 + vh)).copy()
        draw = ImageDraw.Draw(map_crop)

        # Breadcrumbs
        for tb, tn, tx_b, ty_b in traj_history[-40:]:
            t_px, t_py = self.mapper.to_global_pixel_coords(tb, tn, tx_b, ty_b, clamp=self.use_clamp)
            sx = t_px + 8 - x1
            sy = t_py + 8 - y1
            if 0 <= sx < vw and 0 <= sy < vh:
                draw.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(0, 230, 255, 180))

        # Avatar
        sx = px - x1
        sy = py - 16 - y1
        if -16 <= sx < vw and -32 <= sy < vh:
            map_crop.paste(self.avatar_crop, (int(sx), int(sy)), self.avatar_crop)

        # Yellow tile boundary
        draw.rectangle([sx, py - y1, sx + 16, py - y1 + 16], outline=(255, 255, 0, 255), width=2)

        crop_arr = cv2.cvtColor(np.array(map_crop), cv2.COLOR_RGBA2BGR)
        return crop_arr, {"px": px, "py": py, "tx": tx, "ty": ty}

    def run(self):
        self._running = True
        self._reinit_env()
        self.sig_status.emit("GBA Emulator & Swarm Tracker Online.")

        last_tick = time.time()

        while self._running:
            now = time.time()
            elapsed = now - last_tick
            if elapsed < 0.016:
                time.sleep(0.002)
                continue
            last_tick = now

            if self.mode == "manual":
                # Check for queued action
                btn = "IDLE"
                try:
                    btn = self.action_queue.get_nowait()
                except Empty:
                    pass

                act = np.zeros(len(self.buttons), dtype=np.int8)
                if btn != "IDLE" and btn in self.buttons:
                    act[self.buttons.index(btn)] = 1
                    for _ in range(16):
                        self.obs, _, _, _, _ = self.env.step(act)
                    rel = np.zeros(len(self.buttons), dtype=np.int8)
                    for _ in range(2):
                        self.obs, _, _, _, _ = self.env.step(rel)
                    self.step_count += 1
                    self.last_action = btn
                else:
                    self.obs, _, _, _, _ = self.env.step(act)

                telem = self._get_ram_telemetry()
                mb, mn = telem["map_bank"], telem["map_num"]
                lx, ly = telem["layout_x"], telem["layout_y"]
                self.recorded_trajectory.append((mb, mn, lx, ly))

                gba_screen = cv2.cvtColor(self.env.unwrapped.get_screen(), cv2.COLOR_RGB2BGR)
                swarm_crop, pos_info = self._render_swarm_crop(mb, mn, lx, ly, self.recorded_trajectory)
                telem.update(pos_info)
                telem["step_count"] = self.step_count
                telem["last_action"] = self.last_action

                self.sig_frame.emit(gba_screen, swarm_crop, telem)

            elif self.mode == "replay":
                if not self.replay_trajectory:
                    time.sleep(0.05)
                    continue

                if self.replay_auto:
                    self.replay_idx = (self.replay_idx + 1) % len(self.replay_trajectory)
                    time.sleep(0.08)

                mb, mn, lx, ly = self.replay_trajectory[self.replay_idx]
                history = self.replay_trajectory[:self.replay_idx + 1]
                swarm_crop, pos_info = self._render_swarm_crop(mb, mn, lx, ly, history)

                gba_screen = np.zeros((160, 240, 3), dtype=np.uint8)
                telem = {
                    "map_bank": mb,
                    "map_num": mn,
                    "raw_x": lx + 7,
                    "raw_y": ly + 7,
                    "layout_x": lx,
                    "layout_y": ly,
                    "landmark": self.mapper.get_landmark_name(mb, mn),
                    "step_count": self.replay_idx + 1,
                    "total_replay_steps": len(self.replay_trajectory),
                    "last_action": "REPLAY",
                    "boulder_badge": False,
                }
                telem.update(pos_info)
                self.sig_frame.emit(gba_screen, swarm_crop, telem)

        if self.env is not None:
            self.env.close()
