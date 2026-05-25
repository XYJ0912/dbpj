# 垂直兴趣社区

一个以二次元兴趣内容为例的全栈课程项目，当前重点在 MySQL 数据库设计、Flask API、鉴权/权限流程，以及基于真实后端和真实数据库的集成测试。现在仓库里也已经补上了一个可运行的 `Vite + React` 前端骨架，用来承接原型稿并开始正式联调。

当前仓库已经完成这些核心部分：
- MySQL schema、触发器、存储过程、视图、种子数据可落库
- Flask 后端已提供 45 条路由
- 冒烟测试 `smoke_test.py` 已改为复用测试辅助层，并支持测试后自动清理临时数据
- `tests/` 下已补齐一批真实 HTTP + 真实 MySQL 的集成测试
- `frontend/` 已落地 `Vite + React` 工程骨架，并通过构建验证

## 项目结构

```text
.
├─ backend/
│  ├─ app.py
│  ├─ auth.py
│  ├─ config.py
│  ├─ db.py
│  ├─ response.py
│  ├─ services.py
│  ├─ requirements.txt
│  ├─ Dockerfile
│  └─ routes/
│     ├─ admin.py
│     ├─ authorization.py
│     ├─ content.py
│     ├─ homepage.py
│     ├─ social.py
│     └─ user.py
├─ db/
│  ├─ vertical_community_schema.sql
│  ├─ vertical_community_procedures.sql
│  ├─ vertical_community_views.sql
│  ├─ vertical_community_seed_data.sql
│  └─ vertical_community_demo.sql
├─ frontend/
│  ├─ package.json
│  ├─ vite.config.js
│  ├─ index.html
│  └─ src/
│     ├─ App.jsx
│     ├─ main.jsx
│     ├─ components/
│     ├─ context/
│     ├─ lib/
│     ├─ pages/
│     └─ styles/
├─ tests/
│  ├─ helpers/
│  │  ├─ api_client.py
│  │  └─ db_helper.py
│  └─ integration/
│     ├─ base.py
│     ├─ test_admin.py
│     ├─ test_authorization_owner.py
│     ├─ test_auth_failures.py
│     ├─ test_content_visibility.py
│     ├─ test_db_procedures.py
│     ├─ test_duplicate_and_validation_errors.py
│     └─ test_work_detail.py
├─ smoke_test.py
├─ docker-compose.yml
├─ 垂直兴趣社区_前端.jsx
├─ 垂直兴趣社区_Editorial.jsx
└─ README.md
```

## 技术栈

- 数据库：MySQL 8.0
- 后端：Flask 3.1、PyMySQL、PyJWT、Flask-CORS
- 前端：Vite、React 18、React Router
- Python：推荐 3.11
- Node.js：建议 18+
- 部署：Docker Compose 或手动部署
- 测试：`unittest` + `requests` + 真实 MySQL

## 数据库组成

`db/` 目录中的 SQL 按以下顺序导入：

1. `vertical_community_schema.sql`
2. `vertical_community_procedures.sql`
3. `vertical_community_views.sql`
4. `vertical_community_seed_data.sql`
5. `vertical_community_demo.sql`（演示脚本，可选）

当前数据库层包含：
- 19 张表
- 20 个触发器
- 9 个存储过程
- 16 个视图
- 1 个事件

### Local Portfolio Library 最小库

如果演示的是 local-first 个人资产库和静态作品集发布器，请使用独立最小 schema。新库推荐命名为 `portfolio_library`：

```sql
CREATE DATABASE IF NOT EXISTS portfolio_library
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE portfolio_library;
SOURCE E:/Code/db/new_pj/db/creator_workspace_minimal.sql;
```

历史版本使用过 `creator_workspace`。如果本地已有旧库，可以继续使用；后端默认仍兼容该旧库名。旧版数据库升级 Work 展示字段时执行：

```sql
USE portfolio_library;
SOURCE E:/Code/db/new_pj/db/creator_workspace_work_display_migration.sql;
```

如果仍在使用旧库名，则先 `USE creator_workspace;` 再执行同一个 migration。

Work 展示模型由 `work` 表维护，不再由后端请求时动态改表：

