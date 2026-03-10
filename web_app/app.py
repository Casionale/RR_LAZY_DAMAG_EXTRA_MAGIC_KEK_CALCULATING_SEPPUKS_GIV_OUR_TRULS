from __future__ import annotations

import csv
import hashlib
import hmac
import io
import os
import time
from datetime import datetime
from decimal import Decimal
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, make_response, redirect, render_template, request, send_file, session, url_for
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_config import get_database_url
from new_models import NsOrder
from utils import Utils
from web_app.session_store import SessionStore, validate_cookie_payload

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("WEB_SECRET_KEY", "dev-secret-change-me")
store = SessionStore()

_session_factory = None


def get_session_factory():
    global _session_factory
    if _session_factory is not None:
        return _session_factory
    try:
        engine = create_engine(get_database_url())
        _session_factory = sessionmaker(bind=engine)
        return _session_factory
    except ModuleNotFoundError as error:
        raise RuntimeError("Не найден DB-драйвер для DATABASE_URL. Установите нужный пакет (например pymysql).") from error


def _serialize_order(order: NsOrder) -> dict:
    return {
        "id": order.id,
        "name": order.name,
        "url": order.url,
        "price": float(order.price),
        "limit": int(order.limit),
        "is_attack": bool(order.is_attack),
        "end_date": order.end_date.isoformat() if order.end_date else None,
    }


def _is_telegram_payload_valid(payload: dict, bot_token: str) -> bool:
    if not payload.get("hash"):
        return False

    check_hash = payload["hash"]
    fields = []
    for key in sorted(k for k in payload.keys() if k != "hash"):
        fields.append(f"{key}={payload[key]}")
    data_check_string = "\n".join(fields)

    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_hash, check_hash)


def _is_telegram_auth_fresh(auth_date: str, max_age_seconds: int = 86400) -> bool:
    try:
        auth_ts = int(auth_date)
    except (TypeError, ValueError):
        return False
    return int(time.time()) - auth_ts <= max_age_seconds


