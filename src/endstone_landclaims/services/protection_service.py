from typing import Optional, Tuple
from endstone_landclaims.models.basemate import BasemateRank
from endstone_landclaims.models.claim import ClaimData
from endstone_landclaims.config import ConfigManager
from endstone_landclaims.services.claim_service import ClaimService

try:
    from endstone_clans_api import ClansApi
except ImportError:
    ClansApi = None


class ProtectionService:

    def __init__(
        self,
        config: ConfigManager,
        claim_service: ClaimService,
        clans_api=None,
    ) -> None:
        self.config = config
        self.claim_service = claim_service
        self.clans_api = clans_api

    def is_protection_enabled(self, protection_type: str) -> bool:
        return bool(self.config.get(f"protection.{protection_type}", True))

    def _get_claim(self, x: int, z: int, dimension: str) -> Optional[ClaimData]:
        return self.claim_service.get_claim_at_position(x, z, dimension)

    def _are_clan_mates(self, xuid_a: int, xuid_b: int) -> bool:
        if not self.clans_api:
            return False
        try:
            clan_a = self.clans_api.db.get_member_clan(xuid_a)
            if not clan_a:
                return False
            return xuid_b in clan_a.members_xuids
        except Exception:
            return False

    def get_clan_members_xuids(self, owner_xuid: int) -> set:
        if not self.clans_api:
            return set()
        try:
            clan = self.clans_api.db.get_member_clan(owner_xuid)
            if not clan:
                return set()
            return clan.members_xuids
        except Exception:
            return set()

    def _is_allowed_in_claim(self, claim: ClaimData, player_xuid: int) -> bool:
        if claim.owner_xuid == player_xuid:
            return True
        if self.claim_service.is_basemate(claim.id, player_xuid):
            return True
        if self.clans_api and self._are_clan_mates(claim.owner_xuid, player_xuid):
            return True
        return False

    def _is_env_action_allowed(self, protection_type: str, x: int, z: int, dimension: str) -> bool:
        if not self.is_protection_enabled(protection_type):
            return True
        return self._get_claim(x, z, dimension) is None

    def can_build(
        self,
        x: int,
        z: int,
        player_xuid: int,
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
        if self._is_allowed_in_claim(claim, player_xuid):
            return True, None
        if claim.permissions.get("allow_build", False):
            return True, None

        return False, f"Cannot build in {claim.name} (owner: {claim.owner_name})"

    def can_interact(
        self,
        x: int,
        z: int,
        player_xuid: int,
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
        if self._is_allowed_in_claim(claim, player_xuid):
            return True, None
        if claim.permissions.get("allow_interact", False):
            return True, None

        return False, f"Cannot interact in {claim.name} (owner: {claim.owner_name})"

    def can_damage_entity(
        self,
        victim_x: int,
        victim_z: int,
        attacker_xuid: int = 0,
        victim_xuid: int = 0,
        is_pvp: bool = False,
        dimension: str = "overworld",
        is_op: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        if is_op:
            return True, None

        claim = self._get_claim(victim_x, victim_z, dimension)
        if not claim:
            return True, None

        if is_pvp:
            if not self.is_protection_enabled("protect_pvp"):
                return True, None
            if self._is_allowed_in_claim(claim, attacker_xuid):
                return True, None
            if claim.permissions.get("allow_pvp", False):
                return True, None
            return False, f"PvP is disabled in {claim.name}"

        if not self.is_protection_enabled("protect_passive_mobs"):
            return True, None
        if self._is_allowed_in_claim(claim, attacker_xuid):
            return True, None
        if victim_xuid and not self._is_allowed_in_claim(claim, victim_xuid):
            return True, None

        return False, None

    def can_use_explosives(self, x: int, z: int, dimension: str = "overworld") -> bool:
        return self._is_env_action_allowed("protect_explosions", x, z, dimension)

    def can_use_fire(self, x: int, z: int, dimension: str = "overworld") -> bool:
        return self._is_env_action_allowed("protect_fire", x, z, dimension)

    def can_use_piston(self, x: int, z: int, dimension: str = "overworld") -> bool:
        return self._is_env_action_allowed("protect_piston_push", x, z, dimension)

    def is_owner(self, claim_id: str, player_xuid: int) -> bool:
        claim = self.claim_service.get_claim(claim_id)
        return claim is not None and claim.owner_xuid == player_xuid

    def is_manager(self, claim_id: str, player_xuid: int) -> bool:
        rank = self.claim_service.get_basemate_rank(claim_id, player_xuid)
        return rank is not None and rank >= BasemateRank.MANAGER

    def can_manage_claim(self, claim_id: str, player_xuid: int, is_op: bool = False) -> bool:
        if is_op:
            return True
        return self.is_owner(claim_id, player_xuid) or self.is_manager(claim_id, player_xuid)