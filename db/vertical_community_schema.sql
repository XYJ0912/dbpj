-- ============================================================
-- 垂直兴趣社区数据库 Schema（MySQL 8.0+）
-- 基于《垂直兴趣社区_数据库概念设计_v3.2》整理
-- ============================================================

SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

-- 先清理旧触发器，避免重复创建
DROP TRIGGER IF EXISTS `trg_like_insert`;

DROP TRIGGER IF EXISTS `trg_like_delete`;

DROP TRIGGER IF EXISTS `trg_like_update`;

DROP TRIGGER IF EXISTS `trg_comment_insert`;

DROP TRIGGER IF EXISTS `trg_comment_delete`;

DROP TRIGGER IF EXISTS `trg_comment_status_update`;

DROP TRIGGER IF EXISTS `trg_comment_update`;

DROP TRIGGER IF EXISTS `trg_browse_insert`;

DROP TRIGGER IF EXISTS `trg_tag_before_insert`;

DROP TRIGGER IF EXISTS `trg_tag_before_update`;

DROP TRIGGER IF EXISTS `trg_comment_before_insert`;

DROP TRIGGER IF EXISTS `trg_comment_before_update`;

DROP TRIGGER IF EXISTS `trg_follow_before_insert`;

DROP TRIGGER IF EXISTS `trg_follow_before_update`;

DROP TRIGGER IF EXISTS `trg_tag_relation_before_insert`;

DROP TRIGGER IF EXISTS `trg_tag_relation_before_update`;

DROP TRIGGER IF EXISTS `trg_content_relation_before_insert`;

DROP TRIGGER IF EXISTS `trg_content_relation_before_update`;

DROP TRIGGER IF EXISTS `trg_homepage_before_insert`;

DROP TRIGGER IF EXISTS `trg_homepage_before_update`;

DROP TRIGGER IF EXISTS `trg_user_before_delete`;

-- 兼容旧版结构时，按依赖逆序清理历史表
DROP TABLE IF EXISTS `component_content_ref`;

DROP TABLE IF EXISTS `asset_usage`;

DROP TABLE IF EXISTS `homepage_component`;

DROP TABLE IF EXISTS `homepage_template`;

DROP TABLE IF EXISTS `work_character`;

DROP TABLE IF EXISTS `content_character`;

DROP TABLE IF EXISTS `content_work`;

DROP TABLE IF EXISTS `browse_history`;

DROP TABLE IF EXISTS `favorite_record`;

DROP TABLE IF EXISTS `like_record`;

DROP TABLE IF EXISTS `content_relation`;

DROP TABLE IF EXISTS `content_media`;

DROP TABLE IF EXISTS `tag_relation`;

DROP TABLE IF EXISTS `content_tag`;

DROP TABLE IF EXISTS `follow`;

DROP TABLE IF EXISTS `user_role`;

DROP TABLE IF EXISTS `asset_authorization`;

DROP TABLE IF EXISTS `asset_authorization_request`;

DROP TABLE IF EXISTS `user_asset`;

DROP TABLE IF EXISTS `user_homepage`;

DROP TABLE IF EXISTS `comment`;

DROP TABLE IF EXISTS `media_asset`;

DROP TABLE IF EXISTS `content`;

DROP TABLE IF EXISTS `character`;

DROP TABLE IF EXISTS `work`;

DROP TABLE IF EXISTS `tag`;

DROP TABLE IF EXISTS `role`;

DROP TABLE IF EXISTS `user`;

-- ────────────────────────────────────────────
-- 一、核心实体
-- ────────────────────────────────────────────

DROP TABLE IF EXISTS `user`;

