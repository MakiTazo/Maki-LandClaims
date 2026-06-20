from endstone.plugin import Plugin
from endstone.command import Command, CommandSender
from typing import List, Optional
from endstone_clans_api import ClansApi
from endstone_landclaims.config import ConfigManager
from endstone_landclaims.database import Database
from endstone_landclaims.services.claim_service import ClaimService
from endstone_landclaims.services.spacing_service import SpacingService
from endstone_landclaims.services.protection_service import ProtectionService
from endstone_landclaims.services.economy_service import EconomyService
from endstone_landclaims.events.handlers import EventHandlers
from endstone_landclaims.commands.claim_commands import ClaimCommands

class LandClaimsPlugin(Plugin):
    api_version = "0.11"
    depend = ["jweconomy"]
    commands = {
        "claim": {
            "description": "Land claim management",
            "usages": ["/claim <create|info|list|view|delete|add|remove> [args: string]"],
            "permissions": ["landclaim.claim.use"],
        },
        "claimadmin": {
            "description": "Admin commands for LandClaim",
            "usages": ["/claimadmin <reload>"],
            "permissions": ["landclaim.admin"],
        },
    }

    permissions = {
        "landclaim.claim.use": {
            "description": "Use claim commands",
            "default": "true",
        },
        "landclaim.admin": {
            "description": "Bypass all protections",
            "default": "op",
        },
    }

    def on_enable(self) -> None:
        try:
            self.config_manager = ConfigManager(str(self.data_folder))
            self.logger.info("LandClaims plugin loading...")
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return

        try:
            db_path = self.config_manager.get("database.sqlite_path", "landclaim.db")
            self.database = Database(db_path, str(self.data_folder))
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            return

        clans_api: Optional[ClansApi] = None
        if self.config_manager.get("clans.enabled", False):
            try:
                plugin = self.server.plugin_manager.get_plugin("clans_api")
                clans_api = plugin.api if plugin else None
            except Exception as xe:
                clans_api = None
                self.logger.warning(f"{xe}")
            if clans_api:
                self.logger.info("Clans integration enabled")

        try:
            self.claim_service = ClaimService(self.database, self.config_manager)
            self.spacing_service = SpacingService(self.config_manager)
            self.protection_service = ProtectionService(self.config_manager, self.claim_service, clans_api)
            self.economy_service = EconomyService(self.config_manager, self)
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            return

        try:
            self.event_handlers = EventHandlers(
                self,
                self.protection_service,
                self.config_manager,
                self.database,
            )
            self.event_handlers.register()
        except Exception as e:
            self.logger.error(f"Failed to register events: {e}")
            return

        try:
            self.claim_commands = ClaimCommands(
                self,
                self.config_manager,
                self.claim_service,
                self.spacing_service,
                self.protection_service,
                self.economy_service,
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize commands: {e}")
            return

        self.logger.info("LandClaim plugin enabled successfully!")

    def on_disable(self) -> None:
        db = getattr(self, "database", None)
        if db:
            try:
                db.close()
                self.logger.info("Database closed")
            except Exception as e:
                self.logger.error(f"Error closing database: {e}")

    def on_command(
        self,
        sender: CommandSender,
        command: Command,
        args: List[str],
    ) -> bool:
        if not hasattr(self, "claim_commands"):
            sender.send_message("§cPlugin not fully loaded yet.")
            return True

        if command.name == "claimadmin":
            return self._handle_admin_command(sender, args)

        return self.claim_commands.handle_command(sender, command, args)

    def _handle_admin_command(self, sender: CommandSender, args: List[str]) -> bool:
        if not args:
            sender.send_message("§cUsage: /claimadmin <reload>")
            return True

        sub = args[0].lower()

        if sub == "reload":
            try:
                self.config_manager.reload()
                sender.send_message("§aConfig reloaded.")
            except Exception as e:
                sender.send_message(f"§cFailed to reload config: {e}")
            return True

        sender.send_message(f"§cUnknown subcommand: {sub}")
        return True