def require_auth(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        if request.method == "OPTIONS":
            return _build_preflight_response()
        if not session.get("user"):
            return jsonify({"ok": False, "error": "Требуется авторизация через Telegram"}), 401
        return handler(*args, **kwargs)

    return wrapper


def _build_preflight_response():
    response = make_response("", 204)
    return _add_cors_headers(response)


def _add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.after_request
def apply_cors_headers(response):
    if request.path.startswith("/api/"):
        response = _add_cors_headers(response)
    return response


@app.get("/")
def index():
    return render_template(
        "index.html",
        tg_bot_username=os.getenv("TELEGRAM_BOT_USERNAME", ""),
        tg_auth_url=url_for("auth_telegram", _external=True),
    )


@app.get("/auth/telegram")
def auth_telegram():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        return jsonify({"ok": False, "error": "TELEGRAM_BOT_TOKEN не настроен на backend"}), 500

    payload = {k: v for k, v in request.args.items()}
    if not payload:
        return jsonify({"ok": False, "error": "Пустой ответ от Telegram Login Widget"}), 400

    if not _is_telegram_payload_valid(payload, bot_token):
        return jsonify({"ok": False, "error": "Подпись Telegram невалидна"}), 401

    if not _is_telegram_auth_fresh(payload.get("auth_date", "")):
        return jsonify({"ok": False, "error": "Telegram-авторизация устарела"}), 401

    session["user"] = {
        "id": payload.get("id"),
        "first_name": payload.get("first_name"),
        "last_name": payload.get("last_name"),
        "username": payload.get("username"),
        "photo_url": payload.get("photo_url"),
        "auth_date": payload.get("auth_date"),
    }
    return redirect(url_for("index"))


@app.post("/api/auth/logout")
def logout():
    session.pop("user", None)
    return jsonify({"ok": True})


@app.get("/api/auth/me")
def auth_me():
    user = session.get("user")
    return jsonify({"authenticated": bool(user), "user": user})


@app.get("/api/orders")
@require_auth
def get_orders():
    try:
        Session = get_session_factory()
    except RuntimeError as error:
        return jsonify({"ok": False, "error": str(error)}), 500

    session_db = Session()
    try:
        orders = session_db.execute(select(NsOrder).where(NsOrder.is_end == False)).scalars().all()
        return jsonify([_serialize_order(order) for order in orders])
    finally:
        session_db.close()


@app.post("/api/session/import-cookies")
@require_auth
def import_cookies():
    payload = request.get_json(silent=True) or {}
    try:
        cookies = validate_cookie_payload(payload)
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400

    data = {
        "cookies": cookies,
        "client": payload.get("client", ""),
        "domain": payload.get("domain", "rivalregions.com"),
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "user": session.get("user"),
    }
    store.save(data)
    return jsonify({"ok": True, "message": "Cookies сохранены"})


@app.route("/api/session/import-cookies", methods=["OPTIONS"])
def import_cookies_options():
    return _build_preflight_response()


@app.get("/api/session/status")
@require_auth
def session_status():
    data = store.load()
    if not data:
        return jsonify({"connected": False})

    return jsonify(
        {
            "connected": True,
            "domain": data.get("domain"),
            "updated_at": data.get("updated_at"),
            "client_present": bool(data.get("client")),
            "loaded_by": data.get("user", {}).get("username"),
        }
    )

def _build_war_order_data(payload: dict):
    war_id = payload.get("war_id")
    if war_id in (None, ""):
        raise ValueError("Поле war_id обязательно")

    try:
        war_id = int(war_id)
    except (TypeError, ValueError) as error:
        raise ValueError("war_id должен быть целым числом") from error

    is_attack_raw = payload.get("is_attack", True)
    if isinstance(is_attack_raw, bool):
        is_attack = is_attack_raw
    else:
        is_attack = str(is_attack_raw).strip().lower() in {"1", "true", "yes", "да"}

    price_raw = payload.get("price", 1)
    try:
        price = float(price_raw)
    except (TypeError, ValueError) as error:
        raise ValueError("price должен быть числом") from error

    stop_at = str(payload.get("stop_at", "")).strip()
    if not stop_at:
        raise ValueError("Поле stop_at обязательно (формат HH:MM DD.MM.YYYY)")

    limit_raw = payload.get("limit", 30000000)
    try:
        limit = int(limit_raw)
    except (TypeError, ValueError) as error:
        raise ValueError("limit должен быть целым числом") from error

    is_limit_raw = payload.get("is_limit", True)
    if isinstance(is_limit_raw, bool):
        is_limit = is_limit_raw
    else:
        is_limit = str(is_limit_raw).strip().lower() in {"1", "true", "yes", "да"}

    return [war_id, is_attack, price, stop_at, limit, is_limit]


def _calculate_war_rows(order_data: list, cookies: dict):
    try:
        info, dm = Utils.new_main(order_data=order_data, cookies=cookies)
    except Exception as error:
        raise RuntimeError(f"Ошибка расчёта: {error}") from error

    war_id, _, price, stop_at, _, _ = order_data

    result = []
    for member, damage in info.items():
        calc = Utils.calculate_truls_for_war(
            damage=damage,
            id_war=war_id,
            price=float(price),
            stop_time=stop_at,
            name=member,
        )
        member_id = next((item.get("id") for item in dm if item.get("name") == member), None)
        result.append(
            {
                "name": member,
                "id": member_id,
                "damage": int(calc["damage"]),
                "sum": Decimal(str(calc["sum"])).quantize(Decimal("1.00")),
            }
        )

    return [
        {
            **row,
            "sum": float(row["sum"]),
            "profile_url": f"https://rivalregions.com/#slide/profile/{row['id']}" if row["id"] else None,
        }
        for row in result
    ]


@app.post("/api/calculate/<int:order_id>")
@require_auth
def calculate_order(order_id: int):
    state = store.load()
    if not state:
        return jsonify({"ok": False, "error": "Сессия не инициализирована. Импортируйте cookies."}), 400

    try:
        Session = get_session_factory()
    except RuntimeError as error:
        return jsonify({"ok": False, "error": str(error)}), 500

    session_db = Session()
    try:
        order = session_db.execute(select(NsOrder).where(NsOrder.id == order_id)).scalar_one_or_none()
    finally:
        session_db.close()

    if order is None:
        return jsonify({"ok": False, "error": "Заказ не найден"}), 404
    if order.end_date is None:
        return jsonify({"ok": False, "error": "У заказа не заполнено поле end_date"}), 400

    data = [
        order.url,
        order.is_attack,
        float(order.price),
        order.end_date.strftime("%H:%M %d.%m.%Y"),
        int(order.limit) + 30000000,
        True,
    ]

    try:
        rows = _calculate_war_rows(data, state["cookies"])
    except RuntimeError as error:
        return jsonify({"ok": False, "error": str(error)}), 500

    return jsonify({"ok": True, "order": _serialize_order(order), "rows": rows})


@app.post("/api/calculate/<int:order_id>/csv")
@require_auth
def calculate_order_csv(order_id: int):
    response = calculate_order(order_id)
    if isinstance(response, tuple):
        return response

    payload = response.get_json()
    if not payload.get("ok"):
        return jsonify(payload), 400

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Аккаунт", "url", "Дамаг учтён.", "Плата"])
    for row in payload["rows"]:
        writer.writerow([row["name"], row.get("profile_url") or "", row["damage"], int(row["sum"])])

    mem = io.BytesIO(output.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=f"payment_{order_id}.csv")




@app.post("/api/war/calculate")
@require_auth
def calculate_war():
    state = store.load()
    if not state:
        return jsonify({"ok": False, "error": "Сессия не инициализирована. Импортируйте cookies."}), 400

    payload = request.get_json(silent=True) or {}
    try:
        order_data = _build_war_order_data(payload)
    except ValueError as error:
        return jsonify({"ok": False, "error": str(error)}), 400

    try:
        rows = _calculate_war_rows(order_data, state["cookies"])
    except RuntimeError as error:
        return jsonify({"ok": False, "error": str(error)}), 500

    return jsonify({"ok": True, "war": {
        "war_id": order_data[0],
        "is_attack": order_data[1],
        "price": order_data[2],
        "stop_at": order_data[3],
        "limit": order_data[4],
        "is_limit": order_data[5],
    }, "rows": rows})


@app.post("/api/war/calculate/csv")
@require_auth
def calculate_war_csv():
    response = calculate_war()
    if isinstance(response, tuple):
        return response

    payload = response.get_json()
    if not payload.get("ok"):
        return jsonify(payload), 400

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Аккаунт", "url", "Дамаг учтён.", "Плата"])
    for row in payload["rows"]:
        writer.writerow([row["name"], row.get("profile_url") or "", row["damage"], int(row["sum"])])

    mem = io.BytesIO(output.getvalue().encode("utf-8"))
    mem.seek(0)
    war_id = payload.get("war", {}).get("war_id", "war")
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=f"war_payment_{war_id}.csv")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "tg_login_enabled": bool(os.getenv("TELEGRAM_BOT_TOKEN"))})


if __name__ == "__main__":
    Path("web_app/runtime").mkdir(parents=True, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
