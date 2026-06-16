from typing import Optional, Tuple
from endstone_landclaim.models.basemate import BasemateRank
from endstone_landclaim.models.claim import ClaimData
from endstone_landclaim.config import ConfigManager
from endstone_landclaim.services.claim_service import ClaimService

class ProtectionService:

    def __init__(self, config: ConfigManager, claim_service: ClaimService) -> None:
        self.config = config
        self.claim_service = claim_service

    def is_protection_enabled(self, protection_type: str) -> bool:
        return bool(self.config.get(f"protection.{protection_type}", True))

    def _get_claim(self, x: int, z: int, dimension: str) -> Optional[ClaimData]:
        return self.claim_service.get_claim_at_position(x, z, dimension)

    def _is_allowed_in_claim(self, claim: ClaimData, player_uuid: str) -> bool:
        return (
            claim.owner_uuid == player_uuid
            or self.claim_service.is_basemate(claim.id, player_uuid)
        )

    def _is_env_action_allowed(self, protection_type: str, x: int, z: int, dimension: str) -> bool:
        if not self.is_protection_enabled(protection_type):
            return True
        return self._get_claim(x, z, dimension) is None

    def can_build(
        self,
        x: int,
        z: int,
        player_uuid: str,
        dimension: str = "overworld",
        is_op: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        if not self.is_protection_enabled("protect_block_place"):
            return True, None
        if not self.is_protection_enabled("protect_block_break"):
            return True, None
        if is_op:
            return True, None

        claim = self._get_claim(x, z, dimension)
        if not claim:
            return True, None
        if self._is_allowed_in_claim(claim, player_uuid):
            return True, None
        if claim.permissions.get("allow_build", False):
            return True, None

        return False, f"Cannot build in {claim.name} (owner: {claim.owner_name})"

    def can_interact(
        self,
        x: int,
        z: int,
        player_uuid: str,
        dimension: str = "overworld",
        is_op: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        if not self.is_protection_enabled("protect_interact"):
            return True, None
        if is_op:
            return True, None

        claim = self._get_claim(x, z, dimension)
        if not claim:
            return True, None
        if self._is_allowed_in_claim(claim, player_uuid):
            return True, None
        if claim.permissions.get("allow_interact", False):
            return True, None

        return False, f"Cannot interact in {claim.name} (owner: {claim.owner_name})"

    def can_damage_entity(
        self,
        victim_x: int,
        victim_z: int,
        attacker_uuid: str,
        is_player: bool = False,
        dimension: str = "overworld",
        is_op: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        if is_op:
            return True, None

        claim = self._get_claim(victim_x, victim_z, dimension)
        if not claim:
            return True, None

        if is_player:
            if not self.is_protection_enabled("protect_pvp"):
                return True, None
            if self._is_allowed_in_claim(claim, attacker_uuid):
                return True, None
            if claim.permissions.get("allow_pvp", False):
                return True, None
            return False, f"PvP is disabled in {claim.name}"

        if not self.is_protection_enabled("protect_passive_mobs"):
            return True, None
        if self._is_allowed_in_claim(claim, attacker_uuid):
            return True, None

        return True, None

    def can_use_explosives(self, x: int, z: int, dimension: str = "overworld") -> bool:
        return self._is_env_action_allowed("protect_explosions", x, z, dimension)

    def can_use_fire(self, x: int, z: int, dimension: str = "overworld") -> bool:
        return self._is_env_action_allowed("protect_fire", x, z, dimension)

    def can_use_piston(self, x: int, z: int, dimension: str = "overworld") -> bool:
        return self._is_env_action_allowed("protect_piston_push", x, z, dimension)

    def is_owner(self, claim_id: str, player_uuid: str) -> bool:
        claim = self.claim_service.get_claim(claim_id)
        return claim is not None and claim.owner_uuid == player_uuid

    def is_manager(self, claim_id: str, player_uuid: str) -> bool:
        rank = self.claim_service.get_basemate_rank(claim_id, player_uuid)
        return rank is not None and rank >= BasemateRank.MANAGER

    def can_manage_claim(self, claim_id: str, player_uuid: str, is_op: bool = False) -> bool:
        if is_op:
            return True
        return self.is_owner(claim_id, player_uuid) or self.is_manager(claim_id, player_uuid)