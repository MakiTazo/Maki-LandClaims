from typing import List
from endstone import Player
from endstone_landclaims.commands.base_handler import BaseHandler

class ListHandler(BaseHandler):

    def handle(self, player: Player, args: List[str]) -> bool:
        claims = self.claim_service.get_player_claims(int(player.xuid))

        if not claims:
            player.send_message("§7You have no claims.")
            return True

        player.send_message(f"§b=== Your Claims ({len(claims)}) ===")
        for claim in claims:
            status = "§c[EXPIRED]" if claim.is_expired else "§a[ACTIVE]"
            player.send_message(f"§7- {status} §e{claim.name} §7({claim.width}x{claim.depth})")
        return True