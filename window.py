import io
import json
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText

from tkcalendar import DateEntry
from tkinter.messagebox import showerror

from utils import Utils


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
    settings = {
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
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(settings, f, indent=4)
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
                    "True" if limit_bool_var.get() else "False",
                ),
            )
            row_window.destroy()
        except Exception as e:
            showerror("Ошибка", str(e))

    row_window = tk.Toplevel(root)
    row_window.title("Добавить строку")
    row_window.geometry("400x300")

    tk.Label(row_window, text="ID битвы:").grid(row=0, column=0, pady=5, padx=5, sticky="w")
    id_entry = tk.Entry(row_window)
    id_entry.grid(row=0, column=1, padx=5)

    tk.Label(row_window, text="Атака?").grid(row=1, column=0, pady=5, padx=5, sticky="w")
    bool_var = tk.BooleanVar()
    bool_checkbox = tk.Checkbutton(row_window, variable=bool_var)
    bool_checkbox.grid(row=1, column=1, sticky="w", padx=5)

    tk.Label(row_window, text="Цена:").grid(row=2, column=0, pady=5, padx=5, sticky="w")
    value1_entry = tk.Entry(row_window)
    value1_entry.grid(row=2, column=1, padx=5)

    tk.Label(row_window, text="ID партии:").grid(row=3, column=0, pady=5, padx=5, sticky="w")
    value2_entry = tk.Entry(row_window)
    value2_entry.grid(row=3, column=1, padx=5)

    tk.Label(row_window, text="Дата:").grid(row=4, column=0, pady=5, padx=5, sticky="w")
    calendar = DateEntry(row_window, date_pattern="dd.MM.yyyy")
    calendar.grid(row=4, column=1, padx=5)

    tk.Label(row_window, text="Время (чч:мм):").grid(row=5, column=0, pady=5, padx=5, sticky="w")
    time_entry = tk.Entry(row_window)
    time_entry.insert(0, "00:00")
    time_entry.grid(row=5, column=1, padx=5)

    tk.Label(row_window, text="Лимит").grid(row=6, column=0, pady=5, padx=5, sticky="w")
    limit_entry = tk.Entry(row_window)
    limit_entry.grid(row=6, column=1, padx=5)

    tk.Label(row_window, text="Лимит?").grid(row=7, column=0, pady=5, padx=5, sticky="w")
    limit_bool_var = tk.BooleanVar()
    limit_bool_checkbox = tk.Checkbutton(row_window, variable=limit_bool_var)
    limit_bool_checkbox.grid(row=7, column=1, sticky="w", padx=5)

    save_button = tk.Button(row_window, text="Сохранить", command=save_row)
    save_button.grid(row=8, column=0, columnspan=2, pady=10)


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

    #Utils.old_main(data)
    print("Collected Data:", data)

def end_script():
    global worker
    worker.join()

root = tk.Tk()
root.title("@setux где деньги?")

# Загружаем настройки
settings = load_settings()

# Поля для ввода путей
frame_paths = tk.Frame(root)
frame_paths.pack(padx=10, pady=5, fill=tk.X)

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
tk.Button(frame_buttons, text="Старт", command=start_script).pack(side=tk.RIGHT, padx=5)
#tk.Button(frame_buttons, text="Стоп", command=end_script).pack(side=tk.RIGHT, padx=5)

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

table.bind("<Double-1>", edit_cell)

root.mainloop()
