import sqlite3
import os

def get_db_path() -> str:
    return os.getenv("RECOENGINE_DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "recoengine.db")))

def get_db_connection(db_path: str = None):
    target_path = db_path or get_db_path()
    is_uri = target_path.startswith("file:") or "mode=memory" in target_path
    if is_uri or target_path == ":memory:":
        conn = sqlite3.connect(target_path, check_same_thread=False, uri=is_uri)
    else:
        conn = sqlite3.connect(target_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: str = None):
    conn = get_db_connection(db_path)
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                tags TEXT NOT NULL,
                price REAL DEFAULT 0.0,
                avg_rating REAL DEFAULT 4.5,
                feature_vector_blob BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                persona TEXT DEFAULT 'General',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS interactions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                weight REAL NOT NULL,
                timestamp_epoch REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recommendation_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                strategy TEXT NOT NULL,
                recommended_count INTEGER NOT NULL,
                latency_ms REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_interactions_user ON interactions(user_id);
            CREATE INDEX IF NOT EXISTS idx_interactions_item ON interactions(item_id);
            CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
        """)
    return conn
