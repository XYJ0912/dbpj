from __future__ import annotations

import math
import os
import struct
import wave
from pathlib import Path

import pymysql
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "demo_assets"
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "Xiongyingjie@mysql"),
    "database": os.getenv("DB_NAME", "creator_workspace"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}


def make_dirs() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)


def save_art_image(path: Path, palette: tuple[tuple[int, int, int], ...], title: str, seed: int) -> None:
    width, height = 1200, 900
    image = Image.new("RGB", (width, height), palette[0])
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            nx = x / width
            ny = y / height
            wave_a = math.sin((nx * 8.0 + seed) + math.cos(ny * 7.0))
            wave_b = math.cos((ny * 9.0 - seed) + math.sin(nx * 5.0))
            t = (wave_a + wave_b + 2.0) / 4.0
            c1 = palette[int(t * (len(palette) - 1))]
            c2 = palette[min(len(palette) - 1, int((1 - t) * (len(palette) - 1)))]
            vignette = 1 - min(0.46, math.dist((nx, ny), (0.5, 0.48)) * 0.72)
            pixels[x, y] = tuple(max(0, min(255, int((a * t + b * (1 - t)) * vignette))) for a, b in zip(c1, c2))

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(18):
        x = int((math.sin(seed + i * 1.7) * 0.42 + 0.5) * width)
        y = int((math.cos(seed + i * 1.1) * 0.38 + 0.5) * height)
        radius = 90 + (i % 5) * 36
        color = (*palette[(i + seed) % len(palette)], 36)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    image = Image.alpha_composite(image.convert("RGBA"), overlay).filter(ImageFilter.SMOOTH_MORE)

    draw = ImageDraw.Draw(image)
    draw.rectangle((70, 70, width - 70, height - 70), outline=(255, 255, 255, 86), width=2)
    draw.text((94, height - 138), title, fill=(255, 255, 255, 224))
    image.convert("RGB").save(path, quality=92)


def save_audio(path: Path) -> None:
    sample_rate = 44100
    duration = 5
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        for i in range(sample_rate * duration):
            t = i / sample_rate
            value = 0.38 * math.sin(2 * math.pi * 220 * t) + 0.18 * math.sin(2 * math.pi * 330 * t)
            envelope = min(1, t / 0.3, (duration - t) / 0.7)
            handle.writeframes(struct.pack("<h", int(32767 * value * max(0, envelope))))


def write_demo_files() -> dict[str, Path]:
    make_dirs()
    files = {
        "night": ASSET_DIR / "night-patrol-cover.png",
        "spring": ASSET_DIR / "spring-archive-cover.png",
        "portrait": ASSET_DIR / "portrait-practice-cover.png",
        "restricted": ASSET_DIR / "restricted-reference.png",
        "audio": ASSET_DIR / "ambient-loop.wav",
        "document": ASSET_DIR / "lookbook-notes.md",
        "video": ASSET_DIR / "process-reel.mp4",
        "other": ASSET_DIR / "palette-swatches.json",
    }
    save_art_image(files["night"], ((12, 18, 38), (32, 92, 122), (214, 78, 104), (246, 205, 130)), "Night Patrol", 4)
    save_art_image(files["spring"], ((238, 213, 205), (197, 223, 191), (124, 166, 140), (96, 90, 118)), "Spring Archive", 8)
    save_art_image(files["portrait"], ((30, 30, 38), (91, 65, 98), (191, 119, 118), (242, 200, 153)), "Portrait Practice", 12)
    save_art_image(files["restricted"], ((42, 35, 34), (92, 54, 50), (168, 111, 89), (228, 189, 144)), "Restricted Reference", 16)
    save_audio(files["audio"])
    files["document"].write_text(
        "# Lookbook Notes\n\nA short markdown document used as a public document asset example.\n\n- palette references\n- shooting notes\n- licensing checklist\n",
        encoding="utf-8",
    )
    files["video"].write_bytes(b"Demo process reel placeholder. Replace with a real MP4 for production preview.\n")
    files["other"].write_text('{"palette":["#0c1226","#205c7a","#d64e68","#f6cd82"]}\n', encoding="utf-8")
    return files


def upsert_license(cursor, asset_id: int, status: str, allow_public: bool) -> None:
    cursor.execute(
        """INSERT INTO asset_license_note
           (asset_id, authorization_status, source_name, license_note, allow_public_display, attribution_required)
           VALUES (%s, %s, 'demo seed', 'Generated local demo asset for coursework.', %s, FALSE)
           ON DUPLICATE KEY UPDATE
             authorization_status = VALUES(authorization_status),
             source_name = VALUES(source_name),
             license_note = VALUES(license_note),
             allow_public_display = VALUES(allow_public_display),
             attribution_required = VALUES(attribution_required)""",
        (asset_id, status, allow_public),
    )


