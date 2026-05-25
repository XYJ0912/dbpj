-- ============================================================
-- 垂直兴趣社区数据库 Demo（MySQL 8.0+）
-- 执行顺序：
--   1. vertical_community_schema.sql
--   2. vertical_community_procedures.sql
--   3. vertical_community_views.sql
--   4. vertical_community_seed_data.sql
--   5. 本文件
-- ============================================================

-- ────────────────────────────────────────────
-- Demo 1：视图查询
-- ────────────────────────────────────────────

SELECT '>>> Demo 1.1: v_work 兼容视图' AS `demo`;
SELECT `work_id`, `work_name`, `work_type`, `work_status`
FROM `v_work`
ORDER BY `work_id`
LIMIT 5;

SELECT '>>> Demo 1.2: 某作品下的公开内容流（规范读层组合）' AS `demo`;
SELECT
    act.`tag_name` AS `work_name`,
    pc.`content_id`,
    pc.`title`,
    pc.`author_id`,
    pc.`created_at`,
    pc.`like_count`
FROM `v_active_content_tag` act
JOIN `v_public_content` pc
  ON pc.`content_id` = act.`content_id`
WHERE act.`tag_id` = 108
ORDER BY pc.`created_at` DESC;

SELECT '>>> Demo 1.3: 某内容关联的全部活跃标签' AS `demo`;
SELECT
    pc.`content_id`,
    pc.`title`,
    act.`tag_type`,
    act.`tag_name`,
    act.`tagged_at`
FROM `v_published_content` pc
JOIN `v_active_content_tag` act
  ON act.`content_id` = pc.`content_id`
WHERE pc.`content_id` = 1
ORDER BY act.`tag_type`, act.`tag_name`;

SELECT '>>> Demo 1.4: 某作品包含哪些角色' AS `demo`;
SELECT
    `source_tag_name` AS `work_name`,
    `target_tag_name` AS `character_name`,
    `role_in_relation`
FROM `v_active_tag_relation`
WHERE `relation_type` = 'work_contains_character'
  AND `source_tag_id` = 108
ORDER BY `target_tag_name`;

SELECT '>>> Demo 1.5: 用户资料与关注统计' AS `demo`;
SELECT
    p.`user_id`,
    p.`username`,
    p.`account_status`,
    s.`follower_count`,
    s.`following_count`,
    p.`homepage_updated_at`
FROM `v_user_profile` p
JOIN `v_user_follow_stats` s
  ON s.`user_id` = p.`user_id`
WHERE p.`user_id` = 2;

SELECT '>>> Demo 1.6: 主页组件展开视图' AS `demo`;
SELECT
    `user_id`,
    `component_id`,
    `component_type`,
    `title`,
    `z_index`
FROM `v_user_homepage_component`
WHERE `user_id` = 2
ORDER BY `z_index`, `component_id`;

SELECT '>>> Demo 1.7: 公共评论视图' AS `demo`;
SELECT
    `content_id`,
    `author_name`,
    `comment_text`,
    `created_at`
FROM `v_public_comment`
WHERE `content_id` = 1
ORDER BY `created_at`;

SELECT '>>> Demo 1.8: 待处理资源授权申请' AS `demo`;
SELECT
    `request_id`,
    `asset_name`,
    `owner_name`,
    `requester_name`,
    `requested_at`
FROM `v_pending_asset_request`
ORDER BY `requested_at`;

-- ────────────────────────────────────────────
-- Demo 2：存储过程
-- ────────────────────────────────────────────

SELECT '>>> Demo 2.1: 注册用户' AS `demo`;
SET @new_user_id = NULL;
SET @out_code = NULL;
SET @out_msg = NULL;
CALL `sp_register_user`(
    'demo_new_user',
    'demo_new_user@example.com',
    '$2b$12$placeholder_hash_demo_new_user',
    '/avatars/demo_new.jpg',
    '通过 demo 创建的新用户。',
    @new_user_id, @out_code, @out_msg
);
SELECT @new_user_id AS `new_user_id`, @out_code AS `code`, @out_msg AS `msg`;

