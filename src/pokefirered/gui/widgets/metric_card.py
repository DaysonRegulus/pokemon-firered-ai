"""
Modern Metric KPI Card Widget for PokeRL Studio.
Displays key metrics, exploration frontiers, hardware stats, and model indicators.
"""
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel


class MetricCard(QFrame):
    """Sleek KPI metric card with title, primary value, subtitle, and accent color."""

    def __init__(
        self,
        title: str,
        value: str = "--",
        sub: str = "",
        icon: str = "•",
        accent_color: str = "#00E5FF",
        subtitle: Optional[str] = None,
        color_accent: Optional[str] = None,
        parent=None
    ):
        super().__init__(parent)
        self.setProperty("class", "Card")
        sub_text = subtitle if subtitle is not None else sub
        acc = color_accent if color_accent is not None else accent_color
        self.accent_color = acc

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        # Header: Icon + Title
        hdr_layout = QHBoxLayout()
        hdr_layout.setSpacing(6)

        self.icon_label = QLabel(icon)
        self.icon_label.setStyleSheet(f"color: {self.accent_color}; font-size: 13px; font-weight: bold;")
        hdr_layout.addWidget(self.icon_label)

        self.title_label = QLabel(title.upper())
        self.title_label.setProperty("class", "CardTitle")
        hdr_layout.addWidget(self.title_label)
        hdr_layout.addStretch()

        layout.addLayout(hdr_layout)

        # Primary Value
        self.val_label = QLabel(value)
        self.val_label.setProperty("class", "CardValue")
        layout.addWidget(self.val_label)

        # Subtitle / Details
        self.sub_label = QLabel(sub_text)
        self.sub_label.setProperty("class", "CardSub")
        layout.addWidget(self.sub_label)

    def set_value(self, val_str: str, sub_str: Optional[str] = None):
        """Updates metric value and subtitle text."""
        self.val_label.setText(str(val_str))
        if sub_str is not None:
            self.sub_label.setText(str(sub_str))

    def set_accent(self, color_hex: str):
        """Changes accent color."""
        self.accent_color = color_hex
        self.icon_label.setStyleSheet(f"color: {color_hex}; font-size: 13px; font-weight: bold;")
