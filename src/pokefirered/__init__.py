"""
Pokemon FireRed RL Package.
Provides custom retro environment wrappers, RAM reward managers,
RND curiosity exploration modules, and training callbacks for Pokemon FireRed GBA.
"""

__version__ = "2.0.0"

from .paths import get_project_root, get_workspace_root

__all__ = ["get_project_root", "get_workspace_root", "__version__"]

