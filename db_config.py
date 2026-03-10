from pathlib import Path
import os

_CONNECTION_FILES = (
    Path("msql_connection_string.txt"),
    Path("msql_connecting_string.txt"),
)


def get_database_url() -> str:
    env_value = os.getenv("DATABASE_URL", "").strip()
    if env_value:
        return env_value

    for path in _CONNECTION_FILES:
        if path.exists():
            value = path.read_text(encoding="utf-8").strip()
            if value:
                return value

    raise FileNotFoundError(
        "Не найдена строка подключения к БД. "
        "Создайте msql_connection_string.txt или msql_connecting_string.txt "
        "либо задайте переменную окружения DATABASE_URL."
    )
