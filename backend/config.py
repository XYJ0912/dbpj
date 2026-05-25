# ============================================================
# config.py — 全局配置
# ============================================================
import os


class Config:
    """应用配置，优先读取环境变量，否则使用本地开发默认值"""

    # ── MySQL 连接 ──
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Xiongyingjie@mysql")
    # New deployments should use "portfolio_library".
    # The legacy default remains "creator_workspace" so existing local demos keep running.
    DB_NAME = os.getenv("DB_NAME", "creator_workspace")
    DB_CHARSET = "utf8mb4"

    # ── JWT 认证 ──
    JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production-portfolio-library-secret")
    JWT_EXPIRE_HOURS = 24

    # ── 其它 ──
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    PAGE_SIZE_DEFAULT = 20
    PAGE_SIZE_MAX = 100
    UPLOAD_ROOT = os.getenv("UPLOAD_ROOT")
    EXPORT_ROOT = os.getenv("EXPORT_ROOT")
