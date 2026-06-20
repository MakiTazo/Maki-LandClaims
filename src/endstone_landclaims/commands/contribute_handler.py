from typing import List
from endstone import Player, asyncio as endstone_asyncio
from endstone_landclaims.commands.base_handler import BaseHandler


class ContributeHandler(BaseHandler):

    def __init__(self, plugin, config, claim_service, protection_service, economy_service) -> None:
        super().__init__(plugin, config, claim_service, protection_service)
        self.economy = economy_service

    def handle(self, player: Player, args: List[str]) -> bool:
        player_uuid = str(player.unique_id)
        player_xuid = int(player.xuid)

        if self.claim_service.player_has_claim_space(player_xuid) is False:
            player.send_message("§cYou have no claim slots available to contribute.")
            return True

        claim = self._get_claim_at_player(player)
        if not claim:
            player.send_message("§cYou are not standing in a claim.")
            return True

        if not self.protection.is_owner(claim.id, player_xuid) and not self._is_member(claim, player_xuid):
            player.send_message("§cYou are not a member of this claim.")
            return True

        if claim.owner_xuid == player_xuid:
            player.send_message("§cYou cannot contribute to your own claim. You already own it.")
            return True

        added_radius = self.claim_service.get_contribution_radius()
        if added_radius <= 0:
            player.send_message("§cContributions are disabled (radius too small to split).")
            return True

        contribution_cost = self.economy.get_creation_cost() / 2

        has_balance = endstone_asyncio.submit(
            self.economy.check_balance(player_uuid, contribution_cost)
        ).result()

        if not has_balance:
            player.send_message(f"§cInsufficient funds. Need {contribution_cost} coins.")
            return True

        endstone_asyncio.submit(
            self.economy.charge_player(player_uuid, contribution_cost)
        ).result()

        updated_claim = self.claim_service.contribute_to_claim(claim.id, player_xuid)

        if updated_claim:
            player.send_message(f"§aContributed to {updated_claim.name}! New size: {updated_claim.width}x{updated_claim.depth}")
            player.send_message(f"§7Cost: {contribution_cost} coins.")
        else:
            player.send_message("§cFailed to contribute to claim.")

        return True

    def _is_member(self, claim, player_xuid: int) -> bool:
        if player_xuid in claim.basemates:
            return True
        clan_members = self.protection.get_clan_members_xuids(claim.owner_xuid)
        return player_xuid in clan_members