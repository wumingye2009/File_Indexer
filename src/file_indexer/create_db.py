# src/file_indexer/create_db.py
import sqlite3
from pathlib import Path

# 项目根目录 = 本文件的上上级目录（src/file_indexer 的上级再上级）
ROOT_DIR = Path(__file__).resolve().parents[2]

DB_PATH = ROOT_DIR / "data" / "workspace" / "archive_work.db"
SCHEMA_FILE = ROOT_DIR / "sql" / "schema_v1.sql"

def create_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Initializing database at: {DB_PATH}")
    print(f"[INFO] Using schema file: {SCHEMA_FILE}")

    conn = sqlite3.connect(DB_PATH)
    try:
        schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
        conn.executescript(schema_sql)
        conn.commit()
        print("[OK] Database initialized successfully.")
    finally:
        conn.close()

if __name__ == "__main__":
    create_db()
