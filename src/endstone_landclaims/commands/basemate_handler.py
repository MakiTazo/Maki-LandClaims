from typing import List
from endstone import Player
from endstone_landclaims.commands.base_handler import BaseHandler

class BasemateHandler(BaseHandler):

    def handle_add(self, player: Player, args: List[str]) -> bool:
        if not args:
            player.send_message("§cUsage: /claimadd <player_name>")
            return True

        claim = self._get_claim_at_player(player)
        if not claim:
            player.send_message("§cYou are not in a claim.")
            return True

        if not self.protection.is_owner(claim.id, int(player.xuid)):
            player.send_message("§cYou are not the owner of this claim.")
            return True

        mate_name = args[0]
        try:
            mate_player = self.claim_service.db.get_player_by_name(mate_name)
            if not mate_player:
                player.send_message(f"§cPlayer '{mate_name}' not found in database.")
                return True

            if self.claim_service.add_basemate(claim.id, mate_player["xuid"]):
                player.send_message(f"§aAdded {mate_name} as a basemate.")
            else:
                player.send_message(f"§c{mate_name} is already a basemate.")
        except Exception:
            player.send_message("§cError adding basemate.")

        return True

    def handle_remove(self, player: Player, args: List[str]) -> bool:
        if not args:
            player.send_message("§cUsage: /claimremove <player_name>")
            return True

        claim = self._get_claim_at_player(player)
        if not claim:
            player.send_message("§cYou are not in a claim.")
            return True

        if not self.protection.is_owner(claim.id, int(player.xuid)):
            player.send_message("§cYou are not the owner of this claim.")
            return True

        mate_name = args[0]
        try:
            mate_player = self.claim_service.db.get_player_by_name(mate_name)
            if not mate_player:
                player.send_message(f"§cPlayer '{mate_name}' not found.")
                return True

            if self.claim_service.remove_basemate(claim.id, mate_player["xuid"]):
                player.send_message(f"§aRemoved {mate_name} from basemates.")
            else:
                player.send_message(f"§c{mate_name} is not a basemate.")
        except Exception:
            player.send_message("§cError removing basemate.")

        return True