```text
summary        卡片短摘要
body           作品长文正文
content_type   auto / visual / text / mixed / document / video / audio / collection
cover_mode     auto / image / title
cover_asset_id 指定封面资产，外键指向 media_asset(asset_id)
```

`media_asset.media_type` 只表示文件类型；`work.content_type` 才表示作品在主页中的整体展示类型。发布时会先导出统一 Portfolio Library Schema，再交给 `creator_gallery` adapter 生成静态主页。

上传文件默认保存到 `uploads/user-<user_id>/`，数据库中的 `media_asset.local_path` 只在本地工作台和发布器内部使用。生成 snapshot 时，发布器会把符合条件的公开资产复制到 `exports/snapshot-<id>/media/works/`，公开主页和 `data/*.json` 只保留相对路径。资产必须同时满足 `media_asset.visibility = public`、`media_asset.import_status = active`、`work_media.is_public = true`、授权不是 `restricted`，才会进入静态主页。

资产授权状态使用 `asset_license_note.authorization_status`：`unknown` 表示未确认授权，会导出但进入 warning；`original` 表示自有原创；`licensed` 表示已获授权或可按许可展示；`restricted` 表示不能公开展示，发布时会跳过。

文档资产预览采用本地解码：`md/txt` 直接读取文本，`docx` 解压读取 `word/document.xml`，`pptx` 解压读取 slide 文本，`pdf` 在安装 `pypdf` 时可提取文本。旧版 `doc/ppt` 二进制格式不做可靠解码，建议转换为 `docx/pptx`。在 Work 编辑页中，文档类 asset 可以使用 “Use text as body” 把解码文本写入 `work.body`，用于发布主页的详情弹窗。

个人主页信息在前端 `Profile` 页面维护，并保存到 `creator_profile.homepage_config`：`display_name`、`bio`、`avatar_asset_id`、`creator_tags`、`contact_links`、`license_text`。头像从已上传 image asset 中选择，发布时复制到 snapshot 的 `media/avatar.*`。联系方式只会导出已填写 URL 的条目，空值和 `#` 不会出现在公开主页。

为了让 demo 资产有真实可预览文件，可在导入 schema 后执行：

```powershell
cd E:\Code\db\new_pj
python -m tools.seed_creator_demo_assets
```

脚本会生成本地艺术风格图片和 audio/document/video/other 示例资产，并 upsert 到 demo 用户的资产库。

## 后端路由概览

后端入口在 [backend/app.py](/e:/Code/db/dbpj/backend/app.py)。

基础路由：
- `GET /`：服务健康检查
- `GET /api`：返回已注册路由列表

按 Blueprint 划分的业务模块：
- `user`：注册、登录、个人资料、行为、偏好、Feed
- `content`：内容发布、详情、评论、浏览、点赞、收藏、归档、删除、按标签/作品查询
- `social`：关注/取消关注、标签列表、作品列表、作品详情、角色列表
- `authorization`：授权申请、待处理列表、审批、撤销、概览、我的资源、活跃使用情况
- `homepage`：主页配置读写、模板列表
- `admin`：系统统计、用户停用

当前 `GET /api` 返回的路由总数为 45。

## 快速启动

### 方式一：Docker Compose

仓库根目录执行：

```powershell
docker-compose up -d
```

默认服务地址：
- MySQL：`127.0.0.1:3306`
- Backend API：`http://127.0.0.1:5000`
- 路由列表：`http://127.0.0.1:5000/api`

`docker-compose.yml` 的默认数据库配置：
- 数据库名：`vertical_community`
- 用户：`root`
- 密码：`root123`

### 方式二：手动部署

#### 1. 创建数据库并导入 SQL

先进入项目根目录：

```powershell
cd E:\Code\db\dbpj
```

进入 MySQL 客户端：

```powershell
mysql --default-character-set=utf8mb4 -u root -p
```

在 `mysql>` 中执行：

```sql
CREATE DATABASE IF NOT EXISTS `vertical_community`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `vertical_community`;

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SOURCE E:/Code/db/dbpj/db/vertical_community_schema.sql;
SOURCE E:/Code/db/dbpj/db/vertical_community_procedures.sql;
SOURCE E:/Code/db/dbpj/db/vertical_community_views.sql;
SOURCE E:/Code/db/dbpj/db/vertical_community_seed_data.sql;
```

