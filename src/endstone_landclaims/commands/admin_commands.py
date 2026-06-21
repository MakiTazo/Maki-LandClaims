from typing import List
from endstone.command import CommandSender
from endstone_landclaims.config import ConfigManager

class AdminCommands:

    def __init__(self, config: ConfigManager) -> None:
        self.config = config

    def handle_command(self, sender: CommandSender, args: List[str]) -> bool:
        if not args:
            sender.send_message("§cUsage: /claimadmin <reload>")
            return True

        sub = args[0].lower()

        if sub == "reload":
            return self._handle_reload(sender)

        sender.send_message(f"§cUnknown subcommand: {sub}")
        return True

    def _handle_reload(self, sender: CommandSender) -> bool:
        try:
            self.config.reload()
            sender.send_message("§aConfig reloaded.")
        except Exception as e:
            sender.send_message(f"§cFailed to reload config: {e}")
        return True