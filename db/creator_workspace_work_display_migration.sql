SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Migration: add Work-level display fields for Portfolio Gallery publishing.
-- Use this only for an existing portfolio_library / creator_workspace database created before
-- content_type / cover_mode / cover_asset_id / summary / body were added.

DELIMITER $$

DROP PROCEDURE IF EXISTS add_column_if_missing $$
CREATE PROCEDURE add_column_if_missing(
  IN p_table_name VARCHAR(64),
  IN p_column_name VARCHAR(64),
  IN p_column_definition TEXT,
  IN p_after_column VARCHAR(64)
)
BEGIN
  IF NOT EXISTS (
    SELECT 1
      FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE()
       AND TABLE_NAME = p_table_name
       AND COLUMN_NAME = p_column_name
  ) THEN
    SET @ddl = CONCAT(
      'ALTER TABLE `', p_table_name, '` ADD COLUMN `',
      p_column_name, '` ', p_column_definition,
      IF(p_after_column IS NULL OR p_after_column = '', '', CONCAT(' AFTER `', p_after_column, '`'))
    );
    PREPARE stmt FROM @ddl;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END $$

DROP PROCEDURE IF EXISTS add_index_if_missing $$
CREATE PROCEDURE add_index_if_missing(
  IN p_table_name VARCHAR(64),
  IN p_index_name VARCHAR(64),
  IN p_index_definition TEXT
)
BEGIN
  IF NOT EXISTS (
    SELECT 1
      FROM INFORMATION_SCHEMA.STATISTICS
     WHERE TABLE_SCHEMA = DATABASE()
       AND TABLE_NAME = p_table_name
       AND INDEX_NAME = p_index_name
  ) THEN
    SET @ddl = CONCAT('ALTER TABLE `', p_table_name, '` ADD ', p_index_definition);
    PREPARE stmt FROM @ddl;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END $$

DROP PROCEDURE IF EXISTS add_fk_if_missing $$
CREATE PROCEDURE add_fk_if_missing(
  IN p_table_name VARCHAR(64),
  IN p_constraint_name VARCHAR(64),
  IN p_constraint_definition TEXT
)
BEGIN
  IF NOT EXISTS (
    SELECT 1
      FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
     WHERE TABLE_SCHEMA = DATABASE()
       AND TABLE_NAME = p_table_name
       AND CONSTRAINT_NAME = p_constraint_name
  ) THEN
    SET @ddl = CONCAT('ALTER TABLE `', p_table_name, '` ADD CONSTRAINT `', p_constraint_name, '` ', p_constraint_definition);
    PREPARE stmt FROM @ddl;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END $$

DELIMITER ;

CALL add_column_if_missing('work', 'summary', 'VARCHAR(500) DEFAULT NULL', 'description');
CALL add_column_if_missing('work', 'body', 'LONGTEXT DEFAULT NULL', 'summary');
CALL add_column_if_missing(
  'work',
  'content_type',
  'ENUM(''auto'', ''visual'', ''text'', ''mixed'', ''document'', ''video'', ''audio'', ''collection'') NOT NULL DEFAULT ''auto''',
  'body'
);
CALL add_column_if_missing(
  'work',
  'cover_mode',
  'ENUM(''auto'', ''image'', ''title'') NOT NULL DEFAULT ''auto''',
  'content_type'
);
CALL add_column_if_missing('work', 'cover_asset_id', 'BIGINT UNSIGNED DEFAULT NULL', 'cover_mode');

CALL add_index_if_missing('work', 'idx_work_cover_asset', 'KEY `idx_work_cover_asset` (`cover_asset_id`)');
CALL add_fk_if_missing(
  'work',
  'fk_work_cover_asset',
  'FOREIGN KEY (`cover_asset_id`) REFERENCES `media_asset` (`asset_id`) ON UPDATE CASCADE ON DELETE SET NULL'
);

UPDATE work
   SET summary = LEFT(description, 500)
 WHERE summary IS NULL
   AND description IS NOT NULL
   AND description <> '';

UPDATE work
   SET body = description
 WHERE body IS NULL
   AND description IS NOT NULL
   AND CHAR_LENGTH(description) > 160;

UPDATE work
   SET content_type = CASE work_type
     WHEN 'illustration' THEN 'visual'
     WHEN 'photography' THEN 'visual'
     WHEN 'article' THEN 'text'
     WHEN 'video' THEN 'video'
     WHEN 'design' THEN 'mixed'
     ELSE 'auto'
   END
 WHERE content_type = 'auto';

DROP PROCEDURE IF EXISTS add_column_if_missing;
DROP PROCEDURE IF EXISTS add_index_if_missing;
DROP PROCEDURE IF EXISTS add_fk_if_missing;
