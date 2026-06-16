from endstone import Player
from endstone.actor import Actor
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

        victim_x = int(victim.location.x)
        victim_z = int(victim.location.z)
        victim_dimension = self._get_dimension_key(victim)
        attacker_x = int(attacker.location.x)
        attacker_z = int(attacker.location.z)
        attacker_dimension = self._get_dimension_key(attacker)
        is_player_victim = isinstance(victim, Player)
        is_op_attacker = isinstance(attacker, Player) and attacker.is_op
        can_damage, reason = self.protection.can_damage_entity(
            victim_x, victim_z,
            attacker_uuid=str(attacker.unique_id) if isinstance(attacker, Player) else "",
            attacker_name=attacker.name if isinstance(attacker, Player) else str(attacker.type),
            is_player=is_player_victim,
            dimension=victim_dimension,
            is_op=is_op_attacker,
        )
        if not can_damage:
            event.is_cancelled = True
            if isinstance(attacker, Player):
                attacker.send_message(f"§c{reason}")

    def _get_dimension_key(self, entity: Actor) -> str:
        try:
            dim = entity.location.dimension
            dim_name = dim.name.lower()
            if "nether" in dim_name:
                return "nether"
            if "end" in dim_name:
                return "end"
        except Exception:
            pass
        return "overworld"