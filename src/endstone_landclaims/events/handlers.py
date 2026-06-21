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
from endstone_landclaims.services.claim_service import ClaimService
from endstone_landclaims.config import ConfigManager
from endstone_landclaims.events.block_events import BlockEventHandler
from endstone_landclaims.events.interact_events import InteractEventHandler
from endstone_landclaims.events.damage_events import DamageEventHandler
from endstone_landclaims.events.explosion_events import ExplosionEventHandler

try:
    from endstone_clans_api import clan_event_handler, ClanKickEvent, ClanLeaveEvent
except ImportError:
    clan_event_handler = None
    ClanKickEvent = None
    ClanLeaveEvent = None


class EventHandlers:

    def __init__(
        self,
        plugin: Plugin,
        protection_service: ProtectionService,
        claim_service: ClaimService,
        config: ConfigManager,
        database,
    ) -> None:
        self.plugin = plugin
        self.protection = protection_service
        self.claim_service = claim_service
        self.config = config
        self.database = database
        self.block_handler = BlockEventHandler(protection_service, config)
        self.interact_handler = InteractEventHandler(protection_service, config)
        self.damage_handler = DamageEventHandler(protection_service, config)
        self.explosion_handler = ExplosionEventHandler(protection_service, config)

    def register(self) -> None:
        self.plugin.register_events(self)

        clans_api = getattr(self.protection, "clans_api", None)
        if clans_api:
            clans_api.register_events(self)

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
        default_slots = self.claim_service.get_default_claim_slots()
        self.database.get_or_create_player(int(event.player.xuid), event.player.name, default_slots)

    if clan_event_handler:
        @clan_event_handler
        def on_clan_kick(self, event: ClanKickEvent) -> None:
            self._release_contributions(int(event.player.xuid))

        @clan_event_handler
        def on_clan_leave(self, event: ClanLeaveEvent) -> None:
            self._release_contributions(int(event.player.xuid))

    def _release_contributions(self, player_xuid: int) -> None:
        try:
            self.claim_service.release_all_player_contributions(player_xuid)
        except Exception as e:
            self.plugin.logger.warning(f"Failed to release contributions for {player_xuid}: {e}")