-- Optional: start fresh
DELETE FROM delete_plan;

INSERT INTO delete_plan (
    hash_value,
    library_id,
    entry_id,
    full_path,
    rn,
    size_bytes,
    is_keep,
    delete_flag,
    verify_flag,
    reason,
    safety_status,
    group_size,
    group_has_rn1,
    group_multi_rn1,
    group_bytes_total,
    bytes_to_free
)
SELECT
    dr.hash_value,
    dr.library_id,
    dr.entry_id,
    dr.full_path,
    dr.rn,
    dr.size_bytes,

    -- per-row role
    CASE WHEN dr.rn = 1 THEN 1 ELSE 0 END AS is_keep,

    -- auto delete flag: only rn>1 AND group has exactly one rn=1
    CASE
        WHEN dr.rn > 1
             AND g.has_rn1 = 1
             AND g.multi_rn1 = 0
        THEN 1 ELSE 0
    END AS delete_flag,

    0 AS verify_flag,  -- you will flip to 1 after manual review

    'auto: rn>1, single keep per hash' AS reason,

    -- safety status at group level
    CASE
        WHEN g.has_rn1 = 0 THEN 'ERROR_NO_KEEP'
        WHEN g.multi_rn1 = 1 THEN 'ERROR_MULTI_KEEP'
        ELSE 'OK'
    END AS safety_status,

    -- group stats
    g.group_size,
    g.has_rn1,
    g.multi_rn1,
    g.total_bytes AS group_bytes_total,

    CASE
        WHEN dr.rn > 1
             AND g.has_rn1 = 1
             AND g.multi_rn1 = 0
        THEN dr.size_bytes
        ELSE 0
    END AS bytes_to_free
FROM dup_ranked dr
JOIN (
    SELECT
        hash_value,
        COUNT(*)                    AS group_size,
        SUM(size_bytes)             AS total_bytes,
        MAX(CASE WHEN rn = 1 THEN 1 ELSE 0 END) AS has_rn1,
        CASE
            WHEN SUM(CASE WHEN rn = 1 THEN 1 ELSE 0 END) > 1
            THEN 1 ELSE 0
        END                          AS multi_rn1
    FROM dup_ranked
    GROUP BY hash_value
) g ON g.hash_value = dr.hash_value;
