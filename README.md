# Local Portfolio Library 本地个人资产库与静态作品集发布器

这是面向数据库大作业和本地演示的最小可运行版本。它不只面向创作者，也适合学生、设计师、摄影师、内容创作者和普通用户整理本地资产并发布个人作品集主页。

核心链路：

```text
登记资产 -> 创建 Work -> 绑定资产 -> 设置授权和公开状态 -> 配置 Work 展示方式 -> 发布检查 -> 生成静态个人主页
```

## 1. 数据库

新建数据库推荐使用更通用的库名 `portfolio_library`：

```sql
CREATE DATABASE IF NOT EXISTS portfolio_library
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE portfolio_library;
SOURCE E:/Code/db/new_pj/db/creator_workspace_minimal.sql;
```

注意：`creator_workspace_minimal.sql` 是重置式初始化脚本，会 drop 并重建相关表，适合新库或演示库重置；已有数据需要保留时不要直接执行它，应使用 migration 脚本。

历史版本使用过 `creator_workspace`。如果你本地已经有旧库，可以继续使用；后端默认仍兼容 `creator_workspace`。如果要切到新库名，启动后端前设置：

```powershell
$env:DB_NAME='portfolio_library'
```

Demo 账号：

```text
username: demo
password: secret
```

如果你的本地库已经是旧版 schema 建出来的，需要额外执行 Work 展示字段迁移：

```sql
USE portfolio_library;
SOURCE E:/Code/db/new_pj/db/creator_workspace_work_display_migration.sql;
```

如果你仍在使用旧库名：

```sql
USE creator_workspace;
SOURCE E:/Code/db/new_pj/db/creator_workspace_work_display_migration.sql;
```

如果 `demo / secret` 登录失败，通常是旧库里的 demo 密码 hash 与当前后端 `hash_password()` 不一致，执行：

```sql
USE portfolio_library;
SOURCE E:/Code/db/new_pj/db/creator_workspace_demo_password_fix.sql;
```

或对旧库执行：

```sql
USE creator_workspace;
SOURCE E:/Code/db/new_pj/db/creator_workspace_demo_password_fix.sql;
```

为了让演示资产有真实可预览文件，初始化或迁移数据库后建议执行一次 demo asset seed：

```powershell
cd E:\Code\db\new_pj
python -m tools.seed_creator_demo_assets
```

如果使用新库名：

```powershell
$env:DB_NAME='portfolio_library'
python -m tools.seed_creator_demo_assets
```

该脚本会在 `demo_assets/` 下生成艺术风格 PNG、WAV 音频、Markdown 文档、MP4/JSON 示例资产，并把它们写入 demo 用户的 `media_asset`。脚本可重复执行，会更新同名资产，不会重复插入。

## 2. Work 展示模型

`media_asset.media_type` 表示资产文件类型：

```text
image / video / audio / document / other
```

`work.content_type` 表示作品整体在主页中的展示类型：

```text
auto / visual / text / mixed / document / video / audio / collection
```

`work.cover_mode` 表示主页卡片封面策略：

```text
auto  - 有可用封面图则显示 image-card，否则显示 title-card
image - 优先显示 image-card，图片缺失时 fallback 到 title-card
title - 强制显示 title-card
```

新增字段位于 `work` 表：

```text
summary        卡片短摘要，最多 500 字符
body           作品长文正文
content_type   Work 级展示类型
cover_mode     卡片封面模式
cover_asset_id 指定封面资产，可为空，外键指向 media_asset(asset_id)
```

注意：`cover_asset_id` 只决定封面候选；发布时仍会检查该 asset 是否 public、active、非 restricted，且必须是 image 才会作为指定封面导出。

当 `cover_asset_id` 为空并且 Work 没有 public image asset 时，发布器会尝试使用第一个 public video asset 的第一帧生成封面图。该功能需要运行后端的环境能找到 `ffmpeg`，否则会回退为 title-card 并在 `publish_report.json` 中写入 warning。

## 3. 后端

