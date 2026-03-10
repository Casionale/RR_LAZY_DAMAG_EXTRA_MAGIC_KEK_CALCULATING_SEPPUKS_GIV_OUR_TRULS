import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List

from mozDecompress import mozlz4_to_text

# Куки сессии
cookies = {}

URL_MAIN = "https://rivalregions.com/#overview"
SETTINGS_PATH = Path("SETTINGS.txt")
BATTLES_PATH = Path("BATTLES.txt")
client = ""


@dataclass(frozen=True)
class BattleConfig:
    war_id: int
    is_attack: bool
    price: int
    party_id: int
    stop_at: str


class BattleConfigError(ValueError):
    pass


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise BattleConfigError(f"Неверное значение стороны: {value!r}. Ожидалось True или False")


def parse_battles_file(path: Path) -> List[BattleConfig]:
    if not path.exists():
        raise BattleConfigError(f"Файл {path} не найден")

    battles: List[BattleConfig] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) != 5:
                raise BattleConfigError(
                    f"Строка {line_number}: ожидалось 5 колонок, получено {len(parts)}"
                )

            try:
                battles.append(
                    BattleConfig(
                        war_id=int(parts[0]),
                        is_attack=_parse_bool(parts[1]),
                        price=int(parts[2]),
                        party_id=int(parts[3]),
                        stop_at=parts[4].strip(),
                    )
                )
            except ValueError as error:
                raise BattleConfigError(f"Строка {line_number}: ошибка преобразования данных ({error})") from error

    if not battles:
        raise BattleConfigError("Файл BATTLES.txt пуст или содержит только пустые строки")

    return battles


def get_cookies(settings):
    global cookies

    def get_cookie_from_firefox(cookies_file_uri, session_file_uri):
        connection = sqlite3.connect(cookies_file_uri)

        cursor = connection.cursor()
        cursor.execute(
            """
    SELECT name, value FROM moz_cookies WHERE (name = ? OR name = ? OR name = ? OR name = ? OR name = ?) AND host = ?
    """,
            ("rr", "rr_add", "rr_f", "rr_id", "PHPSESSID", "rivalregions.com"),
        )
        results = cursor.fetchall()

        connection.close()

        local_cookies = {}

        for row in results:
            local_cookies[row[0]] = row[1]

        session_cookies = mozlz4_to_text(session_file_uri)
        txt = session_cookies.decode("utf-8")
        session_cookies = json.loads(txt)
        session_cookies = session_cookies["cookies"]
        local_cookies["PHPSESSID"] = ""

        for cookie in session_cookies:
            if cookie["host"] == "rivalregions.com" and cookie["name"] == "PHPSESSID":
                local_cookies["PHPSESSID"] = cookie["value"]

        return local_cookies

    cookies_file_uri = settings["cookies_file_uri"]
    session_file_uri = settings["session_file_uri"]
    cookies = get_cookie_from_firefox(cookies_file_uri, session_file_uri)


def get_manual_cookies(settings):
    global cookies
    cookies = {
        "PHPSESSID": settings["PHPSESSID"],
        "rr": settings["rr"],
        "rr_add": settings["rr_add"],
        "rr_f": settings["rr_f"],
        "rr_id": settings["rr_id"],
    }


def kek_calculating(is_simple=False):
    from utils import Bot, Utils
    is_error = True
    while is_error:
        try:
            bot = Bot(cookies=cookies, client=client)
            data_main = bot.get_data_main(url=URL_MAIN)
            print(data_main)
            if data_main in ("Сессия устарела!", "Пустой ответ"):
                raise RuntimeError(data_main)
            is_error = False
        except Exception as e:
            print(f"Новая попытка посчитать: {e}")

    is_error = True
    while is_error:
        print("Начинаю смотреть шо там по урону")

        try:
            battles = parse_battles_file(BATTLES_PATH)
        except BattleConfigError as error:
            print(f"Проверь файл BATTLES.txt: {error}")
            return

        ids = [battle.war_id for battle in battles]
        is_attacks = [battle.is_attack for battle in battles]
        prices = [battle.price for battle in battles]
        id_party = battles[0].party_id
        stop_at = [battle.stop_at for battle in battles]

        unique_party_ids = {battle.party_id for battle in battles}
        if len(unique_party_ids) > 1:
            print(f"Внимание: найдено несколько ID партии {sorted(unique_party_ids)}, используется первый: {id_party}")

        try:
            if is_simple:
                print(Utils.sums_per_member_from_wars(Bot(cookies=cookies, client=client), ids, is_attacks, prices, id_party))
            else:
                print(
                    Utils.sums_per_member_from_wars_witch_stop_word(
                        Bot(cookies=cookies, client=client),
                        ids,
                        is_attacks,
                        prices,
                        id_party,
                        stop_at,
                    )
                )
            is_error = False
        except Exception as e:
            print("Новая попытка", e)


def main():
    global client
    print(f'╔{"═" * 40}╗')
    print(f'║{"@setux где деньги?":^40}║')
    print(f'╚{"═" * 40}╝')

    print(f'╭⋟{"─" * 39}╮')
    print(f'│{"Использовать ли куки из FurryFox?":^40}│')
    print(f'│{"1. Да, они там есть и я ленюся":<40}│')
    print(f'│{"2. Нет, использовать заполненный мною":<40}│')
    print(f'╰{"─" * 39}⋞╯')
    firefox_cookies_answer = input("Каков твой выбор: ")
    is_firefox_cookies = firefox_cookies_answer == "1"

    if is_firefox_cookies:
        print("Извращенец ~(˘▾˘~)")

    with SETTINGS_PATH.open("r", encoding="utf-8") as file:
        settings_txt = file.read()

    settings = json.loads(settings_txt.replace("\r", " ").replace("\n", " ").replace("\\", "\\\\"))

    client = settings["client"]

    if is_firefox_cookies:
        get_cookies(settings)
    else:
        get_manual_cookies(settings)

    print(f'╭⋟{"─" * 39}╮')
    print(f'│{"МЕНЮ":^40}│')
    print(f'│{"1. Шо там по деньгам ДО 46 часов!":<40}│')
    print(f'│{"2. Шо там вообще по деньгам-то?":<40}│')
    print(f'╰{"─" * 39}⋞╯')

    choose = input("Ну так што: ")
    if choose == "1":
        kek_calculating(False)
    if choose == "2":
        kek_calculating(True)


if __name__ == "__main__":
    main()
    input("Нажмите Enter для завершения программы...")