说明：
- `SOURCE` 是 `mysql` 客户端命令，不是标准 SQL
- `vertical_community_procedures.sql` 建议始终在 `utf8mb4` 会话里导入，避免过程中的中文字符串或排序规则被错误写入

#### 2. 创建 Python 环境并安装后端依赖

推荐使用 Python 3.11。以 conda 为例：

```powershell
conda create -n dbpj python=3.11 pip -y
conda activate dbpj
cd .\backend
pip install -r requirements.txt
```

#### 3. 配置数据库连接并启动后端

后端默认读取 [backend/config.py](/e:/Code/db/dbpj/backend/config.py)。也支持环境变量覆盖：
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `JWT_SECRET`
- `FLASK_DEBUG`

本地常见启动方式：

```powershell
cd E:\Code\db\dbpj\backend
python app.py
```

启动后访问：
- `http://127.0.0.1:5000/`
- `http://127.0.0.1:5000/api`

#### 4. 安装并启动前端

```powershell
cd E:\Code\db\dbpj\frontend
npm install
npm run dev
```

Vite 默认地址：
- `http://127.0.0.1:5173`

前端默认请求：
- `http://127.0.0.1:5000/api`

如果后端地址不同，可在前端启动前设置环境变量：

```powershell
$env:VITE_API_BASE='http://127.0.0.1:5000/api'
npm run dev
```

## 前端说明

现在仓库中已经有独立的 [frontend/](/e:/Code/db/dbpj/frontend) 工程，不再只是原型文件。

这个前端骨架的来源和定位：
- 视觉方向参考 [垂直兴趣社区_Editorial.jsx](/e:/Code/db/dbpj/垂直兴趣社区_Editorial.jsx)
- 工程实现采用 `Vite + React + React Router`
- 不是把原型文件直接搬进去，而是拆成了真正可扩展的模块结构

当前前端已落地的核心模块：
- [frontend/src/context/AuthContext.jsx](/e:/Code/db/dbpj/frontend/src/context/AuthContext.jsx)：认证状态与本地持久化
- [frontend/src/lib/api.js](/e:/Code/db/dbpj/frontend/src/lib/api.js)：统一 API 请求与响应解包
- [frontend/src/components/AppShell.jsx](/e:/Code/db/dbpj/frontend/src/components/AppShell.jsx)：导航、页壳、页脚
- [frontend/src/styles/global.css](/e:/Code/db/dbpj/frontend/src/styles/global.css)：全局视觉系统与响应式样式

当前已接好的页面：
- [frontend/src/pages/HomePage.jsx](/e:/Code/db/dbpj/frontend/src/pages/HomePage.jsx)
- [frontend/src/pages/DiscoverPage.jsx](/e:/Code/db/dbpj/frontend/src/pages/DiscoverPage.jsx)
- [frontend/src/pages/AuthPage.jsx](/e:/Code/db/dbpj/frontend/src/pages/AuthPage.jsx)
- [frontend/src/pages/PublishPage.jsx](/e:/Code/db/dbpj/frontend/src/pages/PublishPage.jsx)
- [frontend/src/pages/ContentPage.jsx](/e:/Code/db/dbpj/frontend/src/pages/ContentPage.jsx)
- [frontend/src/pages/ProfilePage.jsx](/e:/Code/db/dbpj/frontend/src/pages/ProfilePage.jsx)
- [frontend/src/pages/TagPage.jsx](/e:/Code/db/dbpj/frontend/src/pages/TagPage.jsx)
- [frontend/src/pages/WorkPage.jsx](/e:/Code/db/dbpj/frontend/src/pages/WorkPage.jsx)
- [frontend/src/pages/NotFoundPage.jsx](/e:/Code/db/dbpj/frontend/src/pages/NotFoundPage.jsx)

当前前端已经直接对接后端真实接口，而不是纯静态页。已接入的能力包括：
- 登录 / 注册
- 首页内容流
- 发现页
- 内容详情与评论列表
- 个人主页
- 标签页
- 作品详情页
- 发布内容

### 前端构建命令

开发：

```powershell
cd E:\Code\db\dbpj\frontend
npm run dev
```

生产构建：

```powershell
cd E:\Code\db\dbpj\frontend
npm run build
```

