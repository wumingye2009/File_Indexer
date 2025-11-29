# file_indexer

A small toolkit for indexing files and archives (ZIP, 7z, RAR, TAR…), detecting duplicates, and doing basic statistics using CSV + SQLite + Python.

This project was originally created to manage a very large BGM/audio library (10–15 TB) spread across local disks and cloud drives, but the tools are generic enough to be used for any kind of files.

# File & Archive Indexer

A small toolkit for indexing files and archives (ZIP, 7z, RAR, TAR…), detecting duplicates, and doing basic statistics using CSV + SQLite + Python.

This project was originally created to manage a very large BGM/audio library (10–15 TB) spread across local disks and cloud drives, but the tools are generic enough to be used for any kind of files.

---

## Features (Planned & Current)

- **File/Archive Indexer**
  - Recursively scan a root folder and list:
    - Archive files (e.g. `.zip`, `.7z`, `.rar`, `.tar`, `.tgz`, …)
    - Optional: normal files (e.g. `.mp3`, `.wav`, `.flac`, `.jpg`, …)
  - Use `7z` (`7-Zip`) to list archive contents *without extracting*.
  - Export all metadata to a CSV file:
    - `archive_path`, `archive_ext`, `archive_size_bytes`, `archive_mtime_iso`, `archive_hash`
    - `entry_path_in_archive`, `entry_ext`, `entry_size_bytes`, `is_dir`, `is_encrypted`, `method`

- **SQLite Integration** (planned)
  - Import CSV into SQLite tables.
  - Provide example SQL queries for:
    - Finding duplicate archives (same hash/size).
    - Finding candidate duplicate files (same size/ext, later by content hash).

- **Duplicate Detection** (planned)
  - Archive-level dedupe: identify identical archives stored in multiple locations.
  - File-level dedupe: identify identical or highly similar files.
  - Output reports as CSV (for manual review before deleting anything).

- **Statistics & Reports** (planned)
  - File count and total size by extension, folder, or device.
  - Duplicate ratio and potential space savings.
  - Simple summaries for large audio/BGM collections.

---

## Project Structure

```text
file-indexer/
├─ README.md
├─ .gitignore
├─ requirements.txt
├─ src/
│  └─ file_indexer/
│     ├─ __init__.py
│     ├─ index_archives.py     # main indexing script (archives + normal files → CSV)
│     ├─ db_import.py          # CSV → SQLite (planned)
│     ├─ dedupe_archives.py    # duplicate archives detection (planned)
│     ├─ dedupe_files.py       # duplicate files detection (planned)
│     └─ stats_report.py       # basic statistics / reporting (planned)
├─ sql/
│  ├─ create_tables.sql        # table definitions for SQLite (planned)
│  └─ example_queries.sql      # example queries for dedupe + stats (planned)
├─ data/
│  ├─ samples/                 # small sample CSV/DB files for testing
│  └─ workspace/               # real CSV/SQLite files (ignored by git)
└─ scripts/
   ├─ windows/
   │  └─ run_index_archives.ps1
   └─ linux/
      └─ run_index_archives.sh

```

## 脚本用法示例
### 1.只扫描压缩包
···
python index_bgm_archives.py --root "E:\BGM_Raw" --out "D:\index_bgm_archives.csv"
···

### 2.扫描压缩包 + 扫描所有普通文件
···
python index_bgm_archives.py --root "E:\BGM_Raw" --out "D:\index_all_files.csv" --include-files
···

### 3.只扫描压缩包 + 扫描指定类型音频文件（.mp3、.wav）
```
python index_bgm_archives.py --root "E:\BGM_Raw" --out "D:\index_bgm_and_archives.csv" --include-files --file-exts ".mp3,.wav"
```

### 4.开启 MD5（对压缩包和普通文件都计算 hash）
```
python index_bgm_archives.py --root "E:\BGM_Raw" --out "D:\index_with_hash.csv" --include-files --hash md5
```


## 字段说明
```
① archive_size_bytes

含义：archive_path 这个文件本身在磁盘上的大小（单位：字节）

对压缩包：就是压缩包体积

对普通文件：就是 mp3/docx 等的文件大小

② archive_mtime_iso

含义：archive_path 文件的最后修改时间（ISO 格式，方便对比 & 排序）
例：2024-05-28T08:08:25

③ entry_size_bytes

如果这是压缩包内部的 文件：

表示该文件 解压后的大小（单位：字节）

如果是压缩包内部的 目录（is_dir = 1）：

一般为 0 或空

如果是普通文件行（entry_path_in_archive 为空）：

这个字段一般为空（因为没意义）

④ is_dir

"1" → 这是一个目录（压缩包内部的文件夹）

"0" → 这是一个文件（普通文件 / 压缩包内部的 mp3/zip/rar 等）

注意：
即使是普通 mp3 行（entry_path_in_archive 为空），我们也写 is_dir = 0，表明“这不是目录”。

⑤ method

压缩算法 / 存储方式

示例：

Store → 不压缩，原样存储

Deflate → 常见的 zip 压缩算法

v6:m3:16M → rar/7z 自己的一些内部方法标记

你可以用它来分析：

哪些压缩包是无损封装（Store）→ 解压速度快

哪些使用了较重的压缩 → 解压会慢，后续处理时要注意。
```