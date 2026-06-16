from typing import Any
from endstone_landclaim.services.protection_service import ProtectionService
from endstone_landclaim.config import ConfigManager

class ExplosionEventHandler:

    def __init__(self, protection_service: ProtectionService, config: ConfigManager) -> None:
        self.protection = protection_service
        self.config = config

    def handle_block_explode(self, event: Any) -> None:
        if not self.config.get("protection.protect_explosions", True):
            return

        block_list = event.block_list
        if not block_list:
            return

        protected_blocks = []

        for block in block_list:
            x, z = self._get_block_coords(block)

            if not self.protection.can_use_explosives(x, z):
                protected_blocks.append(block)

        for block in protected_blocks:
            if block in block_list:
                block_list.remove(block)

    def handle_piston_move(self, event: Any) -> None:
        if not self.config.get("protection.protect_piston_push", True):
            return

        block = event.block
        x, z = self._get_block_coords(block)

        if not self.protection.can_use_piston(x, z):
            event.is_cancelled = True

    def _get_block_coords(self, block: Any) -> tuple:
        try:
            x = int(getattr(block, "x", 0))
            z = int(getattr(block, "z", 0))
            return x, z
        except Exception:
            pass
        return 0, 0