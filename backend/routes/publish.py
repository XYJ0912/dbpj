import os
import subprocess
import time
import shutil
from pathlib import Path

from flask import Blueprint, abort, g, redirect, request, send_file, send_from_directory

from auth import login_required
from creator_publish import (
    EXPORT_ROOT,
    TEMPLATE_REGISTRY,
    build_portfolio_library_schema,
    create_snapshot_zip,
    generate_publish_site,
    parse_json,
    report_items,
    report_summary,
    safe_package_name,
    snapshot_zip_path,
)
from db import execute, query, query_one
from response import success


bp = Blueprint("publish", __name__, url_prefix="/api/publish")


def snapshot_site_url(snapshot_id):
    return f"{request.host_url.rstrip('/')}/api/publish/snapshots/{snapshot_id}/site/"


def snapshot_file_url(snapshot_id, filename):
    return f"{request.host_url.rstrip('/')}/api/publish/snapshots/{snapshot_id}/site/{filename}"


def snapshot_report_url(snapshot_id):
    return f"{request.host_url.rstrip('/')}/api/publish/snapshots/{snapshot_id}/report"


def snapshot_download_url(snapshot_id):
    return f"{request.host_url.rstrip('/')}/api/publish/snapshots/{snapshot_id}/download"


def snapshot_git_deploy_url(snapshot_id):
    return f"{request.host_url.rstrip('/')}/api/publish/snapshots/{snapshot_id}/git-deploy"


def run_git(args, cwd, timeout=120):
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    completed = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    output = (completed.stdout or "").strip()
    error_output = (completed.stderr or "").strip()
    if completed.returncode != 0:
        details = error_output or output or f"git {' '.join(args)} failed"
        raise RuntimeError(details[:1000])
    return output or error_output


def ensure_git_available():
    if not shutil.which("git"):
        raise RuntimeError("Git was not found. Install Git for Windows first, then restart Portfolio Library.")


def remove_deploy_contents(target):
    for item in target.iterdir():
        if item.name == ".git":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def copy_snapshot_to_repo(output_dir, deploy_dir):
    remove_deploy_contents(deploy_dir)
    for item in output_dir.iterdir():
        target = deploy_dir / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def deploy_dir_for(repo_url):
    name = safe_package_name(str(repo_url).rstrip("/").rsplit("/", 1)[-1].replace(".git", "") or "portfolio-site")
    return EXPORT_ROOT / "git-deploy" / name


def prepare_git_repo(repo_url, branch):
    deploy_dir = deploy_dir_for(repo_url)
    deploy_dir.parent.mkdir(parents=True, exist_ok=True)
    steps = []
    if (deploy_dir / ".git").exists():
        run_git(["remote", "set-url", "origin", repo_url], deploy_dir)
        steps.append("Updated local deploy repository remote.")
    else:
        if deploy_dir.exists():
            shutil.rmtree(deploy_dir)
        deploy_dir.mkdir(parents=True)
        try:
            run_git(["clone", "--branch", branch, repo_url, str(deploy_dir)], deploy_dir.parent, timeout=180)
            steps.append("Cloned existing remote repository.")
        except RuntimeError:
            shutil.rmtree(deploy_dir)
            deploy_dir.mkdir(parents=True)
            run_git(["init"], deploy_dir)
            run_git(["branch", "-M", branch], deploy_dir)
            run_git(["remote", "add", "origin", repo_url], deploy_dir)
            steps.append("Initialized local deploy repository.")
    run_git(["checkout", "-B", branch], deploy_dir)
    return deploy_dir, steps


@bp.get("/templates")
@login_required
def templates():
    return success(list(TEMPLATE_REGISTRY.values()))


@bp.post("/check")
@login_required
def check():
    payload = request.get_json(silent=True) or {}
    schema, report, _media_manifest = build_portfolio_library_schema(g.user_id, payload)
    return success({"schema": schema, "report": {"summary": report_summary(report), "items": report_items(report), **report}})


