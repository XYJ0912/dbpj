-- ============================================================
-- 垂直兴趣社区数据库视图（MySQL 8.0+）
-- 基于《垂直兴趣社区_数据库概念设计_v3.2》整理
-- ============================================================

-- 参数敏感的权限判断不再用静态视图表达。
-- viewer_id 相关查询建议在 DAO / Service 层使用参数化 SQL 处理。

DROP VIEW IF EXISTS `v_pending_asset_request`;
DROP VIEW IF EXISTS `v_public_comment`;
DROP VIEW IF EXISTS `v_user_homepage_component`;
DROP VIEW IF EXISTS `v_user_homepage_raw`;
DROP VIEW IF EXISTS `v_user_follow_stats`;
DROP VIEW IF EXISTS `v_user_profile`;
DROP VIEW IF EXISTS `v_active_tag_relation`;
DROP VIEW IF EXISTS `v_public_content`;
DROP VIEW IF EXISTS `v_published_content`;
DROP VIEW IF EXISTS `v_active_content_tag`;
DROP VIEW IF EXISTS `v_active_tag`;
DROP VIEW IF EXISTS `v_work_character`;
DROP VIEW IF EXISTS `v_content_character`;
DROP VIEW IF EXISTS `v_content_work`;
DROP VIEW IF EXISTS `v_character`;
DROP VIEW IF EXISTS `v_work`;

-- ────────────────────────────────────────────
-- 3.1 基础兼容层
-- ────────────────────────────────────────────

CREATE VIEW `v_work` AS
SELECT
    t.`tag_id`                AS `work_id`,
    t.`tag_name`              AS `work_name`,
    t.`work_type`,
    t.`description`,
    t.`created_by`,
    t.`tag_status`            AS `work_status`,
    t.`merged_into_tag_id`    AS `merged_into_work_id`,
    t.`created_at`
FROM `tag` t
WHERE t.`tag_type` = 'work';

CREATE VIEW `v_character` AS
SELECT
    t.`tag_id`                AS `character_id`,
    t.`tag_name`              AS `character_name`,
    t.`description`,
    t.`created_by`,
    t.`tag_status`            AS `character_status`,
    t.`merged_into_tag_id`    AS `merged_into_character_id`,
    t.`created_at`
FROM `tag` t
WHERE t.`tag_type` = 'character';

CREATE VIEW `v_content_work` AS
SELECT
    ct.`content_id`,
    ct.`tag_id`               AS `work_id`,
    ct.`tagged_at`            AS `created_at`
FROM `content_tag` ct
JOIN `tag` t
  ON t.`tag_id` = ct.`tag_id`
WHERE t.`tag_type` = 'work';

CREATE VIEW `v_content_character` AS
SELECT
    ct.`content_id`,
    ct.`tag_id`               AS `character_id`,
    ct.`tagged_at`            AS `created_at`
FROM `content_tag` ct
JOIN `tag` t
  ON t.`tag_id` = ct.`tag_id`
WHERE t.`tag_type` = 'character';

CREATE VIEW `v_work_character` AS
SELECT
    tr.`source_tag_id`        AS `work_id`,
    tr.`target_tag_id`        AS `character_id`,
    tr.`role_in_relation`     AS `role_in_work`,
    tr.`created_at`
FROM `tag_relation` tr
WHERE tr.`relation_type` = 'work_contains_character';

-- ────────────────────────────────────────────
-- 3.2 规范标签与内容读层
-- ────────────────────────────────────────────

CREATE VIEW `v_active_tag` AS
SELECT
    t.`tag_id`,
    t.`tag_name`,
    t.`tag_type`,
    t.`tag_category`,
    t.`parent_tag_id`,
    t.`description`,
    t.`work_type`,
    t.`created_by`,
    t.`created_at`
FROM `tag` t
WHERE t.`tag_status` = 'active';

CREATE VIEW `v_active_content_tag` AS
SELECT
    ct.`content_id`,
    t.`tag_id`,
    t.`tag_name`,
    t.`tag_type`,
    t.`tag_category`,
    t.`parent_tag_id`,
    t.`description`,
    t.`work_type`,
    ct.`tagged_at`,
    ct.`tagged_by`
FROM `content_tag` ct
JOIN `v_active_tag` t
  ON t.`tag_id` = ct.`tag_id`;

CREATE VIEW `v_published_content` AS
SELECT
    c.`content_id`,
    c.`author_id`,
    c.`title`,
    c.`body`,
    c.`content_type`,
    c.`visibility`,
    c.`created_at`,
    c.`updated_at`,
    c.`view_count`,
    c.`like_count`,
    c.`comment_count`
FROM `content` c
WHERE c.`content_status` = 'published';

CREATE VIEW `v_public_content` AS
SELECT
    *
FROM `v_published_content`
WHERE `visibility` = 'public';

