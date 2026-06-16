import os
from typing import Dict, Any
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

class ConfigManager:

    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        self.config_path = os.path.join(data_dir, "config.yml")
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.default_flow_style = False
        self.config: Dict[str, Any] = {}
        self._ensure_config()

    def _ensure_config(self) -> None:
        if os.path.exists(self.config_path):
            self._load()
        else:
            self._create_default()

    def _load(self) -> None:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = self.yaml.load(f)
                self.config = data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = {}

    def _create_default(self) -> None:
        os.makedirs(self.data_dir, exist_ok=True)

        config = CommentedMap()

        config["database"] = CommentedMap()
        config["database"]["type"] = "sqlite"
        config["database"].yaml_set_comment_before_after_key(
            "type",
            before="Database type: 'sqlite' (local) or 'mysql' (remote)\nCurrently only SQLite is supported.",
        )
        config["database"]["sqlite_path"] = "landclaim.db"
        config["database"].yaml_set_comment_before_after_key(
            "sqlite_path",
            before="Path where the SQLite database will be stored",
        )

        config["claims"] = CommentedMap()
        config.yaml_set_comment_before_after_key(
            "claims",
            before="\n# ═══════════════════════════════════════════════════════════════\n"
                   "# CLAIMS CONFIGURATION\n"
                   "# ═══════════════════════════════════════════════════════════════",
        )

        config["claims"]["max_per_player"] = 3
        config["claims"].yaml_set_comment_before_after_key(
            "max_per_player",
            before="Maximum number of claims per player",
        )

        config["claims"]["min_distance_between_claims"] = 50
        config["claims"].yaml_set_comment_before_after_key(
            "min_distance_between_claims",
            before="Minimum distance (blocks) between claim edges",
        )

        config["claims"]["min_distance_from_spawn"] = 100
        config["claims"].yaml_set_comment_before_after_key(
            "min_distance_from_spawn",
            before="Minimum distance from spawn to create a claim",
        )

        config["claims"]["spawn_center"] = [0, 0]
        config["claims"].yaml_set_comment_before_after_key(
            "spawn_center",
            before="Spawn center coordinates (X, Z)",
        )

        config["claims"]["spawn_protection_radius"] = 200
        config["claims"].yaml_set_comment_before_after_key(
            "spawn_protection_radius",
            before="Spawn protection radius (no claiming allowed inside)",
        )

        config["claims"]["default_radius"] = 5
        config["claims"].yaml_set_comment_before_after_key(
            "default_radius",
            before="Default radius (blocks) for new claims from center",
        )

        config["economy"] = CommentedMap()
        config.yaml_set_comment_before_after_key(
            "economy",
            before="\n# ═══════════════════════════════════════════════════════════════\n"
                   "# ECONOMY\n"
                   "# ═══════════════════════════════════════════════════════════════",
        )

        config["economy"]["claim_creation_cost"] = 5000
        config["economy"].yaml_set_comment_before_after_key(
            "claim_creation_cost",
            before="Cost to create a new claim",
        )

        config["economy"]["claim_daily_maintenance"] = 100
        config["economy"].yaml_set_comment_before_after_key(
            "claim_daily_maintenance",
            before="Daily maintenance cost per claim",
        )

        config["economy"]["claim_expansion_cost_per_block"] = 10
        config["economy"].yaml_set_comment_before_after_key(
            "claim_expansion_cost_per_block",
            before="Cost per block when expanding a claim",
        )

        config["economy"]["claim_expiration_days"] = 7
        config["economy"].yaml_set_comment_before_after_key(
            "claim_expiration_days",
            before="Days until a claim expires if maintenance is not paid",
        )

        config["economy"]["grace_period_days"] = 2
        config["economy"].yaml_set_comment_before_after_key(
            "grace_period_days",
            before="Grace period days after expiration before claim deletion",
        )

        config["economy"]["admin_bypass_cost"] = True
        config["economy"].yaml_set_comment_before_after_key(
            "admin_bypass_cost",
            before="Do OPs bypass all costs?",
        )

        config["protection"] = CommentedMap()
        config.yaml_set_comment_before_after_key(
            "protection",
            before="\n# ═══════════════════════════════════════════════════════════════\n"
                   "# PROTECTION\n"
                   "# ═══════════════════════════════════════════════════════════════",
        )

        config["protection"]["protect_block_place"] = True
        config["protection"]["protect_block_break"] = True
        config["protection"]["protect_interact"] = True
        config["protection"]["protect_passive_mobs"] = True
        config["protection"]["protect_explosions"] = True
        config["protection"]["protect_pvp"] = True
        config["protection"]["protect_fire"] = True
        config["protection"]["protect_piston_push"] = True

        config["protection"].yaml_set_comment_before_after_key(
            "protect_block_place",
            before="Protect against block placement",
        )
        config["protection"].yaml_set_comment_before_after_key(
            "protect_block_break",
            before="Protect against block breaking",
        )
        config["protection"].yaml_set_comment_before_after_key(
            "protect_interact",
            before="Protect against interaction (chests, doors, etc)",
        )
        config["protection"].yaml_set_comment_before_after_key(
            "protect_passive_mobs",
            before="Protect passive animals",
        )
        config["protection"].yaml_set_comment_before_after_key(
            "protect_explosions",
            before="Protect against explosions (creepers, TNT, etc)",
        )
        config["protection"].yaml_set_comment_before_after_key(
            "protect_pvp",
            before="Protect against PvP (player damage)",
        )
        config["protection"].yaml_set_comment_before_after_key(
            "protect_fire",
            before="Protect against fire spreading",
        )
        config["protection"].yaml_set_comment_before_after_key(
            "protect_piston_push",
            before="Protect against pistons pushing blocks",
        )

        config["clans"] = CommentedMap()
        config.yaml_set_comment_before_after_key(
            "clans",
            before="\n# ═══════════════════════════════════════════════════════════════\n"
                   "# CLANS (Future Integration)\n"
                   "# ═══════════════════════════════════════════════════════════════",
        )

        config["clans"]["enabled"] = False
        config["clans"].yaml_set_comment_before_after_key(
            "enabled",
            before="Enable clan system integration?",
        )

        config["clans"]["api_plugin_name"] = "clanapi"
        config["clans"].yaml_set_comment_before_after_key(
            "api_plugin_name",
            before="Name of the plugin that provides the clan API",
        )

        config["debug"] = CommentedMap()
        config.yaml_set_comment_before_after_key(
            "debug",
            before="\n# ═══════════════════════════════════════════════════════════════\n"
                   "# DEBUG\n"
                   "# ═══════════════════════════════════════════════════════════════",
        )

        config["debug"]["log_level"] = "INFO"
        config["debug"].yaml_set_comment_before_after_key(
            "log_level",
            before="Logging level: DEBUG, INFO, WARNING, ERROR",
        )

        config["debug"]["log_events"] = False
        config["debug"].yaml_set_comment_before_after_key(
            "log_events",
            before="Log all protection events (very verbose)",
        )

        self.config = config
        self._save()

    def _save(self) -> None:
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                self.yaml.dump(self.config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def get_all(self) -> Dict[str, Any]:
        return self.config

    def reload(self) -> None:
        self._load()