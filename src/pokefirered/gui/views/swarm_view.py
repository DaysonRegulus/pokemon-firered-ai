"""
Swarm Studio View:
Generates animated multi-agent swarm videos and GIFs compositing Peter Whidden style
exploring agents onto the 1:1 32-bit GBA FireRed composite map.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QLineEdit,
    QProgressBar,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QGroupBox,
    QMessageBox,
)

from ..widgets.metric_card import MetricCard
from pokefirered.visualization import SwarmRenderer

from pokefirered.paths import get_project_root

PROJECT_ROOT = get_project_root()


class SwarmRenderWorker(QThread):
    """Background thread for rendering swarm video/GIF without freezing the UI."""
    sig_progress = Signal(int, int, str)  # (current_step, total_steps, status_text)
    sig_finished = Signal(str, str)       # (video_path, gif_path)
    sig_error = Signal(str)

    def __init__(
        self,
        traj_data: Dict[int, List],
        video_out: Path,
        gif_out: Optional[Path],
        fps: int = 30,
        custom_title: Optional[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.traj_data = traj_data
        self.video_out = video_out
        self.gif_out = gif_out
        self.fps = fps
        self.custom_title = custom_title

    def run(self):
        try:
            renderer = SwarmRenderer(viewport_w=760, viewport_h=480)
            renderer.render_trajectories_video(
                trajectories_by_gen=self.traj_data,
                output_video_path=self.video_out,
                output_gif_path=self.gif_out,
                fps=self.fps,
                custom_title=self.custom_title,
            )
            self.sig_finished.emit(str(self.video_out), str(self.gif_out) if self.gif_out else "")
        except Exception as e:
            self.sig_error.emit(str(e))


class SwarmView(QWidget):
    """
    Swarm Studio: Multi-agent trajectory video and GIF creator.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.render_worker: Optional[SwarmRenderWorker] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # 1. Header & Source Selector
        top_box = QFrame()
        top_box.setObjectName("Card")
        top_layout = QVBoxLayout(top_box)
        top_layout.setContentsMargins(14, 12, 14, 12)
        top_layout.setSpacing(10)

        head = QHBoxLayout()
        title = QLabel("🗺️ Swarm Studio — Multi-Agent Video & GIF Generator")
        title.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 13px;")
        head.addWidget(title)
        head.addStretch(1)

        btn_refresh = QPushButton("🔄 Refresh Files")
        btn_refresh.clicked.connect(self.scan_trajectories)
        head.addWidget(btn_refresh)
        top_layout.addLayout(head)

        lbl_desc = QLabel(
            "Select one or more agent trajectory JSON recordings to render animated Peter Whidden-style "
            "swarms advancing across the canonical 32-bit GBA FireRed composite map."
        )
        lbl_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        lbl_desc.setWordWrap(True)
        top_layout.addWidget(lbl_desc)

        main_layout.addWidget(top_box)

        # 2. Main content: File list on left, Options on right
        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)

        # Left: Trajectory file list
        files_box = QFrame()
        files_box.setObjectName("Card")
        files_layout = QVBoxLayout(files_box)
        files_layout.setContentsMargins(12, 10, 12, 10)
        files_layout.setSpacing(8)

        lbl_files = QLabel("📁 Available Trajectories (`checkpoints/*_trajectories.json`):")
        lbl_files.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 12px;")
        files_layout.addWidget(lbl_files)

        self.list_trajectories = QListWidget()
        self.list_trajectories.setSelectionMode(QListWidget.MultiSelection)
        self.list_trajectories.setStyleSheet("""
            QListWidget {
                background-color: #0b0f19;
                color: #e2e8f0;
                border: 1px solid #1e293b;
                border-radius: 4px;
                padding: 4px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #0c4a6e;
                color: #38bdf8;
                font-weight: 600;
            }
        """)
        files_layout.addWidget(self.list_trajectories, stretch=1)

        btn_browse = QPushButton("📂 Browse External JSON...")
        btn_browse.clicked.connect(self._on_browse_external)
        files_layout.addWidget(btn_browse)

        content_layout.addWidget(files_box, stretch=1)

        # Right: Render Settings
        opts_box = QFrame()
        opts_box.setObjectName("Card")
        opts_layout = QVBoxLayout(opts_box)
        opts_layout.setContentsMargins(14, 12, 14, 12)
        opts_layout.setSpacing(12)

        opts_title = QLabel("⚙️ Export Settings")
        opts_title.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 12px;")
        opts_layout.addWidget(opts_title)

        grid = QGridLayout()
        grid.setSpacing(10)

        # Framerate
        grid.addWidget(QLabel("Frame Rate (FPS):"), 0, 0)
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["15", "30", "60"])
        self.combo_fps.setCurrentText("30")
        grid.addWidget(self.combo_fps, 0, 1)

        # Title
        grid.addWidget(QLabel("HUD Video Title:"), 1, 0)
        self.txt_title = QLineEdit("POKEMON FIRERED RL SWARM")
        grid.addWidget(self.txt_title, 1, 1)

        # Output filename
        grid.addWidget(QLabel("Output Base Name:"), 2, 0)
        self.txt_outname = QLineEdit("swarm_render")
        grid.addWidget(self.txt_outname, 2, 1)

        opts_layout.addLayout(grid)

        # Formats
        fmt_group = QGroupBox("Target Formats")
        fmt_layout = QVBoxLayout(fmt_group)
        self.chk_mp4 = QCheckBox("Export MP4 Video (H.264 / mp4v)")
        self.chk_mp4.setChecked(True)
        self.chk_gif = QCheckBox("Export Animated GIF (Optimized)")
        self.chk_gif.setChecked(True)
        fmt_layout.addWidget(self.chk_mp4)
        fmt_layout.addWidget(self.chk_gif)
        opts_layout.addWidget(fmt_group)

        # Render Button & Progress
        opts_layout.addStretch(1)

        self.btn_render = QPushButton("🎬 Start Swarm Rendering")
        self.btn_render.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: 700;
                padding: 10px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.btn_render.clicked.connect(self._on_start_render)
        opts_layout.addWidget(self.btn_render)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 4px;
                text-align: center;
                color: #f8fafc;
                font-weight: 600;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: #059669;
                border-radius: 4px;
            }
        """)
        opts_layout.addWidget(self.progress_bar)

        self.lbl_render_status = QLabel("Ready.")
        self.lbl_render_status.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_render_status.setWordWrap(True)
        opts_layout.addWidget(self.lbl_render_status)

        content_layout.addWidget(opts_box, stretch=1)
        main_layout.addLayout(content_layout, stretch=1)

        self.scan_trajectories()

    def scan_trajectories(self):
        """Scans checkpoints folder for trajectory JSON files."""
        self.list_trajectories.clear()
        chk_dir = PROJECT_ROOT / "checkpoints"
        if not chk_dir.exists():
            return

        files = list(chk_dir.glob("*_trajectories.json"))
        for p in files:
            size_mb = p.stat().st_size / (1024 * 1024)
            item = QListWidgetItem(f"{p.name} ({size_mb:.2f} MB)")
            item.setData(Qt.UserRole, str(p))
            self.list_trajectories.addItem(item)

        if self.list_trajectories.count() > 0:
            self.list_trajectories.setCurrentRow(0)

    def _on_browse_external(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Select Trajectory JSON", str(PROJECT_ROOT), "JSON Files (*.json)"
        )
        if f:
            p = Path(f)
            item = QListWidgetItem(f"[Ext] {p.name}")
            item.setData(Qt.UserRole, str(p))
            self.list_trajectories.addItem(item)
            item.setSelected(True)

    def _on_start_render(self):
        selected_items = self.list_trajectories.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Files Selected", "Please select at least one trajectory file from the list.")
            return

        trajectories_by_gen: Dict[int, List] = {}
        for idx, item in enumerate(selected_items):
            file_path = item.data(Qt.UserRole)
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                gen_id = (idx + 1) * 10
                if isinstance(data, list):
                    if len(data) > 0 and isinstance(data[0], list) and isinstance(data[0][0], list):
                        trajectories_by_gen[gen_id] = data
                    else:
                        trajectories_by_gen[gen_id] = [data]
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load {file_path}:\n{e}")
                return

        out_dir = PROJECT_ROOT / "visual_evidence" / "swarm_renders"
        out_dir.mkdir(parents=True, exist_ok=True)
        base_name = self.txt_outname.text().strip() or "swarm_render"

        video_path = out_dir / f"{base_name}.mp4" if self.chk_mp4.isChecked() else out_dir / f"{base_name}_temp.mp4"
        gif_path = out_dir / f"{base_name}.gif" if self.chk_gif.isChecked() else None

        self.btn_render.setEnabled(False)
        self.progress_bar.setRange(0, 0) # Indeterminate spinner
        self.lbl_render_status.setText(f"Rendering {len(selected_items)} run(s) with GBA avatars...")
        self.lbl_render_status.setStyleSheet("color: #38bdf8; font-weight: 600;")

        fps = int(self.combo_fps.currentText())
        title = self.txt_title.text().strip()

        self.render_worker = SwarmRenderWorker(
            traj_data=trajectories_by_gen,
            video_out=video_path,
            gif_out=gif_path,
            fps=fps,
            custom_title=title,
        )
        self.render_worker.sig_finished.connect(self._on_render_finished)
        self.render_worker.sig_error.connect(self._on_render_error)
        self.render_worker.start()

    def _on_render_finished(self, v_path: str, g_path: str):
        self.btn_render.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)

        msg = f"Export Complete! ✓\nVideo: {Path(v_path).name}"
        if g_path:
            msg += f"\nGIF: {Path(g_path).name}"
        self.lbl_render_status.setText(msg)
        self.lbl_render_status.setStyleSheet("color: #10b981; font-weight: 700;")

    def _on_render_error(self, err: str):
        self.btn_render.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.lbl_render_status.setText(f"Render Error: {err}")
        self.lbl_render_status.setStyleSheet("color: #ef4444; font-weight: 700;")
