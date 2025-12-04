-- 1. 重建 dup_ranked
DROP TABLE IF EXISTS dup_ranked;

CREATE TABLE Dup_Ranked AS

-- 第 1 层：先算出需要排序用的列
WITH base AS (
    SELECT
        d.*,

        -- 目录优先级
        CASE
            WHEN d.folder_path = 'D:\Code\Git_Project\File_indexer\data\samples\test_1'
              OR d.folder_path LIKE 'D:\Code\Git_Project\File_indexer\data\samples\test_1\作业\%' THEN 1
			      WHEN d.folder_path = 'G:\音效素材\主库2'
              OR d.folder_path LIKE 'G:\音效素材\主库2\%'   THEN 2			
            ELSE 99
        END AS pref_rank,

        -- 目录深度
        (LENGTH(d.folder_path) - LENGTH(REPLACE(d.folder_path, '\', ''))) AS depth,

        -- 路径长度
        LENGTH(d.folder_path) AS path_len
    FROM Dup_Check d
),

-- 第 2 层：在 base 的基础上做 ROW_NUMBER 分组排序
ranked AS (
    SELECT
        base.*,
        ROW_NUMBER() OVER (
            PARTITION BY base.hash_value
            ORDER BY
                base.pref_rank ASC,
                base.depth ASC,
                base.path_len ASC,
                base.folder_path ASC,
                base.filename ASC
        ) AS rn
    FROM base
)

SELECT *
FROM ranked;


-- 2. 建索引
CREATE INDEX idx_dup_ranked_hash
    ON dup_ranked(hash_value);

CREATE INDEX idx_dup_ranked_hash_rn
    ON dup_ranked(hash_value, rn);