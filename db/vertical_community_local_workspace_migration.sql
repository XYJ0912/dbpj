-- Local creator workspace migration.
-- Run after the existing schema/procedures/views/seed SQL files.

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

ALTER TABLE `media_asset`
  MODIFY COLUMN `media_type` ENUM('image', 'audio', 'video', 'gif', 'document', 'other') NOT NULL;

ALTER TABLE `media_asset`
  ADD COLUMN `storage_mode` ENUM('reference', 'managed', 'external') NOT NULL DEFAULT 'reference',
  ADD COLUMN `local_path` VARCHAR(1024) DEFAULT NULL,
  ADD COLUMN `checksum_sha256` CHAR(64) DEFAULT NULL,
  ADD COLUMN `thumbnail_path` VARCHAR(1024) DEFAULT NULL,
  ADD COLUMN `public_export_path` VARCHAR(1024) DEFAULT NULL,
  ADD COLUMN `visibility` ENUM('private', 'public') NOT NULL DEFAULT 'private',
  ADD COLUMN `import_status` ENUM('active', 'missing', 'archived') NOT NULL DEFAULT 'active',
  ADD COLUMN `file_exists` BOOLEAN NOT NULL DEFAULT TRUE,
  ADD COLUMN `last_checked_at` DATETIME DEFAULT NULL,
  ADD COLUMN `missing_reason` VARCHAR(255) DEFAULT NULL,
  ADD KEY `idx_media_visibility_type` (`visibility`, `media_type`),
  ADD KEY `idx_media_import_status` (`import_status`);

ALTER TABLE `content_media`
  ADD COLUMN `role` ENUM('cover', 'main', 'process', 'reference', 'attachment') NOT NULL DEFAULT 'main',
  ADD COLUMN `is_public` BOOLEAN NOT NULL DEFAULT TRUE,
  ADD KEY `idx_contentmedia_public_role` (`is_public`, `role`);

DROP TABLE IF EXISTS `asset_license_note`;
CREATE TABLE `asset_license_note` (
    `license_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `media_id` BIGINT UNSIGNED NOT NULL,
    `authorization_status` ENUM('original', 'licensed', 'unknown', 'restricted') NOT NULL DEFAULT 'unknown',
    `source_name` VARCHAR(200) DEFAULT NULL,
    `source_url` VARCHAR(512) DEFAULT NULL,
    `license_note` VARCHAR(1000) DEFAULT NULL,
    `allow_public_display` BOOLEAN NOT NULL DEFAULT FALSE,
    `allow_commercial_use` BOOLEAN NOT NULL DEFAULT FALSE,
    `attribution_required` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`license_id`),
    UNIQUE KEY `uk_license_media` (`media_id`),
    KEY `idx_license_status` (`authorization_status`),
    CONSTRAINT `fk_license_media` FOREIGN KEY (`media_id`)
      REFERENCES `media_asset` (`media_id`)
      ON UPDATE CASCADE
      ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '本地作品资产授权说明';

DROP TABLE IF EXISTS `publish_report`;
DROP TABLE IF EXISTS `publish_item`;
DROP TABLE IF EXISTS `publish_snapshot`;

CREATE TABLE `publish_snapshot` (
    `snapshot_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `snapshot_name` VARCHAR(200) NOT NULL,
    `output_dir` VARCHAR(1024) NOT NULL,
    `homepage_config` JSON NOT NULL,
    `public_data` JSON NOT NULL,
    `status` ENUM('draft', 'generated', 'failed') NOT NULL DEFAULT 'draft',
    `package_size_bytes` BIGINT UNSIGNED DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`snapshot_id`),
    KEY `idx_publish_user_time` (`user_id`, `created_at`),
    CONSTRAINT `fk_publish_user` FOREIGN KEY (`user_id`)
      REFERENCES `user` (`user_id`)
      ON UPDATE CASCADE
      ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '静态主页发布快照';