@bp.get("/homepage")
@login_required
def homepage():
    row = query_one(
        "SELECT display_name, bio, avatar_url, homepage_config FROM creator_profile WHERE user_id = %s",
        (g.user_id,),
    )
    config = parse_json(row.get("homepage_config") if row else None, {})
    if row:
        config.setdefault("display_name", row.get("display_name") or "")
        config.setdefault("bio", row.get("bio") or "")
        config.setdefault("avatar_url", row.get("avatar_url") or "")
    return success(config)


@bp.patch("/homepage")
@login_required
def update_homepage():
    payload = request.get_json(silent=True) or {}
    row = query_one(
        "SELECT display_name, bio, avatar_url, homepage_config FROM creator_profile WHERE user_id = %s",
        (g.user_id,),
    )
    config = parse_json(row.get("homepage_config") if row else None, {})
    for field in (
        "template_id",
        "theme",
        "accent_color",
        "featured_work_ids",
        "creator_tags",
        "contact_links",
        "license_text",
        "display_name",
        "bio",
        "avatar_asset_id",
        "avatar_url",
    ):
        if field in payload:
            config[field] = payload[field]
    config.setdefault("template_id", "creator_gallery")
    config.setdefault("theme", "warm_gallery")
    config.setdefault("accent_color", "#8fb8a8")
    config.setdefault("featured_work_ids", [])
    config.setdefault("creator_tags", [])
    config.setdefault("contact_links", [])
    config.setdefault("license_text", "Unless otherwise noted, works are for portfolio display only.")
    execute(
        "UPDATE creator_profile SET display_name = %s, bio = %s, avatar_url = %s, homepage_config = %s WHERE user_id = %s",
        (
            config.get("display_name") or row.get("display_name") if row else None,
            config.get("bio") or row.get("bio") if row else None,
            config.get("avatar_url") or row.get("avatar_url") if row else None,
            parse_json_string(config),
            g.user_id,
        ),
    )
    return success(config, msg="homepage config saved")


@bp.post("/generate")
@login_required
def generate():
    req = request.get_json(silent=True) or {}
    result = generate_publish_site(g.user_id, req)
    snapshot = result["snapshot"]
    report = result["report"]
    snapshot_id = snapshot["snapshot_id"]
    data = {
        "ok": True,
        "snapshot": {
            **snapshot,
            "site_url": snapshot_site_url(snapshot_id),
            "index_url": snapshot_site_url(snapshot_id),
            "report_url": snapshot_report_url(snapshot_id),
            "download_url": snapshot_download_url(snapshot_id),
        },
        "publish_dir": snapshot.get("output_dir"),
        "index_path": str(Path(snapshot["output_dir"]) / "index.html"),
        "report_path": str(Path(snapshot["output_dir"]) / "publish_report.json"),
        "exported_works_count": report.get("exported_works_count", 0),
        "exported_assets_count": report.get("exported_assets_count", 0),
        "warnings_count": len(report.get("warnings", [])),
        "errors_count": len(report.get("errors", [])),
        "report": {"summary": report_summary(report), "items": report_items(report), **report},
    }
    return success(data, msg="creator gallery site generated")


@bp.post("/snapshot")
@login_required
def snapshot():
    return generate()


@bp.get("/snapshots")
@login_required
def snapshots():
    rows = query(
        "SELECT * FROM v_publish_report_summary WHERE user_id = %s ORDER BY created_at DESC, snapshot_id DESC",
        (g.user_id,),
    )
    for row in rows:
        row["site_url"] = snapshot_site_url(row["snapshot_id"])
        row["report_url"] = snapshot_report_url(row["snapshot_id"])
        row["download_url"] = snapshot_download_url(row["snapshot_id"])
        row["git_deploy_url"] = snapshot_git_deploy_url(row["snapshot_id"])
    return success(rows)


