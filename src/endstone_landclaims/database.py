import sqlite3
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

class Database:

    def __init__(self, db_path: str, data_folder: str = "") -> None:
        if not os.path.isabs(db_path) and data_folder:
            db_path = os.path.join(data_folder, db_path)
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA journal_mode=WAL")
        return self.conn

    def _row(self, row: sqlite3.Row) -> Dict[str, Any]:
        return dict(row)

    def _init_schema(self) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                xuid INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                id TEXT PRIMARY KEY,
                owner_xuid INTEGER NOT NULL,
                name TEXT NOT NULL,
                x1 INTEGER NOT NULL,
                z1 INTEGER NOT NULL,
                x2 INTEGER NOT NULL,
                z2 INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_maintained TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_expired INTEGER DEFAULT 0,
                dimension TEXT DEFAULT 'overworld',
                FOREIGN KEY(owner_xuid) REFERENCES players(xuid)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS basemates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id TEXT NOT NULL,
                player_xuid INTEGER NOT NULL,
                rank INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(claim_id) REFERENCES claims(id),
                FOREIGN KEY(player_xuid) REFERENCES players(xuid),
                UNIQUE(claim_id, player_xuid)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS claim_permissions (
                claim_id TEXT PRIMARY KEY,
                allow_build INTEGER DEFAULT 0,
                allow_interact INTEGER DEFAULT 0,
                allow_mob_damage INTEGER DEFAULT 0,
                allow_pvp INTEGER DEFAULT 0,
                FOREIGN KEY(claim_id) REFERENCES claims(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id TEXT,
                player_xuid INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(claim_id) REFERENCES claims(id),
                FOREIGN KEY(player_xuid) REFERENCES players(xuid)
            )
        """)

        conn.commit()

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_or_create_player(self, xuid: int, name: str) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM players WHERE xuid = ?", (xuid,))
        row = cursor.fetchone()

        if row:
            cursor.execute("UPDATE players SET last_seen = CURRENT_TIMESTAMP WHERE xuid = ?", (xuid,))
            conn.commit()
            return self._row(row)

        cursor.execute("INSERT INTO players (xuid, name) VALUES (?, ?)", (xuid, name))
        conn.commit()
        cursor.execute("SELECT * FROM players WHERE xuid = ?", (xuid,))
        return self._row(cursor.fetchone())

    def get_player_by_xuid(self, xuid: int) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players WHERE xuid = ?", (xuid,))
        row = cursor.fetchone()
        return self._row(row) if row else None

    def get_player_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players WHERE name = ?", (name,))
        row = cursor.fetchone()
        return self._row(row) if row else None

    def create_claim(
        self,
        claim_id: str,
        owner_xuid: int,
        owner_name: str,
        name: str,
        x1: int,
        z1: int,
        x2: int,
        z2: int,
        dimension: str = "overworld",
        expiration_days: int = 7,
    ) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT OR IGNORE INTO players (xuid, name) VALUES (?, ?)",
            (owner_xuid, owner_name),
        )

        expires_at = (datetime.utcnow() + timedelta(days=expiration_days)).isoformat()

        cursor.execute(
            """
            INSERT INTO claims
            (id, owner_xuid, name, x1, z1, x2, z2, dimension, expires_at, last_maintained)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (claim_id, owner_xuid, name, x1, z1, x2, z2, dimension, expires_at),
        )

        cursor.execute("INSERT INTO claim_permissions (claim_id) VALUES (?)", (claim_id,))
        conn.commit()

        cursor.execute("SELECT * FROM claims WHERE id = ?", (claim_id,))
        return self._row(cursor.fetchone())

    def get_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM claims WHERE id = ?", (claim_id,))
        row = cursor.fetchone()
        return self._row(row) if row else None

    def get_claims_by_owner(self, owner_xuid: int) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM claims WHERE owner_xuid = ? AND is_expired = 0",
            (owner_xuid,),
        )
        return [self._row(row) for row in cursor.fetchall()]

    def get_claim_at_position(self, x: int, z: int, dimension: str = "overworld") -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM claims
            WHERE dimension = ? AND is_expired = 0
            AND x1 <= ? AND x2 >= ? AND z1 <= ? AND z2 >= ?
            LIMIT 1
            """,
            (dimension, x, x, z, z),
        )
        row = cursor.fetchone()
        return self._row(row) if row else None

    def get_all_claims(self, dimension: str = "overworld") -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM claims WHERE dimension = ? AND is_expired = 0",
            (dimension,),
        )
        return [self._row(row) for row in cursor.fetchall()]

    def update_claim(self, claim_id: str, **kwargs) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()

        allowed_keys = {"name", "x1", "z1", "x2", "z2", "expires_at", "last_maintained", "is_expired"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_keys}

        if not updates:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        cursor.execute(
            f"UPDATE claims SET {set_clause} WHERE id = ?",
            [*updates.values(), claim_id],
        )
        conn.commit()
        return True

    def delete_claim(self, claim_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM basemates WHERE claim_id = ?", (claim_id,))
            cursor.execute("DELETE FROM claim_permissions WHERE claim_id = ?", (claim_id,))
            cursor.execute("DELETE FROM claims WHERE id = ?", (claim_id,))
            conn.commit()
            return True
        except Exception:
            return False

    def add_basemate(self, claim_id: str, player_xuid: int, rank: int = 0) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO basemates (claim_id, player_xuid, rank) VALUES (?, ?, ?)",
                (claim_id, player_xuid, rank),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_basemate(self, claim_id: str, player_xuid: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM basemates WHERE claim_id = ? AND player_xuid = ?",
            (claim_id, player_xuid),
        )
        conn.commit()
        return cursor.rowcount > 0

    def get_basemates(self, claim_id: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT bm.*, p.name FROM basemates bm
            JOIN players p ON bm.player_xuid = p.xuid
            WHERE bm.claim_id = ?
            """,
            (claim_id,),
        )
        return [self._row(row) for row in cursor.fetchall()]

    def get_basemate_rank(self, claim_id: str, player_xuid: int) -> Optional[int]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT rank FROM basemates WHERE claim_id = ? AND player_xuid = ?",
            (claim_id, player_xuid),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else None

    def set_basemate_rank(self, claim_id: str, player_xuid: int, rank: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE basemates SET rank = ? WHERE claim_id = ? AND player_xuid = ?",
            (rank, claim_id, player_xuid),
        )
        conn.commit()
        return cursor.rowcount > 0

    def get_permissions(self, claim_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM claim_permissions WHERE claim_id = ?", (claim_id,))
        row = cursor.fetchone()
        return self._row(row) if row else None

    def set_permissions(self, claim_id: str, **kwargs) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()

        allowed_keys = {"allow_build", "allow_interact", "allow_mob_damage", "allow_pvp"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_keys}

        if not updates:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        cursor.execute(
            f"UPDATE claim_permissions SET {set_clause} WHERE claim_id = ?",
            [*updates.values(), claim_id],
        )
        conn.commit()
        return True

    def add_transaction(
        self,
        player_xuid: int,
        transaction_type: str,
        amount: float,
        claim_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO transactions
            (player_xuid, transaction_type, amount, claim_id, reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            (player_xuid, transaction_type, amount, claim_id, reason),
        )
        conn.commit()
        return cursor.lastrowid

    def get_transactions(
        self,
        player_xuid: Optional[int] = None,
        claim_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM transactions WHERE 1=1"
        params: List[Any] = []

        if player_xuid:
            query += " AND player_xuid = ?"
            params.append(player_xuid)
        if claim_id:
            query += " AND claim_id = ?"
            params.append(claim_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [self._row(row) for row in cursor.fetchall()]

    def mark_expired_claims(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE claims SET is_expired = 1
            WHERE is_expired = 0 AND expires_at < CURRENT_TIMESTAMP
            """
        )
        conn.commit()
        return cursor.rowcount

    def get_expired_claims(self, grace_period_days: int = 2) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        grace_date = (datetime.utcnow() - timedelta(days=grace_period_days)).isoformat()
        cursor.execute(
            "SELECT * FROM claims WHERE is_expired = 1 AND expires_at < ?",
            (grace_date,),
        )
        return [self._row(row) for row in cursor.fetchall()]

    def renew_claim(self, claim_id: str, days: int = 7) -> bool:
        now = datetime.utcnow()
        return self.update_claim(
            claim_id,
            expires_at=(now + timedelta(days=days)).isoformat(),
            last_maintained=now.isoformat(),
            is_expired=0,
        )