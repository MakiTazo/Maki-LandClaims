from typing import List, Optional
from endstone import Player, asyncio as endstone_asyncio
from endstone.command import CommandSender, Command
from endstone_landclaim.services.claim_service import ClaimService
from endstone_landclaim.services.spacing_service import SpacingService
from endstone_landclaim.services.protection_service import ProtectionService
from endstone_landclaim.services.economy_service import EconomyService
from endstone_landclaim.config import ConfigManager

class ClaimCommands:

    def __init__(
        self,
        plugin,
        config: ConfigManager,
        claim_service: ClaimService,
        spacing_service: SpacingService,
        protection_service: ProtectionService,
        economy_service: EconomyService,
    ) -> None:
        self.plugin = plugin
        self.config = config
        self.claim_service = claim_service
        self.spacing_service = spacing_service
        self.protection = protection_service
        self.economy = economy_service

    def handle_command(
        self,
        sender: CommandSender,
        command: Command,
        args: List[str],
    ) -> bool:
        player = self._as_player(sender)
        if not player:
            sender.send_message("§cThis command is player-only.")
            return True

        cmd_name = (command.name or "").lower()

        if cmd_name == "claimcreate":
            return self._handle_claim_create(player, args)
        if cmd_name == "claiminfo":
            return self._handle_claim_info(player, args)
        if cmd_name == "claimlist":
            return self._handle_claim_list(player, args)
        if cmd_name == "claimdelete":
            return self._handle_claim_delete(player, args)
        if cmd_name == "claimadd":
            return self._handle_claim_add_mate(player, args)
        if cmd_name == "claimremove":
            return self._handle_claim_remove_mate(player, args)
        if cmd_name == "claimvisualize":
            return self._handle_claim_visualize(player, args)

        return False

    def _handle_claim_create(self, player: Player, args: List[str]) -> bool:
        player_uuid = str(player.unique_id)

        if not self.claim_service.player_has_claim_space(player_uuid):
            player.send_message("§cYou have reached the maximum number of claims.")
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

        location = player.location
        x = int(location.x)
        z = int(location.z)
        claim_name = " ".join(args) if args else "Claim"
        dimension = self._get_dimension_key(player)
        radius = self.config.get("claims.default_radius", 50)
        claim = self.claim_service.create_claim(
            owner_uuid=player_uuid,
            owner_name=player.name,
            claim_name=claim_name,
            x1=x - radius,
            z1=z - radius,
            x2=x + radius,
            z2=z + radius,
            dimension=dimension,
        )

        if claim:
            player.send_message(f"§aCreated claim: {claim_name} ({claim.width}x{claim.depth})")
            player.send_message(f"§7Cost: {creation_cost} coins.")
        else:
            player.send_message("§cFailed to create claim.")

        return True

    def _handle_claim_info(self, player: Player, args: List[str]) -> bool:
        location = player.location
        claim = self.claim_service.get_claim_at_position(
            int(location.x), int(location.z), self._get_dimension_key(player)
        )

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

    def _handle_claim_list(self, player: Player, args: List[str]) -> bool:
        claims = self.claim_service.get_player_claims(str(player.unique_id))

        if not claims:
            player.send_message("§7You have no claims.")
            return True

        player.send_message(f"§b=== Your Claims ({len(claims)}) ===")
        for claim in claims:
            status = "§c[EXPIRED]" if claim.is_expired else "§a[ACTIVE]"
            player.send_message(f"§7- {status} §e{claim.name} §7({claim.width}x{claim.depth})")
        return True

    def _handle_claim_delete(self, player: Player, args: List[str]) -> bool:
        if not args:
            player.send_message("§cUsage: /claimdelete <claim_name>")
            return True

        claim_name = " ".join(args)
        claims = self.claim_service.get_player_claims(str(player.unique_id))
        claim_to_delete = next((c for c in claims if c.name.lower() == claim_name.lower()), None)

        if not claim_to_delete:
            player.send_message(f"§cClaim '{claim_name}' not found.")
            return True

        if self.claim_service.delete_claim(claim_to_delete.id):
            player.send_message(f"§aDeleted claim: {claim_to_delete.name}")
        else:
            player.send_message("§cFailed to delete claim.")

        return True

    def _get_claim_at_player(self, player: Player):
        location = player.location
        return self.claim_service.get_claim_at_position(
            int(location.x), int(location.z), self._get_dimension_key(player)
        )

    def _handle_claim_add_mate(self, player: Player, args: List[str]) -> bool:
        if not args:
            player.send_message("§cUsage: /claimadd <player_name>")
            return True

        claim = self._get_claim_at_player(player)
        if not claim:
            player.send_message("§cYou are not in a claim.")
            return True

        if not self.protection.is_owner(claim.id, str(player.unique_id)):
            player.send_message("§cYou are not the owner of this claim.")
            return True

        mate_name = args[0]
        try:
            mate_player = self.claim_service.db.get_player_by_name(mate_name)
            if not mate_player:
                player.send_message(f"§cPlayer '{mate_name}' not found in database.")
                return True

            if self.claim_service.add_basemate(claim.id, mate_player["uuid"]):
                player.send_message(f"§aAdded {mate_name} as a basemate.")
            else:
                player.send_message(f"§c{mate_name} is already a basemate.")
        except Exception:
            player.send_message("§cError adding basemate.")

        return True

    def _handle_claim_remove_mate(self, player: Player, args: List[str]) -> bool:
        if not args:
            player.send_message("§cUsage: /claimremove <player_name>")
            return True

        claim = self._get_claim_at_player(player)
        if not claim:
            player.send_message("§cYou are not in a claim.")
            return True

        if not self.protection.is_owner(claim.id, str(player.unique_id)):
            player.send_message("§cYou are not the owner of this claim.")
            return True

        mate_name = args[0]
        try:
            mate_player = self.claim_service.db.get_player_by_name(mate_name)
            if not mate_player:
                player.send_message(f"§cPlayer '{mate_name}' not found.")
                return True

            if self.claim_service.remove_basemate(claim.id, mate_player["uuid"]):
                player.send_message(f"§aRemoved {mate_name} from basemates.")
            else:
                player.send_message(f"§c{mate_name} is not a basemate.")
        except Exception:
            player.send_message("§cError removing basemate.")

        return True

    def _handle_claim_visualize(self, player: Player, args: List[str]) -> bool:
        claim = self._get_claim_at_player(player)

        if not claim:
            player.send_message("§7You are in wilderness (no claim here).")
            return True

        y = player.location.y
        step = 5
        duration_ticks = 200
        particle_type = "minecraft:endrod"

        def show_particles():
            from endstone.command import CommandSenderWrapper
            silent_sender = CommandSenderWrapper(self.plugin.server.command_sender, on_message=lambda msg: None)
            for x_pos in range(claim.x1, claim.x2 + 1, step):
                self.plugin.server.dispatch_command(silent_sender, f"execute as {player.name} at @s run particle {particle_type} {x_pos} {y} {claim.z1 - 1}")
                self.plugin.server.dispatch_command(silent_sender, f"execute as {player.name} at @s run particle {particle_type} {x_pos} {y} {claim.z2 + 1}")
            for z_pos in range(claim.z1, claim.z2 + 1, step):
                self.plugin.server.dispatch_command(silent_sender, f"execute as {player.name} at @s run particle {particle_type} {claim.x1 - 1} {y} {z_pos}")
                self.plugin.server.dispatch_command(silent_sender, f"execute as {player.name} at @s run particle {particle_type} {claim.x2 + 1} {y} {z_pos}")

        particle_task = self.plugin.server.scheduler.run_task(
            self.plugin, show_particles, delay=0, period=1
        )

        def stop_particles():
            particle_task.cancel()
            player.send_message("§7Visualization ended.")

        self.plugin.server.scheduler.run_task(
            self.plugin, stop_particles, delay=duration_ticks
        )

        player.send_message("§aVisualizing claim boundaries for 10 seconds...")
        return True

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