def upsert_asset(cursor, user_id: int, name: str, media_type: str, path: Path, status: str, allow_public: bool) -> int:
    mime = {
        "image": "image/png",
        "audio": "audio/wav",
        "document": "text/markdown",
        "video": "video/mp4",
        "other": "application/json",
    }[media_type]
    cursor.execute(
        """SELECT asset_id FROM media_asset WHERE owner_id = %s AND asset_name = %s""",
        (user_id, name),
    )
    row = cursor.fetchone()
    if row:
        asset_id = row["asset_id"]
        cursor.execute(
            """UPDATE media_asset
                  SET media_type = %s,
                      local_path = %s,
                      public_export_path = NULL,
                      thumbnail_path = NULL,
                      file_size = %s,
                      mime_type = %s,
                      visibility = 'public',
                      import_status = 'active',
                      file_exists = TRUE,
                      last_checked_at = NOW()
                WHERE asset_id = %s""",
            (media_type, str(path), path.stat().st_size, mime, asset_id),
        )
    else:
        cursor.execute(
            """INSERT INTO media_asset
               (owner_id, asset_name, media_type, local_path, file_size, mime_type,
                visibility, import_status, file_exists, last_checked_at)
               VALUES (%s, %s, %s, %s, %s, %s, 'public', 'active', TRUE, NOW())""",
            (user_id, name, media_type, str(path), path.stat().st_size, mime),
        )
        cursor.execute("SELECT LAST_INSERT_ID() AS asset_id")
        asset_id = cursor.fetchone()["asset_id"]
    upsert_license(cursor, asset_id, status, allow_public)
    return asset_id


def attach(cursor, work_id: int, asset_id: int, role: str, order: int) -> None:
    cursor.execute(
        """INSERT INTO work_media (work_id, asset_id, role, display_order, is_public)
           VALUES (%s, %s, %s, %s, TRUE)
           ON DUPLICATE KEY UPDATE role = VALUES(role), display_order = VALUES(display_order), is_public = TRUE""",
        (work_id, asset_id, role, order),
    )


def main() -> None:
    files = write_demo_files()
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cursor:
        cursor.execute("SELECT user_id FROM user_account WHERE username = 'demo'")
        user = cursor.fetchone()
        if not user:
            raise RuntimeError("demo user not found; import the local portfolio schema first")
        user_id = user["user_id"]

        assets = {
            "night": upsert_asset(cursor, user_id, "night-patrol-cover.png", "image", files["night"], "original", True),
            "spring": upsert_asset(cursor, user_id, "spring-archive-cover.png", "image", files["spring"], "original", True),
            "portrait": upsert_asset(cursor, user_id, "portrait-practice-cover.png", "image", files["portrait"], "licensed", True),
            "restricted": upsert_asset(cursor, user_id, "restricted-reference.png", "image", files["restricted"], "restricted", False),
            "audio": upsert_asset(cursor, user_id, "ambient-loop.wav", "audio", files["audio"], "original", True),
            "document": upsert_asset(cursor, user_id, "lookbook-notes.md", "document", files["document"], "original", True),
            "video": upsert_asset(cursor, user_id, "process-reel.mp4", "video", files["video"], "licensed", True),
            "other": upsert_asset(cursor, user_id, "palette-swatches.json", "other", files["other"], "original", True),
        }

        for title, key in (("Night Patrol", "night"), ("Spring Archive", "spring"), ("Portrait Practice", "portrait")):
            cursor.execute("SELECT work_id FROM work WHERE owner_id = %s AND title = %s", (user_id, title))
            work = cursor.fetchone()
            if work:
                attach(cursor, work["work_id"], assets[key], "cover", 1)
                cursor.execute("UPDATE work SET cover_asset_id = %s WHERE work_id = %s", (assets[key], work["work_id"]))

        cursor.execute("SELECT work_id FROM work WHERE owner_id = %s AND title = 'Spring Archive'", (user_id,))
        spring = cursor.fetchone()
        if spring:
            attach(cursor, spring["work_id"], assets["document"], "attachment", 2)
            attach(cursor, spring["work_id"], assets["audio"], "process", 3)
            attach(cursor, spring["work_id"], assets["video"], "process", 4)
            attach(cursor, spring["work_id"], assets["other"], "reference", 5)

    conn.close()
    print(f"Seeded demo assets in {ASSET_DIR}")


if __name__ == "__main__":
    main()
