from typing import List, Tuple, Optional
from math import hypot
from endstone_landclaim.models.claim import ClaimData
from endstone_landclaim.config import ConfigManager

class SpacingService:

    def __init__(self, config: ConfigManager) -> None:
        self.config = config

    def get_spawn_center(self) -> Tuple[int, int]:
        spawn = self.config.get("claims.spawn_center", [0, 0])
        return int(spawn[0]), int(spawn[1])

    def get_spawn_radius(self) -> int:
        return int(self.config.get("claims.spawn_protection_radius", 200))

    def get_min_distance_between_claims(self) -> int:
        return int(self.config.get("claims.min_distance_between_claims", 50))

    def get_min_distance_from_spawn(self) -> int:
        return int(self.config.get("claims.min_distance_from_spawn", 100))

    def is_inside_spawn_radius(self, x: int, z: int) -> bool:
        sx, sz = self.get_spawn_center()
        radius = self.get_spawn_radius()
        distance = hypot(x - sx, z - sz)
        return distance <= radius

    def distance_to_spawn(self, x: int, z: int) -> float:
        sx, sz = self.get_spawn_center()
        return hypot(x - sx, z - sz)

    def distance_between_points(self, x1: int, z1: int, x2: int, z2: int) -> float:
        return hypot(x1 - x2, z1 - z2)

    def is_too_close_to_spawn(self, claim: ClaimData) -> bool:
        min_dist = self.get_min_distance_from_spawn()
        spawn_radius = self.get_spawn_radius()

        center_x, center_z = claim.center_x, claim.center_z
        distance = self.distance_to_spawn(int(center_x), int(center_z))

        return distance < spawn_radius + claim.width

    def check_claim_spacing(self, new_claim: ClaimData, existing_claims: List[ClaimData]) -> List[str]:
        conflicts: List[str] = []
        min_distance = self.get_min_distance_between_claims()

        for existing in existing_claims:
            if existing.dimension != new_claim.dimension:
                continue

            distance = new_claim.distance_to_claim(existing)

            if distance < min_distance:
                conflicts.append(existing.owner_name)

        return conflicts

    def get_maximum_radius_at_position(
            self,
            x: int,
            z: int,
            owner_name: str,
            existing_claims: List[ClaimData],
            max_area: int = 10000,
    ) -> int:
        if self.is_inside_spawn_radius(x, z):
            return 0

        max_radius = int(max_area ** 0.5) // 2

        for r in range(max_radius, 0, -10):
            test_claim = ClaimData(
                claim_id="test",
                owner_uuid="test",
                owner_name=owner_name,
                name="test",
                x1=x - r,
                z1=z - r,
                x2=x + r,
                z2=z + r,
            )

            conflicts = self.check_claim_spacing(test_claim, existing_claims)

            if not conflicts:
                return r

        return 0

    def validate_claim_creation(
            self,
            claim: ClaimData,
            existing_claims: List[ClaimData],
    ) -> Tuple[bool, Optional[str]]:
        if self.is_too_close_to_spawn(claim):
            return False, f"Too close to spawn (minimum {self.get_min_distance_from_spawn()} blocks)"

        conflicts = self.check_claim_spacing(claim, existing_claims)
        if conflicts:
            return False, f"Too close to bases: {', '.join(set(conflicts))}"

        return True, None