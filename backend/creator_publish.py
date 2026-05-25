import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

from config import Config
from db import execute, query, query_one
from document_extract import extract_asset_text, summarize_text


EXPORT_ROOT = Path(Config.EXPORT_ROOT).resolve() if Config.EXPORT_ROOT else Path(__file__).resolve().parents[1] / "exports"
TEMPLATE_ROOT = Path(__file__).resolve().parent / "templates"
LARGE_FILE_THRESHOLD_MB = 20

LOCAL_PATH_PATTERNS = [
    re.compile(r"local_path", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z])[A-Za-z]:\\"),
    re.compile(r"(?<![A-Za-z])[A-Za-z]:/"),
    re.compile(r"/Users/"),
    re.compile(r"/home/"),
]
API_KEY_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]
SENSITIVE_SUFFIXES = {".env", ".db", ".sqlite", ".sqlite3"}
SENSITIVE_NAME_PARTS = {"dump", "backup"}
IMAGE_TYPES = {"image", "gif"}
VIDEO_TYPES = {"video"}
TEXT_ASSET_SUFFIXES = {".txt", ".md", ".markdown", ".docx", ".pptx", ".pdf"}
PUBLISH_TEXT_LIMIT = 12000


TEMPLATE_REGISTRY = {
    "creator_gallery": {
        "template_id": "creator_gallery",
        "template_name": "Portfolio Gallery",
        "source_type": "built_in",
        "source_url": None,
        "license": "project-owned",
        "adapter_name": "CreatorGalleryAdapter",
        "output_dir": "",
        "description": "A built-in gallery-style portfolio template for personal works and visual collections.",
    }
}


DEMO_WORKS = [
    {
        "id": "demo_001",
        "title": "Night Patrol",
        "summary": "A character design study built around neon lighting and quiet urban scenes.",
        "body": "A character design study built around neon lighting and quiet urban scenes.",
        "description": "A character design study built around neon lighting and quiet urban scenes.",
        "content_type": "visual",
        "cover_mode": "auto",
        "cover": "",
        "tags": ["Character", "Cyberpunk", "Original"],
        "featured": True,
        "authorization_status": "original",
        "visibility": "public",
        "assets": [],
    },
    {
        "id": "demo_002",
        "title": "Spring Archive",
        "summary": "A soft-color illustration series exploring seasonal memory and personal objects.",
        "body": "A soft-color illustration series exploring seasonal memory and personal objects.",
        "description": "A soft-color illustration series exploring seasonal memory and personal objects.",
        "content_type": "visual",
        "cover_mode": "auto",
        "cover": "",
        "tags": ["Illustration", "Series"],
        "featured": True,
        "authorization_status": "original",
        "visibility": "public",
        "assets": [],
    },
    {
        "id": "demo_003",
        "title": "Portrait Practice",
        "summary": "A collection of lighting and expression studies.",
        "body": "A collection of lighting and expression studies.",
        "description": "A collection of lighting and expression studies.",
        "content_type": "visual",
        "cover_mode": "auto",
        "cover": "",
        "tags": ["Portrait", "Study"],
        "featured": False,
        "authorization_status": "licensed",
        "visibility": "public",
        "assets": [],
    },
]


def parse_json(value, fallback):
    if value is None:
        return fallback
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback
    return value if isinstance(value, dict) else fallback


def selected_work_ids(payload):
    ids = payload.get("work_ids") or []
    return [int(item) for item in ids if int(item) > 0]


def get_homepage_config(user_id):
    profile = query_one(
        """SELECT u.username, p.display_name, p.bio, p.avatar_url, p.homepage_config
             FROM user_account u
             JOIN creator_profile p ON p.user_id = u.user_id
            WHERE u.user_id = %s""",
        (user_id,),
    )
    config = parse_json(profile.get("homepage_config") if profile else None, {})
    return profile or {}, config


def collect_work_rows(user_id, request_payload):
    ids = selected_work_ids(request_payload)
    if ids:
        placeholders = ", ".join(["%s"] * len(ids))
        return query(
            f"""SELECT *
                  FROM work
                 WHERE owner_id = %s AND work_id IN ({placeholders})
                 ORDER BY updated_at DESC, work_id DESC""",
            [user_id, *ids],
        )
    return query(
        """SELECT *
             FROM work
            WHERE owner_id = %s AND visibility = 'public' AND work_status = 'ready'
            ORDER BY updated_at DESC, work_id DESC""",
        (user_id,),
    )

