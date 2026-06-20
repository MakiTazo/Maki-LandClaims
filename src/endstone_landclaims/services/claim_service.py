from typing import List, Optional, Dict, Any
from endstone_landclaims.models.claim import ClaimData
from endstone_landclaims.database import Database
from endstone_landclaims.config import ConfigManager


class ClaimService:

    def __init__(self, db: Database, config: ConfigManager) -> None:
        self.db = db
        self.config = config

    def get_max_claims_per_player(self) -> int:
        return int(self.config.get("claims.max_per_player", 3))

    def get_claim_expiration_days(self) -> int:
        return int(self.config.get("economy.claim_expiration_days", 7))

    def get_grace_period_days(self) -> int:
        return int(self.config.get("economy.grace_period_days", 2))

    def get_contribution_radius(self) -> int:
        default_radius = int(self.config.get("claims.default_radius", 50))
        return default_radius // 2

    def _claim_from_dict(self, db_claim: Dict[str, Any], owner_name: Optional[str] = None) -> ClaimData:
        if owner_name is None:
            owner = self.db.get_player_by_xuid(db_claim["owner_xuid"])
            owner_name = owner["name"] if owner else "Unknown"

        return ClaimData(
            claim_id=db_claim["id"],
            owner_xuid=db_claim["owner_xuid"],
            owner_name=owner_name,
            name=db_claim["name"],
            x1=db_claim["x1"],
            z1=db_claim["z1"],
            x2=db_claim["x2"],
            z2=db_claim["z2"],
            center_y=db_claim.get("center_y", 64),
            dimension=db_claim["dimension"],
            created_at=db_claim["created_at"],
            expires_at=db_claim["expires_at"],
            is_expired=bool(db_claim["is_expired"]),
        )

    def create_claim(
        self,
        owner_xuid: int,
        owner_name: str,
        claim_name: str,
        x1: int,
        z1: int,
        x2: int,
        z2: int,
        center_y: int = 64,
        dimension: str = "overworld",
    ) -> Optional[ClaimData]:
        claim_id = f"{owner_name}_{len(self.get_player_claims(owner_xuid))}"
        expiration_days = self.get_claim_expiration_days()

        try:
            db_claim = self.db.create_claim(
                claim_id=claim_id,
                owner_xuid=owner_xuid,
                owner_name=owner_name,
                name=claim_name,
                x1=x1,
                z1=z1,
                x2=x2,
                z2=z2,
                center_y=center_y,
                dimension=dimension,
                expiration_days=expiration_days,
            )
            return self._claim_from_dict(db_claim, owner_name)
        except Exception:
            return None

    def get_claim(self, claim_id: str) -> Optional[ClaimData]:
        try:
            db_claim = self.db.get_claim(claim_id)
            if not db_claim:
                return None

            claim = self._claim_from_dict(db_claim)

            perms = self.db.get_permissions(claim_id)
            if perms:
                claim.permissions = {
                    "allow_build": bool(perms["allow_build"]),
                    "allow_interact": bool(perms["allow_interact"]),
                    "allow_mob_damage": bool(perms["allow_mob_damage"]),
                    "allow_pvp": bool(perms["allow_pvp"]),
                }

            for bm in self.db.get_basemates(claim_id):
                claim.basemates.append(bm["player_xuid"])
                claim.basemate_ranks[bm["player_xuid"]] = bm["rank"]

            return claim
        except Exception:
            return None

    def get_player_claims(self, owner_xuid: int) -> List[ClaimData]:
        try:
            return [
                self._claim_from_dict(db_claim)
                for db_claim in self.db.get_claims_by_owner(owner_xuid)
            ]
        except Exception:
            return []

    def get_claim_at_position(self, x: int, z: int, dimension: str = "overworld") -> Optional[ClaimData]:
        try:
            db_claim = self.db.get_claim_at_position(x, z, dimension)
            if not db_claim:
                return None
            return self.get_claim(db_claim["id"])
        except Exception:
            return None

    def get_all_claims(self, dimension: str = "overworld") -> List[ClaimData]:
        try:
            return [
                claim
                for db_claim in self.db.get_all_claims(dimension)
                if (claim := self.get_claim(db_claim["id"])) is not None
            ]
        except Exception:
            return []

    def update_claim(
        self,
        claim_id: str,
        name: Optional[str] = None,
        x1: Optional[int] = None,
        z1: Optional[int] = None,
        x2: Optional[int] = None,
        z2: Optional[int] = None,
        center_y: Optional[int] = None,
    ) -> bool:
        try:
            updates: Dict[str, Any] = {}

            if name is not None:
                updates["name"] = name
            if x1 is not None and x2 is not None:
                updates["x1"] = min(x1, x2)
                updates["x2"] = max(x1, x2)
            if z1 is not None and z2 is not None:
                updates["z1"] = min(z1, z2)
                updates["z2"] = max(z1, z2)
            if center_y is not None:
                updates["center_y"] = center_y

            return self.db.update_claim(claim_id, **updates) if updates else True
        except Exception:
            return False

    def delete_claim(self, claim_id: str) -> bool:
        try:
            return self.db.delete_claim(claim_id)
        except Exception:
            return False

    def renew_claim_subscription(self, claim_id: str, days: Optional[int] = None) -> bool:
        try:
            return self.db.renew_claim(claim_id, days or self.get_claim_expiration_days())
        except Exception:
            return False

    def set_claim_permissions(
        self,
        claim_id: str,
        allow_build: Optional[bool] = None,
        allow_interact: Optional[bool] = None,
        allow_mob_damage: Optional[bool] = None,
        allow_pvp: Optional[bool] = None,
    ) -> bool:
        try:
            updates: Dict[str, Any] = {}

            if allow_build is not None:
                updates["allow_build"] = int(allow_build)
            if allow_interact is not None:
                updates["allow_interact"] = int(allow_interact)
            if allow_mob_damage is not None:
                updates["allow_mob_damage"] = int(allow_mob_damage)
            if allow_pvp is not None:
                updates["allow_pvp"] = int(allow_pvp)

            return self.db.set_permissions(claim_id, **updates) if updates else True
        except Exception:
            return False

    def add_basemate(self, claim_id: str, player_xuid: int, rank: int = 0) -> bool:
        try:
            return self.db.add_basemate(claim_id, player_xuid, rank)
        except Exception:
            return False

    def remove_basemate(self, claim_id: str, player_xuid: int) -> bool:
        try:
            return self.db.remove_basemate(claim_id, player_xuid)
        except Exception:
            return False

    def set_basemate_rank(self, claim_id: str, player_xuid: int, rank: int) -> bool:
        try:
            return self.db.set_basemate_rank(claim_id, player_xuid, rank)
        except Exception:
            return False

    def get_basemate_rank(self, claim_id: str, player_xuid: int) -> Optional[int]:
        try:
            return self.db.get_basemate_rank(claim_id, player_xuid)
        except Exception:
            return None

    def is_basemate(self, claim_id: str, player_xuid: int) -> bool:
        return self.get_basemate_rank(claim_id, player_xuid) is not None

    def mark_expired_claims(self) -> int:
        try:
            return self.db.mark_expired_claims()
        except Exception:
            return 0

    def cleanup_expired_claims(self) -> int:
        try:
            grace_days = self.get_grace_period_days()
            expired_claims = self.db.get_expired_claims(grace_days)
            return sum(1 for claim in expired_claims if self.delete_claim(claim["id"]))
        except Exception:
            return 0

    def get_contributions_count(self, player_xuid: int) -> int:
        try:
            return len(self.db.get_contributions_by_player(player_xuid))
        except Exception:
            return 0

    def player_has_claim_space(self, owner_xuid: int) -> bool:
        own_claims = len(self.get_player_claims(owner_xuid))
        contributions = self.get_contributions_count(owner_xuid)
        return (own_claims + contributions) < self.get_max_claims_per_player()

    def contribute_to_claim(self, claim_id: str, player_xuid: int) -> Optional[ClaimData]:
        try:
            claim = self.get_claim(claim_id)
            if not claim:
                return None

            added_radius = self.get_contribution_radius()
            if added_radius <= 0:
                return None

            new_radius = claim.radius + added_radius

            success = self.db.update_claim(
                claim_id,
                x1=int(claim.center_x - new_radius),
                z1=int(claim.center_z - new_radius),
                x2=int(claim.center_x + new_radius),
                z2=int(claim.center_z + new_radius),
            )

            if not success:
                return None

            self.db.add_contribution(claim_id, player_xuid, added_radius)
            return self.get_claim(claim_id)
        except Exception:
            return None

    def release_player_contributions(self, claim_id: str, player_xuid: int) -> int:
        try:
            return self.db.remove_contributions(claim_id, player_xuid)
        except Exception:
            return 0

    def release_all_player_contributions(self, player_xuid: int) -> List[str]:
        try:
            return self.db.remove_all_player_contributions(player_xuid)
        except Exception:
            return []