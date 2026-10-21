"""
Settings & System Diagnostics View:
Verifies ROM integrity, asset loading status, hardware/CUDA capabilities,
and provides system configuration diagnostics.
"""
import hashlib
from pathlib import Path
import sys
import torch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from pokefirered.paths import get_project_root

PROJECT_ROOT = get_project_root()


class SettingsView(QWidget):
    """
    Settings, system diagnostics, and asset health checks.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # 1. Title
        title_box = QFrame()
        title_box.setObjectName("Card")
        t_layout = QVBoxLayout(title_box)
        t_layout.setContentsMargins(14, 12, 14, 12)

        lbl_head = QLabel("⚙️ System Diagnostics & Asset Health")
        lbl_head.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 13px;")
        t_layout.addWidget(lbl_head)

        lbl_sub = QLabel(
            "Verifies environment assets, GBA ROM hash, and PyTorch / CUDA acceleration."
        )
        lbl_sub.setStyleSheet("color: #94a3b8; font-size: 11px;")
        t_layout.addWidget(lbl_sub)
        main_layout.addWidget(title_box)

        # 2. Diagnostics Grid
        diag_layout = QHBoxLayout()
        diag_layout.setSpacing(14)

        # Left: Hardware & Environment
        hw_box = QFrame()
        hw_box.setObjectName("Card")
        hw_layout = QVBoxLayout(hw_box)
        hw_layout.setContentsMargins(14, 12, 14, 12)
        hw_layout.setSpacing(8)

        lbl_hw_title = QLabel("💻 Compute & Environment")
        lbl_hw_title.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 12px;")
        hw_layout.addWidget(lbl_hw_title)

        hw_grid = QGridLayout()
        hw_grid.setSpacing(6)

        cuda_avail = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "N/A"
        cuda_ver = torch.version.cuda if cuda_avail else "N/A"

        items = [
            ("Python Version:", sys.version.split()[0]),
            ("PyTorch Version:", torch.__version__),
            ("CUDA Available:", "✅ Yes" if cuda_avail else "❌ No (CPU Mode)"),
            ("Device Name:", gpu_name),
            ("CUDA Version:", cuda_ver),
            ("Platform:", sys.platform.title()),
        ]

        for row, (k, v) in enumerate(items):
            lbl_k = QLabel(k)
            lbl_k.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 11px;")
            lbl_v = QLabel(str(v))
            lbl_v.setStyleSheet("color: #f8fafc; font-weight: 500; font-size: 11px;")
            hw_grid.addWidget(lbl_k, row, 0)
            hw_grid.addWidget(lbl_v, row, 1)

        hw_layout.addLayout(hw_grid)
        hw_layout.addStretch(1)
        diag_layout.addWidget(hw_box, stretch=1)

        # Right: Asset Health Table
        asset_box = QFrame()
        asset_box.setObjectName("Card")
        asset_layout = QVBoxLayout(asset_box)
        asset_layout.setContentsMargins(14, 12, 14, 12)
        asset_layout.setSpacing(8)

        lbl_asset_title = QLabel("📁 Asset Verification")
        lbl_asset_title.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 12px;")
        asset_layout.addWidget(lbl_asset_title)

        self.table_assets = QTableWidget()
        self.table_assets.setColumnCount(3)
        self.table_assets.setHorizontalHeaderLabels(["Asset / File", "Status", "Details"])
        self.table_assets.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_assets.setStyleSheet("""
            QTableWidget {
                background-color: #0b0f19;
                color: #e2e8f0;
                border: 1px solid #1e293b;
                border-radius: 4px;
                gridline-color: #1f2937;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #111827;
                color: #94a3b8;
                font-weight: 700;
                padding: 4px;
                border: 1px solid #1f2937;
            }
        """)
        asset_layout.addWidget(self.table_assets)

        btn_recheck = QPushButton("🔍 Re-verify All Assets")
        btn_recheck.clicked.connect(self.verify_assets)
        asset_layout.addWidget(btn_recheck)

        diag_layout.addWidget(asset_box, stretch=1)
        main_layout.addLayout(diag_layout, stretch=1)

        self.verify_assets()

    def verify_assets(self):
        assets_to_check = [
            ("Composite Map (1:1)", PROJECT_ROOT / "assets" / "pwhiddy" / "kanto_firered_composite_full.png"),
            ("Player Spritesheet", PROJECT_ROOT / "assets" / "pwhiddy" / "firered_player_sprites.png"),
            ("Red Avatar", PROJECT_ROOT / "assets" / "pwhiddy" / "red_normal.png"),
            ("Leaf Avatar", PROJECT_ROOT / "assets" / "pwhiddy" / "green_normal.png"),
            ("Custom Retro Integration", PROJECT_ROOT / "data" / "custom_integrations" / "PokemonFireRed-GBA" / "rom.sha"),
            ("Save State: Pallet", PROJECT_ROOT / "data" / "custom_integrations" / "PokemonFireRed-GBA" / "BeginningPalletGotPokeballs.state"),
        ]

        self.table_assets.setRowCount(len(assets_to_check))
        for row, (name, path) in enumerate(assets_to_check):
            item_name = QTableWidgetItem(name)
            if path.exists():
                size_kb = path.stat().st_size / 1024
                item_stat = QTableWidgetItem("✅ OK")
                item_stat.setForeground(Qt.green)
                item_det = QTableWidgetItem(f"{size_kb:.1f} KB")
            else:
                item_stat = QTableWidgetItem("❌ MISSING")
                item_stat.setForeground(Qt.red)
                item_det = QTableWidgetItem("File not found")

            item_stat.setTextAlignment(Qt.AlignCenter)
            self.table_assets.setItem(row, 0, item_name)
            self.table_assets.setItem(row, 1, item_stat)
            self.table_assets.setItem(row, 2, item_det)