def work_tags(work_id):
    return query(
        """SELECT t.tag_name, t.tag_type
             FROM work_tag wt
             JOIN tag t ON t.tag_id = wt.tag_id
            WHERE wt.work_id = %s AND t.tag_status = 'active'
            ORDER BY t.tag_type, t.tag_name""",
        (work_id,),
    )


def work_assets(work_id):
    return query(
        """SELECT wm.role, wm.display_order, wm.is_public,
                  a.asset_id, a.asset_name, a.media_type, a.local_path, a.thumbnail_path,
                  a.public_export_path, a.file_size, a.mime_type, a.visibility, a.import_status,
                  COALESCE(l.authorization_status, 'unknown') AS authorization_status,
                  COALESCE(l.allow_public_display, 0) AS allow_public_display
             FROM work_media wm
             JOIN media_asset a ON a.asset_id = wm.asset_id
        LEFT JOIN asset_license_note l ON l.asset_id = a.asset_id
            WHERE wm.work_id = %s
            ORDER BY wm.display_order, a.asset_id""",
        (work_id,),
    )


def default_profile(profile_row, config):
    display_name = config.get("display_name") or profile_row.get("display_name") or profile_row.get("username") or "Mori Studio"
    avatar = config.get("avatar") or config.get("avatar_url") or profile_row.get("avatar_url") or ""
    if contains_local_path(avatar):
        avatar = ""
    contact_links = []
    for link in config.get("contact_links") or []:
        url = str((link or {}).get("url") or "").strip()
        label = str((link or {}).get("label") or "").strip()
        if not url or url == "#":
            continue
        contact_links.append({"label": label or "Contact", "url": url})
    return {
        "display_name": display_name,
        "bio": config.get("bio") or profile_row.get("bio") or "Illustration, character design, and visual storytelling.",
        "avatar": avatar,
        "avatar_asset_id": config.get("avatar_asset_id"),
        "creator_tags": config.get("creator_tags") or [],
        "contact_links": contact_links,
        "license_text": config.get("license_text") or "Unless otherwise noted, works are for portfolio display only.",
    }


def default_homepage(config, template_id):
    return {
        "template_id": template_id,
        "theme": config.get("theme") or "warm_gallery",
        "accent_color": config.get("accent_color") or "#8fb8a8",
        "featured_work_ids": config.get("featured_work_ids") or [],
    }