SELECT '>>> Demo 2.2: 发布新内容（统一 tag 桥表）' AS `demo`;
SET @new_content_id = NULL;
SET @out_code = NULL;
SET @out_msg = NULL;
CALL `sp_publish_content`(
    NULL,
    2,
    '【新帖】咒术回战最终章观后感',
    '最终章看完后，最强烈的感受还是角色成长节奏终于闭环。',
    'text',
    'public',
    JSON_ARRAY(15, 19, 25, 107, 210),
    NULL,
    @new_content_id, @out_code, @out_msg
);
SELECT @new_content_id AS `new_content_id`, @out_code AS `code`, @out_msg AS `msg`;

SELECT `content_id`, `title`, `content_status`, `visibility`
FROM `content`
WHERE `content_id` = @new_content_id;

SELECT t.`tag_type`, t.`tag_name`
FROM `content_tag` ct
JOIN `tag` t
  ON t.`tag_id` = ct.`tag_id`
WHERE ct.`content_id` = @new_content_id
ORDER BY t.`tag_type`, t.`tag_name`;

SELECT '>>> Demo 2.3: 归档内容' AS `demo`;
SET @out_code = NULL;
SET @out_msg = NULL;
CALL `sp_delete_or_archive_content`(3, 2, 'archive', @out_code, @out_msg);
SELECT @out_code AS `code`, @out_msg AS `msg`;
SELECT `content_id`, `title`, `content_status`
FROM `content`
WHERE `content_id` = 3;

SELECT '>>> Demo 2.4: 审批资源授权申请' AS `demo`;
SET @out_code = NULL;
SET @out_msg = NULL;
CALL `sp_resolve_authorization_request`(2, 5, 'approved', '2025-12-31 23:59:59', @out_code, @out_msg);
SELECT @out_code AS `code`, @out_msg AS `msg`;
SELECT `request_id`, `request_status`, `resolved_by`
FROM `asset_authorization_request`
WHERE `request_id` = 2;
SELECT `authorization_id`, `asset_id`, `grantee_id`, `authorization_status`
FROM `asset_authorization`
WHERE `request_id` = 2;

SELECT '>>> Demo 2.5: 撤销授权' AS `demo`;
SET @out_code = NULL;
SET @out_msg = NULL;
CALL `sp_revoke_authorization`(2, 3, @out_code, @out_msg);
SELECT @out_code AS `code`, @out_msg AS `msg`;
SELECT `authorization_id`, `authorization_status`
FROM `asset_authorization`
WHERE `authorization_id` = 2;

SELECT '>>> Demo 2.6: 保存主页 JSON 配置' AS `demo`;
SET @old_updated_at = (SELECT `updated_at` FROM `user_homepage` WHERE `user_id` = 4);
SET @out_code = NULL;
SET @out_msg = NULL;
CALL `sp_save_homepage_config`(
    4,
    JSON_OBJECT(
        'template', JSON_OBJECT('name', 'reading_room', 'slot_count', 3),
        'theme', 'paper',
        'background_url', '/assets/bg/novel_v2.jpg',
        'layout', JSON_ARRAY(
            JSON_OBJECT(
                'component_id', 'r1',
                'component_type', 'recent_content',
                'position', JSON_OBJECT('x', 0, 'y', 0, 'w', 12, 'h', 4),
                'z_index', 1,
                'title', '更新后的书单',
                'config', JSON_OBJECT('content_ids', JSON_ARRAY(7, 8), 'limit', 2)
            )
        )
    ),
    @old_updated_at,
    @out_code, @out_msg
);
SELECT @out_code AS `code`, @out_msg AS `msg`;
SELECT `component_id`, `component_type`, `title`
FROM `v_user_homepage_component`
WHERE `user_id` = 4;

