from typing import List
from endstone import Player
from endstone_landclaims.commands.base_handler import BaseHandler
from endstone_landclaims.models.basemate import BasemateRank


class MembersHandler(BaseHandler):

    _RANK_LABELS = {
        BasemateRank.MEMBER: "Member",
        BasemateRank.MANAGER: "Manager",
        BasemateRank.OWNER: "Owner",
    }

    def handle(self, player: Player, args: List[str]) -> bool:
        claim = self._get_claim_at_player(player)

        if not claim:
            player.send_message("§7You are in wilderness (no claim here).")
            return True

        player.send_message(f"§b=== Members of {claim.name} ===")
        player.send_message(f"§7Owner: §e{claim.owner_name}")

        player.send_message("§7Basemates:")
        if claim.basemates:
            for xuid in claim.basemates:
                rank = claim.basemate_ranks.get(xuid, BasemateRank.MEMBER)
                rank_label = self._RANK_LABELS.get(BasemateRank(rank), "Member")
                name = self._resolve_name(xuid)
                player.send_message(f"§7- §e{name} §7({rank_label})")
        else:
            player.send_message("§7  None")

        clan_members = self.protection.get_clan_members_xuids(claim.owner_xuid)
        clan_members -= {claim.owner_xuid, *claim.basemates}

        player.send_message("§7Clan members:")
        if clan_members:
            for xuid in clan_members:
                name = self._resolve_name(xuid)
                player.send_message(f"§7- §e{name}")
        else:
            player.send_message("§7  None")

        return True

    def _resolve_name(self, xuid: int) -> str:
        for online in self.plugin.server.online_players:
            if int(online.xuid) == xuid:
                return online.name

        record = self.claim_service.db.get_player_by_xuid(xuid)
        if record:
            return record["name"]

        return f"Unknown ({xuid})"