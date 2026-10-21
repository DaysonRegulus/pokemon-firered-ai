"""
PokéRL Studio — Unified Desktop Application Entry Point.
Launches the PySide6 modern dark-themed GUI suite for autonomous Pokémon FireRed RL.
"""
import multiprocessing
import os
from pathlib import Path
import sys

# Ensure src/ is on Python search path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from pokefirered.gui.main_window import MainWindow


def main():
    multiprocessing.freeze_support()

    # If called with --train flag, execute headless training subprocess directly
    if "--train" in sys.argv:
        sys.argv.remove("--train")
        from scripts.train import main as train_main
        train_main()
        return

    # High DPI scaling is enabled by default in Qt 6
    app = QApplication(sys.argv)
    app.setApplicationName("PokéRL Studio")
    app.setOrganizationName("DeepMind / Antigravity")

    # Set default modern UI font
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)

    # Set application icon if present
    icon_path = PROJECT_ROOT / "assets" / "pwhiddy" / "firered_player_sprites.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
