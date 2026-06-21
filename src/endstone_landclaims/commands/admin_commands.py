from typing import List
from endstone.command import CommandSender
from endstone_landclaims.config import ConfigManager
from endstone_landclaims.database import Database

class AdminCommands:
    def __init__(self, config: ConfigManager, database: Database, plugin) -> None:
        self.config = config
        self.database = database
        self.plugin = plugin

    def handle_command(self, sender: CommandSender, args: List[str]) -> bool:
        if not args:
            sender.send_message("§cUsage: /claimadmin <reload|addclaim>")
            return True

        sub = args[0].lower()
        if sub == "reload":
            return self._handle_reload(sender)
        if sub == "addclaim":
            return self._handle_addclaim(sender, args[1:])
        sender.send_message(f"§cUnknown subcommand: {sub}")
        return True

    def _handle_reload(self, sender: CommandSender) -> bool:
        try:
            self.config.reload()
            sender.send_message("§aConfig reloaded.")
        except Exception as e:
            sender.send_message(f"§cFailed to reload config: {e}")
        return True

    def _handle_addclaim(self, sender: CommandSender, args: List[str]) -> bool:
        if len(args) < 2:
            sender.send_message("§cUsage: /claimadmin addclaim <player> <count>")
            return True

        target_name = args[0]

        try:
            count = int(args[1])
        except ValueError:
            sender.send_message("§cCount must be a number.")
            return True

        if count <= 0:
            sender.send_message("§cCount must be greater than 0.")
            return True

        target_xuid = self._resolve_xuid(target_name)
        if target_xuid is None:
            sender.send_message(f"§cPlayer '{target_name}' not found.")
            return True

        success = self.database.add_claim_slots(target_xuid, count)
        if success:
            sender.send_message(f"§aAdded {count} claim slot(s) to {target_name}.")
        else:
            sender.send_message(f"§cFailed to add claim slots to {target_name}.")

        return True

    def _resolve_xuid(self, name: str):
        for online in self.plugin.server.online_players:
            if online.name.lower() == name.lower():
                return int(online.xuid)

        record = self.database.get_player_by_name(name)
        if record:
            return record["xuid"]

        return None