# ============================================================
# db.py — 数据库连接与工具函数
# ============================================================
# 设计说明：
#   - 使用 Flask 的 g 对象管理每次请求的连接生命周期
#   - 提供 query / execute / call_proc 三个核心函数
#   - call_proc 专门封装存储过程调用，处理 OUT 参数读取
# ============================================================

import pymysql
import pymysql.cursors
from flask import g, current_app


def get_db():
    """获取当前请求的数据库连接（懒加载，每个请求复用同一连接）"""
    if "db" not in g:
        cfg = current_app.config
        g.db = pymysql.connect(
            host=cfg["DB_HOST"],
            port=cfg["DB_PORT"],
            user=cfg["DB_USER"],
            password=cfg["DB_PASSWORD"],
            database=cfg["DB_NAME"],
            charset=cfg["DB_CHARSET"],
            cursorclass=pymysql.cursors.DictCursor,  # 返回 dict 而非 tuple
            autocommit=True,  # 视图查询不需要手动 commit
        )
    return g.db


def close_db(e=None):
    """请求结束时关闭连接（注册到 app.teardown_appcontext）"""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, params=None):
    """
    执行 SELECT 查询，返回 list[dict]。

    用法：
        rows = query("SELECT * FROM v_public_content LIMIT %s", (20,))
    """
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def query_one(sql, params=None):
    """执行 SELECT 查询，返回单条 dict 或 None"""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def execute(sql, params=None):
    """
    执行 INSERT / UPDATE / DELETE，返回受影响行数。

    用法：
        affected = execute("INSERT INTO like_record VALUES (%s, %s, NOW())", (user_id, content_id))
    """
    conn = get_db()
    with conn.cursor() as cur:
        affected = cur.execute(sql, params)
        conn.commit()
        return affected


def call_proc(proc_name, in_params, out_count):
    """
    调用存储过程并读取 OUT 参数。

    参数：
        proc_name  — 存储过程名称，如 'sp_publish_content'
        in_params  — IN 参数列表，如 [1, 'title', 'body', ...]
        out_count  — OUT 参数数量（存储过程末尾的 OUT 参数个数）

    返回：
        dict，包含 out_0, out_1, ... 对应每个 OUT 参数的值

    原理：
        MySQL 的 pymysql 不能直接读取 OUT 参数，需要用 @变量 中转：
        1. SET @_out_0 = NULL, @_out_1 = NULL, ...;
        2. CALL proc(in1, in2, ..., @_out_0, @_out_1, ...);
        3. SELECT @_out_0, @_out_1, ...;

    用法：
        result = call_proc('sp_publish_content',
                           [None, 1, '标题', '正文', 'text', 'public', '[1,2]', '[3,4]'],
                           3)
        # result = {'out_0': 16, 'out_1': 0, 'out_2': '内容发布成功'}
    """
    conn = get_db()

    # 构造 OUT 变量名
    out_vars = [f"@_out_{i}" for i in range(out_count)]

    with conn.cursor() as cur:
        # 1) 初始化 OUT 变量
        if out_vars:
            init_sql = "SET " + ", ".join(f"{v} = NULL" for v in out_vars)
            cur.execute(init_sql)

        # 2) 构造 CALL 语句
        all_placeholders = ["%s"] * len(in_params) + out_vars
        call_sql = f"CALL `{proc_name}`({', '.join(all_placeholders)})"
        cur.execute(call_sql, in_params)

        # 消费可能的结果集（某些存储过程内部有 SELECT）
        while cur.nextset():
            pass

        # 3) 读取 OUT 参数
        if out_vars:
            cur.execute(f"SELECT {', '.join(out_vars)}")
            row = cur.fetchone()
            # 转换为 out_0, out_1, ... 的 dict
            result = {}
            for i, var in enumerate(out_vars):
                result[f"out_{i}"] = row.get(var)
            return result

    return {}


def init_app(app):
    """在 Flask app 上注册数据库相关钩子"""
    app.config.setdefault("DB_HOST", "127.0.0.1")
    app.teardown_appcontext(close_db)
