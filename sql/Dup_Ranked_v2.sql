-- =========================================================
-- 1. Rebuild dup_ranked
--    - Adds entry_id, library_id for safe linking to entries
--    - Keeps your original ranking rules
-- =========================================================

DROP TABLE IF EXISTS dup_ranked;

CREATE TABLE dup_ranked AS
WITH raw AS (
    SELECT
        e.id          AS entry_id,
        e.library_id  AS library_id,
        e.name        AS filename,
        d.folder_path AS folder_path,
        e.full_path   AS full_path,
        e.size_bytes  AS size_bytes,
        e.hash_value  AS hash_value
    FROM dup_check d
    JOIN entries e
      ON e.full_path = d.folder_path || '\' || d.filename
      -- 可选的额外保护（不是必须）：
      AND e.size_bytes = d.size_bytes
      AND e.hash_value = d.hash_value
),

base AS (
    SELECT
        raw.*,

        -- 目录优先级：根据你的实际路径调整
        CASE
            WHEN raw.folder_path = 'D:\Code\Git_Project\File_indexer\data\samples\test_1'
              OR raw.folder_path LIKE 'D:\Code\Git_Project\File_indexer\data\samples\test_1\作业\%' THEN 1

            WHEN raw.folder_path = 'G:\音效素材\主库2'
              OR raw.folder_path LIKE 'G:\音效素材\主库2\%' THEN 2

            ELSE 99
        END AS pref_rank,

        -- 目录深度：统计 "\" 的数量
        (LENGTH(raw.folder_path) - LENGTH(REPLACE(raw.folder_path, '\', ''))) AS depth,

        -- 路径长度
        LENGTH(raw.folder_path) AS path_len
    FROM raw
),

ranked AS (
    SELECT
        base.*,
        ROW_NUMBER() OVER (
            -- 当前版本：按 hash_value 分组，一个 hash 只保留 1 个文件
            -- 如需跨库优先级，可改为 PARTITION BY base.hash_value
            PARTITION BY base.hash_value
            ORDER BY
                base.pref_rank ASC,
                base.depth    ASC,
                base.path_len ASC,
                base.folder_path ASC,
                base.filename    ASC
        ) AS rn
    FROM base
)

SELECT *
FROM ranked;

-- =========================================================
-- 2. Indexes
-- =========================================================

-- 按 hash_value 查找一组重复文件
CREATE INDEX IF NOT EXISTS idx_dup_ranked_hash
    ON dup_ranked (hash_value);

-- 按 hash_value + rn 快速定位“保留文件(rn=1)”和“待删文件(rn>1)”
CREATE INDEX IF NOT EXISTS idx_dup_ranked_hash_rn
    ON dup_ranked (hash_value, rn);

-- 可选：按 entry_id / library_id 查询
CREATE INDEX IF NOT EXISTS idx_dup_ranked_entry
    ON dup_ranked (entry_id);

CREATE INDEX IF NOT EXISTS idx_dup_ranked_lib_hash
    ON dup_ranked (library_id, hash_value);
