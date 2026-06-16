from typing import Dict, Any, List, Optional
from datetime import datetime

class PlayerData:

    def __init__(
        self,
        uuid: str,
        name: str,
        created_at: Optional[str] = None,
        last_seen: Optional[str] = None,
    ) -> None:
        self.uuid = uuid
        self.name = name
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.last_seen = last_seen or datetime.utcnow().isoformat()

        self.claims: List[str] = []
        self.clan_tag: Optional[str] = None
        self.wallet_bypass: bool = False

    def update_last_seen(self) -> None:
        self.last_seen = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "created_at": self.created_at,
            "last_seen": self.last_seen,
            "claims": self.claims,
            "clan_tag": self.clan_tag,
            "wallet_bypass": self.wallet_bypass,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PlayerData":
        player = PlayerData(
            uuid=data["uuid"],
            name=data["name"],
            created_at=data.get("created_at"),
            last_seen=data.get("last_seen"),
        )
        player.claims = data.get("claims", [])
        player.clan_tag = data.get("clan_tag")
        player.wallet_bypass = data.get("wallet_bypass", False)
        return player

    def __repr__(self) -> str:
        return f"PlayerData(name={self.name}, claims={len(self.claims)})"