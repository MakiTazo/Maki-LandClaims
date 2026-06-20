from typing import List
from endstone import Player
from endstone.command import CommandSenderWrapper
from endstone_landclaims.commands.base_handler import BaseHandler

class VisualizeHandler(BaseHandler):

    PARTICLE_TYPE = "minecraft:villager_happy"
    DURATION_TICKS = 200

    def handle(self, player: Player, args: List[str]) -> bool:
        claim = self._get_claim_at_player(player)

        if not claim:
            player.send_message("§7You are in wilderness (no claim here).")
            return True

        y_bottom = claim.y1
        y_top = claim.y2 + 1

        def show_particles():
            silent_sender = CommandSenderWrapper(self.plugin.server.command_sender, on_message=lambda msg: None)

            def spawn(x: float, sy: float, z: float) -> None:
                self.plugin.server.dispatch_command(
                    silent_sender,
                    f"execute as {player.name} at @s run particle {self.PARTICLE_TYPE} {x:.2f} {sy:.2f} {z:.2f}",
                )

            x1, x2 = claim.x1, claim.x2 + 1
            z1, z2 = claim.z1, claim.z2 + 1

            for y in (y_bottom, y_top):
                for x in range(x1, x2 + 1):
                    spawn(x, y, z1)
                    spawn(x, y, z2)
                for z in range(z1, z2 + 1):
                    spawn(x1, y, z)
                    spawn(x2, y, z)

            for cx, cz in [(x1, z1), (x1, z2), (x2, z1), (x2, z2)]:
                y = y_bottom
                while y <= y_top:
                    spawn(cx, y, cz)
                    y += 1

        particle_task = self.plugin.server.scheduler.run_task(
            self.plugin, show_particles, delay=0, period=4
        )

        def stop_particles():
            particle_task.cancel()
            player.send_message("§7Visualization ended.")

        self.plugin.server.scheduler.run_task(
            self.plugin, stop_particles, delay=self.DURATION_TICKS
        )

        player.send_message("§aVisualizing claim boundaries for 10 seconds...")
        return True