import json
import os
import shutil
import sqlite3
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from mozDecompress import mozlz4_to_text
# импорт моделей
from new_models import Base, NsOrder  # <-- твой файл с моделями
from utils import Utils

# настройка подключения (замени на свои параметры)
with open('msql_connection_string.txt', 'r', encoding='utf-8') as f:
    DATABASE_URL = f.read()

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NS Orders")
        self.geometry("800x400")

        # конфигурация 3 колонок (панели)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=2)

        # ---- левая панель ----
        left_frame = ttk.Frame(self, padding=10)
        left_frame.grid(row=0, column=0, sticky="nswe")

        ttk.Label(left_frame, text="Выберите заказ:").pack(anchor="w")
        self.order_combo = ttk.Combobox(left_frame, state="readonly")
        self.order_combo.pack(fill="x", pady=5)

        # переменная для комиссии
        self.commission_var = tk.DoubleVar(value=0.0)

        # лейбл + текстбокс
        ttk.Label(left_frame, text="Введите процент комиссии:").pack(anchor="w", pady=(10, 0))
        self.commission_entry = ttk.Entry(left_frame, textvariable=self.commission_var)
        self.commission_entry.pack(fill="x", pady=5)
        self.commission_var.set(5)


        # ---- центральная панель ----
        center_frame = ttk.Frame(self, padding=10)
        center_frame.grid(row=0, column=1, sticky="ns")

        self.calc_button = ttk.Button(center_frame, text="Рассчитать оплату",
                                      command=self.calculate_payment)
        self.calc_button.pack(pady=20)

        # ---- правая панель ----
        right_frame = ttk.Frame(self, padding=10)
        right_frame.grid(row=0, column=2, sticky="nswe")

        ttk.Label(right_frame, text="Логи:").pack(anchor="w")
        self.log_text = tk.Text(right_frame, wrap="word", height=20)
        self.log_text.pack(fill="both", expand=True)

        # загрузка данных из БД
        self.load_orders()

    def load_orders(self):
        """Загрузить заказы из таблицы NS_ORDER"""
        session = Session()
        try:
            orders = session.execute(select(NsOrder)).scalars().all()
            self.orders = {o.name: o.id for o in orders}

            self.order_combo["values"] = list(self.orders.keys())
            if self.orders:
                self.order_combo.current(0)
        finally:
            session.close()

    def calculate_payment(self):
        """Пока просто выводит выбранный заказ в лог"""
        selected_name = self.order_combo.get()
        if not selected_name:
            self.log("⚠ Заказ не выбран")
            return

        order_id = self.orders[selected_name]
        self.log(f"▶ Рассчитываем оплату для заказа: {selected_name} (id={order_id})")
        order = get_order_by_id(order_id)
        commission = self.commission_var.get()

        DOMAIN = "rivalregions.com"
        PROFILE = "iko8fy3f.default-release"
        cookies = get_firefox_cookies_for_requests(DOMAIN, PROFILE)

        EXTRA_LIMIT = 30000000

        data = [order.url, order.is_attack, order.price, order.end_date.strftime("%H:%M %d.%m.%Y"),
                order.limit + EXTRA_LIMIT, True]

        info, dm = Utils.new_main(order_data=data, cookies=cookies)

        full_result = {}

        for member in info:
            result = Utils.calculate_truls_for_war(damage=info[member], id_war=order.url, price=order.price * (commission / 100),
                                                   stop_time=order.end_date.strftime("%H:%M %d.%m.%Y"), name=member)
            #ТУТ НАДО ПРИПАРКОВАТЬ РЕСАЛТ К ДМ

        pass

    def log(self, message: str):
        """Вывод сообщения в правую панель логов"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)


def get_order_by_id(order_id: int):
    session = Session()
    try:
        return session.execute(
            select(NsOrder).where(NsOrder.id == order_id)
        ).scalar_one_or_none()
    finally:
        session.close()

def get_firefox_cookies_for_requests(domain: str, profile_name: str) -> dict:
    """
    Получить куки Firefox для указанного домена из конкретного профиля в формате для requests.
    :param domain: домен (например 'example.com')
    :param profile_name: имя профиля, например 'iko8fy3f.default-release'
    :return: dict с куки
    """
    # Путь к профилям Firefox
    if os.name == "nt":  # Windows
        profiles_path = Path(os.getenv("APPDATA")) / "Mozilla" / "Firefox" / "Profiles"
    else:  # Linux / macOS
        profiles_path = Path.home() / ".mozilla" / "firefox"

    profile_path = profiles_path / profile_name
    #session_path = profile_path / "sessionstore-backups" / "previous.jsonlz4"
    session_path = profile_path / "sessionstore-backups" / "recovery.baklz4"
    cookies_sqlite = profile_path / "cookies.sqlite"

    if not cookies_sqlite.exists():
        raise FileNotFoundError(f"Файл cookies.sqlite не найден в {profile_path}")

    # Создаем временный путь
    tmp_path = Path(tempfile.gettempdir()) / "tmp_cookies.sqlite"
    shutil.copy2(cookies_sqlite, tmp_path)

    cookies = {}
    try:
        conn = sqlite3.connect(tmp_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, value FROM moz_cookies WHERE host LIKE ?", (f"%{domain}",))
        for name, value in cursor.fetchall():
            cookies[name] = value
        conn.close()
    finally:
        if tmp_path.exists():
            tmp_path.unlink()  # удаляем временный файл

    session_cookies = mozlz4_to_text(session_path)
    txt = session_cookies.decode('utf-8')
    session_cookies = json.loads(txt)
    session_cookies = session_cookies['cookies']
    cookies['PHPSESSID'] = ''

    for cookie in session_cookies:
        if cookie['host'] == f'{domain}' and cookie['name'] == 'PHPSESSID':
            cookies['PHPSESSID'] = cookie['value']

    return cookies

if __name__ == "__main__":
    app = App()
    app.mainloop()