@bp.patch("/snapshots/<int:snapshot_id>")
@login_required
def rename_snapshot(snapshot_id):
    payload = request.get_json(silent=True) or {}
    name = (payload.get("snapshot_name") or "").strip()
    if not name:
        return success(None, msg="snapshot_name is required")
    execute(
        "UPDATE publish_snapshot SET snapshot_name = %s WHERE user_id = %s AND snapshot_id = %s",
        (name[:200], g.user_id, snapshot_id),
    )
    row = query_one(
        "SELECT * FROM publish_snapshot WHERE user_id = %s AND snapshot_id = %s",
        (g.user_id, snapshot_id),
    )
    if not row:
        abort(404)
    row["site_url"] = snapshot_site_url(snapshot_id)
    row["report_url"] = snapshot_report_url(snapshot_id)
    row["download_url"] = snapshot_download_url(snapshot_id)
    row["git_deploy_url"] = snapshot_git_deploy_url(snapshot_id)
    return success(row, msg="snapshot renamed")


@bp.get("/snapshots/<int:snapshot_id>/report")
@login_required
def snapshot_report(snapshot_id):
    snapshot = query_one(
        "SELECT * FROM publish_snapshot WHERE user_id = %s AND snapshot_id = %s",
        (g.user_id, snapshot_id),
    )
    if not snapshot:
        abort(404)
    rows = query(
        """SELECT check_type, severity, message, related_table, related_id, created_at
             FROM publish_report
            WHERE snapshot_id = %s
            ORDER BY FIELD(severity, 'error', 'warning', 'info'), report_id""",
        (snapshot_id,),
    )
    warnings = [row for row in rows if row.get("severity") == "warning"]
    errors = [row for row in rows if row.get("severity") == "error"]
    public_data = parse_json(snapshot.get("public_data"), {})
    report = {
        "snapshot_id": snapshot_id,
        "snapshot_name": snapshot.get("snapshot_name"),
        "output_dir": snapshot.get("output_dir"),
        "summary": {
            "works": len(public_data.get("works", [])),
            "assets": sum(len(work.get("assets", [])) for work in public_data.get("works", [])),
            "warnings": len(warnings),
            "errors": len(errors),
        },
        "items": rows,
        "warnings": warnings,
        "errors": errors,
    }
    return success({"report": report})


@bp.get("/snapshots/<int:snapshot_id>/download")
@login_required
def download_snapshot(snapshot_id):
    snapshot = query_one(
        "SELECT * FROM publish_snapshot WHERE user_id = %s AND snapshot_id = %s AND status = 'generated'",
        (g.user_id, snapshot_id),
    )
    if not snapshot or not snapshot.get("output_dir"):
        abort(404)
    output_dir = Path(snapshot["output_dir"]).resolve()
    if EXPORT_ROOT.resolve() != output_dir and EXPORT_ROOT.resolve() not in output_dir.parents:
        abort(404)
    if not output_dir.exists() or not output_dir.is_dir():
        abort(404)
    zip_path = create_snapshot_zip(snapshot_id, output_dir, snapshot.get("snapshot_name"))
    download_name = f"{safe_package_name(snapshot.get('snapshot_name') or f'snapshot-{snapshot_id}')}.zip"
    return send_file(zip_path, as_attachment=True, download_name=download_name)