CREATE TABLE `publish_item` (
    `snapshot_id` BIGINT UNSIGNED NOT NULL,
    `item_type` ENUM('content', 'media') NOT NULL,
    `item_id` BIGINT UNSIGNED NOT NULL,
    `public_url` VARCHAR(1024) DEFAULT NULL,
    `exported_size_bytes` BIGINT UNSIGNED DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`snapshot_id`, `item_type`, `item_id`),
    KEY `idx_publish_item_type_id` (`item_type`, `item_id`),
    CONSTRAINT `fk_publish_item_snapshot` FOREIGN KEY (`snapshot_id`)
      REFERENCES `publish_snapshot` (`snapshot_id`)
      ON UPDATE CASCADE
      ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '发布快照导出条目';

CREATE TABLE `publish_report` (
    `report_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `snapshot_id` BIGINT UNSIGNED NOT NULL,
    `check_type` VARCHAR(80) NOT NULL,
    `severity` ENUM('info', 'warning', 'error') NOT NULL DEFAULT 'info',
    `message` VARCHAR(500) NOT NULL,
    `related_table` VARCHAR(80) DEFAULT NULL,
    `related_id` BIGINT UNSIGNED DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`report_id`),
    KEY `idx_report_snapshot_severity` (`snapshot_id`, `severity`),
    CONSTRAINT `fk_report_snapshot` FOREIGN KEY (`snapshot_id`)
      REFERENCES `publish_snapshot` (`snapshot_id`)
      ON UPDATE CASCADE
      ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '发布安全检查报告';

CREATE OR REPLACE VIEW `v_workspace_asset` AS
SELECT
    m.`media_id`,
    m.`uploader_id`,
    m.`media_type`,
    m.`file_path`,
    m.`file_size`,
    m.`mime_type`,
    m.`width`,
    m.`height`,
    m.`duration`,
    m.`upload_time`,
    m.`storage_mode`,
    m.`local_path`,
    m.`thumbnail_path`,
    m.`public_export_path`,
    m.`visibility`,
    m.`import_status`,
    m.`file_exists`,
    m.`last_checked_at`,
    m.`missing_reason`,
    COALESCE(l.`authorization_status`, 'unknown') AS `authorization_status`,
    l.`source_name`,
    l.`source_url`,
    l.`license_note`,
    l.`allow_public_display`,
    l.`attribution_required`
FROM `media_asset` m
LEFT JOIN `asset_license_note` l ON l.`media_id` = m.`media_id`;

CREATE OR REPLACE VIEW `v_workspace_work` AS
SELECT
    c.`content_id`,
    c.`author_id`,
    c.`title`,
    c.`body`,
    c.`content_type`,
    c.`content_status`,
    c.`visibility`,
    c.`created_at`,
    c.`updated_at`,
    COUNT(cm.`media_id`) AS `asset_count`,
    SUM(CASE WHEN cm.`is_public` THEN 1 ELSE 0 END) AS `public_asset_count`
FROM `content` c
LEFT JOIN `content_media` cm ON cm.`content_id` = c.`content_id`
WHERE c.`content_status` <> 'deleted'
GROUP BY c.`content_id`, c.`author_id`, c.`title`, c.`body`, c.`content_type`,
         c.`content_status`, c.`visibility`, c.`created_at`, c.`updated_at`;

CREATE OR REPLACE VIEW `v_publishable_content` AS
SELECT *
FROM `v_workspace_work`
WHERE `content_status` = 'published'
  AND `visibility` = 'public';

CREATE OR REPLACE VIEW `v_publish_report_summary` AS
SELECT
    ps.`snapshot_id`,
    ps.`user_id`,
    ps.`snapshot_name`,
    ps.`status`,
    ps.`output_dir`,
    ps.`created_at`,
    SUM(CASE WHEN pr.`severity` = 'error' THEN 1 ELSE 0 END) AS `error_count`,
    SUM(CASE WHEN pr.`severity` = 'warning' THEN 1 ELSE 0 END) AS `warning_count`,
    SUM(CASE WHEN pr.`severity` = 'info' THEN 1 ELSE 0 END) AS `info_count`
FROM `publish_snapshot` ps
LEFT JOIN `publish_report` pr ON pr.`snapshot_id` = ps.`snapshot_id`
GROUP BY ps.`snapshot_id`, ps.`user_id`, ps.`snapshot_name`, ps.`status`, ps.`output_dir`, ps.`created_at`;
