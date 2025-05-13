import io
import json
import os
import sys
import threading
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import re

from tkcalendar import DateEntry
from tkinter.messagebox import showerror, showinfo

from StatWindow import OrderStatsWindow
from utils import Utils
from utils2 import Utils2


class StdoutGuiRedirector(io.StringIO):
    def __init__(self, text_widget):
        self.text_widget = text_widget
        #self.encoding = 'utf-8'
        super().__init__()

    def write(self, s):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, s)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)
        self.text_widget.update()

    def flush(self):
        pass



CONFIG_FILE = "settings.json"
worker = None

def load_settings():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
    return {}


def save_settings():
    global settings
    settings_s = {
        "cookies_file_uri": cookies_entry.get(),
        "session_file_uri": session_entry.get(),
        "client": client_entry.get(),
        "rr": rr_entry.get(),
        "rr_add": rr_add_entry.get(),
        "rr_f": rr_f_entry.get(),
        "rr_id": rr_id_entry.get(),
        "PHPSESSID": phpsessid_entry.get(),
        "use_browser": use_browser_var.get(),
        "table_data": [
            table.item(row)["values"]
            for row in table.get_children()
        ],
        "deps_table":settings['deps_table'],
    }
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(settings_s, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

def browse_file(entry):
    filepath = filedialog.askopenfilename()
    if filepath:
        entry.delete(0, tk.END)
        entry.insert(0, filepath)

def delete_row():
    selected_item = table.selection()[0]
    table.delete(selected_item)

def open_stats_window():
    OrderStatsWindow(root)

def parse_order(text):
    result = {
        'war_url': None,
        'region_url': None,
        'limit': None,
        'price': None
    }

    # Извлечение URL (учитываем символы # и / в ссылках)
    url_pattern = r'https?://[^\s/]+(?:\/[^#\s]*)?#(?:war|map)/details/\d+'
    urls = re.findall(url_pattern, text)
    for url in urls:
        if "#war/details/" in url:
            result['war_url'] = url
        elif "#map/details/" in url:
            result['region_url'] = url

    # Извлечение лимита (1ККК)
    limit_match = re.search(
        r'(?i)(?:limit|лимит)[\s/:-]*(\d+[кkкk]{1,3})',
        text
    )
    if limit_match:
        result['limit'] = limit_match.group(1).upper().replace('K', 'К')

    # Извлечение цены (7К/1)
    price_match = re.search(
        r'(?i)(?:price|прайс)[\s/:-]*(\d+[кk]/\d+)',
        text
    )
    if price_match:
        result['price'] = price_match.group(1).upper().replace('K', 'К')

    return result

def add_row():
    def save_row():
        try:
            table.insert(
                "",
                tk.END,
                values=(
                    id_entry.get(),
                    "True" if bool_var.get() else "False",
                    value1_entry.get(),
                    value2_entry.get(),
                    f"{time_entry.get()} {calendar.get()}",
                    limit_entry.get(),
                    "True" if limit_entry.get() != '' else "False",
                ),
            )
            row_window.destroy()
        except Exception as e:
            showerror("Ошибка", str(e))

    def handle_order():
        # Заглушка для обработки данных из ордера
        order_text = order_input.get("1.0", tk.END).strip()
        parsed_order = parse_order(order_text)
        is_attack = True if "attack" in order_text.lower() else \
            True if  "атака" in order_text.lower() else False

        if parsed_order['limit'] is not None:
            parsed_order['limit'].replace('К', 'K')
            limit_entry.delete(0, tk.END)
            limit_entry.insert(0, parsed_order['limit'])

        price = parsed_order['price'].lower()
        price = price[:price.index('/')]
        price = price.replace('k','000')
        price = price.replace('к','000')

        value1_entry.delete(0, tk.END)
        value1_entry.insert(0, price)

        bool_var.set(is_attack)

        id = parsed_order['war_url']
        id = id[id.rfind('/')+1:]

        id_entry.delete(0, tk.END)
        id_entry.insert(0, id)


    row_window = tk.Toplevel(root)
    row_window.title("Добавить строку")
    row_window.geometry("750x400")
    row_window.grid_columnconfigure(0, weight=1)
    row_window.grid_columnconfigure(1, weight=1)
    row_window.grid_rowconfigure(0, weight=1)

    # Левая панель с полями ввода
    left_frame = tk.Frame(row_window)
    left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    # Правая панель с текстовым полем
    right_frame = tk.Frame(row_window)
    right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    # Левая часть - поля формы
    tk.Label(left_frame, text="ID битвы:").grid(row=0, column=0, pady=5, sticky="w")
    id_entry = tk.Entry(left_frame)
    id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(left_frame, text="Атака?").grid(row=1, column=0, pady=5, sticky="w")
    bool_var = tk.BooleanVar()
    bool_checkbox = tk.Checkbutton(left_frame, variable=bool_var)
    bool_checkbox.grid(row=1, column=1, sticky="w", padx=5)

    tk.Label(left_frame, text="Цена:").grid(row=2, column=0, pady=5, sticky="w")
    value1_entry = tk.Entry(left_frame)
    value1_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(left_frame, text="ID партии:").grid(row=3, column=0, pady=5, sticky="w")
    value2_entry = tk.Entry(left_frame)
    value2_entry.insert(tk.END, "140")
    value2_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(left_frame, text="Дата:").grid(row=4, column=0, pady=5, sticky="w")
    calendar = DateEntry(left_frame, date_pattern="dd.MM.yyyy")
    calendar.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(left_frame, text="Время (чч:мм):").grid(row=5, column=0, pady=5, sticky="w")
    time_entry = tk.Entry(left_frame)
    time_entry.insert(0, "00:00")
    time_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(left_frame, text="Лимит").grid(row=6, column=0, pady=5, sticky="w")
    limit_entry = tk.Entry(left_frame)
    limit_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

    # Правая часть - текстовое поле и кнопка
    order_input = tk.Text(right_frame, wrap=tk.WORD, width=40, height=15)
    order_input.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

    order_button = tk.Button(right_frame, text="Из ордера", command=handle_order)
    order_button.grid(row=1, column=0, sticky="ew")

    # Настройка растягивания
    left_frame.grid_columnconfigure(1, weight=1)
    right_frame.grid_rowconfigure(0, weight=1)
    right_frame.grid_columnconfigure(0, weight=1)

    # Кнопка сохранения
    save_button = tk.Button(left_frame, text="Сохранить", command=save_row)
    save_button.grid(row=7, column=0, columnspan=2, pady=10, sticky="ew")


def start_script():
    global worker
    data = {
        "cookies_file_uri": cookies_entry.get(),
        "session_file_uri": session_entry.get(),
        "client": client_entry.get(),
        "rr": rr_entry.get(),
        "rr_add": rr_add_entry.get(),
        "rr_f": rr_f_entry.get(),
        "rr_id": rr_id_entry.get(),
        "PHPSESSID": phpsessid_entry.get(),
        "use_browser": use_browser_var.get(),
        "table_data": [
            table.item(row)["values"]
            for row in table.get_children()
        ],
    }

    worker = threading.Thread(target=Utils.old_main, daemon=True, args=(data,))
    worker.start()

    print("Collected Data:", data)

def deps():
    global worker
    global settings
    data = {
        "cookies_file_uri": cookies_entry.get(),
        "session_file_uri": session_entry.get(),
        "client": client_entry.get(),
        "rr": rr_entry.get(),
        "rr_add": rr_add_entry.get(),
        "rr_f": rr_f_entry.get(),
        "rr_id": rr_id_entry.get(),
        "PHPSESSID": phpsessid_entry.get(),
        "use_browser": use_browser_var.get(),
        "table_data": [
            table.item(row)["values"]
            for row in table.get_children()
        ],
    }

    def get_deps(data):
        worker = threading.Thread(target=Utils.deps, daemon=True, args=(data,settings,))
        worker.start()

    def restore(data):
        if data is not None:
            for i, row_data in enumerate(data):
                if i >= len(rows):
                    break
                start_entry, end_entry, limit_entry, id_entry, price_entry, check_vars = rows[i]
                start_entry.delete(0, tk.END)
                start_entry.insert(0, row_data.get("начало", ""))
                end_entry.delete(0, tk.END)
                end_entry.insert(0, row_data.get("конец", ""))
                limit_entry.delete(0, tk.END)
                limit_entry.insert(0, str(row_data.get("лимит", "")))
                id_entry.delete(0, tk.END)
                id_entry.insert(0, str(row_data.get("id", "")))
                price_entry.delete(0, tk.END)
                price_entry.insert(0, str(row_data.get("цена", "")))
                for j, var in enumerate(check_vars):
                    var.set(row_data["чекбоксы"][j] if j < len(row_data["чекбоксы"]) else False)

    deps_window = tk.Toplevel(root)
    deps_window.title("Депы")
    deps_window.geometry("950x250")

    labels = ["id", "цена", "Начало", "Конец", "Лимит", "Здан", "Зол", "Нфт", "Руд", "Алм", "Ур", "Жид", "Гл3", "Тнк", "Ксм", "Эсм"]

    for j, label in enumerate(labels):
        header = tk.Label(deps_window, text=label, font=("Arial", 10, "bold"))
        header.grid(row=0, column=j, padx=5, pady=2)

    rows = []
    now = datetime.now().strftime("%d.%m.%y %H:%M")
    last_week = (datetime.now() - timedelta(days=7)).strftime("%d.%m.%y %H:%M")


    for i in range(5):

        id_entry = tk.Entry(deps_window)
        id_entry.grid(row=i + 1, column=0, padx=5, pady=2)

        price_entry = tk.Entry(deps_window)
        price_entry.grid(row=i + 1, column=1, padx=5, pady=2)

        start_entry = tk.Entry(deps_window)
        start_entry.insert(0, last_week)
        start_entry.grid(row=i + 1, column=2, padx=5, pady=2)

        end_entry = tk.Entry(deps_window)
        end_entry.insert(0, now)
        end_entry.grid(row=i + 1, column=3, padx=5, pady=2)

        limit_entry = tk.Entry(deps_window)
        limit_entry.grid(row=i + 1, column=4, padx=5, pady=2)

        check_vars = []
        for j in range(5, len(labels)):
            var = tk.BooleanVar()
            check = tk.Checkbutton(deps_window, variable=var)
            check.grid(row=i + 1, column=j, padx=2, pady=2)
            check_vars.append(var)

        rows.append((start_entry, end_entry, limit_entry, id_entry, price_entry, check_vars))


    def calculate():
        result = get_table()
        settings['deps_table'] = result
        get_deps(result)

    def get_table():
        result = []
        for start_entry, end_entry, limit_entry, id_entry, price_entry, check_vars in rows:
            row_data = {
                "начало": start_entry.get(),
                "конец": end_entry.get(),
                "лимит": int(limit_entry.get()) if limit_entry.get().isdigit() else 0,
                "id": int(id_entry.get()) if id_entry.get().isdigit() else 0,
                "цена": int(price_entry.get()) if price_entry.get().isdigit() else 0,
                "чекбоксы": [var.get() for var in check_vars],
                "партия": entry_id_party.get()
            }
            result.append(row_data)
        return result

    lbl_patry = tk.Label(deps_window, text='Партия', font=("Arial", 10, "bold"))
    lbl_patry.grid(row=6, column=0, padx=5, pady=2)

    entry_id_party = tk.Entry(deps_window)
    entry_id_party.insert(0, '140')
    entry_id_party.grid(row=6, column=1, padx=5, pady=2)

    calc_button = tk.Button(deps_window, text="Расчёт", command=calculate, width=20)
    calc_button.grid(row=6, column=2, columnspan=6, pady=2)

    if 'deps_table' in settings.keys():
        restore(settings['deps_table'])

    def close_window():
        print("Закрыл окно депов")
        result = get_table()
        settings['deps_table'] = result
        deps_window.destroy()

    deps_window.protocol('WM_DELETE_WINDOW', close_window)

    deps_window.grid_columnconfigure(0, weight=25)
    deps_window.grid_columnconfigure(1, weight=25)
    deps_window.grid_columnconfigure(2, weight=30)
    deps_window.grid_columnconfigure(3, weight=30)
    deps_window.grid_columnconfigure(4, weight=30)


def end_script():
    global worker
    worker.join()

root = tk.Tk()
root.title("@setux где деньги?")
root.configure(bg='Snow')


# Загружаем настройки
settings = load_settings()

# Поля для ввода путей
frame_paths = tk.Frame(root)
frame_paths.pack(padx=10, pady=5, fill=tk.X)

frame_paths.configure(bg='Lavender')

tk.Label(frame_paths, text="Cookies File URI:").grid(row=0, column=0, sticky="w")
cookies_entry = tk.Entry(frame_paths, width=50)
cookies_entry.grid(row=0, column=1, padx=5)
cookies_entry.insert(0, settings.get("cookies_file_uri", ""))
tk.Button(frame_paths, text="Обзор", command=lambda: browse_file(cookies_entry)).grid(row=0, column=2, padx=5)

tk.Label(frame_paths, text="Session File URI:").grid(row=1, column=0, sticky="w")
session_entry = tk.Entry(frame_paths, width=50)
session_entry.grid(row=1, column=1, padx=5)
session_entry.insert(0, settings.get("session_file_uri", ""))
tk.Button(frame_paths, text="Обзор", command=lambda: browse_file(session_entry)).grid(row=1, column=2, padx=5)

# Прочие текстовые поля
frame_fields = tk.Frame(root)
frame_fields.configure(bg='Lavender')
frame_fields.pack(padx=10, pady=5, fill=tk.X)

fields = [
    ("Client:", "client_entry", "client"),
    ("RR:", "rr_entry", "rr"),
    ("RR Add:", "rr_add_entry", "rr_add"),
    ("RR F:", "rr_f_entry", "rr_f"),
    ("RR ID:", "rr_id_entry", "rr_id"),
    ("PHPSESSID:", "phpsessid_entry", "PHPSESSID"),
]

for i, (label, var_name, setting_key) in enumerate(fields):
    tk.Label(frame_fields, text=label).grid(row=i, column=0, sticky="w")
    entry = tk.Entry(frame_fields, width=50)
    entry.insert(0, settings.get(setting_key, ""))
    entry.grid(row=i, column=1, padx=5, pady=2)
    globals()[var_name] = entry

# Чекбокс
use_browser_var = tk.BooleanVar()
use_browser_var = tk.BooleanVar(value=settings.get("use_browser", False))
tk.Checkbutton(root, text="Использовать FurryFox ~(˘▾˘~)", variable=use_browser_var).pack(padx=10, pady=5, anchor="w")

# Таблица для данных
frame_table = tk.Frame(root)
frame_table.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

columns = ("ID битвы:", "Атака?", "Цена:", "ID партии:", "Стоп слово в", "Лимит", "Лимит?")
table = ttk.Treeview(frame_table, columns=columns, show="headings", height=10)

for col in columns:
    table.heading(col, text=col)
    table.column(col, width=100)

table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(frame_table, orient=tk.VERTICAL, command=table.yview)
table.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

if "table_data" in settings:
        for row in settings["table_data"]:
            table.insert("", tk.END, values=row)

# Кнопки управления
frame_buttons = tk.Frame(root)
frame_buttons.pack(padx=10, pady=10, fill=tk.X)


tk.Button(frame_buttons, text="Добавить строку", command=add_row).pack(side=tk.LEFT, padx=5)
tk.Button(frame_buttons, text="Удалить строку", command=delete_row).pack(side=tk.LEFT, padx=5)
tk.Button(frame_buttons, text="Стат. заказов", command=open_stats_window).pack(side=tk.LEFT, padx=5)

tk.Button(frame_buttons, text="Департаменты", command=deps).pack(side=tk.RIGHT, padx=5)
tk.Button(frame_buttons, text="Старт", command=start_script).pack(side=tk.RIGHT, padx=5)


# Создаём виджет ScrolledText для вывода текста
console_text = ScrolledText(root, wrap=tk.WORD, height=10, width=70)
console_text.pack(padx=10, pady=10)

sys.stdout = StdoutGuiRedirector(console_text)

# Событие закрытия окна
root.protocol("WM_DELETE_WINDOW", lambda: [save_settings(), root.destroy()])

def copy(event):
    print('copy')
def paste(event):
    print('paste')

def _onKeyRelease(event):
    ctrl  = (event.state & 0x4) != 0
    if event.keycode==88 and  ctrl and event.keysym.lower() != "x":
        event.widget.event_generate("<<Cut>>")

    if event.keycode==86 and  ctrl and event.keysym.lower() != "v":
        event.widget.event_generate("<<Paste>>")

    if event.keycode==67 and  ctrl and event.keysym.lower() != "c":
        event.widget.event_generate("<<Copy>>")

root.bind_all("<Key>", _onKeyRelease, "+")

def edit_cell(event):
    # Получаем текущий выбранный элемент
    selected_item = table.focus()
    if not selected_item:
        return

    # Получаем координаты ячейки
    region = table.identify("region", event.x, event.y)
    if region != "cell":
        return

    column = table.identify_column(event.x)
    column_index = int(column.replace("#", "")) - 1
    row = table.identify_row(event.y)

    # Получаем текущие данные
    item = table.item(row)
    values = item["values"]
    current_value = values[column_index] if column_index < len(values) else ""

    # Создаем Entry для редактирования
    entry = tk.Entry(root)
    entry.insert(0, current_value)
    entry.place(x=event.x_root - root.winfo_x(), y=event.y_root - root.winfo_y())
    entry.focus()

    def save_edit(event):
        # Сохраняем новое значение
        new_value = entry.get()
        values[column_index] = new_value
        table.item(row, values=values)
        entry.destroy()

    def cancel_edit(event):
        entry.destroy()

    entry.bind("<Return>", save_edit)
    entry.bind("<Escape>", save_edit)

table.bind("<Double-1>", edit_cell)

root.mainloop()
