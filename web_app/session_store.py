from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Dict, Any

STORE_PATH = Path("web_app/runtime/session.json")
_REQUIRED_COOKIES = {"PHPSESSID", "rr", "rr_add", "rr_f", "rr_id"}


class SessionStore:
    def __init__(self, path: Path = STORE_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def save(self, payload: Dict[str, Any]) -> None:
        with self._lock:
            self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        with self._lock:
            return json.loads(self.path.read_text(encoding="utf-8"))

    def clear(self) -> None:
        with self._lock:
            if self.path.exists():
                self.path.unlink()


def validate_cookie_payload(data: Dict[str, Any]) -> Dict[str, str]:
    cookies = data.get("cookies")
    if not isinstance(cookies, dict):
        raise ValueError("Поле 'cookies' должно быть объектом JSON")

    missing = sorted(_REQUIRED_COOKIES - set(cookies))
    if missing:
        raise ValueError(f"Не хватает обязательных cookies: {', '.join(missing)}")

    normalized = {}
    for key in _REQUIRED_COOKIES:
        value = cookies.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Cookie '{key}' должен быть непустой строкой")
        normalized[key] = value.strip()

    return normalized
