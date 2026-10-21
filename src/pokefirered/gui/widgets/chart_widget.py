"""
Embedded Matplotlib Real-Time Chart Widget for PySide6.
Dark themed, lightweight, and optimized for real-time RL metrics.
"""
from typing import List, Optional
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class LiveMetricChart(QFrame):
    """Real-time updating line chart widget styled in dark theme."""

    def __init__(
        self,
        title: str,
        x_label: str = "Steps",
        y_label: str = "Value",
        series_names: Optional[List[str]] = None,
        series_colors: Optional[List[str]] = None,
        ylabel: Optional[str] = None,
        colors: Optional[List[str]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.setProperty("class", "Card")

        eff_y_label = ylabel if ylabel is not None else y_label
        eff_colors = colors if colors is not None else series_colors

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.title_label = QLabel(title.upper())
        self.title_label.setProperty("class", "CardTitle")
        layout.addWidget(self.title_label)

        # Matplotlib Figure
        self.fig = Figure(facecolor="#0F1622")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#0B0F17")

        self.ax.tick_params(colors="#64748B", labelsize=8)
        self.ax.spines['bottom'].set_color('#1E293B')
        self.ax.spines['top'].set_color('#1E293B')
        self.ax.spines['right'].set_color('#1E293B')
        self.ax.spines['left'].set_color('#1E293B')
        self.ax.set_xlabel(x_label, color="#94A3B8", fontsize=9)
        self.ax.set_ylabel(eff_y_label, color="#94A3B8", fontsize=9)
        self.ax.grid(True, linestyle="--", alpha=0.15, color="#FFFFFF")

        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.series_names = series_names or ["Series 1"]
        self.series_colors = eff_colors or ["#00E5FF", "#00E676", "#FFD700", "#FF5252"]

        self.lines = []
        self.x_data = {i: [] for i in range(len(self.series_names))}
        self.y_data = {i: [] for i in range(len(self.series_names))}

        for idx, s_name in enumerate(self.series_names):
            color = self.series_colors[idx % len(self.series_colors)]
            line, = self.ax.plot([], [], label=s_name, color=color, linewidth=1.8)
            self.lines.append(line)

        if len(self.series_names) > 1:
            self.ax.legend(facecolor="#0F1622", edgecolor="#1E293B", labelcolor="#E2E8F0", fontsize=8, loc="upper left")

        self.fig.tight_layout()

    def add_point(self, series_idx: int, x: float, y: float):
        """Appends a data point to a specific series and schedules canvas redraw."""
        if series_idx not in self.x_data:
            return
        self.x_data[series_idx].append(x)
        self.y_data[series_idx].append(y)

        # Cap memory buffer at 2,000 points
        if len(self.x_data[series_idx]) > 2000:
            self.x_data[series_idx] = self.x_data[series_idx][-2000:]
            self.y_data[series_idx] = self.y_data[series_idx][-2000:]

        self.lines[series_idx].set_data(self.x_data[series_idx], self.y_data[series_idx])
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()

    def append_data(self, x: float, y_values: List[float]):
        """Appends multiple series values at step x and redraws once."""
        for idx, val in enumerate(y_values):
            if idx in self.x_data:
                self.x_data[idx].append(x)
                self.y_data[idx].append(val)
                if len(self.x_data[idx]) > 2000:
                    self.x_data[idx] = self.x_data[idx][-2000:]
                    self.y_data[idx] = self.y_data[idx][-2000:]
                self.lines[idx].set_data(self.x_data[idx], self.y_data[idx])
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()


    def set_data(self, series_idx: int, xs: List[float], ys: List[float]):
        """Replaces full data series."""
        if series_idx not in self.x_data:
            return
        self.x_data[series_idx] = list(xs)
        self.y_data[series_idx] = list(ys)
        self.lines[series_idx].set_data(self.x_data[series_idx], self.y_data[series_idx])
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()

    def clear(self):
        """Clears all series."""
        for i in range(len(self.lines)):
            self.x_data[i] = []
            self.y_data[i] = []
            self.lines[i].set_data([], [])
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw_idle()
