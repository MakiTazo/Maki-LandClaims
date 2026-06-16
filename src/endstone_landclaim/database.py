import sqlite3
import os
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta


class Database:
    def __init__(self, db_path: str, data_folder: str = ""):
        if not os.path.isabs(db_path) and data_folder:
            db_path = os.path.join(data_folder, db_path)
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene o crea la conexión a la BD."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            # Enable WAL mode para mejor performance
            self.conn.execute("PRAGMA journal_mode=WAL")
        return self.conn

    def _init_schema(self) -> None:
        """Crea las tablas si no existen."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Tabla de jugadores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                uuid TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla de claims
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                id TEXT PRIMARY KEY,
                owner_uuid TEXT NOT NULL,
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
                FOREIGN KEY(owner_uuid) REFERENCES players(uuid)
            )
        """)

        # Tabla de basemates (jugadores con acceso a un claim)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS basemmates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id TEXT NOT NULL,
                player_uuid TEXT NOT NULL,
                rank INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(claim_id) REFERENCES claims(id),
                FOREIGN KEY(player_uuid) REFERENCES players(uuid),
                UNIQUE(claim_id, player_uuid)
            )
        """)

        # Tabla de permisos del claim
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

        # Tabla de transacciones de economía
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id TEXT,
                player_uuid TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(claim_id) REFERENCES claims(id),
                FOREIGN KEY(player_uuid) REFERENCES players(uuid)
            )
        """)

        conn.commit()

    def close(self) -> None:
        """Cierra la conexión."""
        if self.conn:
            self.conn.close()
            self.conn = None

    # ═══════════════════════════════════════════════════════════════
    # PLAYERS
    # ═══════════════════════════════════════════════════════════════

    def get_or_create_player(self, uuid: str, name: str) -> Dict[str, Any]:
        """Obtiene o crea un registro de jugador."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM players WHERE uuid = ?", (uuid,))
        row = cursor.fetchone()

        if row:
            cursor.execute("UPDATE players SET last_seen = CURRENT_TIMESTAMP WHERE uuid = ?", (uuid,))
            conn.commit()
            return dict(row)

        cursor.execute(
            "INSERT INTO players (uuid, name) VALUES (?, ?)",
            (uuid, name),
        )
        conn.commit()

        cursor.execute("SELECT * FROM players WHERE uuid = ?", (uuid,))
        return dict(cursor.fetchone())

    def get_player_by_uuid(self, uuid: str) -> Optional[Dict[str, Any]]:
        """Obtiene un jugador por UUID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players WHERE uuid = ?", (uuid,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_player_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Obtiene un jugador por nombre."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ═══════════════════════════════════════════════════════════════
    # CLAIMS
    # ═══════════════════════════════════════════════════════════════

    def create_claim(
            self,
            claim_id: str,
            owner_uuid: str,
            owner_name: str,  # Agregar este parámetro
            name: str,
            x1: int,
            z1: int,
            x2: int,
            z2: int,
            dimension: str = "overworld",
            expiration_days: int = 7,
    ) -> Dict[str, Any]:
        """Crea un nuevo claim."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Asegurar que el owner existe
        cursor.execute(
            "INSERT OR IGNORE INTO players (uuid, name) VALUES (?, ?)",
            (owner_uuid, owner_name),
        )

        expires_at = datetime.utcnow() + timedelta(days=expiration_days)

        cursor.execute(
            """
            INSERT INTO claims
            (id, owner_uuid, name, x1, z1, x2, z2, dimension, expires_at, last_maintained)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (claim_id, owner_uuid, name, x1, z1, x2, z2, dimension, expires_at.isoformat()),
        )

        # Crear permisos por defecto
        cursor.execute(
            "INSERT INTO claim_permissions (claim_id) VALUES (?)",
            (claim_id,),
        )

        conn.commit()

        cursor.execute("SELECT * FROM claims WHERE id = ?", (claim_id,))
        return dict(cursor.fetchone())

    def get_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un claim por ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM claims WHERE id = ?", (claim_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_claims_by_owner(self, owner_uuid: str) -> List[Dict[str, Any]]:
        """Obtiene todos los claims de un jugador."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM claims WHERE owner_uuid = ? AND is_expired = 0",
            (owner_uuid,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_claim_at_position(self, x: int, z: int, dimension: str = "overworld") -> Optional[Dict[str, Any]]:
        """Obtiene el claim en una posición específica."""
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
        return dict(row) if row else None

    def get_all_claims(self, dimension: str = "overworld") -> List[Dict[str, Any]]:
        """Obtiene todos los claims activos en una dimensión."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM claims WHERE dimension = ? AND is_expired = 0",
            (dimension,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_claim(self, claim_id: str, **kwargs) -> bool:
        """Actualiza un claim."""
        conn = self._get_connection()
        cursor = conn.cursor()

        allowed_keys = {"name", "x1", "z1", "x2", "z2", "expires_at", "last_maintained", "is_expired"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_keys}

        if not updates:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [claim_id]

        cursor.execute(
            f"UPDATE claims SET {set_clause} WHERE id = ?",
            values,
        )
        conn.commit()
        return True

    def delete_claim(self, claim_id: str) -> bool:
        """Elimina un claim y sus datos asociados."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM basemmates WHERE claim_id = ?", (claim_id,))
            cursor.execute("DELETE FROM claim_permissions WHERE claim_id = ?", (claim_id,))
            cursor.execute("DELETE FROM claims WHERE id = ?", (claim_id,))
            conn.commit()
            return True
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════
    # BASEMATES
    # ═══════════════════════════════════════════════════════════════

    def add_basemate(self, claim_id: str, player_uuid: str, rank: int = 0) -> bool:
        """Añade un basemate a un claim."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO basemmates (claim_id, player_uuid, rank) VALUES (?, ?, ?)",
                (claim_id, player_uuid, rank),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_basemate(self, claim_id: str, player_uuid: str) -> bool:
        """Remueve un basemate de un claim."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM basemmates WHERE claim_id = ? AND player_uuid = ?",
            (claim_id, player_uuid),
        )
        conn.commit()
        return cursor.rowcount > 0

    def get_basemates(self, claim_id: str) -> List[Dict[str, Any]]:
        """Obtiene todos los basemates de un claim."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT bm.*, p.name FROM basemmates bm
            JOIN players p ON bm.player_uuid = p.uuid
            WHERE bm.claim_id = ?
            """,
            (claim_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_basemate_rank(self, claim_id: str, player_uuid: str) -> Optional[int]:
        """Obtiene el rango de un basemate."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT rank FROM basemmates WHERE claim_id = ? AND player_uuid = ?",
            (claim_id, player_uuid),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else None

    def set_basemate_rank(self, claim_id: str, player_uuid: str, rank: int) -> bool:
        """Actualiza el rango de un basemate."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE basemmates SET rank = ? WHERE claim_id = ? AND player_uuid = ?",
            (rank, claim_id, player_uuid),
        )
        conn.commit()
        return cursor.rowcount > 0

    # ═══════════════════════════════════════════════════════════════
    # PERMISSIONS
    # ═══════════════════════════════════════════════════════════════

    def get_permissions(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene los permisos de un claim."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM claim_permissions WHERE claim_id = ?", (claim_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def set_permissions(self, claim_id: str, **kwargs) -> bool:
        """Actualiza los permisos de un claim."""
        conn = self._get_connection()
        cursor = conn.cursor()

        allowed_keys = {"allow_build", "allow_interact", "allow_mob_damage", "allow_pvp"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_keys}

        if not updates:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [claim_id]

        cursor.execute(
            f"UPDATE claim_permissions SET {set_clause} WHERE claim_id = ?",
            values,
        )
        conn.commit()
        return True

    # ═══════════════════════════════════════════════════════════════
    # TRANSACTIONS
    # ═══════════════════════════════════════════════════════════════

    def add_transaction(
        self,
        player_uuid: str,
        transaction_type: str,
        amount: float,
        claim_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> int:
        """Registra una transacción de economía."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO transactions
            (player_uuid, transaction_type, amount, claim_id, reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            (player_uuid, transaction_type, amount, claim_id, reason),
        )
        conn.commit()
        return cursor.lastrowid

    def get_transactions(
        self,
        player_uuid: Optional[str] = None,
        claim_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Obtiene transacciones filtradas."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM transactions WHERE 1=1"
        params: List[str] = []

        if player_uuid:
            query += " AND player_uuid = ?"
            params.append(player_uuid)

        if claim_id:
            query += " AND claim_id = ?"
            params.append(claim_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    # ═══════════════════════════════════════════════════════════════
    # MAINTENANCE & CLEANUP
    # ═══════════════════════════════════════════════════════════════

    def mark_expired_claims(self) -> int:
        """Marca claims como expirados si su fecha ha pasado."""
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
        """Obtiene claims expirados hace más de N días (listos para eliminar)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        grace_date = datetime.utcnow() - timedelta(days=grace_period_days)

        cursor.execute(
            """
            SELECT * FROM claims
            WHERE is_expired = 1 AND expires_at < ?
            """,
            (grace_date.isoformat(),),
        )
        return [dict(row) for row in cursor.fetchall()]

    def renew_claim(self, claim_id: str, days: int = 7) -> bool:
        """Renueva un claim por N días."""
        new_expiration = datetime.utcnow() + timedelta(days=days)
        return self.update_claim(
            claim_id,
            expires_at=new_expiration.isoformat(),
            last_maintained=datetime.utcnow().isoformat(),
            is_expired=0,
        )