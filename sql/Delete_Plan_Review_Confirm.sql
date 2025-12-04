--Review what will be deleted (before setting verify_flag)
SELECT
    id,
    hash_value,
    library_id,
    full_path,
    size_bytes,
    group_size,
    is_keep,
    delete_flag,
    verify_flag,
    safety_status,
    rn
FROM delete_plan
WHERE delete_flag = 1
  AND safety_status = 'OK'
ORDER BY hash_value, group_size DESC, full_path;

--Conservative batch rules to set verify_flag
--Sample rules1:
--Only groups of size 2 and only files from library AA I want to clean up.

UPDATE delete_plan
SET verify_flag = 1,
    reason = reason || '; auto-verified: group_size=2, AA library'
WHERE delete_flag = 1
  AND safety_status = 'OK'
  AND verify_flag = 0
  AND group_size = 2
  AND library_id = (SELECT id FROM library WHERE root_path = 'D:\AA');

--Then confirm:
SELECT COUNT(*) AS files_marked_for_delete,
       SUM(bytes_to_free) AS bytes_to_free
FROM delete_plan
WHERE delete_flag = 1
  AND verify_flag = 1
  AND safety_status = 'OK';


--Sample rules2:
--Only in certain folders (e.g. only under D:\AA\temp):

UPDATE delete_plan
SET verify_flag = 1,
    reason = reason || '; auto-verified: AA\temp'
WHERE delete_flag = 1
  AND safety_status = 'OK'
  AND verify_flag = 0
  AND library_id = (SELECT id FROM library WHERE root_path = 'D:\AA')
  AND full_path LIKE 'D:\AA\temp\%';


--Sample rules3:
--Only groups that already have one keep file in D:\cleaned:
UPDATE delete_plan
SET verify_flag = 1,
    reason = reason || '; auto-verified: duplicate of cleaned'
WHERE delete_flag = 1
  AND safety_status = 'OK'
  AND verify_flag = 0
  AND hash_value IN (
      SELECT hash_value
      FROM delete_plan
      WHERE is_keep = 1
        AND library_id = (SELECT id FROM library WHERE root_path = 'D:\cleaned')
  );

