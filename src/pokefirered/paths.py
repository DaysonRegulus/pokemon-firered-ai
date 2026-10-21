"""
Project path resolution utility.
Works seamlessly in both local Python virtual environments and frozen PyInstaller executables.
"""
from pathlib import Path
import sys


def get_project_root() -> Path:
    """Returns the canonical root directory of the project or frozen bundle."""
    # If running from source
    source_root = Path(__file__).resolve().parent.parent.parent
    if (source_root / "assets").exists():
        return source_root

    # If running as PyInstaller bundle
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            meipass_root = Path(sys._MEIPASS)
            if (meipass_root / "assets").exists():
                return meipass_root
        exe_root = Path(sys.executable).resolve().parent
        if (exe_root / "_internal" / "assets").exists():
            return exe_root / "_internal"
        if (exe_root / "assets").exists():
            return exe_root

    # Fallback to current working directory
    cwd = Path.cwd()
    if (cwd / "assets").exists():
        return cwd

    return source_root


def get_workspace_root() -> Path:
    """Returns the working directory for user saves, checkpoints, and outputs."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return get_project_root()
