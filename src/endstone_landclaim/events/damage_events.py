from endstone import Player
from endstone.event import ActorDamageEvent
from endstone_landclaim.services.protection_service import ProtectionService
from endstone_landclaim.config import ConfigManager

class DamageEventHandler:

    def __init__(self, protection_service: ProtectionService, config: ConfigManager) -> None:
        self.protection = protection_service
        self.config = config

    def handle_entity_damage(self, event: ActorDamageEvent) -> None:
        victim = event.actor
        if not victim:
            return

        attacker = event.damage_source.damaging_actor if event.damage_source else None
        if not attacker:
            return

        is_player_attacker = isinstance(attacker, Player)
        is_player_victim = isinstance(victim, Player)

        can_damage, reason = self.protection.can_damage_entity(
            int(victim.location.x),
            int(victim.location.z),
            attacker_uuid=str(attacker.unique_id) if is_player_attacker else "",
            victim_uuid=str(victim.unique_id) if is_player_victim else "",
            is_pvp=is_player_attacker and is_player_victim,
            dimension=self._get_dimension_key(victim),
            is_op=is_player_attacker and attacker.is_op,
        )

        if not can_damage:
            event.is_cancelled = True
            if is_player_attacker:
                attacker.send_message(f"§c{reason}")

    def _get_dimension_key(self, actor) -> str:
        try:
            dim_name = actor.dimension.name.lower()
            if "nether" in dim_name:
                return "nether"
            if "end" in dim_name:
                return "end"
        except Exception:
            pass
        return "overworld"