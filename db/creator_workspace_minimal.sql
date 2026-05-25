SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS publish_report;
DROP TABLE IF EXISTS publish_snapshot;
DROP TABLE IF EXISTS asset_license_note;
DROP TABLE IF EXISTS work_media;
DROP TABLE IF EXISTS media_asset;
DROP TABLE IF EXISTS work_tag;
DROP TABLE IF EXISTS tag;
DROP TABLE IF EXISTS work;
DROP TABLE IF EXISTS creator_profile;
DROP TABLE IF EXISTS user_account;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE user_account (
  user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(80) NOT NULL,
  email VARCHAR(200) NOT NULL,
  password_hash VARCHAR(128) NOT NULL,
  account_status ENUM('active', 'disabled') NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_at DATETIME DEFAULT NULL,
  PRIMARY KEY (user_id),
  UNIQUE KEY uk_user_username (username),
  UNIQUE KEY uk_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE creator_profile (
  profile_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  display_name VARCHAR(120) NOT NULL,
  bio TEXT,
  avatar_url VARCHAR(1024),
  homepage_config JSON NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (profile_id),
  UNIQUE KEY uk_profile_user (user_id),
  CONSTRAINT fk_profile_user FOREIGN KEY (user_id)
    REFERENCES user_account (user_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE work (
  work_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  owner_id BIGINT UNSIGNED NOT NULL,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  summary VARCHAR(500),
  body LONGTEXT,
  content_type ENUM('auto', 'visual', 'text', 'mixed', 'document', 'video', 'audio', 'collection') NOT NULL DEFAULT 'auto',
  cover_mode ENUM('auto', 'image', 'title') NOT NULL DEFAULT 'auto',
  cover_asset_id BIGINT UNSIGNED DEFAULT NULL,
  work_type ENUM('illustration', 'photography', 'article', 'video', 'design', 'other') NOT NULL DEFAULT 'other',
  visibility ENUM('private', 'public') NOT NULL DEFAULT 'private',
  work_status ENUM('draft', 'ready', 'archived') NOT NULL DEFAULT 'draft',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (work_id),
  KEY idx_work_owner_status (owner_id, work_status, visibility),
  KEY idx_work_cover_asset (cover_asset_id),
  CONSTRAINT fk_work_owner FOREIGN KEY (owner_id)
    REFERENCES user_account (user_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tag (
  tag_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  owner_id BIGINT UNSIGNED NOT NULL,
  tag_name VARCHAR(120) NOT NULL,
  tag_type ENUM('style', 'topic', 'series', 'character', 'tool', 'custom') NOT NULL DEFAULT 'custom',
  tag_status ENUM('active', 'archived') NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (tag_id),
  UNIQUE KEY uk_tag_owner_name_type (owner_id, tag_name, tag_type),
  CONSTRAINT fk_tag_owner FOREIGN KEY (owner_id)
    REFERENCES user_account (user_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE work_tag (
  work_id BIGINT UNSIGNED NOT NULL,
  tag_id BIGINT UNSIGNED NOT NULL,
  tagged_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (work_id, tag_id),
  CONSTRAINT fk_worktag_work FOREIGN KEY (work_id)
    REFERENCES work (work_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_worktag_tag FOREIGN KEY (tag_id)
    REFERENCES tag (tag_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE media_asset (
  asset_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  owner_id BIGINT UNSIGNED NOT NULL,
  asset_name VARCHAR(200) NOT NULL,
  media_type ENUM('image', 'video', 'audio', 'document', 'other') NOT NULL DEFAULT 'image',
  local_path VARCHAR(1024),
  thumbnail_path VARCHAR(1024),
  public_export_path VARCHAR(1024),
  file_size BIGINT UNSIGNED,
  mime_type VARCHAR(120),
  checksum_sha256 CHAR(64),
  visibility ENUM('private', 'public') NOT NULL DEFAULT 'private',
  import_status ENUM('active', 'missing', 'archived') NOT NULL DEFAULT 'active',
  file_exists BOOLEAN NOT NULL DEFAULT FALSE,
  last_checked_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (asset_id),
  KEY idx_asset_owner_visibility (owner_id, visibility, import_status),
  CONSTRAINT fk_asset_owner FOREIGN KEY (owner_id)
    REFERENCES user_account (user_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE work
  ADD CONSTRAINT fk_work_cover_asset FOREIGN KEY (cover_asset_id)
    REFERENCES media_asset (asset_id)
    ON UPDATE CASCADE
    ON DELETE SET NULL;

CREATE TABLE work_media (
  work_id BIGINT UNSIGNED NOT NULL,
  asset_id BIGINT UNSIGNED NOT NULL,
  role ENUM('cover', 'main', 'process', 'reference', 'attachment') NOT NULL DEFAULT 'main',
  display_order INT NOT NULL DEFAULT 0,
  is_public BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (work_id, asset_id),
  CONSTRAINT fk_workmedia_work FOREIGN KEY (work_id)
    REFERENCES work (work_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_workmedia_asset FOREIGN KEY (asset_id)
    REFERENCES media_asset (asset_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE asset_license_note (
  license_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  asset_id BIGINT UNSIGNED NOT NULL,
  authorization_status ENUM('original', 'licensed', 'unknown', 'restricted') NOT NULL DEFAULT 'unknown',
  source_name VARCHAR(200),
  source_url VARCHAR(512),
  license_note VARCHAR(1000),
  allow_public_display BOOLEAN NOT NULL DEFAULT FALSE,
  attribution_required BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (license_id),
  UNIQUE KEY uk_license_asset (asset_id),
  KEY idx_license_status (authorization_status),
  CONSTRAINT fk_license_asset FOREIGN KEY (asset_id)
    REFERENCES media_asset (asset_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE publish_snapshot (
  snapshot_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  snapshot_name VARCHAR(200) NOT NULL,
  output_dir VARCHAR(1024) NOT NULL DEFAULT '',
  homepage_config JSON NOT NULL,
  public_data JSON NOT NULL,
  status ENUM('draft', 'generated', 'failed') NOT NULL DEFAULT 'draft',
  package_size_bytes BIGINT UNSIGNED,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (snapshot_id),
  KEY idx_snapshot_user_time (user_id, created_at),
  CONSTRAINT fk_snapshot_user FOREIGN KEY (user_id)
    REFERENCES user_account (user_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE publish_report (
  report_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  snapshot_id BIGINT UNSIGNED,
  check_type VARCHAR(80) NOT NULL,
  severity ENUM('info', 'warning', 'error') NOT NULL DEFAULT 'info',
  message VARCHAR(500) NOT NULL,
  related_table VARCHAR(80),
  related_id BIGINT UNSIGNED,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (report_id),
  KEY idx_report_snapshot_severity (snapshot_id, severity),
  CONSTRAINT fk_report_snapshot FOREIGN KEY (snapshot_id)
    REFERENCES publish_snapshot (snapshot_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE OR REPLACE VIEW v_workspace_asset AS
SELECT
  a.asset_id,
  a.owner_id,
  a.asset_name,
  a.media_type,
  a.local_path,
  a.thumbnail_path,
  a.public_export_path,
  a.file_size,
  a.mime_type,
  a.visibility,
  a.import_status,
  a.file_exists,
  a.last_checked_at,
  a.created_at,
  COALESCE(l.authorization_status, 'unknown') AS authorization_status,
  l.source_name,
  l.source_url,
  l.allow_public_display,
  l.attribution_required
FROM media_asset a
LEFT JOIN asset_license_note l ON l.asset_id = a.asset_id;

CREATE OR REPLACE VIEW v_workspace_work AS
SELECT
  w.work_id,
  w.owner_id,
  w.title,
  w.description,
  w.summary,
  w.body,
  w.content_type,
  w.cover_mode,
  w.cover_asset_id,
  w.work_type,
  w.visibility,
  w.work_status,
  w.created_at,
  w.updated_at,
  COUNT(wm.asset_id) AS asset_count,
  COALESCE(SUM(CASE WHEN wm.is_public THEN 1 ELSE 0 END), 0) AS public_asset_count
FROM work w
LEFT JOIN work_media wm ON wm.work_id = w.work_id
GROUP BY w.work_id, w.owner_id, w.title, w.description, w.summary, w.body, w.content_type, w.cover_mode, w.cover_asset_id, w.work_type, w.visibility, w.work_status, w.created_at, w.updated_at;

CREATE OR REPLACE VIEW v_publishable_work AS
SELECT *
FROM v_workspace_work
WHERE visibility = 'public'
  AND work_status = 'ready';

CREATE OR REPLACE VIEW v_publish_report_summary AS
SELECT
  s.snapshot_id,
  s.user_id,
  s.snapshot_name,
  s.status,
  s.output_dir,
  s.created_at,
  COALESCE(SUM(CASE WHEN r.severity = 'error' THEN 1 ELSE 0 END), 0) AS error_count,
  COALESCE(SUM(CASE WHEN r.severity = 'warning' THEN 1 ELSE 0 END), 0) AS warning_count,
  COALESCE(SUM(CASE WHEN r.severity = 'info' THEN 1 ELSE 0 END), 0) AS info_count
FROM publish_snapshot s
LEFT JOIN publish_report r ON r.snapshot_id = s.snapshot_id
GROUP BY s.snapshot_id, s.user_id, s.snapshot_name, s.status, s.output_dir, s.created_at;

INSERT INTO user_account (username, email, password_hash, last_login_at)
VALUES ('demo', 'demo@example.com', '$2b$12$2bb80d537b1da3e38bd30361aa855686bde0eacd', NOW());

SET @demo_user_id = LAST_INSERT_ID();

INSERT INTO creator_profile (user_id, display_name, bio, homepage_config)
VALUES (
  @demo_user_id,
  'Demo Library',
  'A local-first personal asset library and portfolio demo.',
  JSON_OBJECT(
    'template_id', 'creator_gallery',
    'theme', 'warm_gallery',
    'accent_color', '#8fb8a8',
    'featured_work_ids', JSON_ARRAY(),
    'creator_tags', JSON_ARRAY('Portfolio', 'Archive', 'Personal Library'),
    'contact_links', JSON_ARRAY(
      JSON_OBJECT('label', 'Email', 'url', 'mailto:hello@example.com'),
      JSON_OBJECT('label', 'Website', 'url', '#')
    ),
    'license_text', 'Unless otherwise noted, public works are for portfolio display only.'
  )
);

SET FOREIGN_KEY_CHECKS = 1;