@bp.post("/snapshots/<int:snapshot_id>/git-deploy")
@login_required
def git_deploy_snapshot(snapshot_id):
    payload = request.get_json(silent=True) or {}
    repo_url = (payload.get("repo_url") or "").strip()
    branch = (payload.get("branch") or "main").strip() or "main"
    commit_message = (payload.get("commit_message") or "Update portfolio snapshot").strip() or "Update portfolio snapshot"
    if not repo_url:
        return success({"ok": False, "steps": [], "error": "repo_url is required"}, msg="repo_url is required")

    snapshot = query_one(
        "SELECT * FROM publish_snapshot WHERE user_id = %s AND snapshot_id = %s AND status = 'generated'",
        (g.user_id, snapshot_id),
    )
    if not snapshot or not snapshot.get("output_dir"):
        abort(404)
    output_dir = Path(snapshot["output_dir"]).resolve()
    exports_root = EXPORT_ROOT.resolve()
    if exports_root != output_dir and exports_root not in output_dir.parents:
        abort(404)
    if not output_dir.exists() or not output_dir.is_dir():
        abort(404)

    started = time.time()
    steps = []
    try:
        ensure_git_available()
        deploy_dir, prepare_steps = prepare_git_repo(repo_url, branch)
        steps.extend(prepare_steps)
        copy_snapshot_to_repo(output_dir, deploy_dir)
        steps.append("Copied snapshot files into local deploy repository.")
        run_git(["add", "."], deploy_dir)
        status = run_git(["status", "--porcelain"], deploy_dir)
        if not status:
            return success(
                {
                    "ok": True,
                    "deployed": False,
                    "no_changes": True,
                    "deploy_dir": str(deploy_dir),
                    "steps": [*steps, "No file changes to commit."],
                    "duration_seconds": round(time.time() - started, 2),
                },
                msg="no changes to deploy",
            )
        run_git(["commit", "-m", commit_message[:200]], deploy_dir)
        steps.append("Committed snapshot files.")
        run_git(["push", "-u", "origin", branch], deploy_dir, timeout=180)
        steps.append(f"Pushed to {branch}.")
        return success(
            {
                "ok": True,
                "deployed": True,
                "deploy_dir": str(deploy_dir),
                "steps": steps,
                "pages_hint": "Enable GitHub Pages from branch main/root if this is the first deployment.",
                "duration_seconds": round(time.time() - started, 2),
            },
            msg="snapshot deployed with git",
        )
    except RuntimeError as exc:
        return success(
            {
                "ok": False,
                "deployed": False,
                "deploy_dir": str(deploy_dir_for(repo_url)),
                "steps": steps,
                "error": str(exc),
                "human_hint": "If this is a private GitHub repository or first push, sign in through Git Credential Manager or GitHub Desktop, then try again.",
            },
            msg="git deploy failed",
        )


@bp.delete("/snapshots/<int:snapshot_id>")
@login_required
def delete_snapshot(snapshot_id):
    row = query_one(
        "SELECT output_dir FROM publish_snapshot WHERE user_id = %s AND snapshot_id = %s",
        (g.user_id, snapshot_id),
    )
    if not row:
        abort(404)
    output_dir = Path(row.get("output_dir") or "").resolve()
    exports_root = EXPORT_ROOT.resolve()
    if row.get("output_dir") and output_dir.exists() and output_dir != exports_root and exports_root in output_dir.parents:
        shutil.rmtree(output_dir)
    zip_path = snapshot_zip_path(snapshot_id)
    if zip_path.exists() and EXPORT_ROOT.resolve() in zip_path.resolve().parents:
        zip_path.unlink()
    execute("DELETE FROM publish_snapshot WHERE user_id = %s AND snapshot_id = %s", (g.user_id, snapshot_id))
    return success({"snapshot_id": snapshot_id}, msg="snapshot deleted")


@bp.get("/snapshots/<int:snapshot_id>/site")
def snapshot_site(snapshot_id):
    return redirect(snapshot_site_url(snapshot_id), code=302)


@bp.get("/snapshots/<int:snapshot_id>/site/")
def snapshot_site_index(snapshot_id):
    return snapshot_file(snapshot_id, "index.html")


@bp.get("/snapshots/<int:snapshot_id>/site/<path:filename>")
def snapshot_file(snapshot_id, filename):
    row = query_one(
        "SELECT output_dir FROM publish_snapshot WHERE snapshot_id = %s AND status = 'generated'",
        (snapshot_id,),
    )
    if not row or not row.get("output_dir"):
        abort(404)
    output_dir = Path(row["output_dir"]).resolve()
    if EXPORT_ROOT.resolve() != output_dir and EXPORT_ROOT.resolve() not in output_dir.parents:
        abort(404)
    target = (output_dir / filename).resolve()
    if output_dir != target and output_dir not in target.parents:
        abort(404)
    if not target.exists() or not target.is_file():
        abort(404)
    if filename == "index.html":
        return send_file(target)
    return send_from_directory(output_dir, filename)


def parse_json_string(value):
    import json

    return json.dumps(value, ensure_ascii=False)
