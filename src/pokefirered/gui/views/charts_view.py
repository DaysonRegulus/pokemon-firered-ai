"""
Analytics & Benchmark Charts View:
Provides live multi-curve dark-themed Matplotlib graphs for rewards,
exploration frontier discovery, training loss, and historical model comparisons.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
)

from ..widgets.chart_widget import LiveMetricChart

from pokefirered.paths import get_project_root

PROJECT_ROOT = get_project_root()


class ChartsView(QWidget):
    """
    Real-time analytics and historical training benchmark comparisons.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        splitter = QSplitter(Qt.Vertical)

        # Top Section: 4 Live Charts (2x2 Grid)
        charts_container = QWidget()
        grid = QGridLayout(charts_container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(12)

        # 1. Rewards
        self.chart_rewards = LiveMetricChart(
            title="Rewards Progression",
            ylabel="Reward Value",
            series_names=["Total Reward", "Extrinsic", "Intrinsic"],
            colors=["#38bdf8", "#10b981", "#f59e0b"]
        )
        grid.addWidget(self.chart_rewards, 0, 0)

        # 2. Exploration Frontier
        self.chart_frontier = LiveMetricChart(
            title="Exploration Frontier",
            ylabel="Unique Count",
            series_names=["Unique Tiles", "Unique Maps"],
            colors=["#a855f7", "#ec4899"]
        )
        grid.addWidget(self.chart_frontier, 0, 1)

        # 3. Loss Dynamics
        self.chart_loss = LiveMetricChart(
            title="Training Loss",
            ylabel="Loss",
            series_names=["Loss", "Policy Loss", "Value Loss"],
            colors=["#ef4444", "#fb923c", "#facc15"]
        )
        grid.addWidget(self.chart_loss, 1, 0)

        # 4. Throughput (SPS)
        self.chart_throughput = LiveMetricChart(
            title="Throughput (SPS)",
            ylabel="Steps / Sec",
            series_names=["SPS"],
            colors=["#06b6d4"]
        )
        grid.addWidget(self.chart_throughput, 1, 1)

        splitter.addWidget(charts_container)

        # Bottom Section: Historical Benchmarks Table
        history_box = QFrame()
        history_box.setObjectName("Card")
        hist_layout = QVBoxLayout(history_box)
        hist_layout.setContentsMargins(14, 10, 14, 10)
        hist_layout.setSpacing(8)

        hist_head = QHBoxLayout()
        hist_title = QLabel("📊 Historical Benchmark Runs (`checkpoints/*_summary.json`)")
        hist_title.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 12px;")
        hist_head.addWidget(hist_title)
        hist_head.addStretch(1)

        self.btn_refresh = QPushButton("🔄 Refresh Benchmarks")
        self.btn_refresh.clicked.connect(self.reload_benchmarks)
        hist_head.addWidget(self.btn_refresh)

        hist_layout.addLayout(hist_head)

        self.table_benchmarks = QTableWidget()
        self.table_benchmarks.setColumnCount(8)
        self.table_benchmarks.setHorizontalHeaderLabels([
            "Run Name", "Algorithm", "Exploration", "Steps", "Time (min)", "SPS", "Tiles Visited", "Total Reward"
        ])
        self.table_benchmarks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_benchmarks.setStyleSheet("""
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
        hist_layout.addWidget(self.table_benchmarks)

        splitter.addWidget(history_box)
        splitter.setSizes([500, 200])

        main_layout.addWidget(splitter)

        self.step_history: List[int] = []
        self.reload_benchmarks()

    def update_live_metrics(self, m: dict):
        step = m.get("current_step", 0)
        if step == 0:
            return

        # Rewards
        r_tot = m.get("reward_total", 0.0)
        r_ext = m.get("reward_ext", 0.0)
        r_int = m.get("reward_int", 0.0)
        self.chart_rewards.append_data(step, [r_tot, r_ext, r_int])

        # Frontier
        tiles = m.get("unique_tiles", 0)
        maps = m.get("unique_maps", 0)
        self.chart_frontier.append_data(step, [tiles, maps])

        # Loss
        loss = m.get("loss", 0.0)
        p_loss = m.get("policy_loss", 0.0)
        v_loss = m.get("value_loss", 0.0)
        self.chart_loss.append_data(step, [loss, p_loss, v_loss])

        # SPS
        sps = m.get("sps", 0.0)
        self.chart_throughput.append_data(step, [sps])

    def clear_charts(self):
        self.chart_rewards.clear()
        self.chart_frontier.clear()
        self.chart_loss.clear()
        self.chart_throughput.clear()

    def reload_benchmarks(self):
        """Scans checkpoints folder for benchmark summary JSONs."""
        chk_dir = PROJECT_ROOT / "checkpoints"
        if not chk_dir.exists():
            return

        summaries = list(chk_dir.glob("*_summary.json"))
        self.table_benchmarks.setRowCount(len(summaries))

        for row, path in enumerate(summaries):
            try:
                with open(path, "r") as f:
                    data = json.load(f)

                name = path.stem.replace("_summary", "")
                algo = data.get("algo", "-")
                expl = data.get("exploration", "-")
                steps = f"{data.get('timesteps', 0):,}"
                elapsed = f"{data.get('elapsed_seconds', 0) / 60:.1f}"
                sps = f"{data.get('sps', 0):.1f}"
                tiles = f"{data.get('unique_tiles', 0)}"
                reward = f"{data.get('total_reward', 0):.2f}"

                for col, val in enumerate([name, algo, expl, steps, elapsed, sps, tiles, reward]):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table_benchmarks.setItem(row, col, item)
            except Exception:
                continue
