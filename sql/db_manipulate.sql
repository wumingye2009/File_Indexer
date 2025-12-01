--empty the database tables before re-indexing
DELETE FROM archives;
DELETE FROM entries;
DELETE FROM library;


SELECT * FROM library;
SELECT COUNT(*) FROM entries;
SELECT COUNT(*) FROM archives;


-- To run the database creation script, use the following command:run under the project root directory D:\Code\Git_Project\File_indexer>
python src/file_indexer/create_db.py





--- Find duplicate files based on hash values

SELECT hash_value,count(*) as dup_count 
FROM Dup_Check         -- It a view created for checking duplicates(see in CTE_Dup_Check.sql)
GROUP BY hash_value
ORDER BY dup_count DESC
limit 10
