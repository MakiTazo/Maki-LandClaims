from typing import Any
from endstone_landclaim.config import ConfigManager

class EconomyService:

    def __init__(self, config: ConfigManager, plugin: Any) -> None:
        self.config = config
        self.plugin = plugin
        self.jweconomy = None
        self.api = None
        self._init_economy()

    def _init_economy(self) -> None:
        try:
            self.jweconomy = self.plugin.server.plugin_manager.get_plugin("jweconomy")
            if not self.jweconomy:
                raise RuntimeError("JWEconomy plugin not found!")

            self.api = self.jweconomy.get_api()
            if not self.api:
                raise RuntimeError("Failed to get JWEconomy API!")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize economy: {e}")

    @property
    def is_enabled(self) -> bool:
        return self.api is not None

    @property
    def admin_bypass_costs(self) -> bool:
        return bool(self.config.get("economy.admin_bypass_cost", True))

    def get_creation_cost(self) -> float:
        return float(self.config.get("economy.claim_creation_cost", 5000))

    def get_daily_maintenance_cost(self) -> float:
        return float(self.config.get("economy.claim_daily_maintenance", 100))

    def get_expansion_cost_per_block(self) -> float:
        return float(self.config.get("economy.claim_expansion_cost_per_block", 10))

    def calculate_claim_creation_cost(self) -> float:
        return self.get_creation_cost()

    def calculate_claim_expansion_cost(self, old_area: int, new_area: int) -> float:
        return float(max(0, new_area - old_area) * self.get_expansion_cost_per_block())

    def calculate_daily_maintenance(self) -> float:
        return self.get_daily_maintenance_cost()

    async def charge_player(self, player_uuid: str, amount: float) -> bool:
        if not self.api:
            return False
        try:
            result = await self.api.remove_balance(player_uuid, amount)
            return result is not None
        except Exception:
            return False

    async def refund_player(self, player_uuid: str, amount: float) -> bool:
        if not self.api:
            return False
        try:
            await self.api.add_balance(player_uuid, amount)
            return True
        except Exception:
            return False

    async def check_balance(self, player_uuid: str, required_amount: float) -> bool:
        if not self.api:
            return True
        try:
            return await self.api.has_balance(player_uuid, required_amount)
        except Exception:
            return False

    async def get_balance(self, player_uuid: str) -> float:
        if not self.api:
            return 0.0
        try:
            balance = await self.api.get_balance(player_uuid)
            return float(balance) if balance else 0.0
        except Exception:
            return 0.0