"""
Kanto World Mapper: Maps local GBA map coordinates (bank, map_num, x, y)
to the canonical 32-bit Game Boy Advance Pokémon FireRed / LeafGreen overworld map grid.
"""
from typing import Tuple, Dict

class KantoWorldMapper:
    """
    Transforms GBA overworld coordinates into pixel coordinates
    on the canonical stitched kanto_firered_clean.png GBA composite map.
    """
    # Mapping from GBA (bank, map_idx) to kanto_firered_clean tile coordinates [X, Y]
    CANONICAL_OFFSETS: Dict[Tuple[int, int], Tuple[int, int]] = {
        # Overworld Routes & Cities (West Kanto Progression Corridor)
        (3, 0): (62, 262),    # Pallet Town (20x18 tiles) -> (992px, 4192px)
        (3, 19): (62, 214),   # Route 1 (20x48 tiles) -> (992px, 3424px)
        (3, 1): (52, 178),    # Viridian City (40x36 tiles) -> (832px, 2848px)
        (3, 20): (62, 118),   # Route 2 (20x60 tiles) -> (992px, 1888px)
        (1, 0): (62, 130),    # Viridian Forest interior corridor overlay
        (3, 2): (50, 60),     # Pewter City (40x36 tiles) -> (800px, 960px)
        (6, 2): (58, 63),     # Pewter Gym arena interior overlay
    }

    # Walkable tile bounds [min_x, max_x, min_y, max_y] per map to eliminate out-of-bounds drift
    WALKABLE_BOUNDS: Dict[Tuple[int, int], Tuple[int, int, int, int]] = {
        (3, 0): (4, 15, 1, 14),      # Pallet Town: interior lawn & roads (fences & water blocked)
        (3, 19): (4, 18, 0, 47),     # Route 1: 48-tile corridor with signpost gap and winding roads
        (3, 1): (14, 27, 0, 35),     # Viridian City: town roads & plaza (boundary trees blocked)
        (3, 20): (9, 12, 0, 59),     # Route 2: path between gatehouses (side forest blocked)
        (3, 2): (12, 24, 16, 35),    # Pewter City: south road & gym square
        (6, 2): (4, 6, 3, 11),       # Pewter Gym: arena floor leading to Brock
        (1, 0): (13, 26, 4, 44),     # Viridian Forest: main corridor
    }

    LANDMARK_NAMES: Dict[Tuple[int, int], str] = {
        (3, 0): "Pallet Town",
        (3, 19): "Route 1",
        (3, 1): "Viridian City",
        (3, 20): "Route 2",
        (1, 0): "Viridian Forest",
        (3, 2): "Pewter City",
        (6, 2): "Pewter Gym (Brock)",
    }

    def __init__(self, tile_size: int = 16):
        self.tile_size = tile_size

    def get_walkable_x_bounds(self, bank: int, num: int, y: int) -> Tuple[int, int]:
        """Returns exact (min_x, max_x) walkable range for a given map and y coordinate."""
        if (bank, num) == (3, 0):
            # Pallet Town
            if y <= 2: return 10, 11
            elif y <= 5: return 9, 12
            elif y <= 12: return 4, 14
            else: return 5, 12
        elif (bank, num) == (3, 19):
            # Route 1 (20x48 GBA FireRed Map, offset 62, 214)
            if y >= 44: return 10, 11   # South entrance corridor from Pallet Town
            elif y >= 38: return 4, 13  # Lower grass clearing approach
            elif y == 37: return 4, 6   # Grass gap to the left of the signpost
            elif y >= 35: return 1, 18  # Lower horizontal dirt road
            elif y >= 28: return 16, 18 # Eastern vertical road
            elif y >= 26: return 9, 18  # Middle horizontal connector road
            elif y >= 16: return 10, 13 # Central vertical road
            elif y >= 11: return 13, 17 # Upper winding road
            elif y >= 8: return 8, 18   # Upper horizontal connector road
            else: return 9, 11          # North tree corridor entering Viridian City
        elif (bank, num) == (3, 1):
            # Viridian City
            if y >= 26: return 19, 21   # South tree entrance corridor
            elif y >= 10: return 18, 22 # Central avenue between houses
            else: return 16, 18         # North exit road between fence and trees at x=17
        elif (bank, num) == (3, 20):
            # Route 2
            return 9, 12
        elif (bank, num) == (1, 0):
            # Viridian Forest
            if y >= 36: return 16, 18
            elif y >= 26: return 16, 26
            elif y >= 16: return 13, 26
            else: return 15, 19
        elif (bank, num) == (3, 2):
            # Pewter City
            if y >= 28: return 18, 21
            elif y >= 20: return 16, 24
            elif y >= 17: return 12, 15
            else: return 12, 14
        elif (bank, num) == (6, 2):
            # Pewter Gym
            return 4, 6
        elif (bank, num) in self.WALKABLE_BOUNDS:
            return self.WALKABLE_BOUNDS[(bank, num)][0], self.WALKABLE_BOUNDS[(bank, num)][1]
        return 0, 40

    def clamp_to_walkable(self, bank: int, num: int, x: int, y: int) -> Tuple[int, int]:
        """Clamps coordinate to strictly walkable within-bounds tiles using piecewise map geometry."""
        if (bank, num) in self.WALKABLE_BOUNDS:
            _, _, min_y, max_y = self.WALKABLE_BOUNDS[(bank, num)]
            clamped_y = max(min_y, min(max_y, y))
            min_x, max_x = self.get_walkable_x_bounds(bank, num, clamped_y)
            clamped_x = max(min_x, min(max_x, x))
            return clamped_x, clamped_y
        return x, y

    def is_walkable(self, bank: int, num: int, x: int, y: int) -> bool:
        """Returns True if (x, y) is on a strictly walkable tile within the map corridor."""
        cx, cy = self.clamp_to_walkable(bank, num, x, y)
        return (cx == x and cy == y)

    def to_global_tile_coords(self, bank: int, num: int, x: int, y: int) -> Tuple[int, int]:
        """Returns global (tile_x, tile_y) on the canonical GBA FireRed composite map grid."""
        cx, cy = self.clamp_to_walkable(bank, num, x, y)
        if (bank, num) == (1, 0):
            # Viridian Forest interior smoothly mapped onto Route 2 Gatehouse corridor (gy 151 -> 118)
            frac_y = max(0.0, min(1.0, (cy - 4) / 40.0))
            frac_x = max(0.0, min(1.0, (cx - 13) / 13.0))
            gy = int(118 + frac_y * (151 - 118))
            gx = int(64 + frac_x * 2)
            return gx, gy
        elif (bank, num) == (6, 2):
            # Pewter Gym interior mapped directly onto Pewter Gym arena facade (gx 63, gy 73..77)
            frac_y = max(0.0, min(1.0, (cy - 3) / 8.0))
            frac_x = max(0.0, min(1.0, (cx - 4) / 2.0))
            gy = int(73 + frac_y * (77 - 73))
            gx = int(62 + frac_x * 2)
            return gx, gy
        offset = self.CANONICAL_OFFSETS.get((bank, num), (62, 262))
        return offset[0] + cx, offset[1] + cy

    def to_global_pixel_coords(self, bank: int, num: int, x: int, y: int) -> Tuple[int, int]:
        """Returns global pixel (px, py) on kanto_firered_clean.png."""
        tx, ty = self.to_global_tile_coords(bank, num, x, y)
        return int(tx * self.tile_size), int(ty * self.tile_size)

    def to_global_coords(self, bank: int, num: int, x: int, y: int) -> Tuple[int, int]:
        """Alias for backwards compatibility with swarm renderer."""
        return self.to_global_pixel_coords(bank, num, x, y)

    def get_landmark_name(self, bank: int, num: int) -> str:
        return self.LANDMARK_NAMES.get((bank, num), f"Map ({bank}, {num})")
