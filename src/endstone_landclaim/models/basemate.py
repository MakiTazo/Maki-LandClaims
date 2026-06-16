from typing import Dict, Any, Optional
from datetime import datetime
from enum import IntEnum

class BasemateRank(IntEnum):
    MEMBER = 0
    MANAGER = 1
    OWNER = 2

class BasemateData:

    def __init__(
        self,
        player_uuid: str,
        player_name: str,
        claim_id: str,
        rank: int | BasemateRank = BasemateRank.MEMBER,
        added_at: Optional[str] = None,
    ) -> None:
        self.player_uuid = player_uuid
        self.player_name = player_name
        self.claim_id = claim_id
        self.rank = BasemateRank(rank) if isinstance(rank, int) else rank
        self.added_at = added_at or datetime.utcnow().isoformat()

    @property
    def rank_name(self) -> str:
        rank_names = {
            BasemateRank.MEMBER: "Member",
            BasemateRank.MANAGER: "Manager",
            BasemateRank.OWNER: "Owner",
        }
        return rank_names.get(self.rank, "Unknown")

    def is_manager(self) -> bool:
        return self.rank >= BasemateRank.MANAGER

    def is_owner(self) -> bool:
        return self.rank == BasemateRank.OWNER

    def can_manage_basemates(self) -> bool:
        return self.rank >= BasemateRank.MANAGER

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_uuid": self.player_uuid,
            "player_name": self.player_name,
            "claim_id": self.claim_id,
            "rank": self.rank,
            "added_at": self.added_at,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "BasemateData":
        return BasemateData(
            player_uuid=data["player_uuid"],
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