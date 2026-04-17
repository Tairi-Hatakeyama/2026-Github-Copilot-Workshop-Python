from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from services.config_service import InMemoryConfigStore
from services.stats_service import InMemoryStatsStore


def create_app(config: dict | None = None) -> Flask:
    """
    App Factory パターンで Flask アプリを生成する。
    config に辞書を渡すとテスト用設定を上書きできる。
    """
    app = Flask(__name__)

    if config:
        app.config.update(config)

    # --- サービス初期化（将来的には DI コンテナで差し替え可能にする） ---
    config_store = InMemoryConfigStore()
    stats_store = InMemoryStatsStore()

    # --- ルーティング ---

    @app.route("/")
    def index():
        return render_template("index.html")

    # --- 設定 API ---

    @app.route("/api/config", methods=["GET"])
    def get_config():
        cfg = config_store.get_config()
        return jsonify({"work_minutes": cfg.work_minutes, "break_minutes": cfg.break_minutes})

    @app.route("/api/config", methods=["PUT"])
    def put_config():
        data = request.get_json(silent=True) or {}
        work = data.get("work_minutes")
        brk = data.get("break_minutes")

        if not isinstance(work, int) or work <= 0:
            return jsonify({"error": "work_minutes は正の整数で指定してください"}), 400
        if not isinstance(brk, int) or brk <= 0:
            return jsonify({"error": "break_minutes は正の整数で指定してください"}), 400

        from domain.models import TimerConfig
        config_store.save_config(TimerConfig(work_minutes=work, break_minutes=brk))
        cfg = config_store.get_config()
        return jsonify({"work_minutes": cfg.work_minutes, "break_minutes": cfg.break_minutes})

    # --- 統計 API ---

    @app.route("/api/stats/today", methods=["GET"])
    def get_today_stats():
        stats = stats_store.get_today_stats()
        return jsonify({
            "date": stats.date,
            "completed_work_sessions": stats.completed_work_sessions,
            "completed_break_sessions": stats.completed_break_sessions,
            "focused_minutes": stats.focused_minutes,
        })

    @app.route("/api/stats/events", methods=["POST"])
    def post_stats_event():
        from datetime import datetime
        data = request.get_json(silent=True) or {}
        event_type = data.get("event_type")
        completed_at_str = data.get("completed_at")

        valid_events = {"work_completed", "break_completed"}
        if event_type not in valid_events:
            return jsonify({"error": f"event_type は {valid_events} のいずれかで指定してください"}), 400

        try:
            completed_at = datetime.fromisoformat(completed_at_str) if completed_at_str else datetime.now()
        except (TypeError, ValueError):
            return jsonify({"error": "completed_at の形式が不正です（ISO 8601）"}), 400

        stats_store.add_session(event_type, completed_at)
        return jsonify({"status": "recorded"}), 201

    # --- エラーハンドラー ---

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad Request", "message": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal Server Error"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=False)
