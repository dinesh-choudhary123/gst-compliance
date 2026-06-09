"""Simple local authentication module.

Uses SQLite + hashing for local-only auth. No network calls.
All data stays on the machine.
"""

import hashlib
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.config import settings


def _get_db() -> sqlite3.Connection:
    """Get a connection to the auth database."""
    db_path = settings.BASE_DIR / "taxflow.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_auth_db():
    """Initialize the authentication database tables."""
    conn = _get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TEXT DEFAULT (datetime('now')),
                is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        conn.commit()

        # Create default admin user if not exists
        cursor = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",))
        if not cursor.fetchone():
            _create_user(conn, "admin", "admin123", "admin")
    finally:
        conn.close()


def _hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt."""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return salt.hex() + ":" + key.hex()


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its stored hash."""
    try:
        salt_hex, key_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        stored_key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return new_key == stored_key
    except (ValueError, AttributeError):
        return False


def _create_user(conn: sqlite3.Connection, username: str, password: str, role: str = "user") -> str:
    """Create a new user and return their ID."""
    user_id = str(uuid.uuid4())
    password_hash = _hash_password(password)
    conn.execute(
        "INSERT INTO users (id, username, password_hash, role) VALUES (?, ?, ?, ?)",
        (user_id, username, password_hash, role),
    )
    conn.commit()
    return user_id


def register_user(username: str, password: str, role: str = "user") -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    conn = _get_db()
    try:
        cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return False, "Username already exists"
        user_id = _create_user(conn, username, password, role)
        return True, f"User {username} created successfully"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> tuple[bool, Optional[str], Optional[str]]:
    """Authenticate a user. Returns (success, user_id, token)."""
    conn = _get_db()
    try:
        cursor = conn.execute(
            "SELECT id, password_hash, is_active FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if not row:
            return False, None, None
        if not row["is_active"]:
            return False, None, None
        if not _verify_password(password, row["password_hash"]):
            return False, None, None

        # Create session
        user_id = row["id"]
        token = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        expires_at = (datetime.now() + timedelta(hours=settings.SESSION_EXPIRE_HOURS)).isoformat()
        conn.execute(
            "INSERT INTO sessions (id, user_id, token, expires_at) VALUES (?, ?, ?, ?)",
            (session_id, user_id, token, expires_at),
        )
        conn.commit()
        return True, user_id, token
    finally:
        conn.close()


def validate_session(token: str) -> Optional[str]:
    """Validate a session token. Returns user_id if valid."""
    conn = _get_db()
    try:
        cursor = conn.execute(
            "SELECT user_id, expires_at FROM sessions WHERE token = ?",
            (token,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.now() > expires_at:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return None
        return row["user_id"]
    finally:
        conn.close()


def logout_user(token: str):
    """Invalidate a session token."""
    conn = _get_db()
    try:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()


def get_users() -> list[dict]:
    """Get all users (for admin panel)."""
    conn = _get_db()
    try:
        cursor = conn.execute("SELECT id, username, role, created_at, is_active FROM users")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