def build_portfolio_library_schema(user_id, request_payload):
    template_id = request_payload.get("template_id") or "creator_gallery"
    profile_row, config = get_homepage_config(user_id)
    homepage = default_homepage(config, template_id)
    if "featured_work_ids" in request_payload:
        homepage["featured_work_ids"] = request_payload.get("featured_work_ids") or []
    profile = default_profile(profile_row, config)
    media_manifest = []
    warnings = []
    errors = []
    skipped_private_assets = []
    skipped_restricted_assets = []
    exported_assets_count = 0

    avatar_asset_id = profile.get("avatar_asset_id")
    if avatar_asset_id:
        avatar_asset = query_one(
            """SELECT a.*, COALESCE(l.authorization_status, 'unknown') AS authorization_status
                 FROM media_asset a
            LEFT JOIN asset_license_note l ON l.asset_id = a.asset_id
                WHERE a.owner_id = %s AND a.asset_id = %s
                  AND a.media_type = 'image' AND a.import_status = 'active'""",
            (user_id, avatar_asset_id),
        )
        if avatar_asset and (avatar_asset.get("authorization_status") or "unknown") != "restricted":
            avatar_path = f"media/avatar{source_suffix(avatar_asset)}"
            profile["avatar"] = avatar_path
            media_manifest.append({"asset": avatar_asset, "relative_path": avatar_path})
            exported_assets_count += 1
    profile.pop("avatar_asset_id", None)

    works = []
    featured_ids = {str(item) for item in homepage.get("featured_work_ids", [])}
    for work in collect_work_rows(user_id, request_payload):
        if work.get("visibility") != "public" or work.get("work_status") != "ready":
            errors.append(
                {
                    "check_type": "private_work_included",
                    "severity": "error",
                    "message": f"work {work['work_id']} is not public and ready",
                    "related_table": "work",
                    "related_id": work["work_id"],
                }
            )
            continue

        exported_assets = []
        cover = ""
        authorization_status = "unknown"
        assets = work_assets(work["work_id"])
        selected_cover_asset_id = work.get("cover_asset_id")
        cover_asset_candidate = None
        first_image_candidate = None
        first_video_candidate = None
        asset_index = 0
        for asset in assets:
            asset_id = asset["asset_id"]
            status = asset.get("authorization_status") or "unknown"
            if not asset.get("is_public") or asset.get("visibility") != "public" or asset.get("import_status") != "active":
                skipped_private_assets.append({"asset_id": asset_id, "work_id": work["work_id"], "asset_name": asset.get("asset_name")})
                continue
            if status == "restricted":
                skipped_restricted_assets.append({"asset_id": asset_id, "work_id": work["work_id"], "asset_name": asset.get("asset_name")})
                continue
            if status == "unknown":
                warnings.append(
                    {
                        "check_type": "unknown_license_included",
                        "severity": "warning",
                        "message": f"asset {asset_id} license is unknown",
                        "related_table": "media_asset",
                        "related_id": asset_id,
                    }
                )

            asset_index += 1
            relative_path = f"media/works/work_{work['work_id']}_{asset_index:02d}{source_suffix(asset)}"
            media_manifest.append({"asset": asset, "relative_path": relative_path})
            exported_assets_count += 1
            if asset.get("media_type") in IMAGE_TYPES:
                if selected_cover_asset_id and int(selected_cover_asset_id) == int(asset_id):
                    cover_asset_candidate = {"path": relative_path, "status": status}
                if not first_image_candidate:
                    first_image_candidate = {"path": relative_path, "status": status}
            elif asset.get("media_type") in VIDEO_TYPES and not first_video_candidate:
                first_video_candidate = {
                    "path": f"media/works/work_{work['work_id']}_video_cover.jpg",
                    "status": status,
                    "asset": asset,
                }

            public_asset = {
                "type": public_asset_type(asset),
                "path": relative_path or "",
                "format": source_suffix(asset).lstrip("."),
                "role": asset.get("role") or "main",
            }
            text_preview = public_asset_text(asset)
            if text_preview:
                public_asset["text"] = text_preview
            exported_assets.append(public_asset)

        selected_cover = cover_asset_candidate or first_image_candidate or first_video_candidate
        if selected_cover:
            cover = selected_cover["path"]
            authorization_status = selected_cover["status"]
            if selected_cover is first_video_candidate:
                media_manifest.append(
                    {
                        "asset": selected_cover["asset"],
                        "relative_path": selected_cover["path"],
                        "operation": "video_frame",
                    }
                )

        tag_names = [item["tag_name"] for item in work_tags(work["work_id"])]
        work_id = f"work_{work['work_id']}"
        content_type = infer_content_type(work, [asset for asset in assets if should_export_asset(asset)])
        cover_mode = work.get("cover_mode") or "auto"
        summary, body = summarize_work(work)
        if not (work.get("body") or "").strip():
            extracted_body = first_asset_text(exported_assets)
            if extracted_body:
                body = extracted_body
                if not summary or summary == (work.get("description") or "").strip():
                    summary = summarize_text(extracted_body)
        works.append(
            {
                "id": work_id,
                "title": work.get("title") or "Untitled work",
                "summary": summary,
                "body": body,
                "description": work.get("description") or "",
                "content_type": content_type,
                "cover_mode": cover_mode,
                "cover": cover,
                "tags": tag_names,
                "featured": str(work["work_id"]) in featured_ids if featured_ids else len(works) < 2,
                "authorization_status": authorization_status,
                "visibility": "public",
                "assets": exported_assets,
            }
        )

    if not works and request_payload.get("use_demo_fallback", True):
        works = DEMO_WORKS
        warnings.append(
            {
                "check_type": "demo_data_used",
                "severity": "warning",
                "message": "No public ready works were found; exported built-in demo works.",
            }
        )

    tags = [{"name": name, "count": count} for name, count in Counter(tag for work in works for tag in work.get("tags", [])).most_common()]
    schema = {"profile": profile, "works": works, "homepage": homepage, "tags": tags}
    report = base_report(schema, warnings, errors, skipped_private_assets, skipped_restricted_assets, exported_assets_count)
    return schema, report, media_manifest