```powershell
cd E:\Code\db\new_pj\backend
pip install -r requirements.txt
python app.py
```

如果使用 `portfolio_library`：

```powershell
$env:DB_NAME='portfolio_library'
python app.py
```

主要 API：

```text
POST /api/user/register
POST /api/user/login
GET  /api/user/me

GET    /api/assets
POST   /api/assets/import
POST   /api/assets/upload
PATCH  /api/assets/:asset_id
POST   /api/assets/:asset_id/archive
POST   /api/assets/:asset_id/restore
DELETE /api/assets/:asset_id

GET    /api/workspace/overview
GET    /api/workspace/works
POST   /api/workspace/works
GET    /api/workspace/works/:work_id
PATCH  /api/workspace/works/:work_id
POST   /api/workspace/works/:work_id/archive
POST   /api/workspace/works/:work_id/restore
DELETE /api/workspace/works/:work_id
POST   /api/workspace/works/:work_id/assets
PATCH  /api/workspace/works/:work_id/assets/:asset_id
DELETE /api/workspace/works/:work_id/assets/:asset_id

GET    /api/publish/templates
GET    /api/publish/homepage
PATCH  /api/publish/homepage
POST   /api/publish/check
POST   /api/publish/generate
POST   /api/publish/snapshot
GET    /api/publish/snapshots
PATCH  /api/publish/snapshots/:snapshot_id
DELETE /api/publish/snapshots/:snapshot_id
GET    /api/publish/snapshots/:snapshot_id/site/
```

## 4. 前端

```powershell
cd E:\Code\db\new_pj\frontend
npm install
npm run dev
```

默认访问：

```text
http://127.0.0.1:5173
```

## 5. 演示流程

1. 用 `demo / secret` 登录。
2. 在 Assets 页面导入或上传资产。
3. 将可公开展示的资产设为 `public`，并标记 `original` 或 `licensed`。
4. 在 Works 页面创建作品。
5. 进入 Work 编辑页，设置：
   - `visibility = public`
   - `status = ready`
   - `content_type`
   - `cover_mode`
   - `cover_asset_id`
   - `summary`
   - `body`
6. 给 Work 绑定 assets。
7. 在 Publish 页面点击 `Run check`，再点击 `Generate Portfolio Gallery Site`。
8. 发布结果输出到：

```text
E:\Code\db\new_pj\exports\snapshot-<snapshot_id>\
```

## 6. 发布输出结构

```text
exports/snapshot-<snapshot_id>/
  index.html
  styles.css
  main.js
  media/
    works/
  data/
    profile.json
    works.json
    homepage.json
    tags.json
  publish_report.json
```

公开主页只展示个人信息和公开 Work，不展示调试报告、`asset_id`、`local_path`、Warnings、Errors。

`publish_report.json` 只给本地工作台查看，包含：

```text
exported_works_count
exported_assets_count
warnings
errors
skipped_private_assets
skipped_restricted_assets
local_path_leak_check
large_file_check
sensitive_file_check
api_key_pattern_check
```

## 7. 归档与删除

Asset 页面区分归档和删除：

- Archive asset：软删除，将 `media_asset.import_status` 设为 `archived`，可在 Archived 过滤器中 Restore。
- Restore asset：把 archived 资产恢复为 `active`。
- Delete permanently：删除数据库中的 asset 记录、授权记录和 Work 绑定关系；本地源文件不会自动删除，但该资产需要重新导入或上传后才能再次使用。

Work 页面同样区分归档和删除：

- Archive work：软删除，将 `work.work_status` 设为 `archived`，可在 Works 页的 Archived 过滤器中找到。
- Restore work：把 archived work 恢复为 `draft`，恢复后可重新编辑并发布。
- Delete permanently：删除 Work 记录、Work-Asset 绑定和 Work-Tag 绑定；不会删除资产库中的 asset 文件。

## 8. 当前不包含

- AI 生成
- 任意 GitHub 模板 clone/build
- GitHub token 自动 push
- 多模板市场
- 社区评论、点赞、访问统计
- 复杂视频转码
- 在线部署
