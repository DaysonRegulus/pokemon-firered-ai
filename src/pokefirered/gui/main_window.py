"""
Main Application Window for PokéRL Studio.
Coordinates sidebar navigation, stacked view containers, and background worker threads.
"""
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QStackedWidget,
    QButtonGroup,
    QStatusBar,
    QMessageBox,
)

from .theme import DARK_THEME_QSS
from .views import (
    DashboardView,
    PlayView,
    TrainView,
    ChartsView,
    SwarmView,
    SettingsView,
)
from .workers import EmulatorWorker, TrainWorker

from pokefirered.paths import get_project_root

PROJECT_ROOT = get_project_root()


class SidebarButton(QPushButton):
    """Custom navigation sidebar button."""
    def __init__(self, text: str, icon_str: str = "", parent=None):
        super().__init__(f"{icon_str}  {text}".strip(), parent)
        self.setCheckable(True)
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                padding-left: 16px;
                border: none;
                border-left: 3px solid transparent;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: #111827;
                color: #f8fafc;
            }
            QPushButton:checked {
                background-color: #0f172a;
                color: #38bdf8;
                border-left: 3px solid #38bdf8;
                font-weight: 700;
            }
        """)


class MainWindow(QMainWindow):
    """
    Main Application Window.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PokéRL Studio — Autonomous Pokémon FireRed RL Suite")
        self.resize(1340, 860)
        self.setMinimumSize(1100, 720)

        # Apply global theme
        self.setStyleSheet(DARK_THEME_QSS)

        # Background Workers
        self.emu_worker: Optional[EmulatorWorker] = None
        self.train_worker: Optional[TrainWorker] = None

        # Build UI
        self._init_ui()

        # Start Emulator Worker
        self._start_emulator()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("""
            #Sidebar {
                background-color: #070a12;
                border-right: 1px solid #1e293b;
            }
        """)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 16)
        sb_layout.setSpacing(4)

        # App Brand Header
        brand_box = QFrame()
        brand_box.setStyleSheet("background-color: #0b0f19; border-bottom: 1px solid #1e293b;")
        brand_layout = QVBoxLayout(brand_box)
        brand_layout.setContentsMargins(16, 18, 16, 18)
        brand_layout.setSpacing(2)

        lbl_logo = QLabel("⚡ PokéRL Studio")
        lbl_logo.setStyleSheet("color: #38bdf8; font-size: 17px; font-weight: 800; letter-spacing: 0.5px;")
        lbl_sub = QLabel("Autonomous FireRed Engine")
        lbl_sub.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 500;")
        brand_layout.addWidget(lbl_logo)
        brand_layout.addWidget(lbl_sub)
        sb_layout.addWidget(brand_box)

        sb_layout.addSpacing(10)

        # Navigation Buttons
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.btn_dash = SidebarButton("Dashboard", "⚡")
        self.btn_play = SidebarButton("Play & Calibrate", "🎮")
        self.btn_train = SidebarButton("Training Studio", "🚀")
        self.btn_charts = SidebarButton("Analytics & Curves", "📈")
        self.btn_swarm = SidebarButton("Swarm Studio", "🗺️")
        self.btn_settings = SidebarButton("Diagnostics", "⚙️")

        self.nav_buttons = [
            self.btn_dash,
            self.btn_play,
            self.btn_train,
            self.btn_charts,
            self.btn_swarm,
            self.btn_settings,
        ]

        for idx, btn in enumerate(self.nav_buttons):
            self.btn_group.addButton(btn, idx)
            sb_layout.addWidget(btn)
            btn.clicked.connect(self._on_nav_clicked)

        self.btn_dash.setChecked(True)
        sb_layout.addStretch(1)

        # Bottom System Indicator
        status_box = QFrame()
        status_box.setStyleSheet("padding: 12px; margin: 8px; background-color: #0d1322; border-radius: 6px; border: 1px solid #1e293b;")
        status_layout = QVBoxLayout(status_box)
        status_layout.setContentsMargins(4, 4, 4, 4)
        status_layout.setSpacing(4)

        self.lbl_emu_badge = QLabel("● Emulator: Starting...")
        self.lbl_emu_badge.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: 600;")
        self.lbl_train_badge = QLabel("● Training: Idle")
        self.lbl_train_badge.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600;")

        status_layout.addWidget(self.lbl_emu_badge)
        status_layout.addWidget(self.lbl_train_badge)
        sb_layout.addWidget(status_box)

        root_layout.addWidget(sidebar)

        # 2. Main Stacked Views
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #070a13;")

        self.view_dashboard = DashboardView()
        self.view_play = PlayView()
        self.view_train = TrainView()
        self.view_charts = ChartsView()
        self.view_swarm = SwarmView()
        self.view_settings = SettingsView()

        self.stack.addWidget(self.view_dashboard)  # 0
        self.stack.addWidget(self.view_play)       # 1
        self.stack.addWidget(self.view_train)      # 2
        self.stack.addWidget(self.view_charts)     # 3
        self.stack.addWidget(self.view_swarm)      # 4
        self.stack.addWidget(self.view_settings)   # 5

        root_layout.addWidget(self.stack, stretch=1)

        # 3. Connect View Signals
        self._wire_signals()

    def _wire_signals(self):
        # Play View actions
        self.view_play.sig_action.connect(self._on_user_action)
        self.view_play.sig_adjust_offset.connect(self._on_adjust_offset)
        self.view_play.sig_reset_offset.connect(self._on_reset_offset)
        self.view_play.sig_load_trajectory.connect(self._on_load_trajectory)
        self.view_play.sig_scrub_replay.connect(self._on_scrub_replay)
        self.view_play.sig_toggle_replay_auto.connect(self._on_toggle_replay_auto)

        # Dashboard View actions
        self.view_dashboard.sig_change_state.connect(self._on_change_state)

        # Training View actions
        self.view_train.sig_start_train.connect(self._on_start_training)
        self.view_train.sig_stop_train.connect(self._on_stop_training)

    def _start_emulator(self):
        self.emu_worker = EmulatorWorker(parent=self)
        self.emu_worker.sig_frame.connect(self._on_emu_frame)
        self.emu_worker.sig_status.connect(self._on_emu_status)
        self.emu_worker.start()

    def _on_emu_status(self, status: str):
        self.lbl_emu_badge.setText("● Emulator: Online")
        self.lbl_emu_badge.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 600;")

    def _on_emu_frame(self, gba_img, swarm_img, telem):
        # Route live frame to active view
        curr_idx = self.stack.currentIndex()
        if curr_idx == 0:
            self.view_dashboard.update_frame(gba_img, swarm_img, telem)
        elif curr_idx == 1:
            self.view_play.update_frame(gba_img, swarm_img, telem)

    def _on_nav_clicked(self):
        idx = self.btn_group.checkedId()
        self.stack.setCurrentIndex(idx)
        if idx == 1:
            self.view_play.setFocus()

    def _on_user_action(self, btn_name: str):
        if self.emu_worker:
            self.emu_worker.send_action(btn_name)

    def _on_adjust_offset(self, dx: int, dy: int):
        if self.emu_worker:
            self.emu_worker.adjust_offsets(dx, dy)

    def _on_reset_offset(self):
        if self.emu_worker:
            self.emu_worker.reset_offsets()

    def _on_load_trajectory(self, path: Path):
        if self.emu_worker:
            self.emu_worker.set_mode_replay(path)

    def _on_scrub_replay(self, idx: int):
        if self.emu_worker:
            self.emu_worker.set_replay_index(idx)

    def _on_toggle_replay_auto(self):
        if self.emu_worker:
            self.emu_worker.toggle_replay_auto()

    def _on_change_state(self, state_name: str):
        if self.emu_worker:
            self.emu_worker.set_mode_manual(state_name)

    def _on_start_training(self, cfg: dict):
        self.view_charts.clear_charts()

        self.train_worker = TrainWorker(
            algo=cfg["algo"],
            exploration=cfg["exploration"],
            num_envs=cfg["num_envs"],
            timesteps=cfg["timesteps"],
            device=cfg["device"],
            fresh=cfg["fresh"],
            record_trajectories=cfg["record_trajectories"],
            parent=self,
        )
        self.train_worker.sig_log.connect(self.view_train.handle_log)
        self.train_worker.sig_progress.connect(self.view_train.handle_progress)
        self.train_worker.sig_metrics.connect(self.view_train.handle_metrics)
        self.train_worker.sig_metrics.connect(self.view_charts.update_live_metrics)
        self.train_worker.sig_finished.connect(self.view_train.handle_finished)
        self.train_worker.sig_finished.connect(self._on_training_finished)

        self.lbl_train_badge.setText(f"● Train: {cfg['algo']} ({cfg['exploration']})")
        self.lbl_train_badge.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 600;")

        self.train_worker.start()

    def _on_stop_training(self):
        if self.train_worker:
            self.train_worker.cancel()

    def _on_training_finished(self, exit_code: int, summary: str):
        self.lbl_train_badge.setText("● Training: Idle")
        self.lbl_train_badge.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600;")
        self.view_charts.reload_benchmarks()
        self.view_swarm.scan_trajectories()

    def closeEvent(self, event: QCloseEvent):
        """Clean shutdown of background threads."""
        if self.train_worker and self.train_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Training in Progress",
                "A training run is currently active. Do you wish to terminate it and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self.train_worker.cancel()
            self.train_worker.wait(2000)

        if self.emu_worker and self.emu_worker.isRunning():
            self.emu_worker.stop()

        event.accept()
