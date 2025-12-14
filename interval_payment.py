import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
from datetime import datetime
import re


class DamageCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Damage Calculator")

        # --- Файл ---
        self.file_path = None
        btn_load = tk.Button(root, text="Загрузить лог", command=self.load_file)
        btn_load.pack(pady=5)

        # --- Интервалы ---
        frame_intervals = tk.LabelFrame(root, text="Интервалы цен")
        frame_intervals.pack(fill="x", padx=10, pady=5)

        self.tree = ttk.Treeview(frame_intervals, columns=("from", "to", "price"), show="headings")
        self.tree.heading("from", text="Время от (HH:MM)")
        self.tree.heading("to", text="Время до (HH:MM)")
        self.tree.heading("price", text="Цена")
        self.tree.pack(fill="x")

        frame_btns = tk.Frame(frame_intervals)
        frame_btns.pack(fill="x")

        tk.Button(frame_btns, text="Добавить", command=self.add_interval).pack(side="left", padx=5, pady=2)
        tk.Button(frame_btns, text="Удалить", command=self.del_interval).pack(side="left", padx=5, pady=2)

        # --- Действия ---
        frame_actions = tk.Frame(root)
        frame_actions.pack(fill="x", pady=10)

        tk.Button(frame_actions, text="Рассчитать", command=self.calculate).pack(side="left", padx=10)
        tk.Button(frame_actions, text="Сохранить CSV", command=self.save_csv).pack(side="left", padx=10)

        # --- Данные ---
        self.lines = []
        self.result = {}

        # --- Редактирование в таблице ---
        self.tree.bind("<Double-1>", self.on_double_click)

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Log files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        self.file_path = path

        with open(path, encoding="utf-8") as f:
            self.lines = f.readlines()

        messagebox.showinfo("Файл загружен", f"Загружено {len(self.lines)} строк.")

    def add_interval(self):
        self.tree.insert("", "end", values=("09:00", "10:00", "13000"))

    def del_interval(self):
        for sel in self.tree.selection():
            self.tree.delete(sel)

    def on_double_click(self, event):
        """Редактирование ячейки по двойному клику"""
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item or not column:
            return

        col_index = int(column.replace("#", "")) - 1
        old_value = self.tree.item(item, "values")[col_index]

        # Получаем координаты ячейки
        x, y, width, height = self.tree.bbox(item, column)

        # Создаём поле ввода поверх
        entry = tk.Entry(self.tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, old_value)
        entry.focus()

        def save_edit(event):
            new_value = entry.get()
            values = list(self.tree.item(item, "values"))
            values[col_index] = new_value
            self.tree.item(item, values=values)
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    def parse_intervals(self):
        intervals = []
        for row in self.tree.get_children():
            t_from, t_to, price = self.tree.item(row)["values"]
            try:
                t_from = datetime.strptime(t_from, "%H:%M").time()
                t_to = datetime.strptime(t_to, "%H:%M").time()
                price = int(price)
                intervals.append((t_from, t_to, price))
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверный формат интервала: {e}")
                return []
        return intervals

    def find_price(self, time_obj, intervals):
        for t_from, t_to, price in intervals:
            if t_from <= time_obj <= t_to:
                return price
        return None

    def parse_intervals(self):
        """Читает таблицу интервалов и возвращает список (t_from, t_to, price).
        Формат времени: HH:MM. Возвращает [] и показывает ошибку при неверном формате.
        """
        intervals = []
        for row in self.tree.get_children():
            t_from_s, t_to_s, price_s = self.tree.item(row)["values"]
            try:
                t_from = datetime.strptime(t_from_s.strip(), "%H:%M").time()
                t_to = datetime.strptime(t_to_s.strip(), "%H:%M").time()
                price = int(str(price_s).strip())
                intervals.append((t_from, t_to, price))
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверный формат интервала '{t_from_s} - {t_to_s}': {e}")
                return []
        return intervals

    def find_price(self, time_obj, intervals):
        """Находит цену для конкретного времени.
        Поддерживает интервалы, которые НЕ пересекают полночь (t_from <= t_to)
        и которые переходят через полночь (t_from > t_to).
        Используем полузакрытый интервал [from, to) — конец исключается.
        """
        for t_from, t_to, price in intervals:
            if t_from <= t_to:
                # обычный интервал в пределах суток
                if t_from <= time_obj < t_to:
                    return price
            else:
                # интервал, который оборачивается через полночь, например 23:00 - 02:00
                if time_obj >= t_from or time_obj < t_to:
                    return price
        return None

    def calculate(self):
        if not self.lines:
            messagebox.showerror("Ошибка", "Сначала загрузите лог")
            return

        intervals = self.parse_intervals()
        if not intervals:
            return

        # Компилируем регулярку для надёжного парсинга строк урона
        dmg_re = re.compile(r'^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(\d+)\b')
        self.result = {}
        current_account = None
        skipped_not_in_intervals = 0
        skipped_no_account = 0
        bad_lines = []

        for raw in self.lines:
            line = raw.strip()
            if not line:
                continue

            # Пропускаем строки Итогов
            if line.upper().startswith("ИТОГО"):
                continue

            m = dmg_re.match(line)
            if m:
                # Строка с уронным событием
                date_str, time_str, dmg_str = m.group(1), m.group(2), m.group(3)
                try:
                    dmg = int(dmg_str)
                    time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
                except Exception as e:
                    bad_lines.append((line, f"parse error: {e}"))
                    continue

                if current_account is None:
                    # нет текущего аккаунта — лог неконсистентен
                    skipped_no_account += 1
                    continue

                price = self.find_price(time_obj, intervals)
                if price is None:
                    skipped_not_in_intervals += 1
                    # можно собирать такие строки в список для отладки
                    continue

                self.result[current_account]["damage"] += dmg
                self.result[current_account]["payment"] += dmg * price
            else:
                # Не строка урона — считаем это именем аккаунта, но пропускаем служебные заголовки
                low = line.lower()
                if any(k in low for k in ("аккаунт", "время", "урон", "цена", "итого", "не оплачиваемая")):
                    continue
                # Это — имя аккаунта
                current_account = line
                if current_account not in self.result:
                    self.result[current_account] = {"damage": 0, "payment": 0}

        info_msg = "Рассчёт завершён!"
        details = []
        if skipped_not_in_intervals:
            details.append(f"Пропущено строк (время не попало в интервалы): {skipped_not_in_intervals}")
        if skipped_no_account:
            details.append(f"Пропущено строк (нет текущего аккаунта до записи урона): {skipped_no_account}")
        if bad_lines:
            details.append(f"Строк с ошибками парсинга: {len(bad_lines)}")

        if details:
            info_msg += "\n" + "\n".join(details)

        messagebox.showinfo("Готово", info_msg)

    def save_csv(self):
        if not self.result:
            messagebox.showerror("Ошибка", "Нет данных для сохранения. Сначала рассчитайте.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return

        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            for acc, data in self.result.items():
                writer.writerow([acc, data["damage"], data["payment"]])

        messagebox.showinfo("Сохранено", f"CSV сохранён в {path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DamageCalculatorApp(root)
    root.mainloop()
