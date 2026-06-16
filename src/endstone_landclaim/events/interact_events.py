from endstone import Player
from endstone.event import PlayerInteractEvent
from endstone_landclaim.services.protection_service import ProtectionService
from endstone_landclaim.config import ConfigManager

class InteractEventHandler:

    def __init__(self, protection_service: ProtectionService, config: ConfigManager) -> None:
        self.protection = protection_service
        self.config = config

    def handle_player_interact(self, event: PlayerInteractEvent) -> None:
        player = event.player
        if not isinstance(player, Player):
            return

        if not self.config.get("protection.protect_interact", True):
            return

        if not event.has_block:
            return

        block = event.block
        x = int(block.x)
        z = int(block.z)
        dimension = self._get_dimension_key(player)

        can_interact, reason = self.protection.can_interact(
            x, z,
            player_uuid=str(player.unique_id),
            player_name=player.name,
            dimension=dimension,
            is_op=player.is_op,
        )

        if not can_interact:
            event.is_cancelled = True
            player.send_message(f"§c{reason}")

    def _get_dimension_key(self, player: Player) -> str:
        try:
            dim = player.location.dimension
            dim_name = dim.name.lower()
            if "nether" in dim_name:
                return "nether"
            if "end" in dim_name:
                return "end"
        except Exception:
            pass
        return "overworld"