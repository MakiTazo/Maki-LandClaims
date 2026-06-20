from endstone.event import PlayerInteractEvent
from endstone_landclaims.services.protection_service import ProtectionService
from endstone_landclaims.config import ConfigManager

class InteractEventHandler:

    def __init__(self, protection_service: ProtectionService, config: ConfigManager) -> None:
        self.protection = protection_service
        self.config = config

    def handle_player_interact(self, event: PlayerInteractEvent) -> None:
        if not self.config.get("protection.protect_interact", True):
            return

        if not event.has_block:
            return

        player = event.player
        block = event.block

        can_interact, reason = self.protection.can_interact(
            block.x,
            block.z,
            player_xuid=int(player.xuid),
            dimension=self._get_dimension_key(block),
            is_op=player.is_op,
        )

        if not can_interact:
            event.is_cancelled = True
            player.send_message(f"§c{reason}")

    def _get_dimension_key(self, block) -> str:
        try:
            dim_name = block.dimension.name.lower()
            if "nether" in dim_name:
                return "nether"
            if "end" in dim_name:
                return "end"
        except Exception:
            pass
        return "overworld"