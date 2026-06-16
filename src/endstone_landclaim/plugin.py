from endstone.plugin import Plugin
from endstone.command import Command, CommandSender
from typing import List
from endstone_landclaim.config import ConfigManager
from endstone_landclaim.database import Database
from endstone_landclaim.services.claim_service import ClaimService
from endstone_landclaim.services.spacing_service import SpacingService
from endstone_landclaim.services.protection_service import ProtectionService
from endstone_landclaim.services.economy_service import EconomyService
from endstone_landclaim.events.handlers import EventHandlers
from endstone_landclaim.commands.claim_commands import ClaimCommands

class LandClaimPlugin(Plugin):
    api_version = "0.11"
    depend = ["jweconomy"]
    commands = {
        "claimcreate": {
            "description": "Create a new land claim",
            "usages": ["/claimcreate [name: str]"],
            "permissions": ["landclaim.claim.create"],
        },
        "claiminfo": {
            "description": "Get info about the claim you are in",
            "usages": ["/claiminfo"],
            "permissions": ["landclaim.claim.info"],
        },
        "claimlist": {
            "description": "List your claims",
            "usages": ["/claimlist"],
            "permissions": ["landclaim.claim.list"],
        },
        "claimvisualize": {
            "description": "Visualize claim boundaries with particles",
            "usages": ["/claimvisualize"],
            "permissions": ["landclaim.claim.info"],
        },
        "claimdelete": {
            "description": "Delete one of your claims",
            "usages": ["/claimdelete <name: str>"],
            "permissions": ["landclaim.claim.delete"],
        },
        "claimadd": {
            "description": "Add a basemate to your claim",
            "usages": ["/claimadd <player: player>"],
            "permissions": ["landclaim.claim.manage"],
        },
        "claimremove": {
            "description": "Remove a basemate from your claim",
            "usages": ["/claimremove <player: player>"],
            "permissions": ["landclaim.claim.manage"],
        },
    }

    permissions = {
        "landclaim.claim.create": {
            "description": "Create claims",
            "default": "true",
        },
        "landclaim.claim.info": {
            "description": "Check claim info",
            "default": "true",
        },
        "landclaim.claim.list": {
            "description": "List your claims",
            "default": "true",
        },
        "landclaim.claim.delete": {
            "description": "Delete your claims",
            "default": "true",
        },
        "landclaim.claim.manage": {
            "description": "Manage basemates",
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
            self.logger.info("LandClaim plugin loading...")
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return

        try:
            db_path = self.config_manager.get("database.sqlite_path", "landclaim.db")
            self.database = Database(db_path, str(self.data_folder))
            self.logger.info(f"Database initialized at {db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            return

        try:
            self.claim_service = ClaimService(self.database, self.config_manager)
            self.spacing_service = SpacingService(self.config_manager)
            self.protection_service = ProtectionService(self.config_manager, self.claim_service)
            self.economy_service = EconomyService(self.config_manager, self)
            self.logger.info("Services initialized")
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
            self.logger.info("Event handlers registered")
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
            self.logger.info("Commands registered")
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

        return self.claim_commands.handle_command(sender, command, args)