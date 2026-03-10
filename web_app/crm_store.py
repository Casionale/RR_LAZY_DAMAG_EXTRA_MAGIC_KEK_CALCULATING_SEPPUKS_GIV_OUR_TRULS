from __future__ import annotations

import json
import threading
from pathlib import Path


class CrmStore:
    def __init__(self, path: str = "web_app/runtime/crm_leads.json"):
        self.path = Path(path)
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[dict]:
        with self._lock:
            if not self.path.exists():
                return []
            raw = self.path.read_text(encoding="utf-8").strip()
            if not raw:
                return []
            data = json.loads(raw)
            return data if isinstance(data, list) else []

    def save(self, rows: list[dict]) -> None:
        with self._lock:
            self.path.write_text(
                json.dumps(rows, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def append(self, row: dict) -> dict:
        rows = self.load()
        rows.append(row)
        self.save(rows)
        return row
