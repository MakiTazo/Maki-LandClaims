from endstone.plugin import Plugin
from endstone.event import (
    event_handler,
    BlockPlaceEvent,
    BlockBreakEvent,
    PlayerInteractEvent,
    PlayerJoinEvent,
    ActorDamageEvent,
    BlockExplodeEvent,
    ActorExplodeEvent,
    BlockPistonExtendEvent,
    BlockPistonRetractEvent,
)
from endstone_landclaims.services.protection_service import ProtectionService
from endstone_landclaims.config import ConfigManager
from endstone_landclaims.events.block_events import BlockEventHandler
from endstone_landclaims.events.interact_events import InteractEventHandler
from endstone_landclaims.events.damage_events import DamageEventHandler
from endstone_landclaims.events.explosion_events import ExplosionEventHandler

class EventHandlers:

    def __init__(
        self,
        plugin: Plugin,
        protection_service: ProtectionService,
        config: ConfigManager,
        database,
    ) -> None:
        self.plugin = plugin
        self.protection = protection_service
        self.config = config
        self.database = database
        self.block_handler = BlockEventHandler(protection_service, config)
        self.interact_handler = InteractEventHandler(protection_service, config)
        self.damage_handler = DamageEventHandler(protection_service, config)
        self.explosion_handler = ExplosionEventHandler(protection_service, config)

    def register(self) -> None:
        self.plugin.register_events(self)

    @event_handler
    def on_block_place(self, event: BlockPlaceEvent) -> None:
        self.block_handler.handle_block_place(event)

    @event_handler
    def on_block_break(self, event: BlockBreakEvent) -> None:
        self.block_handler.handle_block_break(event)

    @event_handler
    def on_player_interact(self, event: PlayerInteractEvent) -> None:
        self.interact_handler.handle_player_interact(event)

    @event_handler
    def on_actor_damage(self, event: ActorDamageEvent) -> None:
        self.damage_handler.handle_entity_damage(event)

    @event_handler
    def on_block_explode(self, event: BlockExplodeEvent) -> None:
        self.explosion_handler.handle_block_explode(event)

    @event_handler
    def on_actor_explode(self, event: ActorExplodeEvent) -> None:
        self.explosion_handler.handle_actor_explode(event)

    @event_handler
    def on_piston_extend(self, event: BlockPistonExtendEvent) -> None:
        self.explosion_handler.handle_piston_extend(event)

    @event_handler
    def on_piston_retract(self, event: BlockPistonRetractEvent) -> None:
        self.explosion_handler.handle_piston_retract(event)

    @event_handler
    def on_player_join(self, event: PlayerJoinEvent) -> None:
        self.database.get_or_create_player(int(event.player.xuid), event.player.name)