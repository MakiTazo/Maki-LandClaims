from typing import List
from endstone import Player, asyncio as endstone_asyncio
from endstone_landclaims.commands.base_handler import BaseHandler
from endstone_landclaims.models.claim import ClaimData


class CreateHandler(BaseHandler):

    def __init__(self, plugin, config, claim_service, protection_service, economy_service, spacing_service) -> None:
        super().__init__(plugin, config, claim_service, protection_service)
        self.economy = economy_service
        self.spacing = spacing_service

    def handle(self, player: Player, args: List[str]) -> bool:
        player_uuid = str(player.unique_id)
        player_xuid = int(player.xuid)

        if not self.claim_service.player_has_claim_space(player_xuid):
            player.send_message("§cYou have reached the maximum number of claims.")
            return True

        location = player.location
        x = int(location.x)
        y = int(location.y)
        z = int(location.z)
        claim_name = " ".join(args) if args else "Claim"
        dimension = self._get_dimension_key(player)
        radius = self.config.get("claims.default_radius", 50)

        candidate = ClaimData(
            claim_id="pending",
            owner_xuid=player_xuid,
            owner_name=player.name,
            name=claim_name,
            x1=x - radius,
            z1=z - radius,
            x2=x + radius,
            z2=z + radius,
            center_y=y,
            dimension=dimension,
        )

        existing_claims = self.claim_service.get_all_claims(dimension)
        is_valid, reason = self.spacing.validate_claim_creation(candidate, existing_claims)

        if not is_valid:
            player.send_message(f"§c{reason}")
            return True

        creation_cost = self.economy.get_creation_cost()
        has_balance = endstone_asyncio.submit(
            self.economy.check_balance(player_uuid, creation_cost)
        ).result()

        if not has_balance:
            player.send_message(f"§cInsufficient funds. Need {creation_cost} coins.")
            return True

        endstone_asyncio.submit(
            self.economy.charge_player(player_uuid, creation_cost)
        ).result()

        claim = self.claim_service.create_claim(
            owner_xuid=player_xuid,
            owner_name=player.name,
            claim_name=claim_name,
            x1=x - radius,
            z1=z - radius,
            x2=x + radius,
            z2=z + radius,
            center_y=y,
            dimension=dimension,
        )

        if claim:
            player.send_message(f"§aCreated claim: {claim_name} ({claim.width}x{claim.depth})")
            player.send_message(f"§7Cost: {creation_cost} coins.")
        else:
            player.send_message("§cFailed to create claim.")

        return True