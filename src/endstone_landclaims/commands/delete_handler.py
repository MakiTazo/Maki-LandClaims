from typing import List
from endstone import Player
from endstone_landclaims.commands.base_handler import BaseHandler

class DeleteHandler(BaseHandler):

    def handle(self, player: Player, args: List[str]) -> bool:
        if not args:
            player.send_message("§cUsage: /claimdelete <claim_name>")
            return True

        claim_name = " ".join(args)
        claims = self.claim_service.get_player_claims(int(player.xuid))
        claim_to_delete = next((c for c in claims if c.name.lower() == claim_name.lower()), None)

        if not claim_to_delete:
            player.send_message(f"§cClaim '{claim_name}' not found.")
            return True

        if self.claim_service.delete_claim(claim_to_delete.id):
            player.send_message(f"§aDeleted claim: {claim_to_delete.name}")
        else:
            player.send_message("§cFailed to delete claim.")

        return True