# create_db.py
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH_DEFAULT = "data/workspace/archive_work.db"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS library (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    root_path  TEXT NOT NULL,
    note       TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    library_id  INTEGER NOT NULL,
    full_path   TEXT NOT NULL,
    parent_path TEXT NOT NULL,
    name        TEXT NOT NULL,
    ext         TEXT,
    is_dir      INTEGER NOT NULL,
    is_archive  INTEGER NOT NULL DEFAULT 0,
    size_bytes  INTEGER,
    mtime       REAL,
    hash_algo   TEXT,
    hash_value  TEXT,
    extra_meta  TEXT,
    FOREIGN KEY (library_id) REFERENCES library(id)
);

CREATE INDEX IF NOT EXISTS idx_entries_lib
    ON entries(library_id);

CREATE INDEX IF NOT EXISTS idx_entries_hash
    ON entries(hash_value);

CREATE INDEX IF NOT EXISTS idx_entries_size
    ON entries(size_bytes);

CREATE INDEX IF NOT EXISTS idx_entries_full_path
    ON entries(full_path);

CREATE TABLE IF NOT EXISTS archives (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    library_id        INTEGER NOT NULL,
    archive_full_path TEXT NOT NULL,
    archive_entry_id  INTEGER,
    member_path       TEXT NOT NULL,
    member_size       INTEGER,
    member_mtime      REAL,
    hash_algo         TEXT,
    hash_value        TEXT,
    extra_meta        TEXT,
    FOREIGN KEY (library_id)       REFERENCES library(id),
    FOREIGN KEY (archive_entry_id) REFERENCES entries(id)
);

CREATE INDEX IF NOT EXISTS idx_archives_hash
    ON archives(hash_value);

CREATE INDEX IF NOT EXISTS idx_archives_archive
    ON archives(archive_full_path);
"""

def create_db(db_path: str = DB_PATH_DEFAULT):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure folder exists

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        print(f"[OK] Database initialized at: {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create SQLite DB with schema")
    parser.add_argument(
        "--db",
        type=str,
        default=DB_PATH_DEFAULT,
        help=f"Output DB path (default: {DB_PATH_DEFAULT})"
    )

    args = parser.parse_args()
    create_db(args.db)
