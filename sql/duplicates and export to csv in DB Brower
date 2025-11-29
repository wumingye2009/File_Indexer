WITH dup AS (
    SELECT
        e.id,
        e.name,
        e.parent_path,
        e.size_bytes,
        e.hash_value,
        e.library_id
    FROM entries e
    WHERE e.library_id = 1
      AND e.is_dir = 0
      AND e.hash_value <> ''
      AND (e.size_bytes, e.hash_value) IN (
            SELECT size_bytes, hash_value
            FROM entries
            WHERE library_id = 1
              AND is_dir = 0
              AND hash_value <> ''
            GROUP BY size_bytes, hash_value
            HAVING COUNT(*) > 1
      )
)
SELECT
    d.name AS filename,

    -- folder_path = root_path + parent_path（相对路径拼接）
    CASE
        WHEN d.parent_path = '.'
            THEN l.root_path
        ELSE
            l.root_path || '\' || d.parent_path
    END AS folder_path,

    d.size_bytes,
    d.hash_value
FROM dup d
JOIN library l
  ON d.library_id = l.id
ORDER BY d.hash_value, filename;
