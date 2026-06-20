from typing import Dict, Any, Optional, Union
from datetime import datetime
from enum import IntEnum

class BasemateRank(IntEnum):
    MEMBER = 0
    MANAGER = 1
    OWNER = 2

class BasemateData:

    _RANK_NAMES: Dict[BasemateRank, str] = {
        BasemateRank.MEMBER: "Member",
        BasemateRank.MANAGER: "Manager",
        BasemateRank.OWNER: "Owner",
    }

    def __init__(
        self,
        player_xuid: int,
        player_name: str,
        claim_id: str,
        rank: Union[int, BasemateRank] = BasemateRank.MEMBER,
        added_at: Optional[str] = None,
    ) -> None:
        self.player_xuid = player_xuid
        self.player_name = player_name
        self.claim_id = claim_id
        self.rank = BasemateRank(rank)
        self.added_at = added_at or datetime.utcnow().isoformat()

    @property
    def rank_name(self) -> str:
        return self._RANK_NAMES.get(self.rank, "Unknown")

    @property
    def is_manager(self) -> bool:
        return self.rank >= BasemateRank.MANAGER

    @property
    def is_owner(self) -> bool:
        return self.rank == BasemateRank.OWNER

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_xuid": self.player_xuid,
            "player_name": self.player_name,
            "claim_id": self.claim_id,
            "rank": int(self.rank),
            "added_at": self.added_at,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "BasemateData":
        return BasemateData(
            player_xuid=data["player_xuid"],
            player_name=data["player_name"],
            claim_id=data["claim_id"],
            rank=data.get("rank", BasemateRank.MEMBER),
            added_at=data.get("added_at"),
        )

    def __repr__(self) -> str:
        return (
            f"BasemateData(name={self.player_name}, "
            f"claim={self.claim_id}, rank={self.rank_name})"
        )