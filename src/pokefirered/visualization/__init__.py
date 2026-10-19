"""
Visualization and trajectory rendering package for Pokémon FireRed AI.
Supports multi-generation swarm path animations and global Kanto exploration heatmaps.
"""
from .world_mapper import KantoWorldMapper
from .swarm_renderer import SwarmRenderer

__all__ = ["KantoWorldMapper", "SwarmRenderer"]
