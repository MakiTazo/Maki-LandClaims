from typing import List
from endstone import Player
from endstone_landclaims.commands.base_handler import BaseHandler

class InfoHandler(BaseHandler):

    def handle(self, player: Player, args: List[str]) -> bool:
        claim = self._get_claim_at_player(player)

        if not claim:
            player.send_message("§7You are in wilderness (no claim here).")
            return True

        player.send_message("§b=== Claim Info ===")
        player.send_message(f"§7Name: §e{claim.name}")
        player.send_message(f"§7Owner: §e{claim.owner_name}")
        player.send_message(f"§7Area: §e{claim.width}x{claim.depth} = {claim.area} blocks")
        player.send_message(f"§7Center: §e{int(claim.center_x)}, {int(claim.center_z)}")
        player.send_message(f"§7Dimension: §e{claim.dimension}")
        return True