SELECT '>>> Demo 2.7: 停用 / 注销用户' AS `demo`;
SET @out_code = NULL;
SET @out_msg = NULL;
CALL `sp_deactivate_user`(8, 'deactivated', 1, @out_code, @out_msg);
SELECT @out_code AS `code`, @out_msg AS `msg`;
SELECT `user_id`, `username`, `account_status`
FROM `user`
WHERE `user_id` = 8;

SELECT '>>> Demo 2.8: 合并词条' AS `demo`;
INSERT INTO `tag`
    (`tag_id`, `tag_name`, `tag_type`, `description`, `work_type`, `created_by`, `tag_status`, `created_at`)
VALUES
    (110, '巨人进击', 'work', '临时重复词条，用于 demo 合并。', 'anime', 7, 'active', NOW());

INSERT INTO `content_tag` (`content_id`, `tag_id`, `tagged_by`)
VALUES (1, 110, 7);

SET @out_code = NULL;
SET @out_msg = NULL;
CALL `sp_merge_tag`(110, 101, 7, @out_code, @out_msg);
SELECT @out_code AS `code`, @out_msg AS `msg`;
SELECT `tag_id`, `tag_name`, `tag_status`, `merged_into_tag_id`
FROM `tag`
WHERE `tag_id` = 110;

SELECT t.`tag_name`
FROM `content_tag` ct
JOIN `tag` t
  ON t.`tag_id` = ct.`tag_id`
WHERE ct.`content_id` = 1
  AND t.`tag_type` = 'work';

SELECT '>>> Demo 2.9: 过期授权清理' AS `demo`;
CALL `sp_expire_authorizations`();
SELECT `authorization_id`, `authorization_status`, `valid_until`
FROM `asset_authorization`
ORDER BY `authorization_id`;

-- ────────────────────────────────────────────
-- Demo 3：触发器验证
-- ────────────────────────────────────────────

SELECT '>>> Demo 3.1: 点赞计数触发器' AS `demo`;
SELECT `like_count` AS `before_like` FROM `content` WHERE `content_id` = 2;
INSERT INTO `like_record` (`user_id`, `content_id`, `liked_at`) VALUES (5, 2, NOW());
SELECT `like_count` AS `after_like` FROM `content` WHERE `content_id` = 2;
DELETE FROM `like_record` WHERE `user_id` = 5 AND `content_id` = 2;
SELECT `like_count` AS `after_unlike` FROM `content` WHERE `content_id` = 2;

SELECT '>>> Demo 3.2: 评论计数触发器' AS `demo`;
SELECT `comment_count` AS `before_comment` FROM `content` WHERE `content_id` = 2;
INSERT INTO `comment` (`content_id`, `author_id`, `parent_comment_id`, `comment_text`, `comment_status`)
VALUES (2, 3, NULL, '临时评论，用于验证 comment_count。', 'visible');
SET @tmp_comment_id = LAST_INSERT_ID();
SELECT `comment_count` AS `after_insert` FROM `content` WHERE `content_id` = 2;
UPDATE `comment` SET `comment_status` = 'hidden' WHERE `comment_id` = @tmp_comment_id;
SELECT `comment_count` AS `after_hide` FROM `content` WHERE `content_id` = 2;
DELETE FROM `comment` WHERE `comment_id` = @tmp_comment_id;
SELECT `comment_count` AS `after_delete` FROM `content` WHERE `content_id` = 2;

SELECT '>>> Demo 3.3: 浏览计数触发器' AS `demo`;
SELECT `view_count` AS `before_browse` FROM `content` WHERE `content_id` = 2;
INSERT INTO `browse_history` (`user_id`, `content_id`, `browse_time`, `duration_seconds`)
VALUES (6, 2, NOW(), 33);
SELECT `view_count` AS `after_browse` FROM `content` WHERE `content_id` = 2;
