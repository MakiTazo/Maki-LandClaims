from endstone.event import BlockPlaceEvent, BlockBreakEvent
from endstone_landclaims.services.protection_service import ProtectionService
from endstone_landclaims.config import ConfigManager

class BlockEventHandler:

    def __init__(self, protection_service: ProtectionService, config: ConfigManager) -> None:
        self.protection = protection_service
        self.config = config

    def handle_block_place(self, event: BlockPlaceEvent) -> None:
        if not self.config.get("protection.protect_block_place", True):
            return
        self._handle_block_event(event)

    def handle_block_break(self, event: BlockBreakEvent) -> None:
        if not self.config.get("protection.protect_block_break", True):
            return
        self._handle_block_event(event)

    def _handle_block_event(self, event) -> None:
        player = event.player
        block = event.block

        can_build, reason = self.protection.can_build(
            block.x,
            block.z,
            player_xuid=int(player.xuid),
            dimension=self._get_dimension_key(block),
            is_op=player.is_op,
        )

        if not can_build:
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