def source_suffix(asset):
    for field in ("asset_name", "local_path", "public_export_path", "thumbnail_path"):
        value = asset.get(field)
        if value:
            suffix = Path(str(value)).suffix.lower()
            if suffix:
                return suffix
    mime = asset.get("mime_type") or ""
    if mime == "text/markdown":
        return ".md"
    if mime == "text/plain":
        return ".txt"
    if mime == "application/pdf":
        return ".pdf"
    if mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return ".docx"
    if mime == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        return ".pptx"
    return ".jpg"


def public_asset_type(asset):
    media_type = asset.get("media_type") or "other"
    if media_type == "other" and source_suffix(asset) in TEXT_ASSET_SUFFIXES:
        return "document"
    return media_type


def public_asset_text(asset):
    if public_asset_type(asset) != "document":
        return ""
    if source_suffix(asset) not in TEXT_ASSET_SUFFIXES:
        return ""
    src = source_path(asset)
    if not src:
        return ""
    text, _reason = extract_asset_text(src, asset.get("mime_type"), asset.get("asset_name"))
    return str(text or "").strip()[:PUBLISH_TEXT_LIMIT]


def first_asset_text(assets):
    for asset in assets:
        text = str(asset.get("text") or "").strip()
        if text:
            return text
    return ""


def infer_content_type(work, assets):
    explicit = work.get("content_type") or "auto"
    if explicit != "auto":
        return explicit
    media_types = {asset.get("media_type") for asset in assets}
    if media_types <= {"image"} and media_types:
        return "visual"
    if "video" in media_types and len(media_types) == 1:
        return "video"
    if "audio" in media_types and len(media_types) == 1:
        return "audio"
    if "document" in media_types and len(media_types) == 1:
        return "document"
    if media_types:
        return "mixed"
    if work.get("body") or work.get("description"):
        return "text"
    return "collection"


def summarize_work(work):
    explicit = (work.get("summary") or "").strip()
    description = (work.get("description") or "").strip()
    body = (work.get("body") or "").strip()
    source = description or body
    if explicit:
        return explicit, body or description
    if len(source) > 160:
        return source[:157].rstrip() + "...", body or source
    return source, body or description


def should_export_asset(asset):
    return (
        asset.get("is_public")
        and asset.get("visibility") == "public"
        and asset.get("import_status") == "active"
        and (asset.get("authorization_status") or "unknown") != "restricted"
    )


def contains_local_path(value):
    text = str(value or "")
    return any(pattern.search(text) for pattern in LOCAL_PATH_PATTERNS)


def source_path(asset):
    for field in ("local_path", "public_export_path", "thumbnail_path"):
        value = asset.get(field)
        if value and Path(str(value)).exists():
            return Path(str(value))
    return None


def ffmpeg_path():
    env_roots = [
        os.getenv("CONDA_PREFIX"),
        os.getenv("VIRTUAL_ENV"),
        sys.prefix,
        str(Path(__file__).resolve().parents[1] / ".venv"),
    ]
    candidates = [
        os.getenv("FFMPEG_PATH"),
        shutil.which("ffmpeg"),
    ]
    for root in env_roots:
        if not root:
            continue
        base = Path(root)
        candidates.extend(
            [
                str(base / "Library" / "bin" / "ffmpeg.exe"),
                str(base / "Scripts" / "ffmpeg.exe"),
                str(base / "bin" / "ffmpeg"),
                str(base / "bin" / "ffmpeg.exe"),
            ]
        )
    candidates.extend(
        [
            str(Path.home() / ".conda" / "envs" / "dbpj" / "Library" / "bin" / "ffmpeg.exe"),
            str(Path.home() / ".conda" / "envs" / "dbpj" / "Scripts" / "ffmpeg.exe"),
        ]
    )
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def extract_video_cover(src, target):
    binary = ffmpeg_path()
    if not binary:
        return False, "ffmpeg was not found"
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        binary,
        "-y",
        "-ss",
        "00:00:00",
        "-i",
        str(src),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(target),
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=30)
    except Exception as exc:
        return False, str(exc)
    if completed.returncode != 0 or not target.exists():
        return False, (completed.stderr or completed.stdout or "ffmpeg failed").strip()[:500]
    return True, ""