本地预览构建产物：

```powershell
cd E:\Code\db\dbpj\frontend
npm run preview
```

## 测试体系

当前测试分两层：

1. 冒烟测试：[`smoke_test.py`](/e:/Code/db/dbpj/smoke_test.py)
2. 集成测试：[`tests/integration`](/e:/Code/db/dbpj/tests/integration)

这两层测试都不是 Flask 的内存级单元测试，而是：
- 请求真实运行中的 Flask 服务
- 连接真实 MySQL 数据库
- 覆盖真实 JWT、存储过程、触发器和权限逻辑

### 测试辅助层

[`tests/helpers/api_client.py`](/e:/Code/db/dbpj/tests/helpers/api_client.py)
- 封装 HTTP 请求
- 统一处理 Bearer Token
- 统一成功/失败响应断言
- 提供注册、登录等基础操作

[`tests/helpers/db_helper.py`](/e:/Code/db/dbpj/tests/helpers/db_helper.py)
- 直接连 MySQL
- 用于授予角色、创建临时资产、创建关注关系、直接查询业务状态
- 负责清理测试期间产生的用户及其关联数据

[`tests/integration/base.py`](/e:/Code/db/dbpj/tests/integration/base.py)
- 提供 `LiveBackendTestCase`
- 统一预检 `GET /api`
- 统一创建临时用户
- 测试结束时自动清理

### 当前集成测试覆盖

已实现的集成测试文件：
- [tests/integration/test_admin.py](/e:/Code/db/dbpj/tests/integration/test_admin.py)
- [tests/integration/test_authorization_owner.py](/e:/Code/db/dbpj/tests/integration/test_authorization_owner.py)
- [tests/integration/test_auth_failures.py](/e:/Code/db/dbpj/tests/integration/test_auth_failures.py)
- [tests/integration/test_content_visibility.py](/e:/Code/db/dbpj/tests/integration/test_content_visibility.py)
- [tests/integration/test_db_procedures.py](/e:/Code/db/dbpj/tests/integration/test_db_procedures.py)
- [tests/integration/test_duplicate_and_validation_errors.py](/e:/Code/db/dbpj/tests/integration/test_duplicate_and_validation_errors.py)
- [tests/integration/test_work_detail.py](/e:/Code/db/dbpj/tests/integration/test_work_detail.py)

覆盖重点包括：
- admin 权限成功路径
- owner 对授权申请的 reject / approve / revoke
- 未登录、普通用户、非 owner 的权限失败路径
- 内容可见性矩阵：`public`、`followers_only`、`private`、`draft`
- 注册、登录、发帖、评论等参数校验与重复操作错误
- 作品详情接口
- 存储过程相关回归：主页并发保存、moderator 归档、admin deactivated 收敛逻辑

### 如何运行集成测试

先确保：
- MySQL 已启动
- 后端服务已运行在 `http://127.0.0.1:5000`
- 使用已安装依赖的 Python 环境

推荐命令：

```powershell
cd E:\Code\db\dbpj
& "$env:USERPROFILE\.conda\envs\dbpj\python.exe" -m unittest discover -s tests -p "test_*.py" -v
```

如果你当前已 `conda activate dbpj`，也可以直接：

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

### 如何运行冒烟测试

```powershell
cd E:\Code\db\dbpj
python smoke_test.py --base-url http://127.0.0.1:5000
```

如果后端就在默认地址，也可以省略参数：

```powershell
python smoke_test.py
```

保留测试数据时使用：

```powershell
python smoke_test.py --base-url http://127.0.0.1:5000 --keep-data
```

### 冒烟测试当前覆盖

`smoke_test.py` 当前会覆盖：
- `GET /`
- `GET /api`
- 公共内容、标签、作品、角色、按标签/作品查询
- 注册、登录
- `user/me`、profile、behavior、tags、works、friends、feed
- follow / unfollow
- homepage 模板、读取、保存
- authorization 概览、我的资源、活跃使用、待处理、发起申请
- content 详情、评论、浏览、点赞、收藏、发布、评论、归档、删除
- owner 路径：审批申请、撤销授权
- admin 路径：系统统计、停用用户

## 自动清理说明

当前 `smoke_test.py` 和 `tests/integration` 都已经支持测试后自动清理临时数据。

