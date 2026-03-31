-- ============================================================
-- 垂直兴趣社区数据库存储过程（MySQL 8.0+）
-- 基于《垂直兴趣社区_数据库概念设计_v3.2》整理
-- ============================================================
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

DELIMITER $$

DROP EVENT IF EXISTS `ev_expire_authorizations`$$

DROP PROCEDURE IF EXISTS `sp_register_user`$$

CREATE PROCEDURE `sp_register_user`(
    IN  p_username        VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    IN  p_email           VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    IN  p_password_hash   VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    IN  p_avatar_url      VARCHAR(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    IN  p_bio             TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    OUT p_out_user_id     BIGINT UNSIGNED,
    OUT p_out_code        TINYINT,
    OUT p_out_msg         VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
)
proc_body: BEGIN
    DECLARE v_role_id BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_exists  INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_out_user_id = NULL;
        SET p_out_code = 2;
        SET p_out_msg = '系统异常，注册事务已回滚';
    END;

    IF CHAR_LENGTH(TRIM(COALESCE(p_username, ''))) = 0
       OR CHAR_LENGTH(TRIM(COALESCE(p_email, ''))) = 0
       OR CHAR_LENGTH(TRIM(COALESCE(p_password_hash, ''))) = 0 THEN
        SET p_out_user_id = NULL;
        SET p_out_code = 1;
        SET p_out_msg = '用户名、邮箱和密码哈希不能为空';
        LEAVE proc_body;
    END IF;

    SELECT COUNT(*)
      INTO v_exists
      FROM `user`
     WHERE `username` = p_username
        OR `email` = p_email;

    IF v_exists > 0 THEN
        SET p_out_user_id = NULL;
        SET p_out_code = 1;
        SET p_out_msg = '用户名或邮箱已存在';
        LEAVE proc_body;
    END IF;

    START TRANSACTION;

    SELECT `role_id`
      INTO v_role_id
      FROM `role`
     WHERE `role_name` = 'normal_user'
     LIMIT 1
     FOR UPDATE;

    IF v_role_id IS NULL THEN
        ROLLBACK;
        SET p_out_user_id = NULL;
        SET p_out_code = 1;
        SET p_out_msg = '缺少 normal_user 角色，无法完成注册';
        LEAVE proc_body;
    END IF;

    INSERT INTO `user` (
        `username`, `email`, `password_hash`, `avatar_url`, `bio`, `account_status`
    ) VALUES (
        p_username, p_email, p_password_hash, p_avatar_url, p_bio, 'active'
    );

    SET p_out_user_id = LAST_INSERT_ID();

    INSERT INTO `user_role` (`user_id`, `role_id`)
    VALUES (p_out_user_id, v_role_id);

    INSERT INTO `user_homepage` (`user_id`, `homepage_config`)
    VALUES (p_out_user_id, JSON_OBJECT('layout', JSON_ARRAY()));

    COMMIT;

    SET p_out_code = 0;
    SET p_out_msg = '用户注册成功';
END$$

DROP PROCEDURE IF EXISTS `sp_publish_content`$$
CREATE PROCEDURE `sp_publish_content`(
    IN  p_content_id      BIGINT UNSIGNED,
    IN  p_author_id       BIGINT UNSIGNED,
    IN  p_title           VARCHAR(300) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    IN  p_body            LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    IN  p_content_type    VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    IN  p_visibility      VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    IN  p_tag_ids         JSON,
    IN  p_media_ids       JSON,
    OUT p_out_content_id  BIGINT UNSIGNED,
    OUT p_out_code        TINYINT,
    OUT p_out_msg         VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
)
proc_body: BEGIN
    DECLARE v_author_exists      INT DEFAULT 0;
    DECLARE v_invalid_tag_count  INT DEFAULT 0;
    DECLARE v_invalid_media_count INT DEFAULT 0;
    DECLARE v_existing_author    BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_existing_status    VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_out_content_id = NULL;
        SET p_out_code = 2;
        SET p_out_msg = '系统异常，发布事务已回滚';
    END;

    IF CHAR_LENGTH(TRIM(COALESCE(p_title, ''))) = 0 THEN
        SET p_out_content_id = NULL;
        SET p_out_code = 1;
        SET p_out_msg = '标题不能为空';
        LEAVE proc_body;
    END IF;

    SELECT COUNT(*)
      INTO v_author_exists
      FROM `user`
     WHERE `user_id` = p_author_id
       AND `account_status` = 'active';

    IF v_author_exists = 0 THEN
        SET p_out_content_id = NULL;
        SET p_out_code = 1;
        SET p_out_msg = '作者不存在或账户不可发布内容';
        LEAVE proc_body;
    END IF;

    IF p_tag_ids IS NOT NULL AND JSON_LENGTH(p_tag_ids) > 0 THEN
        SELECT COUNT(*)
          INTO v_invalid_tag_count
          FROM (
                SELECT DISTINCT jt.`tag_id`
                FROM JSON_TABLE(
                    p_tag_ids,
                    '$[*]' COLUMNS (
                        `tag_id` BIGINT UNSIGNED PATH '$'
                    )
                ) jt
               ) parsed
          LEFT JOIN `tag` t
            ON t.`tag_id` = parsed.`tag_id`
         WHERE t.`tag_id` IS NULL
            OR t.`tag_status` <> 'active';
    END IF;

    IF v_invalid_tag_count > 0 THEN
        SET p_out_content_id = NULL;
        SET p_out_code = 1;
        SET p_out_msg = '存在无效或非 active 状态的 tag_id';
        LEAVE proc_body;
    END IF;

    IF p_media_ids IS NOT NULL AND JSON_LENGTH(p_media_ids) > 0 THEN
        SELECT COUNT(*)
          INTO v_invalid_media_count
          FROM (
                SELECT DISTINCT jt.`media_id`
                FROM JSON_TABLE(
                    p_media_ids,
                    '$[*]' COLUMNS (
                        `media_id` BIGINT UNSIGNED PATH '$'
                    )
                ) jt
               ) parsed
          LEFT JOIN `media_asset` m
            ON m.`media_id` = parsed.`media_id`
         WHERE m.`media_id` IS NULL;
    END IF;

    IF v_invalid_media_count > 0 THEN
        SET p_out_content_id = NULL;
        SET p_out_code = 1;
        SET p_out_msg = '存在无效的 media_id';
        LEAVE proc_body;
    END IF;

    START TRANSACTION;

    IF p_content_id IS NULL OR p_content_id = 0 THEN
        INSERT INTO `content` (
            `author_id`, `title`, `body`, `content_type`, `content_status`, `visibility`
        ) VALUES (
            p_author_id, p_title, p_body, p_content_type, 'published', p_visibility
        );

        SET p_out_content_id = LAST_INSERT_ID();
    ELSE
        SELECT `author_id`, `content_status`
          INTO v_existing_author, v_existing_status
          FROM `content`
         WHERE `content_id` = p_content_id
         LIMIT 1
         FOR UPDATE;

        IF v_existing_author IS NULL THEN
            ROLLBACK;
            SET p_out_content_id = NULL;
            SET p_out_code = 1;
            SET p_out_msg = '指定的 content_id 不存在';
            LEAVE proc_body;
        END IF;

        IF v_existing_author <> p_author_id THEN
            ROLLBACK;
            SET p_out_content_id = NULL;
            SET p_out_code = 1;
            SET p_out_msg = '只能发布自己的草稿内容';
            LEAVE proc_body;
        END IF;

        IF v_existing_status <> 'draft' THEN
            ROLLBACK;
            SET p_out_content_id = NULL;
            SET p_out_code = 1;
            SET p_out_msg = '只有 draft 内容允许通过该过程发布';
            LEAVE proc_body;
        END IF;

        UPDATE `content`
           SET `title` = p_title,
               `body` = p_body,
               `content_type` = p_content_type,
               `visibility` = p_visibility,
               `content_status` = 'published'
         WHERE `content_id` = p_content_id;

        DELETE FROM `content_tag`
         WHERE `content_id` = p_content_id;

        DELETE FROM `content_media`
         WHERE `content_id` = p_content_id;

        SET p_out_content_id = p_content_id;
    END IF;

    IF p_tag_ids IS NOT NULL AND JSON_LENGTH(p_tag_ids) > 0 THEN
        INSERT INTO `content_tag` (`content_id`, `tag_id`, `tagged_by`)
        SELECT
            p_out_content_id,
            parsed.`tag_id`,
            p_author_id
        FROM (
            SELECT DISTINCT jt.`tag_id`
            FROM JSON_TABLE(
                p_tag_ids,
                '$[*]' COLUMNS (
                    `tag_id` BIGINT UNSIGNED PATH '$'
                )
            ) jt
        ) parsed;
    END IF;

    IF p_media_ids IS NOT NULL AND JSON_LENGTH(p_media_ids) > 0 THEN
        INSERT INTO `content_media` (`content_id`, `media_id`, `display_order`)
        SELECT
            p_out_content_id,
            jt.`media_id`,
            jt.`ord` - 1
        FROM JSON_TABLE(
            p_media_ids,
            '$[*]' COLUMNS (
                `ord` FOR ORDINALITY,
                `media_id` BIGINT UNSIGNED PATH '$'
            )
        ) jt;
    END IF;

    COMMIT;

    SET p_out_code = 0;
    SET p_out_msg = '内容发布成功';
END$$

DROP PROCEDURE IF EXISTS `sp_delete_or_archive_content`$$
CREATE PROCEDURE `sp_delete_or_archive_content`(
    IN  p_content_id   BIGINT UNSIGNED,
    IN  p_operator_id  BIGINT UNSIGNED,
    IN  p_mode         VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    OUT p_out_code     TINYINT,
    OUT p_out_msg      VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
)
proc_body: BEGIN
    DECLARE v_author_id BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_status    VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    DECLARE v_is_admin  INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_out_code = 2;
        SET p_out_msg = '系统异常，内容状态更新已回滚';
    END;

    START TRANSACTION;

    SELECT `author_id`, `content_status`
      INTO v_author_id, v_status
      FROM `content`
     WHERE `content_id` = p_content_id
     LIMIT 1
     FOR UPDATE;

    IF v_author_id IS NULL THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '内容不存在';
        LEAVE proc_body;
    END IF;

    SELECT COUNT(*)
      INTO v_is_admin
      FROM `user_role` ur
      JOIN `role` r
        ON r.`role_id` = ur.`role_id`
     WHERE ur.`user_id` = p_operator_id
       AND r.`role_name` IN ('admin', 'content_moderator');

    IF p_operator_id <> v_author_id AND v_is_admin = 0 THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '无权操作该内容';
        LEAVE proc_body;
    END IF;

    IF p_mode = 'archive' THEN
        UPDATE `content`
           SET `content_status` = 'archived'
         WHERE `content_id` = p_content_id
           AND `content_status` <> 'deleted';

        COMMIT;
        SET p_out_code = 0;
        SET p_out_msg = '内容已归档';
    ELSEIF p_mode = 'soft_delete' THEN
        UPDATE `content`
           SET `content_status` = 'deleted'
         WHERE `content_id` = p_content_id;

        COMMIT;
        SET p_out_code = 0;
        SET p_out_msg = '内容已软删除';
    ELSE
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '仅支持 archive 或 soft_delete 模式';
    END IF;
END$$

DROP PROCEDURE IF EXISTS `sp_resolve_authorization_request`$$
CREATE PROCEDURE `sp_resolve_authorization_request`(
    IN  p_request_id   BIGINT UNSIGNED,
    IN  p_resolver_id  BIGINT UNSIGNED,
    IN  p_decision     VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    IN  p_valid_until  DATETIME,
    OUT p_out_code     TINYINT,
    OUT p_out_msg      VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
)
proc_body: BEGIN
    DECLARE v_asset_id       BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_requester_id   BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_request_status VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    DECLARE v_owner_id       BIGINT UNSIGNED DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_out_code = 2;
        SET p_out_msg = '系统异常，授权审批已回滚';
    END;

    START TRANSACTION;

    SELECT `asset_id`, `requester_id`, `request_status`
      INTO v_asset_id, v_requester_id, v_request_status
      FROM `asset_authorization_request`
     WHERE `request_id` = p_request_id
     LIMIT 1
     FOR UPDATE;

    IF v_asset_id IS NULL THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '授权申请不存在';
        LEAVE proc_body;
    END IF;

    IF v_request_status <> 'pending' THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '只有 pending 状态的申请可以审批';
        LEAVE proc_body;
    END IF;

    SELECT `owner_id`
      INTO v_owner_id
      FROM `user_asset`
     WHERE `asset_id` = v_asset_id
     LIMIT 1
     FOR UPDATE;

    IF v_owner_id IS NULL THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '资源不存在';
        LEAVE proc_body;
    END IF;

    IF v_owner_id <> p_resolver_id THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '只有资源所有者可以审批该申请';
        LEAVE proc_body;
    END IF;

    IF p_decision = 'approved' THEN
        IF p_valid_until IS NOT NULL AND p_valid_until < NOW() THEN
            ROLLBACK;
            SET p_out_code = 1;
            SET p_out_msg = 'valid_until 不能早于当前时间';
            LEAVE proc_body;
        END IF;

        UPDATE `asset_authorization_request`
           SET `request_status` = 'approved',
               `resolved_at` = NOW(),
               `resolved_by` = p_resolver_id
         WHERE `request_id` = p_request_id;

        INSERT INTO `asset_authorization` (
            `request_id`, `asset_id`, `grantee_id`, `granted_by`,
            `valid_from`, `valid_until`, `authorization_status`
        ) VALUES (
            p_request_id, v_asset_id, v_requester_id, p_resolver_id,
            NOW(), p_valid_until, 'active'
        );

        COMMIT;
        SET p_out_code = 0;
        SET p_out_msg = '授权申请已批准';
    ELSEIF p_decision = 'rejected' THEN
        UPDATE `asset_authorization_request`
           SET `request_status` = 'rejected',
               `resolved_at` = NOW(),
               `resolved_by` = p_resolver_id
         WHERE `request_id` = p_request_id;

        COMMIT;
        SET p_out_code = 0;
        SET p_out_msg = '授权申请已拒绝';
    ELSE
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = 'decision 仅支持 approved 或 rejected';
    END IF;
END$$

DROP PROCEDURE IF EXISTS `sp_revoke_authorization`$$
CREATE PROCEDURE `sp_revoke_authorization`(
    IN  p_authorization_id BIGINT UNSIGNED,
    IN  p_operator_id      BIGINT UNSIGNED,
    OUT p_out_code         TINYINT,
    OUT p_out_msg          VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
)
proc_body: BEGIN
    DECLARE v_granted_by BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_status     VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    DECLARE v_is_admin   INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_out_code = 2;
        SET p_out_msg = '系统异常，授权撤销已回滚';
    END;

    START TRANSACTION;

    SELECT `granted_by`, `authorization_status`
      INTO v_granted_by, v_status
      FROM `asset_authorization`
     WHERE `authorization_id` = p_authorization_id
     LIMIT 1
     FOR UPDATE;

    IF v_granted_by IS NULL THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '授权记录不存在';
        LEAVE proc_body;
    END IF;

    SELECT COUNT(*)
      INTO v_is_admin
      FROM `user_role` ur
      JOIN `role` r
        ON r.`role_id` = ur.`role_id`
     WHERE ur.`user_id` = p_operator_id
       AND r.`role_name` IN ('admin', 'content_moderator');

    IF p_operator_id <> v_granted_by AND v_is_admin = 0 THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '无权撤销该授权';
        LEAVE proc_body;
    END IF;

    IF v_status <> 'active' THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '只有 active 授权可以撤销';
        LEAVE proc_body;
    END IF;

    UPDATE `asset_authorization`
       SET `authorization_status` = 'revoked'
     WHERE `authorization_id` = p_authorization_id;

    COMMIT;

    SET p_out_code = 0;
    SET p_out_msg = '授权已撤销';
END$$

DROP PROCEDURE IF EXISTS `sp_save_homepage_config`$$
CREATE PROCEDURE `sp_save_homepage_config`(
    IN  p_user_id                 BIGINT UNSIGNED,
    IN  p_homepage_config         JSON,
    IN  p_last_read_updated_at    DATETIME,
    OUT p_out_code                TINYINT,
    OUT p_out_msg                 VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
)
proc_body: BEGIN
    DECLARE v_homepage_id BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_updated_at  DATETIME DEFAULT NULL;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_out_code = 2;
        SET p_out_msg = '系统异常，主页保存已回滚';
    END;

    IF JSON_CONTAINS_PATH(p_homepage_config, 'one', '$.layout') = 0 THEN
        SET p_out_code = 1;
        SET p_out_msg = 'homepage_config 必须包含 layout 字段';
        LEAVE proc_body;
    END IF;

    START TRANSACTION;

    SELECT `homepage_id`, `updated_at`
      INTO v_homepage_id, v_updated_at
      FROM `user_homepage`
     WHERE `user_id` = p_user_id
     LIMIT 1
     FOR UPDATE;

    IF v_homepage_id IS NULL THEN
        INSERT INTO `user_homepage` (`user_id`, `homepage_config`)
        VALUES (p_user_id, p_homepage_config);

        COMMIT;
        SET p_out_code = 0;
        SET p_out_msg = '主页配置已创建';
        LEAVE proc_body;
    END IF;

    IF p_last_read_updated_at IS NOT NULL
       AND v_updated_at <> p_last_read_updated_at THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '主页配置已被他人更新，请刷新后重试';
        LEAVE proc_body;
    END IF;

    UPDATE `user_homepage`
       SET `homepage_config` = p_homepage_config
     WHERE `homepage_id` = v_homepage_id;

    COMMIT;

    SET p_out_code = 0;
    SET p_out_msg = '主页配置已保存';
END$$

DROP PROCEDURE IF EXISTS `sp_deactivate_user`$$
CREATE PROCEDURE `sp_deactivate_user`(
    IN  p_user_id        BIGINT UNSIGNED,
    IN  p_target_status  VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    IN  p_operator_id    BIGINT UNSIGNED,
    OUT p_out_code       TINYINT,
    OUT p_out_msg        VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
)
proc_body: BEGIN
    DECLARE v_current_status VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    DECLARE v_is_admin       INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_out_code = 2;
        SET p_out_msg = '系统异常，用户状态变更已回滚';
    END;

    IF p_user_id = 1 THEN
        SET p_out_code = 1;
        SET p_out_msg = 'system 账户不允许停用或注销';
        LEAVE proc_body;
    END IF;

    SELECT COUNT(*)
      INTO v_is_admin
      FROM `user_role` ur
      JOIN `role` r
        ON r.`role_id` = ur.`role_id`
     WHERE ur.`user_id` = p_operator_id
       AND r.`role_name` = 'admin';

    IF v_is_admin = 0 THEN
        SET p_out_code = 1;
        SET p_out_msg = '只有 admin 可以执行该操作';
        LEAVE proc_body;
    END IF;

    START TRANSACTION;

    SELECT `account_status`
      INTO v_current_status
      FROM `user`
     WHERE `user_id` = p_user_id
     LIMIT 1
     FOR UPDATE;

    IF v_current_status IS NULL THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '用户不存在';
        LEAVE proc_body;
    END IF;

    IF p_target_status = 'suspended' THEN
        UPDATE `user`
           SET `account_status` = 'suspended'
         WHERE `user_id` = p_user_id;

        COMMIT;
        SET p_out_code = 0;
        SET p_out_msg = '用户已停用';
    ELSEIF p_target_status = 'deactivated' THEN
        UPDATE `user`
           SET `account_status` = 'deactivated'
         WHERE `user_id` = p_user_id;

        UPDATE `content`
           SET `content_status` = 'archived'
         WHERE `author_id` = p_user_id
           AND `content_status` <> 'deleted';

        UPDATE `user_asset`
           SET `asset_status` = 'disabled'
         WHERE `owner_id` = p_user_id
           AND `asset_status` <> 'deleted';

        UPDATE `asset_authorization`
           SET `authorization_status` = 'revoked'
         WHERE `granted_by` = p_user_id
           AND `authorization_status` = 'active';

        COMMIT;
        SET p_out_code = 0;
        SET p_out_msg = '用户已注销并完成关联收敛';
    ELSE
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = 'target_status 仅支持 suspended 或 deactivated';
    END IF;
END$$

DROP PROCEDURE IF EXISTS `sp_merge_tag`$$
CREATE PROCEDURE `sp_merge_tag`(
    IN  p_source_tag_id  BIGINT UNSIGNED,
    IN  p_target_tag_id  BIGINT UNSIGNED,
    IN  p_operator_id    BIGINT UNSIGNED,
    OUT p_out_code       TINYINT,
    OUT p_out_msg        VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
)
proc_body: BEGIN
    DECLARE v_source_type   VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    DECLARE v_source_status VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    DECLARE v_target_type   VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    DECLARE v_target_status VARCHAR(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL;
    DECLARE v_can_operate   INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_out_code = 2;
        SET p_out_msg = '系统异常，词条合并已回滚';
    END;

    IF p_source_tag_id = p_target_tag_id THEN
        SET p_out_code = 1;
        SET p_out_msg = '源词条与目标词条不能相同';
        LEAVE proc_body;
    END IF;

    SELECT COUNT(*)
      INTO v_can_operate
      FROM `user_role` ur
      JOIN `role` r
        ON r.`role_id` = ur.`role_id`
     WHERE ur.`user_id` = p_operator_id
       AND r.`role_name` IN ('admin', 'content_moderator');

    IF v_can_operate = 0 THEN
        SET p_out_code = 1;
        SET p_out_msg = '只有 admin 或 content_moderator 可以合并词条';
        LEAVE proc_body;
    END IF;

    START TRANSACTION;

    SELECT `tag_type`, `tag_status`
      INTO v_source_type, v_source_status
      FROM `tag`
     WHERE `tag_id` = p_source_tag_id
     LIMIT 1
     FOR UPDATE;

    SELECT `tag_type`, `tag_status`
      INTO v_target_type, v_target_status
      FROM `tag`
     WHERE `tag_id` = p_target_tag_id
     LIMIT 1
     FOR UPDATE;

    IF v_source_type IS NULL OR v_target_type IS NULL THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '源词条或目标词条不存在';
        LEAVE proc_body;
    END IF;

    IF v_source_status <> 'active' OR v_target_status <> 'active' THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '仅允许将 active 词条合并到 active 词条';
        LEAVE proc_body;
    END IF;

    IF v_source_type <> v_target_type THEN
        ROLLBACK;
        SET p_out_code = 1;
        SET p_out_msg = '源词条与目标词条的 tag_type 必须一致';
        LEAVE proc_body;
    END IF;

    INSERT IGNORE INTO `content_tag` (`content_id`, `tag_id`, `tagged_at`, `tagged_by`)
    SELECT
        ct.`content_id`,
        p_target_tag_id,
        ct.`tagged_at`,
        ct.`tagged_by`
    FROM `content_tag` ct
    WHERE ct.`tag_id` = p_source_tag_id;

    DELETE FROM `content_tag`
     WHERE `tag_id` = p_source_tag_id;

    INSERT IGNORE INTO `tag_relation` (
        `source_tag_id`, `target_tag_id`, `relation_type`, `role_in_relation`, `created_at`
    )
    SELECT
        p_target_tag_id,
        tr.`target_tag_id`,
        tr.`relation_type`,
        tr.`role_in_relation`,
        tr.`created_at`
    FROM `tag_relation` tr
    WHERE tr.`source_tag_id` = p_source_tag_id
      AND tr.`target_tag_id` <> p_target_tag_id;

    INSERT IGNORE INTO `tag_relation` (
        `source_tag_id`, `target_tag_id`, `relation_type`, `role_in_relation`, `created_at`
    )
    SELECT
        tr.`source_tag_id`,
        p_target_tag_id,
        tr.`relation_type`,
        tr.`role_in_relation`,
        tr.`created_at`
    FROM `tag_relation` tr
    WHERE tr.`target_tag_id` = p_source_tag_id
      AND tr.`source_tag_id` <> p_target_tag_id;

    DELETE FROM `tag_relation`
     WHERE `source_tag_id` = p_source_tag_id
        OR `target_tag_id` = p_source_tag_id;

    UPDATE `tag`
       SET `merged_into_tag_id` = p_target_tag_id
     WHERE `merged_into_tag_id` = p_source_tag_id;

    UPDATE `tag`
       SET `tag_status` = 'merged',
           `merged_into_tag_id` = p_target_tag_id
     WHERE `tag_id` = p_source_tag_id;

    COMMIT;

    SET p_out_code = 0;
    SET p_out_msg = '词条已合并';
END$$

DROP PROCEDURE IF EXISTS `sp_expire_authorizations`$$
CREATE PROCEDURE `sp_expire_authorizations`()
BEGIN
    UPDATE `asset_authorization`
       SET `authorization_status` = 'expired'
     WHERE `authorization_status` = 'active'
       AND `valid_until` IS NOT NULL
       AND `valid_until` < NOW();
END$$

CREATE EVENT `ev_expire_authorizations`
    ON SCHEDULE EVERY 1 HOUR
    DO
BEGIN
    CALL `sp_expire_authorizations`();
END$$

DELIMITER ;
