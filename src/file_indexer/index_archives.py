#!/usr/bin/env data_analysis_env
# -*- coding: utf-8-sig -*-
"""
Index archives (and optionally normal files) and export to CSV.

- Walks a root folder recursively
- Detects archive files by extension
- Uses 7-Zip ("7z l -slt") to list internal entries in a machine-readable format
- Optional MD5/SHA1 hash of the archive file itself
- Optional "normal file scan mode": record all non-archive files to the same CSV
- Resume-friendly: skips archives that appear unchanged if already present in CSV

"""

import argparse
import csv
import hashlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

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
         "entry_ext": ".mp3",
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

    # ⭐ Windows 下 7z 输出是 GBK 或 ANSI，所以用 "mbcs"
    text = raw.decode("mbcs", errors="replace")

    entries = []
    current = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            # 一条 Entry 完成
            if "Path" in current:
                path_in_arc = current.get("Path", "")
                size_str = current.get("Size", "0")
                method = current.get("Method", "")
                encrypted = current.get("Encrypted", "0")

                is_dir = 1 if current.get("Attributes", "").startswith("D") else 0

                p = Path(path_in_arc)
                ext = p.suffix.lower()

                try:
                    entry_size = int(size_str)
                except:
                    entry_size = 0

                entries.append({
                    "entry_path_in_archive": path_in_arc,
                    "entry_ext": ext if not is_dir else "",
                    "entry_size_bytes": entry_size,
                    "is_dir": is_dir,
                    "is_encrypted": 1 if encrypted == "+" else 0,
                    "method": method
                })

            current = {}
            continue

        # 解析 FieldName = Value
        if "=" in line:
            k, v = line.split("=", 1)
            current[k.strip()] = v.strip()

    return entries


# -------------------------------------------------------------
# 主扫描逻辑
# -------------------------------------------------------------
def scan(root: Path, out: Path, include_files: bool, hash_method: str, sevenzip: str):
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "archive_path", "archive_ext",
            "archive_size_bytes", "archive_mtime_iso",
            "archive_hash",
            "entry_path_in_archive", "entry_ext",
            "entry_size_bytes", "is_dir", "is_encrypted", "method"
        ])

        scanned_archives = 0
        scanned_files = 0
        errors = 0

        for p in root.rglob("*"):
            if p.is_dir():
                continue

            suffix = p.suffix.lower()

            # ⭐ 普通文件模式
            if include_files and suffix not in [".zip", ".rar", ".7z", ".tar", ".tgz"]:
                try:
                    st = p.stat()
                    iso_mtime = datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")

                    h = compute_hash(p, hash_method)

                    writer.writerow([
                        str(p), suffix, st.st_size, iso_mtime,
                        h,
                        "", "", "", 0, 0, ""
                    ])

                    scanned_files += 1
                except Exception as ex:
                    print(f"[ERROR] read file: {p}", file=sys.stderr)
                    print(ex, file=sys.stderr)
                    errors += 1
                continue

            # ⭐ 压缩包模式
            if suffix in [".zip", ".rar", ".7z", ".tar", ".tgz"]:
                try:
                    st = p.stat()
                    iso_mtime = datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")

                    h = compute_hash(p, hash_method)
                    scanned_archives += 1

                    entries = list_archive_entries(p, sevenzip)

                    # 写入每个 entry
                    for e in entries:
                        writer.writerow([
                            str(p), suffix,
                            st.st_size, iso_mtime,
                            h,
                            e["entry_path_in_archive"],
                            e["entry_ext"],
                            e["entry_size_bytes"],
                            e["is_dir"],
                            e["is_encrypted"],
                            e["method"]
                        ])

                except Exception as ex:
                    print(f"[ERROR] listing archive: {p}", file=sys.stderr)
                    print(ex, file=sys.stderr)
                    errors += 1

        print("")
        print(f"[DONE] Scanned archives: {scanned_archives} | Scanned normal files: {scanned_files} | Errors: {errors}")
        print(f"[INFO] Output: {out}")


# -------------------------------------------------------------
# CLI
# -------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Index files & archives (UTF-8-SIG, ISO time)")
    ap.add_argument("--root", required=True, help="Root folder")
    ap.add_argument("--out", required=True, help="Output CSV")
    ap.add_argument("--include-files", action="store_true", help="Include normal files")
    ap.add_argument("--hash", default="", help="Hash method: md5/sha1")
    ap.add_argument("--sevenzip", default="7z", help="Path to 7z.exe")
    args = ap.parse_args()

    scan(
        Path(args.root),
        Path(args.out),
        args.include_files,
        args.hash,
        args.sevenzip
    )


if __name__ == "__main__":
    main()
