from typing import Dict, Any, List, Optional
from datetime import datetime

class ClaimData:

    def __init__(
        self,
        claim_id: str,
        owner_uuid: str,
        owner_name: str,
        name: str,
        x1: int,
        z1: int,
        x2: int,
        z2: int,
        dimension: str = "overworld",
        created_at: Optional[str] = None,
        expires_at: Optional[str] = None,
        is_expired: bool = False,
    ) -> None:
        self.id = claim_id
        self.owner_uuid = owner_uuid
        self.owner_name = owner_name
        self.name = name
        self.x1 = min(x1, x2)
        self.z1 = min(z1, z2)
        self.x2 = max(x1, x2)
        self.z2 = max(z1, z2)
        self.dimension = dimension
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.expires_at = expires_at
        self.is_expired = is_expired

        self.basemates: List[str] = []
        self.basemate_ranks: Dict[str, int] = {}
        self.permissions: Dict[str, bool] = {
            "allow_build": False,
            "allow_interact": False,
            "allow_mob_damage": False,
            "allow_pvp": False,
        }

    @property
    def width(self) -> int:
        return abs(self.x2 - self.x1) + 1

    @property
    def depth(self) -> int:
        return abs(self.z2 - self.z1) + 1

    @property
    def area(self) -> int:
        return self.width * self.depth

    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2.0

    @property
    def center_z(self) -> float:
        return (self.z1 + self.z2) / 2.0

    def contains_point(self, x: int, z: int) -> bool:
        return self.x1 <= x <= self.x2 and self.z1 <= z <= self.z2

    def overlaps(self, other: "ClaimData") -> bool:
        return not (self.x2 < other.x1 or self.x1 > other.x2 or
                   self.z2 < other.z1 or self.z1 > other.z2)

    def distance_to_point(self, x: int, z: int) -> int:
        dx = max(self.x1 - x, 0, x - self.x2)
        dz = max(self.z1 - z, 0, z - self.z2)
        return int((dx * dx + dz * dz) ** 0.5)

    def distance_to_claim(self, other: "ClaimData") -> int:
        dx = max(self.x2, other.x1) - min(self.x1, other.x2)
        dz = max(self.z2, other.z1) - min(self.z1, other.z2)
        if dx < 0:
            dx = 0
        if dz < 0:
            dz = 0
        return int((dx * dx + dz * dz) ** 0.5)

    def is_expired_now(self) -> bool:
        if not self.expires_at:
            return False
        try:
            exp_dt = datetime.fromisoformat(self.expires_at)
            return datetime.utcnow() > exp_dt
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "owner_uuid": self.owner_uuid,
            "owner_name": self.owner_name,
            "name": self.name,
            "x1": self.x1,
            "z1": self.z1,
            "x2": self.x2,
            "z2": self.z2,
            "dimension": self.dimension,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "is_expired": self.is_expired,
            "basemates": self.basemates,
            "basemate_ranks": self.basemate_ranks,
            "permissions": self.permissions,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ClaimData":
        claim = ClaimData(
            claim_id=data["id"],
            owner_uuid=data["owner_uuid"],
            owner_name=data.get("owner_name", "Unknown"),
            name=data["name"],
            x1=data["x1"],
            z1=data["z1"],
            x2=data["x2"],
            z2=data["z2"],
            dimension=data.get("dimension", "overworld"),
            created_at=data.get("created_at"),
            expires_at=data.get("expires_at"),
            is_expired=data.get("is_expired", False),
        )
        claim.basemates = data.get("basemates", [])
        claim.basemate_ranks = data.get("basemate_ranks", {})
        claim.permissions = data.get("permissions", claim.permissions)
        return claim

    def __repr__(self) -> str:
        return (
            f"ClaimData(id={self.id}, owner={self.owner_name}, "
            f"area={self.area}, dim={self.dimension})"
        )