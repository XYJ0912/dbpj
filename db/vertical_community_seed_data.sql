-- ============================================================
-- 垂直兴趣社区数据库种子数据（MySQL 8.0+）
-- 基于《垂直兴趣社区_数据库概念设计_v3.2》整理
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ────────────────────────────────────────────
-- 1. User / Role / User_Role
-- ────────────────────────────────────────────

INSERT INTO `user`
    (`user_id`, `username`, `email`, `password_hash`, `avatar_url`, `bio`,
     `registration_time`, `last_login_time`, `account_status`)
VALUES
    (1, 'system', 'system@vertical.community',
     '$2b$12$placeholder_hash_system_account',
     '/avatars/system.png',
     '系统账户，用于初始化与社区维护。',
     '2025-01-01 00:00:00', '2025-03-20 00:00:00', 'active'),
    (2, 'sakura_fan', 'sakura@example.com',
     '$2b$12$placeholder_hash_sakura_fan_00',
     '/avatars/sakura.jpg',
     '资深动漫爱好者，最爱魔法少女和剧情考据。',
     '2025-01-01 08:00:00', '2025-03-20 14:30:00', 'active'),
    (3, 'pixel_knight', 'pixel@example.com',
     '$2b$12$placeholder_hash_pixel_knight',
     '/avatars/pixel.jpg',
     '独立游戏开发者，顺手画像素图。',
     '2025-01-02 10:00:00', '2025-03-21 09:00:00', 'active'),
    (4, 'novel_reader', 'novel@example.com',
     '$2b$12$placeholder_hash_novel_reader',
     '/avatars/novel.jpg',
     '轻小说重度用户，偏爱长线世界观。',
     '2025-01-03 12:00:00', '2025-03-19 22:00:00', 'active'),
    (5, 'art_muse', 'artmuse@example.com',
     '$2b$12$placeholder_hash_art_muse_00',
     '/avatars/artmuse.jpg',
     '同人画师，主要做水彩和构图研究。',
     '2025-01-05 09:00:00', '2025-03-22 11:00:00', 'active'),
    (6, 'cosplay_queen', 'cosplay@example.com',
     '$2b$12$placeholder_hash_cosplay_que',
     '/avatars/cosplay.jpg',
     'Coser & 摄影，喜欢做全套装备。',
     '2025-01-06 15:00:00', '2025-03-18 20:00:00', 'active'),
    (7, 'moderator_lin', 'moderator@example.com',
     '$2b$12$placeholder_hash_moderator_0',
     '/avatars/moderator.jpg',
     '社区词条管理员。',
     '2025-01-04 09:30:00', '2025-03-22 09:00:00', 'active'),
    (8, 'shadow_banned', 'shadow@example.com',
     '$2b$12$placeholder_hash_shadow_banne',
     '/avatars/shadow.jpg',
     '这个用户目前处于停用状态。',
     '2025-01-10 10:00:00', '2025-02-15 10:00:00', 'suspended'),
    (9, 'gone_user', 'gone@example.com',
     '$2b$12$placeholder_hash_gone_user_00',
     NULL,
     NULL,
     '2025-01-12 10:00:00', '2025-02-01 10:00:00', 'deactivated');

INSERT INTO `role` (`role_id`, `role_name`, `role_description`)
VALUES
    (1, 'normal_user', '普通注册用户'),
    (2, 'content_moderator', '内容与词条审核管理员'),
    (3, 'admin', '系统管理员');

INSERT INTO `user_role` (`user_id`, `role_id`, `assigned_at`)
VALUES
    (1, 3, '2025-01-01 00:00:00'),
    (2, 1, '2025-01-01 08:00:00'),
    (3, 1, '2025-01-02 10:00:00'),
    (4, 1, '2025-01-03 12:00:00'),
    (5, 1, '2025-01-05 09:00:00'),
    (6, 1, '2025-01-06 15:00:00'),
    (7, 2, '2025-01-04 09:30:00'),
    (8, 1, '2025-01-10 10:00:00'),
    (9, 1, '2025-01-12 10:00:00');

-- ────────────────────────────────────────────
-- 2. Tag / Tag_Relation
-- ────────────────────────────────────────────

