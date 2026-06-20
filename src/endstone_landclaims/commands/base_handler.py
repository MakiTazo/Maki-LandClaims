from typing import Optional
from endstone import Player
from endstone.command import CommandSender

class BaseHandler:

    def __init__(self, plugin, config, claim_service, protection_service) -> None:
        self.plugin = plugin
        self.config = config
        self.claim_service = claim_service
        self.protection = protection_service

    def _as_player(self, sender: CommandSender) -> Optional[Player]:
        return sender if isinstance(sender, Player) else None

    def _get_dimension_key(self, player: Player) -> str:
        try:
            dim_name = player.location.dimension.name.lower()
            if "nether" in dim_name:
                return "nether"
            if "end" in dim_name:
                return "end"
        except Exception:
            pass
        return "overworld"

    def _get_claim_at_player(self, player: Player):
        location = player.location
        return self.claim_service.get_claim_at_position(
            int(location.x), int(location.z), self._get_dimension_key(player)
        )