CREATE TABLE `user` (
    `user_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `avatar_url` VARCHAR(512) DEFAULT NULL,
    `bio` TEXT DEFAULT NULL,
    `registration_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `last_login_time` DATETIME DEFAULT NULL,
    `account_status` ENUM(
        'active',
        'suspended',
        'deactivated'
    ) NOT NULL DEFAULT 'active',
    PRIMARY KEY (`user_id`),
    UNIQUE KEY `uk_user_username` (`username`),
    UNIQUE KEY `uk_user_email` (`email`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '系统用户表';

DROP TABLE IF EXISTS `role`;

CREATE TABLE `role` (
    `role_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `role_name` VARCHAR(50) NOT NULL,
    `role_description` VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY (`role_id`),
    UNIQUE KEY `uk_role_name` (`role_name`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '角色表';

DROP TABLE IF EXISTS `tag`;

CREATE TABLE `tag` (
    `tag_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `tag_name` VARCHAR(120) NOT NULL,
    `tag_type` ENUM(
        'general',
        'work',
        'character'
    ) NOT NULL,
    `tag_category` VARCHAR(50) DEFAULT NULL,
    `parent_tag_id` BIGINT UNSIGNED DEFAULT NULL,
    `description` TEXT DEFAULT NULL,
    `work_type` ENUM(
        'anime',
        'game',
        'novel',
        'manga',
        'other'
    ) DEFAULT NULL,
    `created_by` BIGINT UNSIGNED DEFAULT NULL,
    `tag_status` ENUM('active', 'merged', 'deleted') NOT NULL DEFAULT 'active',
    `merged_into_tag_id` BIGINT UNSIGNED DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `parent_tag_key` BIGINT UNSIGNED NOT NULL DEFAULT 0,
    PRIMARY KEY (`tag_id`),
    UNIQUE KEY `uk_tag_name_type_parent` (
        `tag_name`,
        `tag_type`,
        `parent_tag_key`
    ),
    KEY `idx_tag_status_type` (`tag_status`, `tag_type`),
    KEY `idx_tag_created_by` (`created_by`),
    KEY `idx_tag_parent` (`parent_tag_id`),
    KEY `idx_tag_merged_into` (`merged_into_tag_id`),
    CONSTRAINT `fk_tag_parent` FOREIGN KEY (`parent_tag_id`) REFERENCES `tag` (`tag_id`) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT `fk_tag_created_by` FOREIGN KEY (`created_by`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT `fk_tag_merged_into` FOREIGN KEY (`merged_into_tag_id`) REFERENCES `tag` (`tag_id`) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT `chk_tag_work_type_scope` CHECK (
        `tag_type` = 'work'
        OR `work_type` IS NULL
    )
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '统一标签实体，承载 general/work/character 三类词条';

DROP TABLE IF EXISTS `content`;

CREATE TABLE `content` (
    `content_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `author_id` BIGINT UNSIGNED NOT NULL,
    `title` VARCHAR(300) NOT NULL,
    `body` LONGTEXT DEFAULT NULL,
    `content_type` ENUM(
        'text',
        'image_post',
        'video_post',
        'mixed'
    ) NOT NULL DEFAULT 'text',
    `content_status` ENUM(
        'draft',
        'published',
        'archived',
        'deleted'
    ) NOT NULL DEFAULT 'draft',
    `visibility` ENUM(
        'public',
        'followers_only',
        'private'
    ) NOT NULL DEFAULT 'public',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `view_count` INT UNSIGNED NOT NULL DEFAULT 0,
    `like_count` INT UNSIGNED NOT NULL DEFAULT 0,
    `comment_count` INT UNSIGNED NOT NULL DEFAULT 0,
    PRIMARY KEY (`content_id`),
    KEY `idx_content_status_visibility_time` (
        `content_status`,
        `visibility`,
        `created_at` DESC
    ),
    KEY `idx_content_author_status_time` (
        `author_id`,
        `content_status`,
        `created_at` DESC
    ),
    CONSTRAINT `fk_content_author` FOREIGN KEY (`author_id`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `chk_content_counts_non_negative` CHECK (
        `view_count` >= 0
        AND `like_count` >= 0
        AND `comment_count` >= 0
    )
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '社区内容主表';

DROP TABLE IF EXISTS `media_asset`;

CREATE TABLE `media_asset` (
    `media_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `uploader_id` BIGINT UNSIGNED NOT NULL,
    `media_type` ENUM(
        'image',
        'audio',
        'video',
        'gif'
    ) NOT NULL,
    `file_path` VARCHAR(512) NOT NULL,
    `file_size` BIGINT UNSIGNED DEFAULT NULL,
    `mime_type` VARCHAR(100) DEFAULT NULL,
    `width` INT UNSIGNED DEFAULT NULL,
    `height` INT UNSIGNED DEFAULT NULL,
    `duration` INT UNSIGNED DEFAULT NULL,
    `upload_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`media_id`),
    KEY `idx_media_uploader` (`uploader_id`),
    CONSTRAINT `fk_media_uploader` FOREIGN KEY (`uploader_id`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '内容媒体附件元数据';

DROP TABLE IF EXISTS `comment`;

CREATE TABLE `comment` (
    `comment_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `content_id` BIGINT UNSIGNED NOT NULL,
    `author_id` BIGINT UNSIGNED NOT NULL,
    `parent_comment_id` BIGINT UNSIGNED DEFAULT NULL,
    `comment_text` TEXT NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `comment_status` ENUM(
        'visible',
        'hidden',
        'deleted'
    ) NOT NULL DEFAULT 'visible',
    PRIMARY KEY (`comment_id`),
    KEY `idx_comment_content_time` (
        `content_id`,
        `created_at` ASC
    ),
    KEY `idx_comment_author` (`author_id`),
    KEY `idx_comment_parent` (`parent_comment_id`),
    CONSTRAINT `fk_comment_content` FOREIGN KEY (`content_id`) REFERENCES `content` (`content_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_comment_author` FOREIGN KEY (`author_id`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_comment_parent` FOREIGN KEY (`parent_comment_id`) REFERENCES `comment` (`comment_id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '评论表，支持两层回复';

DROP TABLE IF EXISTS `user_homepage`;

CREATE TABLE `user_homepage` (
    `homepage_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `homepage_config` JSON DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`homepage_id`),
    UNIQUE KEY `uk_homepage_user` (`user_id`),
    CONSTRAINT `fk_homepage_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `chk_homepage_has_layout` CHECK (
        JSON_CONTAINS_PATH(
            `homepage_config`,
            'one',
            '$.layout'
        )
    )
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户主页 JSON 配置';

DROP TABLE IF EXISTS `user_asset`;

CREATE TABLE `user_asset` (
    `asset_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `owner_id` BIGINT UNSIGNED NOT NULL,
    `asset_type` ENUM(
        'background',
        'border',
        'sticker',
        'icon',
        'other'
    ) NOT NULL DEFAULT 'other',
    `asset_name` VARCHAR(200) DEFAULT NULL,
    `file_path` VARCHAR(512) NOT NULL,
    `file_size` BIGINT UNSIGNED DEFAULT NULL,
    `mime_type` VARCHAR(100) DEFAULT NULL,
    `upload_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `asset_status` ENUM(
        'active',
        'disabled',
        'deleted'
    ) NOT NULL DEFAULT 'active',
    `default_visibility` ENUM('private', 'authorized_only') NOT NULL DEFAULT 'private',
    PRIMARY KEY (`asset_id`),
    KEY `idx_asset_owner` (`owner_id`),
    KEY `idx_asset_owner_status` (`owner_id`, `asset_status`),
    CONSTRAINT `fk_asset_owner` FOREIGN KEY (`owner_id`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户私有主页资源';

DROP TABLE IF EXISTS `asset_authorization_request`;

CREATE TABLE `asset_authorization_request` (
    `request_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `asset_id` BIGINT UNSIGNED NOT NULL,
    `requester_id` BIGINT UNSIGNED NOT NULL,
    `request_message` TEXT DEFAULT NULL,
    `request_status` ENUM(
        'pending',
        'approved',
        'rejected',
        'cancelled'
    ) NOT NULL DEFAULT 'pending',
    `requested_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `resolved_at` DATETIME DEFAULT NULL,
    `resolved_by` BIGINT UNSIGNED DEFAULT NULL,
    `pending_key` TINYINT AS (
        CASE
            WHEN `request_status` = 'pending' THEN 1
            ELSE NULL
        END
    ) STORED,
    PRIMARY KEY (`request_id`),
    UNIQUE KEY `uk_authreq_pending` (
        `asset_id`,
        `requester_id`,
        `pending_key`
    ),
    KEY `idx_authreq_asset` (`asset_id`),
    KEY `idx_authreq_requester` (`requester_id`),
    KEY `idx_authreq_resolved_by` (`resolved_by`),
    CONSTRAINT `fk_authreq_asset` FOREIGN KEY (`asset_id`) REFERENCES `user_asset` (`asset_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_authreq_requester` FOREIGN KEY (`requester_id`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_authreq_resolved_by` FOREIGN KEY (`resolved_by`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '资源授权申请';

DROP TABLE IF EXISTS `asset_authorization`;

CREATE TABLE `asset_authorization` (
    `authorization_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `request_id` BIGINT UNSIGNED NOT NULL,
    `asset_id` BIGINT UNSIGNED NOT NULL,
    `grantee_id` BIGINT UNSIGNED NOT NULL,
    `granted_by` BIGINT UNSIGNED NOT NULL,
    `valid_from` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `valid_until` DATETIME DEFAULT NULL,
    `authorization_status` ENUM(
        'active',
        'revoked',
        'expired'
    ) NOT NULL DEFAULT 'active',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`authorization_id`),
    UNIQUE KEY `uk_authorization_request` (`request_id`),
    KEY `idx_auth_asset` (`asset_id`),
    KEY `idx_auth_grantee_status` (
        `grantee_id`,
        `authorization_status`
    ),
    KEY `idx_auth_granted_by_status` (
        `granted_by`,
        `authorization_status`
    ),
    KEY `idx_auth_valid_until` (`valid_until`),
    CONSTRAINT `fk_auth_request` FOREIGN KEY (`request_id`) REFERENCES `asset_authorization_request` (`request_id`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_auth_asset` FOREIGN KEY (`asset_id`) REFERENCES `user_asset` (`asset_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_auth_grantee` FOREIGN KEY (`grantee_id`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_auth_granted_by` FOREIGN KEY (`granted_by`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `chk_auth_valid_range` CHECK (
        `valid_until` IS NULL
        OR `valid_until` >= `valid_from`
    )
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '已生效的资源授权';

-- ────────────────────────────────────────────
-- 二、联系实体 / 中间表
-- ────────────────────────────────────────────

DROP TABLE IF EXISTS `user_role`;

CREATE TABLE `user_role` (
    `user_id` BIGINT UNSIGNED NOT NULL,
    `role_id` BIGINT UNSIGNED NOT NULL,
    `assigned_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`user_id`, `role_id`),
    KEY `idx_userrole_role` (`role_id`),
    CONSTRAINT `fk_userrole_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_userrole_role` FOREIGN KEY (`role_id`) REFERENCES `role` (`role_id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户角色关联';

DROP TABLE IF EXISTS `follow`;

CREATE TABLE `follow` (
    `follower_id` BIGINT UNSIGNED NOT NULL,
    `following_id` BIGINT UNSIGNED NOT NULL,
    `followed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`follower_id`, `following_id`),
    KEY `idx_follow_following` (`following_id`),
    CONSTRAINT `fk_follow_follower` FOREIGN KEY (`follower_id`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_follow_following` FOREIGN KEY (`following_id`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '关注关系';

DROP TABLE IF EXISTS `content_tag`;

CREATE TABLE `content_tag` (
    `content_id` BIGINT UNSIGNED NOT NULL,
    `tag_id` BIGINT UNSIGNED NOT NULL,
    `tagged_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `tagged_by` BIGINT UNSIGNED DEFAULT NULL,
    PRIMARY KEY (`content_id`, `tag_id`),
    KEY `idx_contenttag_tag_content` (`tag_id`, `content_id`),
    KEY `idx_contenttag_tagged_by` (`tagged_by`),
    CONSTRAINT `fk_contenttag_content` FOREIGN KEY (`content_id`) REFERENCES `content` (`content_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_contenttag_tag` FOREIGN KEY (`tag_id`) REFERENCES `tag` (`tag_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_contenttag_tagged_by` FOREIGN KEY (`tagged_by`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '内容与统一标签的唯一关联桥梁';

DROP TABLE IF EXISTS `tag_relation`;

CREATE TABLE `tag_relation` (
    `source_tag_id` BIGINT UNSIGNED NOT NULL,
    `target_tag_id` BIGINT UNSIGNED NOT NULL,
    `relation_type` ENUM('work_contains_character') NOT NULL,
    `role_in_relation` ENUM(
        'protagonist',
        'supporting',
        'minor'
    ) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (
        `source_tag_id`,
        `target_tag_id`,
        `relation_type`
    ),
    KEY `idx_tagrel_target_type_source` (
        `target_tag_id`,
        `relation_type`,
        `source_tag_id`
    ),
    CONSTRAINT `fk_tagrel_source` FOREIGN KEY (`source_tag_id`) REFERENCES `tag` (`tag_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_tagrel_target` FOREIGN KEY (`target_tag_id`) REFERENCES `tag` (`tag_id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '标签间语义关系';

DROP TABLE IF EXISTS `content_media`;

CREATE TABLE `content_media` (
    `content_id` BIGINT UNSIGNED NOT NULL,
    `media_id` BIGINT UNSIGNED NOT NULL,
    `display_order` INT NOT NULL DEFAULT 0,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`content_id`, `media_id`),
    KEY `idx_contentmedia_media` (`media_id`),
    CONSTRAINT `fk_contentmedia_content` FOREIGN KEY (`content_id`) REFERENCES `content` (`content_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_contentmedia_media` FOREIGN KEY (`media_id`) REFERENCES `media_asset` (`media_id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '内容媒体关联';

DROP TABLE IF EXISTS `content_relation`;

CREATE TABLE `content_relation` (
    `source_content_id` BIGINT UNSIGNED NOT NULL,
    `target_content_id` BIGINT UNSIGNED NOT NULL,
    `relation_type` ENUM(
        'sequel',
        'translation',
        'reference',
        'derivative',
        'inspiration'
    ) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `created_by` BIGINT UNSIGNED DEFAULT NULL,
    PRIMARY KEY (
        `source_content_id`,
        `target_content_id`,
        `relation_type`
    ),
    KEY `idx_contentrel_target_type` (
        `target_content_id`,
        `relation_type`
    ),
    KEY `idx_contentrel_created_by` (`created_by`),
    CONSTRAINT `fk_contentrel_source` FOREIGN KEY (`source_content_id`) REFERENCES `content` (`content_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_contentrel_target` FOREIGN KEY (`target_content_id`) REFERENCES `content` (`content_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_contentrel_created_by` FOREIGN KEY (`created_by`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '内容间语义关系';

DROP TABLE IF EXISTS `like_record`;

CREATE TABLE `like_record` (
    `user_id` BIGINT UNSIGNED NOT NULL,
    `content_id` BIGINT UNSIGNED NOT NULL,
    `liked_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`user_id`, `content_id`),
    KEY `idx_like_content` (`content_id`),
    CONSTRAINT `fk_like_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_like_content` FOREIGN KEY (`content_id`) REFERENCES `content` (`content_id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '点赞记录';

DROP TABLE IF EXISTS `favorite_record`;

CREATE TABLE `favorite_record` (
    `user_id` BIGINT UNSIGNED NOT NULL,
    `content_id` BIGINT UNSIGNED NOT NULL,
    `favorited_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`user_id`, `content_id`),
    KEY `idx_favorite_content` (`content_id`),
    CONSTRAINT `fk_favorite_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_favorite_content` FOREIGN KEY (`content_id`) REFERENCES `content` (`content_id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '收藏记录';

DROP TABLE IF EXISTS `browse_history`;

CREATE TABLE `browse_history` (
    `history_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `content_id` BIGINT UNSIGNED NOT NULL,
    `browse_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `duration_seconds` INT UNSIGNED DEFAULT NULL,
    PRIMARY KEY (`history_id`),
    KEY `idx_browse_user_time` (`user_id`, `browse_time` DESC),
    KEY `idx_browse_content_time` (
        `content_id`,
        `browse_time` DESC
    ),
    CONSTRAINT `fk_browse_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_browse_content` FOREIGN KEY (`content_id`) REFERENCES `content` (`content_id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '浏览历史';

-- ────────────────────────────────────────────
-- 三、触发器
-- ────────────────────────────────────────────

DELIMITER $$

CREATE TRIGGER `trg_tag_before_insert`
BEFORE INSERT ON `tag`
FOR EACH ROW
BEGIN
    SET NEW.`parent_tag_key` = IFNULL(NEW.`parent_tag_id`, 0);

    IF NEW.`tag_id` IS NOT NULL AND NEW.`parent_tag_id` = NEW.`tag_id` THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tag.parent_tag_id cannot reference itself';
    END IF;

    IF NEW.`tag_id` IS NOT NULL AND NEW.`merged_into_tag_id` = NEW.`tag_id` THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tag.merged_into_tag_id cannot reference itself';
    END IF;

    IF (NEW.`tag_status` = 'merged' AND NEW.`merged_into_tag_id` IS NULL)
       OR (NEW.`tag_status` <> 'merged' AND NEW.`merged_into_tag_id` IS NOT NULL) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'merged tags must point to a target tag and only merged tags may do so';
    END IF;
END$$

CREATE TRIGGER `trg_tag_before_update`
BEFORE UPDATE ON `tag`
FOR EACH ROW
BEGIN
    SET NEW.`parent_tag_key` = IFNULL(NEW.`parent_tag_id`, 0);

    IF NEW.`parent_tag_id` = NEW.`tag_id` THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tag.parent_tag_id cannot reference itself';
    END IF;

    IF NEW.`merged_into_tag_id` = NEW.`tag_id` THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tag.merged_into_tag_id cannot reference itself';
    END IF;

    IF (NEW.`tag_status` = 'merged' AND NEW.`merged_into_tag_id` IS NULL)
       OR (NEW.`tag_status` <> 'merged' AND NEW.`merged_into_tag_id` IS NOT NULL) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'merged tags must point to a target tag and only merged tags may do so';
    END IF;
END$$

CREATE TRIGGER `trg_comment_before_insert`
BEFORE INSERT ON `comment`
FOR EACH ROW
BEGIN
    IF NEW.`comment_id` IS NOT NULL AND NEW.`parent_comment_id` = NEW.`comment_id` THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'comment.parent_comment_id cannot reference itself';
    END IF;
END$$

CREATE TRIGGER `trg_comment_before_update`
BEFORE UPDATE ON `comment`
FOR EACH ROW
BEGIN
    IF NEW.`parent_comment_id` = NEW.`comment_id` THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'comment.parent_comment_id cannot reference itself';
    END IF;
END$$

CREATE TRIGGER `trg_follow_before_insert`
BEFORE INSERT ON `follow`
FOR EACH ROW
BEGIN
    IF NEW.`follower_id` = NEW.`following_id` THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'users cannot follow themselves';
    END IF;
END$$

CREATE TRIGGER `trg_follow_before_update`
BEFORE UPDATE ON `follow`
FOR EACH ROW
BEGIN
    IF NEW.`follower_id` = NEW.`following_id` THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'users cannot follow themselves';
    END IF;
END$$

CREATE TRIGGER `trg_tag_relation_before_insert`
BEFORE INSERT ON `tag_relation`
FOR EACH ROW
BEGIN
    IF NEW.`source_tag_id` = NEW.`target_tag_id` THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tag_relation source and target must differ';
    END IF;
END$$

CREATE TRIGGER `trg_tag_relation_before_update`
BEFORE UPDATE ON `tag_relation`
FOR EACH ROW
BEGIN
    IF NEW.`source_tag_id` = NEW.`target_tag_id` THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'tag_relation source and target must differ';
    END IF;
END$$

CREATE TRIGGER `trg_content_relation_before_insert`
BEFORE INSERT ON `content_relation`
FOR EACH ROW
BEGIN
    IF NEW.`source_content_id` = NEW.`target_content_id` THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'content_relation source and target must differ';
    END IF;
END$$

CREATE TRIGGER `trg_content_relation_before_update`
BEFORE UPDATE ON `content_relation`
FOR EACH ROW
BEGIN
    IF NEW.`source_content_id` = NEW.`target_content_id` THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'content_relation source and target must differ';
    END IF;
END$$

CREATE TRIGGER `trg_homepage_before_insert`
BEFORE INSERT ON `user_homepage`
FOR EACH ROW
BEGIN
    IF NEW.`homepage_config` IS NULL THEN
        SET NEW.`homepage_config` = JSON_OBJECT('layout', JSON_ARRAY());
    END IF;

    IF NOT JSON_CONTAINS_PATH(NEW.`homepage_config`, 'one', '$.layout') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'homepage_config must contain $.layout';
    END IF;
END$$

CREATE TRIGGER `trg_homepage_before_update`
BEFORE UPDATE ON `user_homepage`
FOR EACH ROW
BEGIN
    IF NEW.`homepage_config` IS NULL THEN
        SET NEW.`homepage_config` = JSON_OBJECT('layout', JSON_ARRAY());
    END IF;

    IF NOT JSON_CONTAINS_PATH(NEW.`homepage_config`, 'one', '$.layout') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'homepage_config must contain $.layout';
    END IF;
END$$

CREATE TRIGGER `trg_like_insert`
AFTER INSERT ON `like_record`
FOR EACH ROW
BEGIN
    UPDATE `content`
       SET `like_count` = `like_count` + 1
     WHERE `content_id` = NEW.`content_id`;
END$$

CREATE TRIGGER `trg_like_delete`
AFTER DELETE ON `like_record`
FOR EACH ROW
BEGIN
    UPDATE `content`
       SET `like_count` = GREATEST(`like_count` - 1, 0)
     WHERE `content_id` = OLD.`content_id`;
END$$

CREATE TRIGGER `trg_like_update`
AFTER UPDATE ON `like_record`
FOR EACH ROW
BEGIN
    IF OLD.`content_id` <> NEW.`content_id` THEN
        UPDATE `content`
           SET `like_count` = GREATEST(`like_count` - 1, 0)
         WHERE `content_id` = OLD.`content_id`;

        UPDATE `content`
           SET `like_count` = `like_count` + 1
         WHERE `content_id` = NEW.`content_id`;
    END IF;
END$$

CREATE TRIGGER `trg_comment_insert`
AFTER INSERT ON `comment`
FOR EACH ROW
BEGIN
    IF NEW.`comment_status` = 'visible' THEN
        UPDATE `content`
           SET `comment_count` = `comment_count` + 1
         WHERE `content_id` = NEW.`content_id`;
    END IF;
END$$

CREATE TRIGGER `trg_comment_delete`
AFTER DELETE ON `comment`
FOR EACH ROW
BEGIN
    IF OLD.`comment_status` = 'visible' THEN
        UPDATE `content`
           SET `comment_count` = GREATEST(`comment_count` - 1, 0)
         WHERE `content_id` = OLD.`content_id`;
    END IF;
END$$

CREATE TRIGGER `trg_comment_update`
AFTER UPDATE ON `comment`
FOR EACH ROW
BEGIN
    IF OLD.`content_id` <> NEW.`content_id` THEN
        IF OLD.`comment_status` = 'visible' THEN
            UPDATE `content`
               SET `comment_count` = GREATEST(`comment_count` - 1, 0)
             WHERE `content_id` = OLD.`content_id`;
        END IF;

        IF NEW.`comment_status` = 'visible' THEN
            UPDATE `content`
               SET `comment_count` = `comment_count` + 1
             WHERE `content_id` = NEW.`content_id`;
        END IF;
    ELSEIF OLD.`comment_status` = 'visible' AND NEW.`comment_status` <> 'visible' THEN
        UPDATE `content`
           SET `comment_count` = GREATEST(`comment_count` - 1, 0)
         WHERE `content_id` = NEW.`content_id`;
    ELSEIF OLD.`comment_status` <> 'visible' AND NEW.`comment_status` = 'visible' THEN
        UPDATE `content`
           SET `comment_count` = `comment_count` + 1
         WHERE `content_id` = NEW.`content_id`;
    END IF;
END$$

CREATE TRIGGER `trg_browse_insert`
AFTER INSERT ON `browse_history`
FOR EACH ROW
BEGIN
    UPDATE `content`
       SET `view_count` = `view_count` + 1
     WHERE `content_id` = NEW.`content_id`;
END$$

CREATE TRIGGER `trg_user_before_delete`
BEFORE DELETE ON `user`
FOR EACH ROW
BEGIN
    UPDATE `content` c
      JOIN `like_record` lr
        ON lr.`content_id` = c.`content_id`
       AND lr.`user_id` = OLD.`user_id`
       SET c.`like_count` = GREATEST(c.`like_count` - 1, 0);
END$$

DELIMITER ;

SET FOREIGN_KEY_CHECKS = 1;
