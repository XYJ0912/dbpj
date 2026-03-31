# ============================================================
# app.py — 垂直兴趣社区后端 主入口
# ============================================================
# Flask 应用工厂 + Blueprint 注册
#
# 启动方式：
#   开发环境：python app.py
#   生产环境：gunicorn -w 4 -b 0.0.0.0:5000 app:app
#
# 环境变量（可选，有默认值）：
#   DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
#   JWT_SECRET, FLASK_DEBUG
# ============================================================

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
import db


def create_app():
    """Flask 应用工厂"""

    app = Flask(__name__)

    # ── 加载配置 ──
    app.config.from_mapping(
        DB_HOST=Config.DB_HOST,
        DB_PORT=Config.DB_PORT,
        DB_USER=Config.DB_USER,
        DB_PASSWORD=Config.DB_PASSWORD,
        DB_NAME=Config.DB_NAME,
        DB_CHARSET=Config.DB_CHARSET,
        JWT_SECRET=Config.JWT_SECRET,
        JWT_EXPIRE_HOURS=Config.JWT_EXPIRE_HOURS,
        PAGE_SIZE_DEFAULT=Config.PAGE_SIZE_DEFAULT,
        PAGE_SIZE_MAX=Config.PAGE_SIZE_MAX,
    )

    # ── 跨域支持（开发阶段允许所有来源）──
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── 初始化数据库连接管理 ──
    db.init_app(app)

    # ── 注册 Blueprint ──
    from routes.user import bp as user_bp
    from routes.content import bp as content_bp
    from routes.social import bp as social_bp
    from routes.authorization import bp as auth_bp
    from routes.homepage import bp as homepage_bp
    from routes.admin import bp as admin_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(content_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(homepage_bp)
    app.register_blueprint(admin_bp)

    # ── 首页（健康检查）──
    @app.get("/")
    def index():
        return jsonify({
            "name": "垂直兴趣社区 API",
            "version": "1.0.0",
            "status": "running",
            "docs": "查看 README.md 获取完整 API 文档",
        })

    # ── API 路由列表（开发调试用）──
    @app.get("/api")
    def api_index():
        """列出所有已注册的 API 路由"""
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint == "static":
                continue
            routes.append({
                "endpoint": rule.endpoint,
                "methods": sorted(rule.methods - {"HEAD", "OPTIONS"}),
                "path": rule.rule,
            })
        routes.sort(key=lambda r: r["path"])
        return jsonify({"total": len(routes), "routes": routes})

    # ── 全局错误处理 ──
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"code": 404, "msg": "接口不存在"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"code": 405, "msg": "请求方法不允许"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"code": 500, "msg": "服务器内部错误"}), 500

    return app


# ── 直接运行 ──
app = create_app()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  垂直兴趣社区 API 服务")
    print("  http://127.0.0.1:5000")
    print("  API 路由列表: http://127.0.0.1:5000/api")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
