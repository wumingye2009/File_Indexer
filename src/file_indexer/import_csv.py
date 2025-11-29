# import_csv.py
import sqlite3
import csv
import argparse
from datetime import datetime

def add_library(conn, name: str, root_path: str, note: str = None) -> int:
    cur = conn.cursor()
    created_at = datetime.now().isoformat(timespec="seconds")
    cur.execute(
        "INSERT INTO library (name, root_path, note, created_at) VALUES (?, ?, ?, ?)",
        (name, root_path, note, created_at),
    )
    conn.commit()
    return cur.lastrowid

def import_entries(conn, library_id: int, entries_csv: str):
    cur = conn.cursor()
    with open(entries_csv, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                library_id,
                row["full_path"],
                row["parent_path"],
                row["name"],
                row.get("ext") or None,
                int(row.get("is_dir", "0") or 0),
                int(row.get("is_archive", "0") or 0),
                int(row["size_bytes"]) if row.get("size_bytes") else None,
                float(row["mtime"]) if row.get("mtime") else None,
                row.get("hash_algo") or None,
                row.get("hash_value") or None,
                None,  # extra_meta 先为空
            )
            for row in reader
        ]

    cur.executemany("""
        INSERT INTO entries (
            library_id, full_path, parent_path, name,
            ext, is_dir, is_archive,
            size_bytes, mtime,
            hash_algo, hash_value, extra_meta
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    print(f"Imported {len(rows)} rows into entries for library_id={library_id}")

def import_archives(conn, library_id: int, archives_csv: str):
    cur = conn.cursor()
    with open(archives_csv, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [
            (
                library_id,
                row["archive_full_path"],
                None,  # archive_entry_id 后面可用 UPDATE 补充
                row["member_path"],
                int(row["member_size"]) if row.get("member_size") else None,
                float(row["member_mtime"]) if row.get("member_mtime") else None,
                row.get("hash_algo") or None,
                row.get("hash_value") or None,
                None,  # extra_meta
            )
            for row in reader
        ]

    cur.executemany("""
        INSERT INTO archives (
            library_id, archive_full_path, archive_entry_id,
            member_path, member_size, member_mtime,
            hash_algo, hash_value, extra_meta
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    print(f"Imported {len(rows)} rows into archives for library_id={library_id}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="archive_work.db")
    parser.add_argument("--library-name", required=True)
    parser.add_argument("--root-path", required=True)
    parser.add_argument("--entries-csv", required=True)
    parser.add_argument("--archives-csv")  # 可选
    parser.add_argument("--note")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    try:
        library_id = add_library(conn, args.library_name, args.root_path, args.note)
        import_entries(conn, library_id, args.entries_csv)
        if args.archives_csv:
            import_archives(conn, library_id, args.archives_csv)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
