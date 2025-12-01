CREATE TABLE library (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,      -- 比如 'organized', 'source_a', 'source_b'
    root_path  TEXT NOT NULL,      -- 实际根路径，如 'D:/整理完成'
    note       TEXT,
    created_at TEXT NOT NULL
);


CREATE TABLE entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    library_id  INTEGER NOT NULL,          -- 来自哪个库
    full_path   TEXT NOT NULL,             -- 绝对路径(统一用 / 或 \\，建议 / )
    parent_path TEXT NOT NULL,             -- 相对 root 的父路径
    name        TEXT NOT NULL,             -- 文件名
    ext         TEXT,                      -- 扩展名（小写）
    is_dir      INTEGER NOT NULL,          -- 0=文件,1=目录
    is_archive  INTEGER NOT NULL DEFAULT 0,-- 0=普通文件,1=压缩包文件

    size_bytes  INTEGER,                   -- 文件大小
    mtime       REAL,                      -- 修改时间(Unix 时间戳，可选)

    hash_algo   TEXT,                      -- 哈希算法，如 'sha256'
    hash_value  TEXT,                      -- 哈希值

    extra_meta  TEXT,                      -- 预留 JSON
    FOREIGN KEY (library_id) REFERENCES library(id)
);

CREATE INDEX idx_entries_lib ON entries(library_id);
CREATE INDEX idx_entries_hash ON entries(hash_value);
CREATE INDEX idx_entries_size ON entries(size_bytes);
CREATE INDEX idx_entries_full_path ON entries(full_path);

CREATE TABLE archives (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    library_id       INTEGER NOT NULL,        -- 来自哪个库(跟压缩包一致)
    archive_full_path TEXT NOT NULL,         -- 压缩包自己的 full_path（用于关联 entries）
    archive_entry_id INTEGER,                -- 后续导入时可填 entries.id（可选）

    member_path      TEXT NOT NULL,          -- 压缩包内部路径，如 'disc1/track01.wav'
    member_size      INTEGER,
    member_mtime     REAL,

    hash_algo        TEXT,
    hash_value       TEXT,

    extra_meta       TEXT,

    FOREIGN KEY (library_id)       REFERENCES library(id),
    FOREIGN KEY (archive_entry_id) REFERENCES entries(id)
);

CREATE INDEX idx_archives_hash ON archives(hash_value);
CREATE INDEX idx_archives_archive ON archives(archive_full_path);
