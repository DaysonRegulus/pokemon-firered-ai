"""
Training Studio View:
Provides an interactive training orchestrator for PPO & QR-DQN with multi-modal curiosity,
hyperparameter configuration, live terminal logs, and real-time training telemetry.
"""
from typing import Optional
from PySide6.QtCore import Qt, Signal
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
    QProgressBar,
    QPlainTextEdit,
    QGroupBox,
)

from ..widgets.metric_card import MetricCard
from ..workers.train_worker import TrainWorker


class TrainView(QWidget):
    """
    Training management and execution view.
    """
    sig_start_train = Signal(dict)
    sig_stop_train = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: Optional[TrainWorker] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(14)

        # 1. Top Configuration Card
        config_box = QFrame()
        config_box.setObjectName("Card")
        config_layout = QVBoxLayout(config_box)
        config_layout.setContentsMargins(14, 12, 14, 12)
        config_layout.setSpacing(10)

        cfg_title = QLabel("⚙️ Training Run Configuration")
        cfg_title.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 13px;")
        config_layout.addWidget(cfg_title)

        grid = QGridLayout()
        grid.setSpacing(10)

        # Algorithm
        grid.addWidget(QLabel("Algorithm:"), 0, 0)
        self.combo_algo = QComboBox()
        self.combo_algo.addItems(["PPO", "QRDQN"])
        grid.addWidget(self.combo_algo, 0, 1)

        # Exploration
        grid.addWidget(QLabel("Exploration:"), 0, 2)
        self.combo_expl = QComboBox()
        self.combo_expl.addItems([
            "RND",
            "SSIM",
            "COORD",
            "RND+COORD",
            "SSIM+COORD",
            "RND+SSIM",
            "RND+SSIM+COORD",
            "NONE"
        ])
        grid.addWidget(self.combo_expl, 0, 3)

        # Envs
        grid.addWidget(QLabel("Parallel Envs:"), 1, 0)
        self.spin_envs = QSpinBox()
        self.spin_envs.setRange(1, 32)
        self.spin_envs.setValue(12)
        grid.addWidget(self.spin_envs, 1, 1)

        # Timesteps
        grid.addWidget(QLabel("Timesteps:"), 1, 2)
        self.combo_steps = QComboBox()
        self.combo_steps.setEditable(True)
        self.combo_steps.addItems([
            "25600",
            "51200",
            "102400",
            "204800",
            "500000",
            "1000000"
        ])
        self.combo_steps.setCurrentText("102400")
        grid.addWidget(self.combo_steps, 1, 3)

        # Device
        grid.addWidget(QLabel("Compute Device:"), 2, 0)
        self.combo_device = QComboBox()
        self.combo_device.addItems(["auto", "cuda", "cpu"])
        grid.addWidget(self.combo_device, 2, 1)

        # Checkboxes
        chk_layout = QHBoxLayout()
        self.chk_fresh = QCheckBox("Fresh Start (Reset Weights)")
        self.chk_fresh.setChecked(True)
        self.chk_trajectories = QCheckBox("Record Per-Agent Trajectories")
        self.chk_trajectories.setChecked(True)
        chk_layout.addWidget(self.chk_fresh)
        chk_layout.addWidget(self.chk_trajectories)
        grid.addLayout(chk_layout, 2, 2, 1, 2)

        config_layout.addLayout(grid)

        # Action Buttons
        btn_bar = QHBoxLayout()
        self.btn_start = QPushButton("🚀 Start Training")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                font-weight: 700;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #10b981;
            }
        """)
        self.btn_start.clicked.connect(self._on_start_clicked)
        btn_bar.addWidget(self.btn_start)

        self.btn_stop = QPushButton("🛑 Stop Training")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #991b1b;
                color: #ffffff;
                font-weight: 700;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #9ca3af;
            }
        """)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        btn_bar.addWidget(self.btn_stop)

        btn_bar.addStretch(1)

        self.lbl_status = QLabel("Idle. Ready to launch.")
        self.lbl_status.setStyleSheet("color: #94a3b8; font-weight: 600;")
        btn_bar.addWidget(self.lbl_status)

        config_layout.addLayout(btn_bar)
        main_layout.addWidget(config_box)

        # 2. Progress and KPI Metric Cards
        progress_box = QFrame()
        progress_box.setObjectName("Card")
        progress_layout = QVBoxLayout(progress_box)
        progress_layout.setContentsMargins(14, 10, 14, 10)
        progress_layout.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Progress: %p% (0 / 0 steps)")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 4px;
                text-align: center;
                color: #f8fafc;
                font-weight: 600;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #0284c7;
                border-radius: 4px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        kpis = QHBoxLayout()
        kpis.setSpacing(10)
        self.card_sps = MetricCard("Speed", "0.0 SPS", "Throughput", "⚡", "#38bdf8")
        self.card_tiles = MetricCard("Exploration", "0 Tiles", "0 Maps", "🧭", "#10b981")
        self.card_reward = MetricCard("Total Reward", "0.00", "Ext: 0.0 | Int: 0.0", "🏆", "#f59e0b")
        self.card_loss = MetricCard("Loss", "0.000", "Optimization", "📉", "#a855f7")

        kpis.addWidget(self.card_sps)
        kpis.addWidget(self.card_tiles)
        kpis.addWidget(self.card_reward)
        kpis.addWidget(self.card_loss)
        progress_layout.addLayout(kpis)

        main_layout.addWidget(progress_box)

        # 3. Terminal Log Viewer
        log_box = QFrame()
        log_box.setObjectName("Card")
        log_layout = QVBoxLayout(log_box)
        log_layout.setContentsMargins(12, 10, 12, 10)

        log_head = QHBoxLayout()
        log_title = QLabel("💻 Live Training Terminal Output")
        log_title.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 12px;")
        log_head.addWidget(log_title)
        log_head.addStretch(1)

        self.chk_autoscroll = QCheckBox("Auto-scroll")
        self.chk_autoscroll.setChecked(True)
        log_head.addWidget(self.chk_autoscroll)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self._clear_logs)
        log_head.addWidget(btn_clear)

        log_layout.addLayout(log_head)

        self.txt_log = QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("""
            QPlainTextEdit {
                background-color: #030712;
                color: #e2e8f0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #1e293b;
                border-radius: 4px;
            }
        """)
        log_layout.addWidget(self.txt_log, stretch=1)
        main_layout.addWidget(log_box, stretch=1)

    def _on_start_clicked(self):
        try:
            steps = int(self.combo_steps.currentText().replace(",", ""))
        except ValueError:
            steps = 102400

        config = {
            "algo": self.combo_algo.currentText(),
            "exploration": self.combo_expl.currentText(),
            "num_envs": self.spin_envs.value(),
            "timesteps": steps,
            "device": self.combo_device.currentText(),
            "fresh": self.chk_fresh.isChecked(),
            "record_trajectories": self.chk_trajectories.isChecked(),
        }

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status.setText(f"Running {config['algo']} ({config['exploration']})...")
        self.lbl_status.setStyleSheet("color: #10b981; font-weight: 600;")
        self.progress_bar.setValue(0)

        self.sig_start_train.emit(config)

    def _on_stop_clicked(self):
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Stopping...")
        self.lbl_status.setStyleSheet("color: #f59e0b; font-weight: 600;")
        self.sig_stop_train.emit()

    def handle_log(self, text: str):
        self.txt_log.appendPlainText(text)
        if self.chk_autoscroll.isChecked():
            self.txt_log.verticalScrollBar().setValue(self.txt_log.verticalScrollBar().maximum())

    def handle_progress(self, current: int, total: int, sps: float):
        pct = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(min(100, pct))
        self.progress_bar.setFormat(f"Progress: {pct}% ({current:,} / {total:,} steps)")
        self.card_sps.set_value(f"{sps:.1f} SPS", "Step speed")

    def handle_metrics(self, m: dict):
        tiles = m.get("unique_tiles", 0)
        maps = m.get("unique_maps", 0)
        self.card_tiles.set_value(f"{tiles} Tiles", f"{maps} Unique Maps")

        tot_rew = m.get("reward_total", 0.0)
        ext_rew = m.get("reward_ext", 0.0)
        int_rew = m.get("reward_int", 0.0)
        self.card_reward.set_value(f"{tot_rew:.2f}", f"Ext: {ext_rew:.2f} | Int: {int_rew:.2f}")

        loss = m.get("loss", 0.0)
        self.card_loss.set_value(f"{loss:.4f}", "Policy / Value Loss")

    def handle_finished(self, exit_code: int, summary: str):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        if exit_code == 0:
            self.lbl_status.setText("Training Complete! ✓")
            self.lbl_status.setStyleSheet("color: #10b981; font-weight: 700;")
        else:
            self.lbl_status.setText("Training Ended.")
            self.lbl_status.setStyleSheet("color: #ef4444; font-weight: 700;")

    def _clear_logs(self):
        self.txt_log.clear()
