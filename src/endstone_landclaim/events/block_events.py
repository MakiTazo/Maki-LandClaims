from endstone import Player
from endstone.event import BlockPlaceEvent, BlockBreakEvent
from endstone_landclaim.services.protection_service import ProtectionService
from endstone_landclaim.config import ConfigManager


class BlockEventHandler:

    def __init__(self, protection_service: ProtectionService, config: ConfigManager) -> None:
        self.protection = protection_service
        self.config = config

    def handle_block_place(self, event: BlockPlaceEvent) -> None:
        player = event.player
        if not isinstance(player, Player):
            return

        if not self.config.get("protection.protect_block_place", True):
            return

        block = event.block
        x = int(block.x)
        z = int(block.z)
        dimension = self._get_dimension_key(player)

        can_build, reason = self.protection.can_build(
            x, z,
            player_uuid=str(player.unique_id),
            player_name=player.name,
            dimension=dimension,
            is_op=player.is_op,
        )

        if not can_build:
            event.is_cancelled = True
            player.send_message(f"§c{reason}")

    def handle_block_break(self, event: BlockBreakEvent) -> None:
        player = event.player
        if not isinstance(player, Player):
            return

        if not self.config.get("protection.protect_block_break", True):
            return

        block = event.block
        x = int(block.x)
        z = int(block.z)
        dimension = self._get_dimension_key(player)

        can_build, reason = self.protection.can_build(
            x, z,
            player_uuid=str(player.unique_id),
            player_name=player.name,
            dimension=dimension,
            is_op=player.is_op,
        )

        if not can_build:
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