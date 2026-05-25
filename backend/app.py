import os

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

    from routes.user import bp as user_bp
    from routes.assets import bp as assets_bp
    from routes.workspace import bp as workspace_bp
    from routes.publish import bp as publish_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(workspace_bp)
    app.register_blueprint(publish_bp)

    @app.get("/")
    def index():
        return jsonify({
            "name": "Portfolio Library API",
            "status": "running",
            "scope": "local asset library, works, publish checks",
        })

    @app.get("/api")
    def api_index():
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
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    print("\n" + "=" * 60)
    print("  Portfolio Library API")
    print(f"  http://127.0.0.1:{port}")
    print("  API 路由列表: http://127.0.0.1:5000/api")
    print("=" * 60 + "\n")
    app.run(host=host, port=port, debug=Config.DEBUG)