CREATE VIEW `v_active_tag_relation` AS
SELECT
    tr.`source_tag_id`,
    src.`tag_name`            AS `source_tag_name`,
    src.`tag_type`            AS `source_tag_type`,
    tr.`target_tag_id`,
    tgt.`tag_name`            AS `target_tag_name`,
    tgt.`tag_type`            AS `target_tag_type`,
    tr.`relation_type`,
    tr.`role_in_relation`,
    tr.`created_at`
FROM `tag_relation` tr
JOIN `v_active_tag` src
  ON src.`tag_id` = tr.`source_tag_id`
JOIN `v_active_tag` tgt
  ON tgt.`tag_id` = tr.`target_tag_id`;

-- ────────────────────────────────────────────
-- 3.4 用户与运营读层
-- ────────────────────────────────────────────

CREATE VIEW `v_user_profile` AS
SELECT
    u.`user_id`,
    u.`username`,
    u.`avatar_url`,
    u.`bio`,
    u.`registration_time`,
    u.`last_login_time`,
    u.`account_status`,
    h.`homepage_id`,
    h.`updated_at`            AS `homepage_updated_at`
FROM `user` u
LEFT JOIN `user_homepage` h
  ON h.`user_id` = u.`user_id`;

CREATE VIEW `v_user_follow_stats` AS
SELECT
    u.`user_id`,
    u.`username`,
    COALESCE(follower_cnt.`cnt`, 0)  AS `follower_count`,
    COALESCE(following_cnt.`cnt`, 0) AS `following_count`
FROM `user` u
LEFT JOIN (
    SELECT
        f.`following_id` AS `user_id`,
        COUNT(*)         AS `cnt`
    FROM `follow` f
    GROUP BY f.`following_id`
) follower_cnt
  ON follower_cnt.`user_id` = u.`user_id`
LEFT JOIN (
    SELECT
        f.`follower_id`  AS `user_id`,
        COUNT(*)         AS `cnt`
    FROM `follow` f
    GROUP BY f.`follower_id`
) following_cnt
  ON following_cnt.`user_id` = u.`user_id`;

CREATE VIEW `v_user_homepage_raw` AS
SELECT
    h.`homepage_id`,
    h.`user_id`,
    u.`username`,
    h.`homepage_config`,
    JSON_EXTRACT(h.`homepage_config`, '$.template')           AS `template_config`,
    JSON_UNQUOTE(JSON_EXTRACT(h.`homepage_config`, '$.theme')) AS `theme`,
    JSON_UNQUOTE(JSON_EXTRACT(h.`homepage_config`, '$.background_url'))
                                                             AS `background_url`,
    h.`created_at`,
    h.`updated_at`
FROM `user_homepage` h
JOIN `user` u
  ON u.`user_id` = h.`user_id`;

CREATE VIEW `v_user_homepage_component` AS
SELECT
    h.`user_id`,
    h.`homepage_id`,
    jt.`component_id`,
    jt.`component_type`,
    jt.`position`,
    COALESCE(jt.`z_index`, 0)      AS `z_index`,
    jt.`title`,
    jt.`component_config`
FROM `user_homepage` h
CROSS JOIN JSON_TABLE(
        h.`homepage_config`,
        '$.layout[*]'
        COLUMNS (
            `component_id`     VARCHAR(64)  PATH '$.component_id' NULL ON EMPTY,
            `component_type`   VARCHAR(64)  PATH '$.component_type' NULL ON EMPTY,
            `position`         JSON         PATH '$.position' NULL ON EMPTY,
            `z_index`          INT          PATH '$.z_index' NULL ON EMPTY,
            `title`            VARCHAR(255) PATH '$.title' NULL ON EMPTY,
            `component_config` JSON         PATH '$.config' NULL ON EMPTY
        )
     ) jt;

CREATE VIEW `v_public_comment` AS
SELECT
    c.`comment_id`,
    c.`content_id`,
    c.`parent_comment_id`,
    c.`comment_text`,
    c.`created_at`,
    u.`user_id`               AS `author_id`,
    u.`username`              AS `author_name`,
    u.`avatar_url`            AS `author_avatar`
FROM `comment` c
JOIN `v_public_content` pc
  ON pc.`content_id` = c.`content_id`
JOIN `user` u
  ON u.`user_id` = c.`author_id`
WHERE c.`comment_status` = 'visible';

CREATE VIEW `v_pending_asset_request` AS
SELECT
    r.`request_id`,
    r.`asset_id`,
    ua.`asset_name`,
    ua.`owner_id`,
    owner_u.`username`        AS `owner_name`,
    r.`requester_id`,
    requester_u.`username`    AS `requester_name`,
    r.`request_message`,
    r.`requested_at`
FROM `asset_authorization_request` r
JOIN `user_asset` ua
  ON ua.`asset_id` = r.`asset_id`
JOIN `user` owner_u
  ON owner_u.`user_id` = ua.`owner_id`
JOIN `user` requester_u
  ON requester_u.`user_id` = r.`requester_id`
WHERE r.`request_status` = 'pending';
