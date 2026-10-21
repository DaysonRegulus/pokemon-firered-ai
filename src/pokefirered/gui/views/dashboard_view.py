"""
Dashboard View: The central mission control for PokéRL Studio.
Features dual live displays (GBA Screen + 1:1 Kanto Swarm Tracker),
dynamic landmark milestone progression bar, and real-time metric cards.
"""
from typing import Dict, Optional
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QComboBox,
    QProgressBar,
    QSizePolicy,
)

from ..widgets.screen_widget import ScreenWidget
from ..widgets.metric_card import MetricCard


class MilestoneBar(QFrame):
    """
    Visual linear pipeline representing player progress from Pallet Town to Pewter Gym.
    """
    STAGES = [
        ("Pallet Town", [(3, 0), (4, 0), (4, 1), (4, 2)]),
        ("Route 1", [(3, 19)]),
        ("Viridian City", [(3, 1), (5, 0), (5, 1), (5, 2)]),
        ("Route 2", [(3, 20)]),
        ("Viridian Forest", [(1, 0)]),
        ("Pewter City", [(3, 2), (6, 0), (6, 1)]),
        ("Brock (Gym)", [(6, 2)]),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MilestoneBar")
        self.setStyleSheet("""
            #MilestoneBar {
                background-color: #0b0f19;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 6px 12px;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self.stage_labels = []
        for i, (name, _) in enumerate(self.STAGES):
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("""
                QLabel {
                    color: #64748b;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 4px 10px;
                    border-radius: 4px;
                    background-color: #111827;
                }
            """)
            layout.addWidget(lbl)
            self.stage_labels.append(lbl)

            if i < len(self.STAGES) - 1:
                arrow = QLabel("➔")
                arrow.setStyleSheet("color: #334155; font-size: 11px; font-weight: bold;")
                layout.addWidget(arrow)

    def update_location(self, map_bank: int, map_num: int, has_badge: bool = False):
        active_idx = -1
        for idx, (_, maps) in enumerate(self.STAGES):
            if (map_bank, map_num) in maps:
                active_idx = idx
                break

        if has_badge:
            active_idx = len(self.STAGES) - 1

        for idx, lbl in enumerate(self.stage_labels):
            if idx < active_idx:
                lbl.setStyleSheet("""
                    QLabel {
                        color: #10b981;
                        font-size: 11px;
                        font-weight: 600;
                        padding: 4px 10px;
                        border-radius: 4px;
                        background-color: #064e3b;
                        border: 1px solid #059669;
                    }
                """)
            elif idx == active_idx:
                lbl.setStyleSheet("""
                    QLabel {
                        color: #38bdf8;
                        font-size: 11px;
                        font-weight: 700;
                        padding: 4px 10px;
                        border-radius: 4px;
                        background-color: #0c4a6e;
                        border: 1px solid #0284c7;
                    }
                """)
            else:
                lbl.setStyleSheet("""
                    QLabel {
                        color: #64748b;
                        font-size: 11px;
                        font-weight: 600;
                        padding: 4px 10px;
                        border-radius: 4px;
                        background-color: #111827;
                    }
                """)


class DashboardView(QWidget):
    """
    Main live monitoring dashboard.
    """
    sig_change_state = Signal(str)
    sig_toggle_pause = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # 1. Top bar: Landmark Progression + Quick Controls
        top_bar = QHBoxLayout()
        self.milestone_bar = MilestoneBar()
        top_bar.addWidget(self.milestone_bar, stretch=1)

        # State selector
        self.state_combo = QComboBox()
        self.state_combo.addItems([
            "BeginningPalletGotPokeballs",
            "ViridianCity",
            "PewterCityEntrance",
        ])
        self.state_combo.currentTextChanged.connect(self.sig_change_state.emit)
        top_bar.addWidget(self.state_combo)

        main_layout.addLayout(top_bar)

        # 2. Dual Viewport Layout (GBA Screen + Swarm Tracker)
        screens_layout = QHBoxLayout()
        screens_layout.setSpacing(14)

        # Left: GBA Screen
        left_box = QFrame()
        left_box.setObjectName("Card")
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_title = QLabel("🎮 GBA Screen (240 × 160)")
        left_title.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 12px;")
        left_layout.addWidget(left_title)

        self.gba_screen = ScreenWidget()
        left_layout.addWidget(self.gba_screen, stretch=1)
        screens_layout.addWidget(left_box, stretch=1)

        # Right: Swarm Map Camera
        right_box = QFrame()
        right_box.setObjectName("Card")
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_title = QLabel("🗺️ 1:1 Kanto Swarm Tracker (480 × 480 Crop)")
        right_title.setStyleSheet("color: #38bdf8; font-weight: 600; font-size: 12px;")
        right_layout.addWidget(right_title)

        self.swarm_screen = ScreenWidget()
        right_layout.addWidget(self.swarm_screen, stretch=1)
        screens_layout.addWidget(right_box, stretch=1)

        main_layout.addLayout(screens_layout, stretch=1)

        # 3. Bottom Row: KPI Metric Cards
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(12)

        self.card_location = MetricCard(
            title="Current Landmark",
            value="Pallet Town",
            subtitle="Map Bank 3 | Num 0",
            icon="📍",
            color_accent="#38bdf8"
        )
        self.card_coords = MetricCard(
            title="Global Coordinates",
            value="X: 68 | Y: 266",
            subtitle="Canvas: 1088, 4256 px",
            icon="🎯",
            color_accent="#a855f7"
        )
        self.card_novelty = MetricCard(
            title="Exploration Novelty",
            value="0 Tiles",
            subtitle="1 Unique Map Visited",
            icon="🧭",
            color_accent="#10b981"
        )
        self.card_badge = MetricCard(
            title="Boulder Badge",
            value="LOCKED",
            subtitle="Pewter City Gym (Brock)",
            icon="🛡️",
            color_accent="#f59e0b"
        )

        metrics_layout.addWidget(self.card_location)
        metrics_layout.addWidget(self.card_coords)
        metrics_layout.addWidget(self.card_novelty)
        metrics_layout.addWidget(self.card_badge)

        main_layout.addLayout(metrics_layout)

    def update_frame(self, gba_img: np.ndarray, swarm_img: np.ndarray, telem: dict):
        """Receives live video frame and telemetry from EmulatorWorker."""
        mb = telem.get("map_bank", 3)
        mn = telem.get("map_num", 0)
        lx = telem.get("layout_x", 0)
        ly = telem.get("layout_y", 0)
        px = telem.get("px", 0)
        py = telem.get("py", 0)
        tx = telem.get("tx", 0)
        ty = telem.get("ty", 0)
        landmark = telem.get("landmark", "Unknown")
        has_badge = telem.get("boulder_badge", False)
        step_cnt = telem.get("step_count", 0)
        last_act = telem.get("last_action", "IDLE")

        # Update screens
        self.gba_screen.update_frame(gba_img)
        self.gba_screen.set_overlay_text(f"Step: {step_cnt:,} | Action: {last_act}")

        self.swarm_screen.update_frame(swarm_img)
        self.swarm_screen.set_overlay_text(f"Global: ({tx}, {ty}) | Local: ({lx}, {ly})")

        # Update milestone progress
        self.milestone_bar.update_location(mb, mn, has_badge)

        # Update metric cards
        self.card_location.set_value(landmark, f"Bank {mb} | Map {mn} (Raw: {telem.get('raw_x',0)}, {telem.get('raw_y',0)})")
        self.card_coords.set_value(f"Tile ({tx}, {ty})", f"Pixels ({px}, {py})")

        if has_badge:
            self.card_badge.set_value("UNLOCKED", "Boulder Badge Acquired! 🏆")
        else:
            self.card_badge.set_value("LOCKED", "Defeat Brock in Pewter Gym")