默认行为：
- 删除测试创建的临时用户
- 删除这些用户关联的内容、评论、点赞、收藏、关注、授权请求、授权记录、资产、主页、角色映射等数据

只有在显式传入 `--keep-data` 时，`smoke_test.py` 才会保留本轮临时数据。

## 当前验证结果

这轮整理后，已经验证通过的结果如下：

集成测试：

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

结果：
- 共 16 个测试
- 全部通过

冒烟测试：

```powershell
python smoke_test.py --base-url http://127.0.0.1:5000
```

结果：
- 总计 47 项检查
- `Passed: 47`
- `Failed: 0`
- `Skipped: 0`

前端构建：

```powershell
cd E:\Code\db\dbpj\frontend
npm run build
```

结果：
- 构建通过
- 已生成 [frontend/dist](/e:/Code/db/dbpj/frontend/dist)

## 已处理过的关键问题

最近一轮主要修了这些问题：
- MySQL schema 中因 `CHECK` 与外键 referential action 冲突导致的建表阻塞问题
- `DELIMITER;` 写法导致的 schema 导入语法错误
- `vertical_community_procedures.sql` 的字符集 / 排序规则问题，避免存储过程与表定义混用 collation
- `smoke_test.py` 早期版本没有清理临时用户的问题
- owner/admin 路径此前在冒烟测试中被跳过的问题
- 新增测试时因同秒更新时间导致主页并发测试不稳定的问题
- 冒烟执行顺序导致公共内容在后续 destructive 场景里失效的问题
- 前端骨架首次构建时因文件 BOM 导致的 Vite JSON 解析错误

## 建议阅读顺序

如果你要快速理解当前项目，建议按这个顺序看：

1. [backend/app.py](/e:/Code/db/dbpj/backend/app.py)
2. [backend/routes/user.py](/e:/Code/db/dbpj/backend/routes/user.py)
3. [backend/routes/content.py](/e:/Code/db/dbpj/backend/routes/content.py)
4. [backend/routes/authorization.py](/e:/Code/db/dbpj/backend/routes/authorization.py)
5. [backend/routes/admin.py](/e:/Code/db/dbpj/backend/routes/admin.py)
6. [db/vertical_community_schema.sql](/e:/Code/db/dbpj/db/vertical_community_schema.sql)
7. [db/vertical_community_procedures.sql](/e:/Code/db/dbpj/db/vertical_community_procedures.sql)
8. [smoke_test.py](/e:/Code/db/dbpj/smoke_test.py)
9. [tests/integration/base.py](/e:/Code/db/dbpj/tests/integration/base.py)
10. [frontend/src/App.jsx](/e:/Code/db/dbpj/frontend/src/App.jsx)
11. [frontend/src/lib/api.js](/e:/Code/db/dbpj/frontend/src/lib/api.js)
12. [frontend/src/pages/HomePage.jsx](/e:/Code/db/dbpj/frontend/src/pages/HomePage.jsx)

## 常见问题

### 1. 为什么测试要连真实数据库，而不是只用 Flask test client？

因为这个项目的大量业务逻辑不只在路由层，还落在存储过程、触发器、视图和权限收敛逻辑里。只测 Flask 内存层，无法覆盖真实数据库行为。

### 2. 为什么推荐 Python 3.11？

当前依赖在 3.11 上比较稳。之前用系统 Python 运行测试时，就因为环境里缺 `pymysql` 导致失败；统一到项目环境后更省事。

### 3. 为什么导入 procedures 时要强调 `utf8mb4`？

因为存储过程中的字符串常量和比较逻辑如果在错误的字符集 / 排序规则会话下创建，后续容易出现乱码或 `Illegal mix of collations` 一类问题。

### 4. 前端现在是完整产品吗？

还不是。现在的 [frontend/](/e:/Code/db/dbpj/frontend) 是第一版可运行骨架，已经能联真实后端，但还没有把所有业务流程和细节交互补齐。

### 5. 为什么前端保留了原型气质，但没有继续用单文件 JSX？

因为单文件原型适合表达视觉方向，不适合后续联调和维护。现在的前端是把原型中的 editorial 视觉语言拆成了真正的工程结构，方便继续接页面、状态和接口。
