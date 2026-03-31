# ============================================================
# routes/homepage.py — 用户主页配置接口
# ============================================================

import copy
import json

from flask import Blueprint, request, g

from db import query, query_one, call_proc
from auth import login_required, optional_login
from response import success, error
from services import (
    fetch_active_tags_map,
    fetch_visible_content_map,
    normalize_id_list,
    parse_json_value,
)

bp = Blueprint("homepage", __name__, url_prefix="/api/homepage")


DEFAULT_TEMPLATES = [
    {"name": "default_two_column", "slot_count": 6, "description": "通用双栏主页"},
    {"name": "grid_mix", "slot_count": 4, "description": "图文混合网格"},
    {"name": "reading_room", "slot_count": 3, "description": "书单与长文展示"},
    {"name": "studio", "slot_count": 4, "description": "作品集工作室"},
    {"name": "stage", "slot_count": 4, "description": "返图与活动页"},
]


def _build_homepage_config_from_request(data):
    if isinstance(data.get("homepage_config"), dict):
        return copy.deepcopy(data["homepage_config"])

    components = []
    for component in data.get("components", []) or []:
        config_value = component.get("config") or component.get("config_json") or {}
        if isinstance(config_value, str):
            config_value = parse_json_value(config_value, {})

        position = component.get("position")
        if position is None and component.get("slot_position") is not None:
            position = {"slot_position": component.get("slot_position")}

        components.append(
            {
                "component_id": component.get("component_id"),
                "component_type": component.get("component_type"),
                "position": position,
                "z_index": component.get("z_index", component.get("display_order", 0)),
                "title": component.get("title"),
                "config": config_value,
            }
        )

    homepage_config = {
        "template": data.get("template") or {
            "name": data.get("template_name", "default_two_column"),
            "slot_count": data.get("slot_count", 6),
        },
        "theme": data.get("theme"),
        "background_url": data.get("background_url"),
        "layout": components,
    }
    return homepage_config


@bp.get("/<int:user_id>")
@optional_login
def get_homepage(user_id):
    raw = query_one(
        "SELECT * FROM v_user_homepage_raw WHERE user_id = %s",
        (user_id,),
    )
    if not raw:
        return error("用户主页不存在", http_status=404)

    homepage_config = parse_json_value(raw.get("homepage_config"), {"layout": []})
    template_config = parse_json_value(raw.get("template_config"), None)
    components = query(
        """SELECT *
             FROM v_user_homepage_component
            WHERE user_id = %s
            ORDER BY z_index, component_id""",
        (user_id,),
    )

    result = {
        "homepage_id": raw["homepage_id"],
        "user_id": raw["user_id"],
        "username": raw["username"],
        "theme": raw.get("theme"),
        "background_url": raw.get("background_url"),
        "template_config": template_config,
        "homepage_config": homepage_config,
        "created_at": raw["created_at"],
        "updated_at": raw["updated_at"],
        "components": [],
    }

    for row in components:
        component_config = parse_json_value(row.get("component_config"), {})
        tag_ids = normalize_id_list(component_config.get("tag_ids"))
        content_ids = normalize_id_list(component_config.get("content_ids"))

        active_tags = fetch_active_tags_map(tag_ids)
        visible_contents = fetch_visible_content_map(content_ids, g.user_id)

        if tag_ids:
            component_config["tag_ids"] = [tag_id for tag_id in tag_ids if tag_id in active_tags]
        if content_ids:
            component_config["content_ids"] = [
                content_id for content_id in content_ids if content_id in visible_contents
            ]

        result["components"].append(
            {
                "component_id": row["component_id"],
                "component_type": row["component_type"],
                "position": parse_json_value(row.get("position"), {}),
                "z_index": row["z_index"],
                "title": row["title"],
                "config": component_config,
                "resolved_tags": [active_tags[tag_id] for tag_id in component_config.get("tag_ids", [])],
                "resolved_contents": [
                    visible_contents[content_id]
                    for content_id in component_config.get("content_ids", [])
                ],
            }
        )

    return success(result)


@bp.put("")
@login_required
def save_homepage():
    data = request.get_json(silent=True) or {}
    homepage_config = _build_homepage_config_from_request(data)
    last_read_updated_at = data.get("last_read_updated_at")

    if "layout" not in homepage_config:
        return error("homepage_config 必须包含 layout")

    result = call_proc(
        "sp_save_homepage_config",
        [g.user_id, json.dumps(homepage_config, ensure_ascii=False), last_read_updated_at],
        2,
    )
    if result.get("out_0") != 0:
        return error(result.get("out_1") or "主页保存失败")
    return success(msg=result.get("out_1") or "主页配置已保存")


@bp.get("/templates")
def list_templates():
    return success(DEFAULT_TEMPLATES)