INSERT INTO `tag`
    (`tag_id`, `tag_name`, `tag_type`, `tag_category`, `parent_tag_id`,
     `description`, `work_type`, `created_by`, `tag_status`, `merged_into_tag_id`, `created_at`)
VALUES
    (10, '动漫', 'general', '总类', NULL, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (11, '游戏', 'general', '总类', NULL, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (12, '创作', 'general', '总类', NULL, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (13, '同人创作', 'general', '创作形式', 12, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (14, '原创', 'general', '创作形式', 12, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (15, '热血', 'general', '风格', 10, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (16, '治愈', 'general', '风格', 10, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (17, '考据', 'general', '内容形式', NULL, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (18, '攻略', 'general', '内容形式', NULL, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (19, '角色分析', 'general', '内容形式', NULL, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (20, 'Cosplay', 'general', '创作形式', 12, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (21, '像素画', 'general', '创作形式', 12, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (22, '水彩', 'general', '创作形式', 12, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (23, '轻小说', 'general', '题材', NULL, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (24, '新番推荐', 'general', '内容形式', NULL, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (25, '剧情讨论', 'general', '内容形式', NULL, NULL, NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (26, '旅行冒险', 'general', '题材', NULL, NULL, NULL, 3, 'active', NULL, '2025-01-08 09:00:00'),

    (101, '进击的巨人', 'work', NULL, NULL, '人类与巨人的生存战争史诗。', 'anime', 1, 'active', NULL, '2025-01-01 00:00:00'),
    (102, '原神', 'work', NULL, NULL, '开放世界冒险 RPG。', 'game', 1, 'active', NULL, '2025-01-01 00:00:00'),
    (103, '刀剑神域', 'work', NULL, NULL, '虚拟现实 MMORPG 轻小说。', 'novel', 1, 'active', NULL, '2025-01-01 00:00:00'),
    (104, '鬼灭之刃', 'work', NULL, NULL, '大正时代人与鬼的战斗故事。', 'manga', 1, 'active', NULL, '2025-01-01 00:00:00'),
    (105, '间谍过家家', 'work', NULL, NULL, '假家庭喜剧。', 'anime', 1, 'active', NULL, '2025-01-01 00:00:00'),
    (106, '塞尔达传说：王国之泪', 'work', NULL, NULL, '海拉鲁天空与地底的冒险。', 'game', 1, 'active', NULL, '2025-01-01 00:00:00'),
    (107, '咒术回战', 'work', NULL, NULL, '现代暗黑咒术战斗作品。', 'anime', 1, 'active', NULL, '2025-01-01 00:00:00'),
    (108, '葬送的芙莉莲', 'work', NULL, NULL, '精灵魔法使的漫长旅途。', 'anime', 1, 'active', NULL, '2025-01-01 00:00:00'),
    (109, '进巨', 'work', NULL, NULL, '旧别名词条，已合并。', 'anime', 7, 'merged', 101, '2025-01-09 10:00:00'),

    (201, '艾伦·耶格尔', 'character', NULL, NULL, '进击的巨人男主角。', NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (202, '三笠·阿克曼', 'character', NULL, NULL, '进击的巨人女主角。', NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (203, '荧', 'character', NULL, NULL, '原神旅行者。', NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (204, '钟离', 'character', NULL, NULL, '原神岩神角色。', NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (205, '桐人', 'character', NULL, NULL, '刀剑神域主角。', NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (206, '灶门炭治郎', 'character', NULL, NULL, '鬼灭之刃主角。', NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (207, '灶门祢豆子', 'character', NULL, NULL, '鬼灭之刃核心角色。', NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (208, '阿尼亚·福杰', 'character', NULL, NULL, '间谍过家家超能力少女。', NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (209, '林克', 'character', NULL, NULL, '塞尔达传说主角。', NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (210, '虎杖悠仁', 'character', NULL, NULL, '咒术回战主角。', NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (211, '芙莉莲', 'character', NULL, NULL, '葬送的芙莉莲主角。', NULL, 1, 'active', NULL, '2025-01-01 00:00:00'),
    (212, '费伦', 'character', NULL, NULL, '芙莉莲的弟子。', NULL, 1, 'active', NULL, '2025-01-01 00:00:00');

INSERT INTO `tag_relation`
    (`source_tag_id`, `target_tag_id`, `relation_type`, `role_in_relation`, `created_at`)
VALUES
    (101, 201, 'work_contains_character', 'protagonist', '2025-01-01 00:00:00'),
    (101, 202, 'work_contains_character', 'supporting',  '2025-01-01 00:00:00'),
    (102, 203, 'work_contains_character', 'protagonist', '2025-01-01 00:00:00'),
    (102, 204, 'work_contains_character', 'supporting',  '2025-01-01 00:00:00'),
    (103, 205, 'work_contains_character', 'protagonist', '2025-01-01 00:00:00'),
    (104, 206, 'work_contains_character', 'protagonist', '2025-01-01 00:00:00'),
    (104, 207, 'work_contains_character', 'supporting',  '2025-01-01 00:00:00'),
    (105, 208, 'work_contains_character', 'protagonist', '2025-01-01 00:00:00'),
    (106, 209, 'work_contains_character', 'protagonist', '2025-01-01 00:00:00'),
    (107, 210, 'work_contains_character', 'protagonist', '2025-01-01 00:00:00'),
    (108, 211, 'work_contains_character', 'protagonist', '2025-01-01 00:00:00'),
    (108, 212, 'work_contains_character', 'supporting',  '2025-01-01 00:00:00');

-- ────────────────────────────────────────────
-- 3. Content / Media / Comment
-- ────────────────────────────────────────────

INSERT INTO `content`
    (`content_id`, `author_id`, `title`, `body`, `content_type`, `content_status`, `visibility`, `created_at`)
VALUES
    (1, 2, '【考据】进击的巨人结局深度解析',
     '从第一集到最终话，我重看了整部作品，整理出主要伏笔与时间线。',
     'text', 'published', 'public', '2025-01-15 10:00:00'),
    (2, 2, '芙莉莲与费伦的师徒情感分析',
     '这部作品最打动我的，是长寿种族与短寿种族之间的理解迟滞。',
     'text', 'published', 'public', '2025-02-01 14:00:00'),
    (3, 2, '我的 2025 冬季新番推荐清单',
     '本季有几部值得追的新番，我先给出一个偏故事向的推荐列表。',
     'text', 'published', 'public', '2025-01-20 18:00:00'),
    (4, 3, '【像素画】原神角色全套像素化',
     '花了两周，把原神一期角色全部画成了 32x32 像素版本。',
     'image_post', 'published', 'public', '2025-01-25 09:00:00'),
    (5, 3, '塞尔达王国之泪全神庙攻略',
     '152 个神庙逐个标注，附地图与简短路线说明。',
     'mixed', 'published', 'public', '2025-02-10 12:00:00'),
    (6, 3, '独立游戏开发日记 #1',
     '分享一下我正在开发的 Roguelike 游戏第一周进展。',
     'text', 'published', 'followers_only', '2025-02-20 20:00:00'),
    (7, 4, '【书评】刀剑神域新篇阶段性评价',
     '读完最新卷后，想聊聊桐人的成长和新篇节奏。',
     'text', 'published', 'public', '2025-02-05 16:00:00'),
    (8, 4, '2025 轻小说年度推荐 TOP 10',
     '从这一季度看下来，最稳定的还是长篇世界观构筑型作品。',
     'text', 'published', 'public', '2025-03-01 10:00:00'),
    (9, 5, '【水彩】鬼灭之刃：炭治郎与祢豆子',
     '用了八小时完成这张水彩，想测试暖色调和空气感。',
     'image_post', 'published', 'public', '2025-02-14 11:00:00'),
    (10, 5, '【同人插画】间谍过家家：阿尼亚的四季',
     '画了四张阿尼亚在不同季节的插画，准备做一个合集。',
     'image_post', 'published', 'public', '2025-02-28 15:00:00'),
    (11, 5, '绘画过程视频：芙莉莲肖像',
     '从线稿到铺色的完整录屏，顺便测试了新的镜头角度。',
     'video_post', 'published', 'public', '2025-03-10 09:00:00'),
    (12, 6, '【Cosplay】三笠全套立体机动装置还原',
     '历时三个月做完的道具组，终于拍到了满意的一组照片。',
     'image_post', 'published', 'public', '2025-03-05 13:00:00'),
    (13, 6, '原神钟离 Cosplay 拍摄手记',
     '在园林场景取景，主要聊服装修整和后期色调。',
     'mixed', 'published', 'public', '2025-03-15 17:00:00'),
    (14, 2, '【草稿】咒术回战角色实力排名',
     '还在整理中，先存一版草稿。',
     'text', 'draft', 'public', '2025-03-18 20:00:00'),
    (15, 8, '被停用前的最后一篇帖子',
     '这是 shadow_banned 在停用前留下的帖子。',
     'text', 'archived', 'public', '2025-02-10 10:00:00');

INSERT INTO `media_asset`
    (`media_id`, `uploader_id`, `media_type`, `file_path`, `file_size`,
     `mime_type`, `width`, `height`, `duration`, `upload_time`)
VALUES
    (1, 3, 'image', '/media/pixel_genshin_01.png', 245760, 'image/png', 1024, 1024, NULL, '2025-01-25 08:50:00'),
    (2, 3, 'image', '/media/pixel_genshin_02.png', 230400, 'image/png', 1024, 1024, NULL, '2025-01-25 08:55:00'),
    (3, 3, 'image', '/media/zelda_shrine_map.jpg', 5242880, 'image/jpeg', 3840, 2160, NULL, '2025-02-10 11:50:00'),
    (4, 5, 'image', '/media/watercolor_tanjiro.jpg', 3145728, 'image/jpeg', 2480, 3508, NULL, '2025-02-14 10:30:00'),
    (5, 5, 'image', '/media/anya_spring.jpg', 2097152, 'image/jpeg', 2000, 2000, NULL, '2025-02-28 14:00:00'),
    (6, 5, 'image', '/media/anya_summer.jpg', 2150400, 'image/jpeg', 2000, 2000, NULL, '2025-02-28 14:10:00'),
    (7, 5, 'image', '/media/anya_autumn.jpg', 2201600, 'image/jpeg', 2000, 2000, NULL, '2025-02-28 14:20:00'),
    (8, 5, 'image', '/media/anya_winter.jpg', 2252800, 'image/jpeg', 2000, 2000, NULL, '2025-02-28 14:30:00'),
    (9, 5, 'video', '/media/frieren_painting_process.mp4', 157286400, 'video/mp4', 1920, 1080, 720, '2025-03-10 08:30:00'),
    (10, 6, 'image', '/media/mikasa_cosplay_01.jpg', 4194304, 'image/jpeg', 3000, 4000, NULL, '2025-03-05 12:30:00'),
    (11, 6, 'image', '/media/zhongli_cosplay_01.jpg', 3145728, 'image/jpeg', 2800, 3800, NULL, '2025-03-15 16:10:00');

INSERT INTO `comment`
    (`comment_id`, `content_id`, `author_id`, `parent_comment_id`, `comment_text`, `created_at`, `comment_status`)
VALUES
    (1, 1, 3, NULL, '这篇考据把时间线梳理得很清楚。', '2025-01-15 11:00:00', 'visible'),
    (2, 1, 2, 1, '我补了两次才敢发，怕漏掉细节。', '2025-01-15 11:20:00', 'visible'),
    (3, 2, 4, NULL, '这篇把师徒关系说透了。', '2025-02-01 15:00:00', 'visible'),
    (4, 4, 5, NULL, '像素色板很舒服，尤其是金色部分。', '2025-01-25 10:30:00', 'visible'),
    (5, 5, 2, NULL, '地图标记真的救命。', '2025-02-10 13:00:00', 'visible'),
    (6, 5, 3, 5, '后面我会再补一个地底路线版。', '2025-02-10 13:10:00', 'visible'),
    (7, 9, 6, NULL, '祢豆子的肤色过渡做得真细。', '2025-02-14 12:30:00', 'visible'),
    (8, 10, 2, NULL, '阿尼亚四季那张冬季版最有氛围。', '2025-02-28 16:00:00', 'visible'),
    (9, 11, 7, NULL, '这个镜头角度确实更适合录过程。', '2025-03-10 10:00:00', 'visible'),
    (10, 13, 5, NULL, '取景很适合钟离。', '2025-03-15 18:00:00', 'hidden');

-- ────────────────────────────────────────────
-- 4. User_Homepage / User_Asset / Authorization
-- ────────────────────────────────────────────

INSERT INTO `user_homepage`
    (`homepage_id`, `user_id`, `homepage_config`, `created_at`, `updated_at`)
VALUES
    (1, 1, '{"layout":[]}', '2025-01-01 00:00:00', '2025-03-20 00:00:00'),
    (2, 2, '{"template":{"name":"default_two_column","slot_count":6},"theme":"amber","background_url":"/assets/bg/sakura.jpg","layout":[{"component_id":"c1","component_type":"work_showcase","position":{"x":0,"y":0,"w":6,"h":4},"z_index":1,"title":"最近在看","config":{"tag_ids":[101,108],"display_mode":"carousel"}},{"component_id":"c2","component_type":"recent_content","position":{"x":6,"y":0,"w":6,"h":3},"z_index":2,"title":"最新发帖","config":{"content_ids":[1,2,3],"limit":3}}]}', '2025-01-01 08:00:00', '2025-03-20 14:00:00'),
    (3, 3, '{"template":{"name":"grid_mix","slot_count":4},"theme":"forest","background_url":"/assets/bg/pixel.jpg","layout":[{"component_id":"c1","component_type":"gallery","position":{"x":0,"y":0,"w":8,"h":4},"z_index":1,"title":"像素实验","config":{"content_ids":[4,5],"columns":2}},{"component_id":"c2","component_type":"work_showcase","position":{"x":8,"y":0,"w":4,"h":4},"z_index":2,"title":"游戏偏好","config":{"tag_ids":[102,106],"display_mode":"stack"}}]}', '2025-01-02 10:00:00', '2025-03-21 09:00:00'),
    (4, 4, '{"template":{"name":"reading_room","slot_count":3},"theme":"paper","background_url":"/assets/bg/novel.jpg","layout":[{"component_id":"c1","component_type":"recent_content","position":{"x":0,"y":0,"w":12,"h":4},"z_index":1,"title":"书单更新","config":{"content_ids":[7,8],"limit":5}}]}', '2025-01-03 12:00:00', '2025-03-19 22:00:00'),
    (5, 5, '{"template":{"name":"studio","slot_count":4},"theme":"wine","background_url":"/assets/bg/art.jpg","layout":[{"component_id":"c1","component_type":"work_showcase","position":{"x":0,"y":0,"w":6,"h":4},"z_index":1,"title":"绘画对象","config":{"tag_ids":[104,108],"display_mode":"carousel"}},{"component_id":"c2","component_type":"recent_content","position":{"x":6,"y":0,"w":6,"h":4},"z_index":2,"title":"作品集","config":{"content_ids":[9,10,11],"limit":3}}]}', '2025-01-05 09:00:00', '2025-03-22 11:00:00'),
    (6, 6, '{"template":{"name":"stage","slot_count":4},"theme":"midnight","background_url":"/assets/bg/cosplay.jpg","layout":[{"component_id":"c1","component_type":"recent_content","position":{"x":0,"y":0,"w":12,"h":4},"z_index":1,"title":"最新返图","config":{"content_ids":[12,13],"limit":2}}]}', '2025-01-06 15:00:00', '2025-03-18 20:00:00'),
    (7, 7, '{"template":{"name":"ops","slot_count":2},"theme":"slate","background_url":"/assets/bg/moderator.jpg","layout":[{"component_id":"c1","component_type":"tag_watchlist","position":{"x":0,"y":0,"w":12,"h":3},"z_index":1,"title":"重点词条","config":{"tag_ids":[109,107],"limit":2}}]}', '2025-01-04 09:30:00', '2025-03-22 09:00:00'),
    (8, 8, '{"layout":[]}', '2025-01-10 10:00:00', '2025-02-15 10:00:00'),
    (9, 9, '{"layout":[]}', '2025-01-12 10:00:00', '2025-02-01 10:00:00');

INSERT INTO `user_asset`
    (`asset_id`, `owner_id`, `asset_type`, `asset_name`, `file_path`, `file_size`,
     `mime_type`, `upload_time`, `asset_status`, `default_visibility`)
VALUES
    (1, 5, 'background', '酒红画室背景', '/assets/user/5/studio-bg.png', 512000, 'image/png', '2025-02-01 10:00:00', 'active', 'authorized_only'),
    (2, 5, 'border', '金边相框', '/assets/user/5/golden-frame.png', 210000, 'image/png', '2025-02-05 12:00:00', 'active', 'authorized_only'),
    (3, 6, 'sticker', '调查兵团徽章', '/assets/user/6/scout-badge.png', 120000, 'image/png', '2025-02-18 09:00:00', 'active', 'authorized_only'),
    (4, 6, 'background', '岩王帝君石庭背景', '/assets/user/6/geo-garden.jpg', 860000, 'image/jpeg', '2025-03-12 18:00:00', 'active', 'authorized_only'),
    (5, 3, 'icon', '像素猫头像框', '/assets/user/3/pixel-cat.png', 64000, 'image/png', '2025-02-20 19:00:00', 'active', 'authorized_only'),
    (6, 8, 'background', '旧主页背景', '/assets/user/8/legacy-bg.jpg', 400000, 'image/jpeg', '2025-01-20 09:00:00', 'disabled', 'private');

INSERT INTO `asset_authorization_request`
    (`request_id`, `asset_id`, `requester_id`, `request_message`,
     `request_status`, `requested_at`, `resolved_at`, `resolved_by`)
VALUES
    (1, 1, 2, '想把这个背景放到我的作品展示页。', 'approved',  '2025-02-10 09:00:00', '2025-02-10 20:00:00', 5),
    (2, 1, 6, '想试一下这个背景配 Cos 返图。',   'pending',   '2025-03-11 10:00:00', NULL, NULL),
    (3, 2, 4, '读书主页想借这个金边做书封样式。', 'rejected',  '2025-02-15 08:30:00', '2025-02-15 14:00:00', 5),
    (4, 5, 2, '像素猫想拿来做头像角标。',         'approved',  '2025-02-22 20:00:00', '2025-02-22 22:00:00', 3),
    (5, 4, 5, '想在芙莉莲过程页借用这张庭院背景。', 'approved', '2025-03-13 10:00:00', '2025-03-13 12:00:00', 6),
    (6, 3, 2, '想把徽章贴到我的主页卡片上。',     'cancelled', '2025-03-01 09:00:00', '2025-03-01 11:00:00', 6);

INSERT INTO `asset_authorization`
    (`authorization_id`, `request_id`, `asset_id`, `grantee_id`, `granted_by`,
     `valid_from`, `valid_until`, `authorization_status`, `created_at`)
VALUES
    (1, 1, 1, 2, 5, '2025-02-10 20:00:00', '2025-12-31 23:59:59', 'active',  '2025-02-10 20:00:00'),
    (2, 4, 5, 2, 3, '2025-02-22 22:00:00', NULL,                   'active',  '2025-02-22 22:00:00'),
    (3, 5, 4, 5, 6, '2025-03-13 12:00:00', '2025-03-25 23:59:59', 'expired', '2025-03-13 12:00:00');

-- ────────────────────────────────────────────
-- 5. 关联数据
-- ────────────────────────────────────────────

INSERT INTO `follow` (`follower_id`, `following_id`, `followed_at`)
VALUES
    (2, 3, '2025-01-10 09:00:00'),
    (2, 5, '2025-01-12 09:00:00'),
    (2, 6, '2025-01-18 09:00:00'),
    (3, 2, '2025-01-11 10:00:00'),
    (3, 5, '2025-01-20 20:00:00'),
    (4, 2, '2025-01-15 11:00:00'),
    (4, 3, '2025-02-01 21:00:00'),
    (5, 2, '2025-01-20 08:00:00'),
    (5, 6, '2025-02-15 08:00:00'),
    (6, 5, '2025-02-16 09:00:00'),
    (6, 2, '2025-02-20 18:00:00');

INSERT INTO `content_tag` (`content_id`, `tag_id`, `tagged_at`, `tagged_by`)
VALUES
    (1, 17, '2025-01-15 10:00:00', 2), (1, 25, '2025-01-15 10:00:00', 2), (1, 101, '2025-01-15 10:00:00', 2), (1, 201, '2025-01-15 10:00:00', 2), (1, 202, '2025-01-15 10:00:00', 2),
    (2, 19, '2025-02-01 14:00:00', 2), (2, 16, '2025-02-01 14:00:00', 2), (2, 108, '2025-02-01 14:00:00', 2), (2, 211, '2025-02-01 14:00:00', 2), (2, 212, '2025-02-01 14:00:00', 2),
    (3, 24, '2025-01-20 18:00:00', 2), (3, 10, '2025-01-20 18:00:00', 2), (3, 105, '2025-01-20 18:00:00', 2), (3, 107, '2025-01-20 18:00:00', 2), (3, 108, '2025-01-20 18:00:00', 2),
    (4, 13, '2025-01-25 09:00:00', 3), (4, 21, '2025-01-25 09:00:00', 3), (4, 102, '2025-01-25 09:00:00', 3), (4, 203, '2025-01-25 09:00:00', 3), (4, 204, '2025-01-25 09:00:00', 3),
    (5, 18, '2025-02-10 12:00:00', 3), (5, 26, '2025-02-10 12:00:00', 3), (5, 106, '2025-02-10 12:00:00', 3), (5, 209, '2025-02-10 12:00:00', 3),
    (6, 14, '2025-02-20 20:00:00', 3), (6, 11, '2025-02-20 20:00:00', 3), (6, 21, '2025-02-20 20:00:00', 3),
    (7, 23, '2025-02-05 16:00:00', 4), (7, 25, '2025-02-05 16:00:00', 4), (7, 103, '2025-02-05 16:00:00', 4), (7, 205, '2025-02-05 16:00:00', 4),
    (8, 23, '2025-03-01 10:00:00', 4), (8, 24, '2025-03-01 10:00:00', 4), (8, 103, '2025-03-01 10:00:00', 4),
    (9, 13, '2025-02-14 11:00:00', 5), (9, 22, '2025-02-14 11:00:00', 5), (9, 104, '2025-02-14 11:00:00', 5), (9, 206, '2025-02-14 11:00:00', 5), (9, 207, '2025-02-14 11:00:00', 5),
    (10, 13, '2025-02-28 15:00:00', 5), (10, 105, '2025-02-28 15:00:00', 5), (10, 208, '2025-02-28 15:00:00', 5),
    (11, 22, '2025-03-10 09:00:00', 5), (11, 108, '2025-03-10 09:00:00', 5), (11, 211, '2025-03-10 09:00:00', 5),
    (12, 20, '2025-03-05 13:00:00', 6), (12, 101, '2025-03-05 13:00:00', 6), (12, 202, '2025-03-05 13:00:00', 6),
    (13, 20, '2025-03-15 17:00:00', 6), (13, 102, '2025-03-15 17:00:00', 6), (13, 204, '2025-03-15 17:00:00', 6),
    (14, 19, '2025-03-18 20:00:00', 2), (14, 107, '2025-03-18 20:00:00', 2), (14, 210, '2025-03-18 20:00:00', 2),
    (15, 15, '2025-02-10 10:00:00', 8), (15, 107, '2025-02-10 10:00:00', 8), (15, 210, '2025-02-10 10:00:00', 8);

INSERT INTO `content_media` (`content_id`, `media_id`, `display_order`, `created_at`)
VALUES
    (4, 1, 0, '2025-01-25 09:00:00'),
    (4, 2, 1, '2025-01-25 09:00:00'),
    (5, 3, 0, '2025-02-10 12:00:00'),
    (9, 4, 0, '2025-02-14 11:00:00'),
    (10, 5, 0, '2025-02-28 15:00:00'),
    (10, 6, 1, '2025-02-28 15:00:00'),
    (10, 7, 2, '2025-02-28 15:00:00'),
    (10, 8, 3, '2025-02-28 15:00:00'),
    (11, 9, 0, '2025-03-10 09:00:00'),
    (12, 10, 0, '2025-03-05 13:00:00'),
    (13, 11, 0, '2025-03-15 17:00:00');

INSERT INTO `content_relation`
    (`source_content_id`, `target_content_id`, `relation_type`, `created_at`, `created_by`)
VALUES
    (1, 3, 'reference',   '2025-01-21 09:00:00', 2),
    (3, 1, 'reference',   '2025-01-21 09:00:00', 2),
    (9, 11, 'inspiration','2025-03-10 09:30:00', 5),
    (11, 9, 'inspiration','2025-03-10 09:30:00', 5),
    (4, 13, 'derivative', '2025-03-15 18:20:00', 6);

INSERT INTO `like_record` (`user_id`, `content_id`, `liked_at`)
VALUES
    (2, 4, '2025-01-25 10:00:00'),
    (2, 5, '2025-02-10 13:05:00'),
    (2, 9, '2025-02-14 12:35:00'),
    (2, 10, '2025-02-28 16:10:00'),
    (3, 1, '2025-01-15 11:05:00'),
    (3, 2, '2025-02-01 15:10:00'),
    (3, 9, '2025-02-14 12:40:00'),
    (4, 1, '2025-01-16 09:00:00'),
    (4, 2, '2025-02-01 15:15:00'),
    (4, 5, '2025-02-11 08:00:00'),
    (5, 4, '2025-01-25 10:40:00'),
    (5, 5, '2025-02-10 13:20:00'),
    (5, 12, '2025-03-05 15:00:00'),
    (6, 9, '2025-02-14 12:45:00'),
    (6, 10, '2025-03-01 09:00:00'),
    (6, 11, '2025-03-10 10:10:00'),
    (7, 1, '2025-01-17 09:00:00'),
    (7, 11, '2025-03-10 10:15:00');

INSERT INTO `favorite_record` (`user_id`, `content_id`, `favorited_at`)
VALUES
    (2, 5, '2025-02-10 13:06:00'),
    (2, 9, '2025-02-14 12:36:00'),
    (3, 1, '2025-01-15 11:06:00'),
    (3, 12, '2025-03-05 15:05:00'),
    (4, 2, '2025-02-01 15:16:00'),
    (4, 5, '2025-02-11 08:05:00'),
    (5, 4, '2025-01-25 10:41:00'),
    (5, 13, '2025-03-15 18:10:00'),
    (6, 10, '2025-03-01 09:05:00'),
    (7, 1, '2025-01-17 09:05:00');

INSERT INTO `browse_history` (`history_id`, `user_id`, `content_id`, `browse_time`, `duration_seconds`)
VALUES
    (1, 2, 4, '2025-01-25 09:20:00', 45),
    (2, 2, 5, '2025-02-10 12:40:00', 120),
    (3, 2, 9, '2025-02-14 12:20:00', 60),
    (4, 2, 10, '2025-02-28 15:40:00', 90),
    (5, 3, 1, '2025-01-15 10:30:00', 180),
    (6, 3, 2, '2025-02-01 14:30:00', 150),
    (7, 3, 9, '2025-02-14 11:50:00', 95),
    (8, 4, 1, '2025-01-16 08:30:00', 140),
    (9, 4, 5, '2025-02-10 13:30:00', 200),
    (10, 4, 11, '2025-03-10 09:30:00', 300),
    (11, 5, 4, '2025-01-25 10:10:00', 80),
    (12, 5, 5, '2025-02-10 13:15:00', 210),
    (13, 5, 12, '2025-03-05 14:00:00', 110),
    (14, 6, 9, '2025-02-14 12:10:00', 70),
    (15, 6, 10, '2025-03-01 08:50:00', 85),
    (16, 6, 11, '2025-03-10 09:50:00', 260),
    (17, 7, 1, '2025-01-17 08:00:00', 100),
    (18, 7, 11, '2025-03-10 09:55:00', 180),
    (19, 3, 4, '2025-01-25 09:35:00', 55),
    (20, 3, 5, '2025-02-10 12:55:00', 140),
    (21, 4, 8, '2025-03-01 10:30:00', 190),
    (22, 2, 13, '2025-03-15 17:30:00', 95),
    (23, 5, 11, '2025-03-10 09:20:00', 220),
    (24, 6, 13, '2025-03-15 17:40:00', 105);

SET FOREIGN_KEY_CHECKS = 1;

-- 简单校验：确认各核心表已有数据
SELECT 'seed_loaded' AS `status`,
       (SELECT COUNT(*) FROM `user`) AS `user_count`,
       (SELECT COUNT(*) FROM `tag`) AS `tag_count`,
       (SELECT COUNT(*) FROM `content`) AS `content_count`,
       (SELECT COUNT(*) FROM `asset_authorization`) AS `authorization_count`;
