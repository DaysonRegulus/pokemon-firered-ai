"""
Visualization and trajectory rendering package for Pokémon FireRed AI.
Supports multi-generation swarm path animations and global Kanto exploration heatmaps.
"""
from .topology import WorldTopology, MapDescriptor, MapType
from .world_mapper import KantoWorldMapper
from .swarm_renderer import SwarmRenderer

__all__ = ["WorldTopology", "MapDescriptor", "MapType", "KantoWorldMapper", "SwarmRenderer"]

