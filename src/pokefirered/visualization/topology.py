"""
Unified Topological World Model for Pokémon FireRed GBA.
Solves the root-cause mapping problem by representing the Kanto world as a
mathematically continuous piecewise-linear manifold for overworld regions,
with formal parent-host warp projections for interiors and unscaled dungeon grids.
"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

from pokefirered.paths import get_project_root


class MapType(Enum):
    OVERWORLD = "overworld"      # Seamless outdoor manifold (Routes, Towns, Cities)
    INTERIOR_ROOM = "interior"   # Local instanced buildings (Homes, PokeCenter, Mart, Gym)
    DUNGEON = "dungeon"          # Large standalone explorable complexes (Viridian Forest, Caves)


@dataclass
class MapDescriptor:
    bank: int
    num: int
    name: str
    map_type: MapType
    width: int
    height: int
    # Origin tile coordinates (X, Y) on the canonical world canvas
    world_origin: Tuple[int, int]
    # For interior rooms: linkage to parent overworld host and entrance door
    host_map: Optional[Tuple[int, int]] = None
    host_door_tile: Optional[Tuple[int, int]] = None
    interior_asset_name: Optional[str] = None
    landmark_rank: int = 0


class WorldTopology:
    """
    Master topological coordinate engine for Pokémon FireRed.
    Converts raw GBA RAM telemetry (bank, map_num, raw_x, raw_y) into:
      1. Seamless, continuous overworld canvas coordinates (zero boundary jumps).
      2. Geographic parent-door projections for interiors (smooth camera, no void flying).
      3. Local room coordinates for detailed inspector views.
    """

    def __init__(self, tile_size: int = 16):
        self.tile_size = tile_size
        self.registry: Dict[Tuple[int, int], MapDescriptor] = {}
        self._build_registry()

    def _build_registry(self):
        """
        Builds the unified topological graph of Kanto.
        Overworld manifold anchors are mathematically aligned to guarantee Δ = 0 at borders:
          - Pallet Town (20x18) @ (60, 260) -> North exit @ Y = 260
          - Route 1 (20x40) @ (60, 220)     -> South enter @ Y = 260, North exit @ Y = 220
          - Viridian City (40x40) @ (48, 180) -> South enter @ Y = 220 (X=73), North exit @ Y = 180 (X=69)
          - Route 2 (20x80) @ (60, 100)     -> South enter @ Y = 180 (X=69), North exit @ Y = 100 (X=68)
          - Pewter City (40x40) @ (48, 60)  -> South enter @ Y = 100 (X=68), East exit @ X = 88 (Y=76)
          - Route 3 (70x18) @ (88, 68)      -> West enter @ X = 88
        """
        # =====================================================================
        # 1. CONTINUOUS OVERWORLD MANIFOLD (Bank 3)
        # =====================================================================
        self._reg(MapDescriptor(
            bank=3, num=0, name="Pallet Town",
            map_type=MapType.OVERWORLD, width=20, height=18,
            world_origin=(60, 260), landmark_rank=0
        ))
        self._reg(MapDescriptor(
            bank=3, num=19, name="Route 1",
            map_type=MapType.OVERWORLD, width=20, height=40,
            world_origin=(60, 220), landmark_rank=1
        ))
        self._reg(MapDescriptor(
            bank=3, num=1, name="Viridian City",
            map_type=MapType.OVERWORLD, width=40, height=40,
            world_origin=(48, 180), landmark_rank=2
        ))
        self._reg(MapDescriptor(
            bank=3, num=20, name="Route 2",
            map_type=MapType.OVERWORLD, width=20, height=80,
            world_origin=(60, 100), landmark_rank=3
        ))
        self._reg(MapDescriptor(
            bank=3, num=2, name="Pewter City",
            map_type=MapType.OVERWORLD, width=40, height=40,
            world_origin=(48, 60), landmark_rank=5
        ))
        self._reg(MapDescriptor(
            bank=3, num=21, name="Route 3",
            map_type=MapType.OVERWORLD, width=70, height=18,
            world_origin=(88, 68), landmark_rank=7
        ))
        self._reg(MapDescriptor(
            bank=3, num=22, name="Route 4",
            map_type=MapType.OVERWORLD, width=90, height=18,
            world_origin=(158, 68), landmark_rank=8
        ))
        self._reg(MapDescriptor(
            bank=3, num=3, name="Cerulean City",
            map_type=MapType.OVERWORLD, width=40, height=40,
            world_origin=(248, 68), landmark_rank=9
        ))

        # =====================================================================
        # 2. INTERIOR ROOMS & BUILDINGS (Host-Linked Projections)
        # =====================================================================
        # Pallet Town Interiors (Bank 4) -> Host is Pallet Town (3, 0)
        self._reg(MapDescriptor(
            bank=4, num=1, name="Hero's Bedroom (2F)",
            map_type=MapType.INTERIOR_ROOM, width=12, height=9,
            world_origin=(45, 262), # Legacy composite atlas tile
            host_map=(3, 0), host_door_tile=(6, 6), # Overworld Red's House front door
            interior_asset_name="Pokemon-FireRed&LeafGreenVersions-PalletTown-Home.png",
            landmark_rank=0
        ))
        self._reg(MapDescriptor(
            bank=4, num=0, name="Hero's Living Room (1F)",
            map_type=MapType.INTERIOR_ROOM, width=12, height=9,
            world_origin=(45, 272),
            host_map=(3, 0), host_door_tile=(6, 6),
            interior_asset_name="Pokemon-FireRed&LeafGreenVersions-PalletTown-Home.png",
            landmark_rank=0
        ))
        self._reg(MapDescriptor(
            bank=4, num=2, name="Rival's House",
            map_type=MapType.INTERIOR_ROOM, width=12, height=9,
            world_origin=(45, 282),
            host_map=(3, 0), host_door_tile=(14, 6),
            landmark_rank=0
        ))
        self._reg(MapDescriptor(
            bank=4, num=3, name="Oak's Pokémon Lab",
            map_type=MapType.INTERIOR_ROOM, width=12, height=12,
            world_origin=(45, 292),
            host_map=(3, 0), host_door_tile=(13, 12),
            landmark_rank=0
        ))

        # Viridian City Interiors (Bank 5) -> Host is Viridian City (3, 1)
        self._reg(MapDescriptor(
            bank=5, num=0, name="Pokémon Center (Viridian)",
            map_type=MapType.INTERIOR_ROOM, width=14, height=8,
            world_origin=(97, 185),
            host_map=(3, 1), host_door_tile=(23, 25),
            landmark_rank=2
        ))
        self._reg(MapDescriptor(
            bank=5, num=1, name="Viridian Gym",
            map_type=MapType.INTERIOR_ROOM, width=20, height=23,
            world_origin=(97, 172),
            host_map=(3, 1), host_door_tile=(32, 7),
            interior_asset_name="Pokemon-FireRed&LeafGreenVersions-ViridianCity-Gym.png",
            landmark_rank=2
        ))
        self._reg(MapDescriptor(
            bank=5, num=2, name="Poké Mart (Viridian)",
            map_type=MapType.INTERIOR_ROOM, width=8, height=8,
            world_origin=(97, 195),
            host_map=(3, 1), host_door_tile=(29, 19),
            landmark_rank=2
        ))
        self._reg(MapDescriptor(
            bank=5, num=3, name="Pokémon Academy",
            map_type=MapType.INTERIOR_ROOM, width=8, height=8,
            world_origin=(97, 205),
            host_map=(3, 1), host_door_tile=(21, 15),
            landmark_rank=2
        ))

        # Pewter City Interiors (Bank 6) -> Host is Pewter City (3, 2)
        self._reg(MapDescriptor(
            bank=6, num=2, name="Pewter Gym (Brock)",
            map_type=MapType.INTERIOR_ROOM, width=12, height=15,
            world_origin=(35, 65), # Legacy composite atlas tile
            host_map=(3, 2), host_door_tile=(15, 16), # Overworld Pewter Gym door @ (63, 76)
            interior_asset_name="Pokemon-FireRed&LeafGreenVersions-PewterCity-Gym.png",
            landmark_rank=6
        ))
        self._reg(MapDescriptor(
            bank=6, num=0, name="Pewter Museum (1F)",
            map_type=MapType.INTERIOR_ROOM, width=20, height=8,
            world_origin=(35, 82),
            host_map=(3, 2), host_door_tile=(14, 7),
            landmark_rank=5
        ))
        self._reg(MapDescriptor(
            bank=6, num=1, name="Pewter Museum (2F)",
            map_type=MapType.INTERIOR_ROOM, width=14, height=8,
            world_origin=(35, 92),
            host_map=(3, 2), host_door_tile=(14, 7),
            landmark_rank=5
        ))
        self._reg(MapDescriptor(
            bank=6, num=3, name="Pokémon Center (Pewter)",
            map_type=MapType.INTERIOR_ROOM, width=14, height=8,
            world_origin=(35, 102),
            host_map=(3, 2), host_door_tile=(13, 25),
            landmark_rank=5
        ))
        self._reg(MapDescriptor(
            bank=6, num=4, name="Poké Mart (Pewter)",
            map_type=MapType.INTERIOR_ROOM, width=8, height=8,
            world_origin=(35, 112),
            host_map=(3, 2), host_door_tile=(23, 17),
            landmark_rank=5
        ))

        # Gatehouses (Bank 15) -> Connecting Gateways
        self._reg(MapDescriptor(
            bank=15, num=0, name="Route 2 South Gatehouse",
            map_type=MapType.INTERIOR_ROOM, width=10, height=8,
            world_origin=(65, 170),
            host_map=(3, 20), host_door_tile=(9, 65),
            landmark_rank=3
        ))
        self._reg(MapDescriptor(
            bank=15, num=3, name="Route 2 North Gatehouse",
            map_type=MapType.INTERIOR_ROOM, width=10, height=8,
            world_origin=(65, 118),
            host_map=(3, 20), host_door_tile=(9, 15),
            landmark_rank=4
        ))

        # =====================================================================
        # 3. DUNGEONS & COMPLEXES (Banks 1 & 2)
        # =====================================================================
        self._reg(MapDescriptor(
            bank=1, num=0, name="Viridian Forest",
            map_type=MapType.DUNGEON, width=54, height=64,
            world_origin=(87, 109), # On full composite: placed east of Route 2
            host_map=(3, 20), host_door_tile=(9, 45),
            interior_asset_name="Pokemon-FireRed&LeafGreenVersions-ViridianForest.png",
            landmark_rank=4
        ))
        self._reg(MapDescriptor(
            bank=1, num=1, name="Mt. Moon (1F)",
            map_type=MapType.DUNGEON, width=48, height=39,
            world_origin=(94, 6),
            host_map=(3, 21), host_door_tile=(50, 10),
            interior_asset_name="Pokemon-FireRed&LeafGreenVersions-MtMoon-1F.png",
            landmark_rank=7
        ))
        self._reg(MapDescriptor(
            bank=1, num=2, name="Mt. Moon (B1F)",
            map_type=MapType.DUNGEON, width=47, height=20,
            world_origin=(122, 6),
            landmark_rank=7
        ))
        self._reg(MapDescriptor(
            bank=1, num=3, name="Mt. Moon (B2F)",
            map_type=MapType.DUNGEON, width=48, height=40,
            world_origin=(150, 6),
            landmark_rank=7
        ))

    def _reg(self, desc: MapDescriptor):
        self.registry[(desc.bank, desc.num)] = desc

    def get_descriptor(self, bank: int, num: int) -> MapDescriptor:
        """Retrieves or creates a graceful fallback descriptor for any map."""
        if (bank, num) in self.registry:
            return self.registry[(bank, num)]
        # Auto-fallback: never crash on unexpected map
        return MapDescriptor(
            bank=bank, num=num,
            name=f"Unknown Area ({bank}, {num})",
            map_type=MapType.OVERWORLD,
            width=40, height=40,
            world_origin=(60, 260), # Fallback to Pallet Town anchor
            landmark_rank=0
        )

    @staticmethod
    def normalize_raw_coords(raw_x: int, raw_y: int) -> Tuple[int, int]:
        """
        Translates raw GBA RAM coordinates into local layout coordinates
        by subtracting the GBA engine's 7-block border buffer (MAP_OFFSET = 7).
        """
        lx = max(0, raw_x - 7) if raw_x >= 7 else raw_x
        ly = max(0, raw_y - 7) if raw_y >= 7 else raw_y
        return lx, ly

    def to_global_coords(
        self,
        bank: int,
        num: int,
        layout_x: int,
        layout_y: int,
        overworld_anchor: bool = False
    ) -> Tuple[int, int, int, int]:
        """
        Converts local layout coordinates into global canvas coordinates.
        Returns: (tile_x, tile_y, pixel_x, pixel_y)
        
        Args:
          overworld_anchor: If True and the map is an interior room, projects
                            the coordinate onto the host building's overworld door,
                            preventing wild camera whips across the sea.
        """
        desc = self.get_descriptor(bank, num)

        if overworld_anchor and desc.map_type == MapType.INTERIOR_ROOM and desc.host_map:
            # Project onto overworld parent building door
            h_bank, h_num = desc.host_map
            h_desc = self.get_descriptor(h_bank, h_num)
            hx, hy = desc.host_door_tile or (0, 0)
            tx = h_desc.world_origin[0] + hx
            ty = h_desc.world_origin[1] + hy
        else:
            # Standard manifold projection
            tx = desc.world_origin[0] + layout_x
            ty = desc.world_origin[1] + layout_y

        px = tx * self.tile_size
        py = ty * self.tile_size
        return tx, ty, px, py

    def get_landmark_name(self, bank: int, num: int) -> str:
        return self.get_descriptor(bank, num).name

    def get_landmark_rank(self, bank: int, num: int) -> int:
        return self.get_descriptor(bank, num).landmark_rank
