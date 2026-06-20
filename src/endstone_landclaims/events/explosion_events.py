from endstone.event import (
    ActorExplodeEvent,
    BlockExplodeEvent,
    BlockPistonExtendEvent,
    BlockPistonRetractEvent,
)
from endstone_landclaims.services.protection_service import ProtectionService
from endstone_landclaims.config import ConfigManager

class ExplosionEventHandler:

    def __init__(self, protection_service: ProtectionService, config: ConfigManager) -> None:
        self.protection = protection_service
        self.config = config

    def handle_block_explode(self, event: BlockExplodeEvent) -> None:
        if not self.config.get("protection.protect_explosions", True):
            return
        if not event.block_list:
            return
        event.block_list = [
            block for block in event.block_list
            if self.protection.can_use_explosives(block.x, block.z)
        ]

    def handle_actor_explode(self, event: ActorExplodeEvent) -> None:
        if not self.config.get("protection.protect_explosions", True):
            return
        if not event.block_list:
            return
        event.block_list = [
            block for block in event.block_list
            if self.protection.can_use_explosives(block.x, block.z)
        ]

    def handle_piston_extend(self, event: BlockPistonExtendEvent) -> None:
        self._handle_piston(event)

    def handle_piston_retract(self, event: BlockPistonRetractEvent) -> None:
        self._handle_piston(event)

    def _handle_piston(self, event) -> None:
        if not self.config.get("protection.protect_piston_push", True):
            return
        block = event.block
        if not self.protection.can_use_piston(block.x, block.z):
            event.is_cancelled = True