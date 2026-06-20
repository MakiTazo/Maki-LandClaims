from typing import List, Optional
from endstone import Player
from endstone.command import CommandSender, Command
from endstone_landclaims.services.claim_service import ClaimService
from endstone_landclaims.services.spacing_service import SpacingService
from endstone_landclaims.services.protection_service import ProtectionService
from endstone_landclaims.services.economy_service import EconomyService
from endstone_landclaims.config import ConfigManager
from endstone_landclaims.commands.create_handler import CreateHandler
from endstone_landclaims.commands.info_handler import InfoHandler
from endstone_landclaims.commands.list_handler import ListHandler
from endstone_landclaims.commands.delete_handler import DeleteHandler
from endstone_landclaims.commands.basemate_handler import BasemateHandler
from endstone_landclaims.commands.visualize_handler import VisualizeHandler
from endstone_landclaims.commands.members_handler import MembersHandler
from endstone_landclaims.commands.contribute_handler import ContributeHandler

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
        self.spacing_service = spacing_service
        self.create_handler = CreateHandler(plugin, config, claim_service, protection_service, economy_service, spacing_service)
        self.info_handler = InfoHandler(plugin, config, claim_service, protection_service)
        self.list_handler = ListHandler(plugin, config, claim_service, protection_service)
        self.delete_handler = DeleteHandler(plugin, config, claim_service, protection_service)
        self.basemate_handler = BasemateHandler(plugin, config, claim_service, protection_service)
        self.visualize_handler = VisualizeHandler(plugin, config, claim_service, protection_service)
        self.member_handler = MembersHandler(plugin, config, claim_service, protection_service)
        self.contribute_handler = ContributeHandler(plugin, config, claim_service, protection_service, economy_service)

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

        if not args:
            player.send_message("§cUsage: /claim <create|info|list|view|delete|add|remove|members|contribute>")
            return True

        sub = args[0].lower()
        sub_args = args[1:]
        if sub == "create":
            return self.create_handler.handle(player, sub_args)
        if sub == "info":
            return self.info_handler.handle(player, sub_args)
        if sub == "list":
            return self.list_handler.handle(player, sub_args)
        if sub == "delete":
            return self.delete_handler.handle(player, sub_args)
        if sub == "add":
            return self.basemate_handler.handle_add(player, sub_args)
        if sub == "remove":
            return self.basemate_handler.handle_remove(player, sub_args)
        if sub == "view":
            return self.visualize_handler.handle(player, sub_args)
        if sub == "members":
            return self.member_handler.handle(player, sub_args)
        if sub == "contribute":
            return self.contribute_handler.handle(player, sub_args)

        player.send_message(f"§cUnknown subcommand: {sub}")
        return True

    def _as_player(self, sender: CommandSender) -> Optional[Player]:
        return sender if isinstance(sender, Player) else None