def base_report(schema, warnings, errors, skipped_private_assets, skipped_restricted_assets, exported_assets_count):
    return {
        "exported_works_count": len(schema.get("works", [])),
        "exported_assets_count": exported_assets_count,
        "warnings": warnings,
        "errors": errors,
        "skipped_private_assets": skipped_private_assets,
        "skipped_restricted_assets": skipped_restricted_assets,
        "local_path_leak_check": {"passed": True, "matches": []},
        "large_file_check": {"passed": True, "threshold_mb": LARGE_FILE_THRESHOLD_MB, "matches": []},
        "sensitive_file_check": {"passed": True, "matches": []},
        "api_key_pattern_check": {"passed": True, "matches": []},
    }


class CreatorGalleryAdapter:
    template_id = "creator_gallery"

    def __init__(self):
        self.template_dir = TEMPLATE_ROOT / self.template_id

    def render(self, output_dir, schema, report, media_manifest):
        output_dir = Path(output_dir)
        ensure_within_exports(output_dir)
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "data").mkdir()
        (output_dir / "media" / "works").mkdir(parents=True)

        self.copy_media(output_dir, media_manifest, report)
        for file_name in ("styles.css", "main.js"):
            shutil.copy2(self.template_dir / file_name, output_dir / file_name)

        write_json(output_dir / "data" / "profile.json", schema["profile"])
        write_json(output_dir / "data" / "works.json", schema["works"])
        write_json(output_dir / "data" / "homepage.json", schema["homepage"])
        write_json(output_dir / "data" / "tags.json", schema["tags"])

        index_template = (self.template_dir / "index.html").read_text(encoding="utf-8")
        inline_json = json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")
        index_html = index_template.replace("__CREATOR_DATA_JSON__", inline_json)
        (output_dir / "index.html").write_text(index_html, encoding="utf-8")

        finalize_report(output_dir, report)
        write_json(output_dir / "publish_report.json", report)
        write_readme(output_dir, schema, report)
        return output_dir

    def copy_media(self, output_dir, media_manifest, report):
        for item in media_manifest:
            src = source_path(item["asset"])
            if not src:
                report["warnings"].append(
                    {
                        "check_type": "missing_media_file",
                        "severity": "warning",
                        "message": f"asset {item['asset']['asset_id']} source file was not found; template fallback will be used.",
                        "related_table": "media_asset",
                        "related_id": item["asset"]["asset_id"],
                    }
                )
                continue
            target = output_dir / item["relative_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            if item.get("operation") == "video_frame":
                ok, reason = extract_video_cover(src, target)
                if not ok:
                    report["warnings"].append(
                        {
                            "check_type": "video_cover_extract_failed",
                            "severity": "warning",
                            "message": f"Could not extract cover frame for video asset {item['asset']['asset_id']}: {reason}",
                            "related_table": "media_asset",
                            "related_id": item["asset"]["asset_id"],
                        }
                    )
                continue
            shutil.copy2(src, target)


def ensure_within_exports(path):
    root = EXPORT_ROOT.resolve()
    target = Path(path).resolve()
    if root != target and root not in target.parents:
        raise ValueError("publish output must stay inside exports directory")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def build_readme_content(title, work_count=0, asset_count=0, warning_count=0, error_count=0):
    return f"""# {title} 静态主页快照

这是 Portfolio Library 导出的完整静态站点目录。目录内已经包含主页、样式、脚本、公开数据和媒体副本，可以直接用于静态托管。

## 目录内容

- `index.html`：公开主页入口。
- `styles.css`：主页样式文件。
- `main.js`：主页交互逻辑。
- `data/profile.json`：公开个人信息。
- `data/works.json`：公开作品数据。
- `data/homepage.json`：主页配置。
- `data/tags.json`：标签统计。
- `media/`：公开主页使用的图片、视频、音频和文档副本。
- `publish_report.json`：本地发布检查报告。
- `README.md`：当前说明文件。

## 本地预览

可以直接双击打开 `index.html`。如果浏览器限制本地文件加载，建议在当前目录启动一个本地静态服务器：

```bash
python -m http.server 8000
```

然后在浏览器访问：

```text
http://localhost:8000
```

## 部署前确认

部署时请上传整个目录。`index.html` 需要和 `styles.css`、`main.js`、`data/`、`media/` 保持在同一层级，这样页面样式、作品数据和媒体文件才能正常加载。

如果替换过资产文件，请先在 Portfolio Library 里重新 Generate snapshot，再下载新的 zip 进行部署。

## GitHub Pages：网页上传方式

适合不熟悉 Git 命令的用户。

1. 在 GitHub 新建一个仓库，例如 `my-portfolio-site`。
2. 解压本 zip。
3. 打开仓库页面，点击 `Add file -> Upload files`。
4. 把解压后目录里的所有文件和文件夹拖进去，包括 `index.html`、`styles.css`、`main.js`、`data/`、`media/`、`publish_report.json` 和 `README.md`。
5. 点击 `Commit changes`。
6. 打开仓库的 `Settings -> Pages`。
7. Source 选择 `Deploy from a branch`。
8. Branch 选择 `main`，目录选择 `/root`。
9. 保存后等待 GitHub Pages 构建完成。
10. 打开 GitHub Pages 给出的访问地址。

## GitHub Pages：Git 命令行方式

适合已经安装 Git 的用户。下面命令假设你已经在 GitHub 新建了一个空仓库。

### 第一次发布

进入解压后的静态站点目录，也就是包含 `index.html` 的目录：

```bash
cd path/to/your/unzipped-snapshot
git init
git branch -M main
git add .
git commit -m "Publish portfolio site"
git remote add origin https://github.com/YOUR_NAME/YOUR_REPO.git
git push -u origin main
```

然后到 GitHub 仓库页面打开 `Settings -> Pages`：

```text
Source: Deploy from a branch
Branch: main
Folder: /root
```

保存后等待部署完成。

### 后续更新

以后每次在 Portfolio Library 里重新生成并下载新的 snapshot 后，可以用新的文件覆盖本地站点目录，再运行：

```bash
cd path/to/your/site-folder
git status
git add .
git commit -m "Update portfolio snapshot"
git push
```

如果 `git commit` 提示没有变化，说明这次导出的内容和线上版本相同，可以不用 push。

### 从 GitHub 拉取仓库后更新

```bash
git clone https://github.com/YOUR_NAME/YOUR_REPO.git
cd YOUR_REPO
```

把新 snapshot 解压后的所有文件复制到这个仓库目录，覆盖旧文件，然后执行：

```bash
git add .
git commit -m "Update portfolio snapshot"
git push
```

## Netlify 部署

1. 登录 Netlify。
2. 选择 `Add new site -> Deploy manually`。
3. 解压本 zip。
4. 把整个解压后的目录拖到 Netlify 的上传区域。
5. 不需要构建命令，发布目录就是当前目录。
6. 发布完成后，Netlify 会给出一个可访问的网址。

## Vercel 部署

1. 登录 Vercel。
2. 新建项目并导入包含本快照目录的仓库。
3. Framework Preset 选择 `Other`。
4. Build Command 留空。
5. Output Directory 使用当前目录。
6. 发布后访问 Vercel 生成的网址。

## 普通静态服务器部署

1. 将整个目录上传到服务器的静态网站根目录。
2. 确认服务器可以直接访问 `index.html`。
3. 确认 `data/` 和 `media/` 没有被服务器规则屏蔽。
4. 如果媒体文件无法显示，优先检查目录结构是否完整上传。

## 导出摘要

- 导出作品数：{work_count}
- 导出资产数：{asset_count}
- 警告数：{warning_count}
- 错误数：{error_count}
"""


def write_readme(output_dir, schema, report):
    profile = schema.get("profile", {})
    work_count = report.get("exported_works_count", len(schema.get("works", [])))
    asset_count = report.get("exported_assets_count", 0)
    title = profile.get("display_name") or "Portfolio Gallery"
    content = build_readme_content(
        title=title,
        work_count=work_count,
        asset_count=asset_count,
        warning_count=len(report.get("warnings", [])),
        error_count=len(report.get("errors", [])),
    )
    (Path(output_dir) / "README.md").write_text(content, encoding="utf-8")
    return
    content = f"""# {title} 静态主页快照

这是 Portfolio Library 导出的完整静态站点目录。它不是单个 HTML 文件，而是一整套可以部署到静态托管平台的主页快照。

## 目录内容

- `index.html`：公开主页入口。
- `styles.css`：主页样式文件。
- `main.js`：主页交互逻辑。
- `data/*.json`：公开导出的个人信息、作品、主页配置和标签数据。
- `media/*`：公开主页使用的媒体副本。
- `publish_report.json`：本地发布检查报告。
- `README.md`：当前说明文件。

## 本地预览

可以直接双击打开 `index.html`。如果浏览器限制本地文件加载，建议在当前目录启动一个本地静态服务器：

```bash
python -m http.server 8000
```

然后在浏览器访问：

```text
http://localhost:8000
```

## 部署说明

部署时必须上传整个目录，不能只上传 `index.html`。`index.html` 需要和 `styles.css`、`main.js`、`data/`、`media/` 保持在同一层级，否则页面样式、作品数据或图片/视频/音频会丢失。

### 部署到 GitHub Pages

1. 新建一个 GitHub 仓库。
2. 把本目录中的所有文件和文件夹上传到仓库根目录，至少包括 `index.html`、`styles.css`、`main.js`、`data/`、`media/`、`publish_report.json` 和 `README.md`。
3. 在仓库设置中打开 `Settings -> Pages`。
4. Source 选择 `Deploy from a branch`。
5. Branch 选择 `main`，目录选择 `/root`。
6. 保存后等待 GitHub Pages 构建完成。
7. 打开 GitHub Pages 给出的访问地址。

### 部署到 Netlify

1. 登录 Netlify。
2. 选择 `Add new site -> Deploy manually`。
3. 把整个快照目录拖到 Netlify 的上传区域。
4. 不需要构建命令，发布目录就是当前目录。
5. 发布完成后，Netlify 会给出一个可访问的网址。

### 部署到 Vercel

1. 登录 Vercel。
2. 新建项目并导入包含本快照目录的仓库，或使用 Vercel CLI 上传。
3. Framework Preset 选择 `Other`。
4. Build Command 留空。
5. Output Directory 使用当前目录。
6. 发布后访问 Vercel 生成的网址。

### 部署到普通静态服务器

1. 将整个目录上传到服务器的静态网站根目录。
2. 确认服务器可以直接访问 `index.html`。
3. 确认 `data/` 和 `media/` 没有被服务器规则屏蔽。
4. 如果媒体文件无法显示，优先检查目录结构是否完整上传。

## 导出摘要

- 导出作品数：{work_count}
- 导出资产数：{asset_count}
- 警告数：{len(report.get("warnings", []))}
- 错误数：{len(report.get("errors", []))}
"""
    (Path(output_dir) / "README.md").write_text(content, encoding="utf-8")


def snapshot_zip_path(snapshot_id):
    package_dir = EXPORT_ROOT / "packages"
    return package_dir / f"snapshot-{snapshot_id}.zip"


def create_snapshot_zip(snapshot_id, output_dir, snapshot_name=None):
    output_dir = Path(output_dir).resolve()
    ensure_within_exports(output_dir)
    if not output_dir.exists() or not output_dir.is_dir():
        raise FileNotFoundError("snapshot output directory does not exist")
    ensure_readme_exists(output_dir, snapshot_name)

    zip_path = snapshot_zip_path(snapshot_id)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()

    root_name = safe_package_name(snapshot_name or f"snapshot-{snapshot_id}")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for root, _dirs, files in os.walk(output_dir):
            for name in files:
                path = Path(root) / name
                if path.resolve() == zip_path.resolve():
                    continue
                rel = path.relative_to(output_dir)
                archive.write(path, Path(root_name) / rel)
    return zip_path


def ensure_readme_exists(output_dir, snapshot_name=None):
    readme_path = Path(output_dir) / "README.md"
    if readme_path.exists():
        pass
    title = snapshot_name or "Portfolio Gallery snapshot"
    readme_path.write_text(build_readme_content(title=title), encoding="utf-8")
    return
    readme_path.write_text(
        f"""# {title}

这是 Portfolio Library 导出的完整静态站点快照。

可以直接打开 `index.html`，也可以在当前目录运行：

```bash
python -m http.server 8000
```

然后访问 `http://localhost:8000`。

部署时请上传整个目录，不要只上传 `index.html`。`styles.css`、`main.js`、`data/`、`media/`、`publish_report.json` 必须和 `index.html` 保持相对路径不变。
""",
        encoding="utf-8",
    )


def safe_package_name(value):
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip()).strip(".-")
    return name[:80] or "portfolio-gallery-snapshot"


