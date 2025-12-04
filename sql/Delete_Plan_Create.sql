CREATE TABLE IF NOT EXISTS delete_plan (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,

    -- group identity
    hash_value        TEXT    NOT NULL,
    library_id        INTEGER NOT NULL,
    entry_id          INTEGER NOT NULL,

    -- file info
    full_path         TEXT    NOT NULL,
    rn                INTEGER NOT NULL,   -- ranking from dup_ranked
    size_bytes        INTEGER,

    -- role in group
    is_keep           INTEGER NOT NULL DEFAULT 0,  -- 1 if rn = 1
    delete_flag       INTEGER NOT NULL DEFAULT 0,  -- 1 if planned to delete
    verify_flag       INTEGER NOT NULL DEFAULT 0,  -- 1 after you manually approve

    -- logic/safety explanation
    reason            TEXT,                       -- "auto: rn>1", etc.
    safety_status     TEXT,                       -- 'OK', 'ERROR_NO_KEEP', 'ERROR_MULTI_KEEP', ...

    -- group-level stats (same across all rows in the same hash)
    group_size        INTEGER,
    group_has_rn1     INTEGER,
    group_multi_rn1   INTEGER,
    group_bytes_total INTEGER,
    bytes_to_free     INTEGER,                    -- = size_bytes if delete_flag=1 else 0

    -- audit info
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at        TEXT,                       -- filled after actual deletion
    error_msg         TEXT,                       -- if deletion failed

    FOREIGN KEY (library_id) REFERENCES library(id),
    FOREIGN KEY (entry_id)  REFERENCES entries(id)
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_delete_plan_hash
    ON delete_plan(hash_value);

CREATE INDEX IF NOT EXISTS idx_delete_plan_delete
    ON delete_plan(delete_flag, verify_flag, safety_status);

CREATE INDEX IF NOT EXISTS idx_delete_plan_entry
    ON delete_plan(entry_id);
