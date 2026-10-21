"""
Play & Calibrate View:
Provides interactive manual controls (Virtual D-pad & keyboard listeners),
trajectory scrubbing/playback, offset calibration tools, and verification snapshots.
"""
from pathlib import Path
from typing import Optional
import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QSlider,
    QFileDialog,
    QGroupBox,
    QSpinBox,
)

from ..widgets.screen_widget import ScreenWidget

from pokefirered.paths import get_project_root

PROJECT_ROOT = get_project_root()


class PlayView(QWidget):
    """
    Play & Verification view for live game testing and trajectory analysis.
    """
    sig_action = Signal(str)
    sig_load_trajectory = Signal(Path)
    sig_scrub_replay = Signal(int)
    sig_toggle_replay_auto = Signal()
    sig_adjust_offset = Signal(int, int)
    sig_reset_offset = Signal()
    sig_snapshot_taken = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Left Column: GBA & Swarm screens
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)

        viewports = QHBoxLayout()
        viewports.setSpacing(12)

        # GBA
        gba_box = QFrame()
        gba_box.setObjectName("Card")
        gba_vbox = QVBoxLayout(gba_box)
        gba_vbox.setContentsMargins(8, 8, 8, 8)
        lbl_gba = QLabel("🎮 Live Screen")
        lbl_gba.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 11px;")
        gba_vbox.addWidget(lbl_gba)
        self.gba_screen = ScreenWidget()
        gba_vbox.addWidget(self.gba_screen, stretch=1)
        viewports.addWidget(gba_box, stretch=1)

        # Swarm
        swarm_box = QFrame()
        swarm_box.setObjectName("Card")
        swarm_vbox = QVBoxLayout(swarm_box)
        swarm_vbox.setContentsMargins(8, 8, 8, 8)
        lbl_swarm = QLabel("🗺️ 1:1 Map Tracker")
        lbl_swarm.setStyleSheet("color: #38bdf8; font-weight: 600; font-size: 11px;")
        swarm_vbox.addWidget(lbl_swarm)
        self.swarm_screen = ScreenWidget()
        swarm_vbox.addWidget(self.swarm_screen, stretch=1)
        viewports.addWidget(swarm_box, stretch=1)

        left_layout.addLayout(viewports, stretch=1)

        # Replay Scrubber Bar
        replay_box = QFrame()
        replay_box.setObjectName("Card")
        replay_vbox = QVBoxLayout(replay_box)
        replay_vbox.setContentsMargins(12, 10, 12, 10)

        replay_head = QHBoxLayout()
        self.lbl_replay_mode = QLabel("Trajectory Playback:")
        self.lbl_replay_mode.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 12px;")
        replay_head.addWidget(self.lbl_replay_mode)

        self.btn_load_traj = QPushButton("📂 Load Trajectory JSON")
        self.btn_load_traj.clicked.connect(self._on_load_trajectory_clicked)
        replay_head.addWidget(self.btn_load_traj)

        self.btn_auto_play = QPushButton("▶ Auto Play")
        self.btn_auto_play.clicked.connect(self._on_toggle_auto_play)
        replay_head.addWidget(self.btn_auto_play)

        self.lbl_step_info = QLabel("Step: 0 / 0")
        self.lbl_step_info.setStyleSheet("color: #38bdf8; font-weight: 600; font-size: 12px;")
        replay_head.addWidget(self.lbl_step_info)

        replay_vbox.addLayout(replay_head)

        self.slider_scrubber = QSlider(Qt.Horizontal)
        self.slider_scrubber.setMinimum(0)
        self.slider_scrubber.setMaximum(0)
        self.slider_scrubber.valueChanged.connect(self._on_slider_scrubbed)
        replay_vbox.addWidget(self.slider_scrubber)

        left_layout.addWidget(replay_box)
        main_layout.addLayout(left_layout, stretch=2)

        # Right Column: Controls, Calibrate, and Snapshot
        right_panel = QFrame()
        right_panel.setObjectName("Card")
        right_panel.setFixedWidth(300)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(14)

        # 1. Virtual D-Pad
        dpad_group = QGroupBox("🎮 Virtual Controls (WASD / Arrows)")
        dpad_layout = QGridLayout(dpad_group)
        dpad_layout.setSpacing(6)

        btn_up = QPushButton("▲")
        btn_up.setObjectName("DpadBtn")
        btn_up.clicked.connect(lambda: self.sig_action.emit("UP"))

        btn_down = QPushButton("▼")
        btn_down.setObjectName("DpadBtn")
        btn_down.clicked.connect(lambda: self.sig_action.emit("DOWN"))

        btn_left = QPushButton("◀")
        btn_left.setObjectName("DpadBtn")
        btn_left.clicked.connect(lambda: self.sig_action.emit("LEFT"))

        btn_right = QPushButton("▶")
        btn_right.setObjectName("DpadBtn")
        btn_right.clicked.connect(lambda: self.sig_action.emit("RIGHT"))

        btn_a = QPushButton("A (Z)")
        btn_a.setObjectName("ActionBtn")
        btn_a.setStyleSheet("background-color: #0284c7; font-weight: 700;")
        btn_a.clicked.connect(lambda: self.sig_action.emit("A"))

        btn_b = QPushButton("B (X)")
        btn_b.setObjectName("ActionBtn")
        btn_b.setStyleSheet("background-color: #b91c1c; font-weight: 700;")
        btn_b.clicked.connect(lambda: self.sig_action.emit("B"))

        btn_start = QPushButton("START")
        btn_start.clicked.connect(lambda: self.sig_action.emit("START"))

        btn_select = QPushButton("SELECT")
        btn_select.clicked.connect(lambda: self.sig_action.emit("SELECT"))

        dpad_layout.addWidget(btn_up, 0, 1)
        dpad_layout.addWidget(btn_left, 1, 0)
        dpad_layout.addWidget(btn_right, 1, 2)
        dpad_layout.addWidget(btn_down, 2, 1)

        dpad_layout.addWidget(btn_b, 0, 3)
        dpad_layout.addWidget(btn_a, 1, 3)
        dpad_layout.addWidget(btn_select, 2, 0)
        dpad_layout.addWidget(btn_start, 2, 2)

        right_layout.addWidget(dpad_group)

        # 2. Offset Calibration Group
        calib_group = QGroupBox("🎯 Offset Calibration (±1 Tile)")
        calib_layout = QGridLayout(calib_group)
        calib_layout.setSpacing(6)

        self.lbl_calib_status = QLabel("Offset: dx=0, dy=0")
        self.lbl_calib_status.setStyleSheet("color: #a855f7; font-weight: 600; font-size: 11px;")
        calib_layout.addWidget(self.lbl_calib_status, 0, 0, 1, 2)

        btn_cal_up = QPushButton("Y - 1")
        btn_cal_up.clicked.connect(lambda: self._adjust_offset(0, -1))
        btn_cal_down = QPushButton("Y + 1")
        btn_cal_down.clicked.connect(lambda: self._adjust_offset(0, 1))
        btn_cal_left = QPushButton("X - 1")
        btn_cal_left.clicked.connect(lambda: self._adjust_offset(-1, 0))
        btn_cal_right = QPushButton("X + 1")
        btn_cal_right.clicked.connect(lambda: self._adjust_offset(1, 0))
        btn_cal_reset = QPushButton("Reset Offsets")
        btn_cal_reset.clicked.connect(self._reset_offset)

        calib_layout.addWidget(btn_cal_up, 1, 1)
        calib_layout.addWidget(btn_cal_left, 2, 0)
        calib_layout.addWidget(btn_cal_right, 2, 1)
        calib_layout.addWidget(btn_cal_down, 3, 1)
        calib_layout.addWidget(btn_cal_reset, 4, 0, 1, 2)

        right_layout.addWidget(calib_group)

        # 3. Verification Snapshot
        snap_group = QGroupBox("📸 Verification Snapshot")
        snap_layout = QVBoxLayout(snap_group)

        self.btn_snapshot = QPushButton("📷 Capture Verified Step")
        self.btn_snapshot.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                font-weight: 700;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #10b981;
            }
        """)
        self.btn_snapshot.clicked.connect(self._on_snapshot_clicked)
        snap_layout.addWidget(self.btn_snapshot)

        self.lbl_snap_result = QLabel("Ready for capture.")
        self.lbl_snap_result.setWordWrap(True)
        self.lbl_snap_result.setStyleSheet("color: #94a3b8; font-size: 11px;")
        snap_layout.addWidget(self.lbl_snap_result)

        right_layout.addWidget(snap_group)
        right_layout.addStretch(1)

        main_layout.addWidget(right_panel)

        self.last_gba_frame: Optional[np.ndarray] = None
        self.last_swarm_frame: Optional[np.ndarray] = None
        self.last_telem: dict = {}
        self.curr_dx = 0
        self.curr_dy = 0

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key_Up, Qt.Key_W):
            self.sig_action.emit("UP")
        elif key in (Qt.Key_Down, Qt.Key_S):
            self.sig_action.emit("DOWN")
        elif key in (Qt.Key_Left, Qt.Key_A):
            self.sig_action.emit("LEFT")
        elif key in (Qt.Key_Right, Qt.Key_D):
            self.sig_action.emit("RIGHT")
        elif key == Qt.Key_Z:
            self.sig_action.emit("A")
        elif key == Qt.Key_X:
            self.sig_action.emit("B")
        elif key == Qt.Key_Return:
            self.sig_action.emit("START")
        elif key == Qt.Key_Shift:
            self.sig_action.emit("SELECT")
        else:
            super().keyPressEvent(event)

    def update_frame(self, gba_img: np.ndarray, swarm_img: np.ndarray, telem: dict):
        self.last_gba_frame = gba_img
        self.last_swarm_frame = swarm_img
        self.last_telem = telem

        self.gba_screen.update_frame(gba_img)
        self.swarm_screen.update_frame(swarm_img)

        # If in replay mode, update slider
        if "total_replay_steps" in telem:
            total = telem["total_replay_steps"]
            curr = telem.get("step_count", 0)
            self.slider_scrubber.blockSignals(True)
            self.slider_scrubber.setMaximum(total)
            self.slider_scrubber.setValue(curr)
            self.slider_scrubber.blockSignals(False)
            self.lbl_step_info.setText(f"Step: {curr} / {total}")

    def _on_load_trajectory_clicked(self):
        checkpoints_dir = PROJECT_ROOT / "checkpoints"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Trajectory JSON",
            str(checkpoints_dir),
            "Trajectory Files (*.json)"
        )
        if file_path:
            p = Path(file_path)
            self.sig_load_trajectory.emit(p)
            self.lbl_replay_mode.setText(f"Replay: {p.name}")

    def _on_toggle_auto_play(self):
        self.sig_toggle_replay_auto.emit()
        if self.btn_auto_play.text().startswith("▶"):
            self.btn_auto_play.setText("⏸ Pause")
        else:
            self.btn_auto_play.setText("▶ Auto Play")

    def _on_slider_scrubbed(self, val: int):
        self.sig_scrub_replay.emit(val)

    def _adjust_offset(self, dx: int, dy: int):
        self.curr_dx += dx
        self.curr_dy += dy
        self.lbl_calib_status.setText(f"Offset: dx={self.curr_dx}, dy={self.curr_dy}")
        self.sig_adjust_offset.emit(dx, dy)

    def _reset_offset(self):
        self.curr_dx = 0
        self.curr_dy = 0
        self.lbl_calib_status.setText("Offset: dx=0, dy=0")
        self.sig_reset_offset.emit()

    def _on_snapshot_clicked(self):
        if self.last_gba_frame is None or self.last_swarm_frame is None:
            return

        out_dir = PROJECT_ROOT / "visual_evidence" / "manual_verification"
        out_dir.mkdir(parents=True, exist_ok=True)
        step = self.last_telem.get("step_count", 0)
        out_path = out_dir / f"verified_gui_step_{step:04d}.png"

        # Side by side sidecar comparison
        gba_resized = cv2.resize(self.last_gba_frame, (480, 320), interpolation=cv2.INTER_NEAREST)
        swarm_resized = cv2.resize(self.last_swarm_frame, (480, 480))

        # Pad GBA to 480 height
        pad_top = (480 - 320) // 2
        gba_padded = cv2.copyMakeBorder(gba_resized, pad_top, 480 - 320 - pad_top, 0, 0, cv2.BORDER_CONSTANT, value=[10, 15, 25])

        combined = np.hstack([gba_padded, swarm_resized])
        cv2.imwrite(str(out_path), combined)

        self.lbl_snap_result.setText(f"Saved: {out_path.name}")
        self.sig_snapshot_taken.emit(str(out_path))