def scan_text_file(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def finalize_report(output_dir, report):
    local_matches = []
    api_key_matches = []
    large_matches = []
    sensitive_matches = []
    for root, _dirs, files in os.walk(output_dir):
        for name in files:
            path = Path(root) / name
            rel = path.relative_to(output_dir).as_posix()
            lower = name.lower()
            if path.suffix.lower() in SENSITIVE_SUFFIXES or any(part in lower for part in SENSITIVE_NAME_PARTS):
                sensitive_matches.append(rel)
            size = path.stat().st_size
            if size > LARGE_FILE_THRESHOLD_MB * 1024 * 1024:
                large_matches.append({"path": rel, "size_mb": round(size / 1024 / 1024, 2)})
            if path.suffix.lower() in {".html", ".json", ".js", ".css"}:
                text = scan_text_file(path)
                for pattern in LOCAL_PATH_PATTERNS:
                    if pattern.search(text):
                        local_matches.append({"path": rel, "pattern": pattern.pattern})
                for pattern in API_KEY_PATTERNS:
                    if pattern.search(text):
                        api_key_matches.append({"path": rel, "pattern": pattern.pattern})

    report["local_path_leak_check"] = {"passed": not local_matches, "matches": local_matches}
    report["large_file_check"] = {"passed": not large_matches, "threshold_mb": LARGE_FILE_THRESHOLD_MB, "matches": large_matches}
    report["sensitive_file_check"] = {"passed": not sensitive_matches, "matches": sensitive_matches}
    report["api_key_pattern_check"] = {"passed": not api_key_matches, "matches": api_key_matches}

    for check_key, check_type in (
        ("local_path_leak_check", "local_path_leak"),
        ("sensitive_file_check", "sensitive_file_in_publish"),
        ("api_key_pattern_check", "api_key_pattern"),
    ):
        if not report[check_key]["passed"]:
            report["errors"].append(
                {
                    "check_type": check_type,
                    "severity": "error",
                    "message": f"{check_type} failed",
                }
            )
    if not report["large_file_check"]["passed"]:
        report["warnings"].append(
            {
                "check_type": "large_file",
                "severity": "warning",
                "message": f"Some exported files exceed {LARGE_FILE_THRESHOLD_MB}MB.",
            }
        )


def report_summary(report):
    return {
        "works": report.get("exported_works_count", 0),
        "assets": report.get("exported_assets_count", 0),
        "warnings": len(report.get("warnings", [])),
        "errors": len(report.get("errors", [])),
    }


def report_items(report):
    items = []
    for severity in ("warning", "error"):
        for item in report.get(f"{severity}s", []):
            normalized = dict(item)
            normalized.setdefault("severity", severity)
            normalized.setdefault("check_type", "publish_check")
            normalized.setdefault("message", "")
            items.append(normalized)
    return items


def generate_publish_site(user_id, request_payload):
    template_id = request_payload.get("template_id") or "creator_gallery"
    if template_id not in TEMPLATE_REGISTRY:
        raise ValueError(f"unknown template_id: {template_id}")

    schema, report, media_manifest = build_portfolio_library_schema(user_id, request_payload)
    execute(
        """INSERT INTO publish_snapshot
           (user_id, snapshot_name, homepage_config, public_data, status)
           VALUES (%s, %s, %s, %s, 'draft')""",
        (
            user_id,
            request_payload.get("snapshot_name") or "creator-gallery",
            json.dumps(schema.get("homepage", {}), ensure_ascii=False),
            json.dumps(schema, ensure_ascii=False),
        ),
    )
    snapshot_id = query_one("SELECT LAST_INSERT_ID() AS id")["id"]
    output_dir = EXPORT_ROOT / f"snapshot-{snapshot_id}"
    adapter = CreatorGalleryAdapter()
    adapter.render(output_dir, schema, report, media_manifest)
    size = directory_size(output_dir)
    execute(
        "UPDATE publish_snapshot SET output_dir = %s, package_size_bytes = %s, status = 'generated', public_data = %s WHERE snapshot_id = %s",
        (str(output_dir), size, json.dumps(schema, ensure_ascii=False), snapshot_id),
    )
    for item in report_items(report):
        execute(
            """INSERT INTO publish_report
               (snapshot_id, check_type, severity, message, related_table, related_id)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                snapshot_id,
                item.get("check_type"),
                item.get("severity"),
                item.get("message"),
                item.get("related_table"),
                item.get("related_id"),
            ),
        )
    snapshot = query_one("SELECT * FROM publish_snapshot WHERE snapshot_id = %s", (snapshot_id,))
    return {"snapshot": snapshot, "schema": schema, "report": report}


def directory_size(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total
