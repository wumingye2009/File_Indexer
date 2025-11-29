#!/usr/bin/env data_analysis_env
# -*- coding: utf-8-sig -*-
"""
Index files & archives and export to TWO CSV files:

1) entries CSV  -> 对应 SQLite 的 entries 表
2) archives CSV -> 对应 SQLite 的 archives 表（压缩包内部成员）

- 递归扫描 root 目录
- 普通文件与压缩包（zip/rar/7z/tar/tgz）
- 使用 7z ("7z l -slt") 列出压缩包内部内容
- 可选对文件/压缩包本身计算 hash (md5/sha1/sha256...)
"""

import argparse
import csv
import hashlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ARCHIVE_EXTS = {".zip", ".rar", ".7z", ".tar", ".tgz", ".tar.gz"}

# -------------------------------------------------------------
# 计算文件 hash
# -------------------------------------------------------------
def compute_hash(path: Path, method: str = "") -> str:
    if not method:
        return ""
    h = hashlib.new(method)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# -------------------------------------------------------------
# 调用 7z 列出压缩包内容
# -------------------------------------------------------------
def list_archive_entries(archive: Path, sevenzip: str = "7z"):
    """
    返回 entries 列表，每个 entry 是 dict:
      {
         "entry_path_in_archive": "...",
         "entry_size_bytes": int,
         "is_dir": 0/1,
         "is_encrypted": 0/1,
         "method": "Deflate" 等
      }
    """
    cmd = [sevenzip, "l", "-slt", str(archive)]

    try:
        raw = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        print(f"[ERROR] 7z not found: {sevenzip}", file=sys.stderr)
        return []
    except subprocess.CalledProcessError as ex:
        print(f"[ERROR] 7z list failed: {archive}", file=sys.stderr)
        print(ex.output.decode("mbcs", "ignore"))
        return []

    text = raw.decode("mbcs", errors="replace")

    entries = []
    current = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            if "Path" in current:
                path_in_arc = current.get("Path", "")
                size_str = current.get("Size", "0")
                method = current.get("Method", "")
                encrypted = current.get("Encrypted", "0")
                is_dir = 1 if current.get("Attributes", "").startswith("D") else 0

                try:
                    entry_size = int(size_str)
                except Exception:
                    entry_size = 0

                entries.append({
                    "entry_path_in_archive": path_in_arc,
                    "entry_size_bytes": entry_size,
                    "is_dir": is_dir,
                    "is_encrypted": 1 if encrypted == "+" else 0,
                    "method": method,
                })

            current = {}
            continue

        if "=" in line:
            k, v = line.split("=", 1)
            current[k.strip()] = v.strip()

    return entries


# -------------------------------------------------------------
# 主扫描逻辑
# -------------------------------------------------------------
def scan(root: Path,
         entries_out: Path,
         archives_out: Path,
         include_files: bool,
         hash_method: str,
         sevenzip: str):

    root = root.resolve()
    entries_out.parent.mkdir(parents=True, exist_ok=True)
    archives_out.parent.mkdir(parents=True, exist_ok=True)

    # 打开两个 CSV
    f_entries = entries_out.open("w", newline="", encoding="utf-8-sig")
    f_archives = archives_out.open("w", newline="", encoding="utf-8-sig")

    entries_writer = csv.writer(f_entries)
    archives_writer = csv.writer(f_archives)

    # 写表头
    entries_writer.writerow([
        "root_path", "full_path", "parent_path", "name",
        "ext", "is_dir", "is_archive",
        "size_bytes", "mtime_iso",
        "hash_algo", "hash_value",
    ])

    archives_writer.writerow([
        "root_path",
        "archive_full_path",
        "member_path",
        "member_size",
        "member_mtime",
        "hash_algo",
        "hash_value",
    ])

    scanned_files = 0
    scanned_archives = 0
    errors = 0

    for p in root.rglob("*"):
        if p.is_dir():
            # v1 阶段我们不把目录写入 entries，避免复杂度
            continue

        suffix = p.suffix.lower()
        is_archive = 1 if suffix in ARCHIVE_EXTS else 0

        try:
            st = p.stat()
            size_bytes = st.st_size
            mtime_ts = st.st_mtime
            hash_value = compute_hash(p, hash_method)
        except Exception as ex:
            print(f"[ERROR] read file: {p}", file=sys.stderr)
            print(ex, file=sys.stderr)
            errors += 1
            continue

        # 计算相对路径 / 父目录
        try:
            rel = p.relative_to(root)
            parent_path = str(rel.parent) if str(rel.parent) != "." else "."
        except ValueError:
            # 理论上不会发生，防御性处理
            parent_path = "."

        mtime_ts = st.st_mtime
        mtime_iso = datetime.fromtimestamp(mtime_ts).isoformat(timespec="seconds")

        entries_writer.writerow([
            str(root),              # root_path
            str(p),                 # full_path
            parent_path,            # parent_path (相对 root)
            p.name,                 # name
            suffix.lstrip("."),     # ext
            0,                      # is_dir (目前只写文件)
            is_archive,             # is_archive
            size_bytes,             # size_bytes
            # mtime_ts,               # mtime (timestamp)
            mtime_iso,              # mtime_iso
            hash_method or "",      # hash_algo
            hash_value or "",       # hash_value
        ])

        if is_archive:
            scanned_archives += 1
            # 列出压缩包内部
            try:
                entries = list_archive_entries(p, sevenzip)
                for e in entries:
                    if e["is_dir"]:
                        # archives 里我们只记录文件，不记录目录
                        continue
                    archives_writer.writerow([
                        str(root),          # root_path
                        str(p),             # archive_full_path
                        e["entry_path_in_archive"],  # member_path
                        e["entry_size_bytes"],
                        "",                 # member_mtime 暂不填
                        "",                 # hash_algo 暂不算
                        "",                 # hash_value
                    ])
            except Exception as ex:
                print(f"[ERROR] listing archive: {p}", file=sys.stderr)
                print(ex, file=sys.stderr)
                errors += 1
        else:
            scanned_files += 1

    f_entries.close()
    f_archives.close()

    print("")
    print(f"[DONE] Scanned files: {scanned_files} | archives: {scanned_archives} | errors: {errors}")
    print(f"[INFO] Entries CSV : {entries_out}")
    print(f"[INFO] Archives CSV: {archives_out}")


# -------------------------------------------------------------
# CLI
# -------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Index files & archives to entries/archives CSV")
    ap.add_argument("--root", required=True, help="Root folder to scan")
    ap.add_argument("--entries-out", required=True, help="Output CSV for entries table")
    ap.add_argument("--archives-out", required=True, help="Output CSV for archives table")
    ap.add_argument("--include-files", action="store_true",
                    help="(保留参数以兼容旧用法，目前总是扫描普通文件，可忽略)")
    ap.add_argument("--hash", default="", help="Hash method: md5/sha1/sha256")
    ap.add_argument("--sevenzip", default="7z", help="Path to 7z.exe")
    args = ap.parse_args()

    scan(
        Path(args.root),
        Path(args.entries_out),
        Path(args.archives_out),
        args.include_files,
        args.hash,
        args.sevenzip,
    )


if __name__ == "__main__":
    main()
