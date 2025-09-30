import tkinter as tk
from tkinter import messagebox
import pymysql

# === настройки базы ===
DB_CONFIG = {
    "host": "194.87.186.28",
    "user": "NS_USER",
    "password": "wLQuFUzmWsr1zJ",
    "database": "NS",
    "charset": "utf8mb4"
}


def parse_input(text):
    """Разбираем текст вида [СК] Имя;число; -> [(name, number), ...]"""
    rows = []
    for line in text.strip().splitlines():
        parts = line.strip().split(";")
        if len(parts) >= 2:
            name = parts[0].strip()
            try:
                num = int(parts[1])
            except ValueError:
                num = None
            rows.append((name, num))
    return rows


def check_accounts():
    text = input_text.get("1.0", tk.END)
    rows = parse_input(text)

    if not rows:
        messagebox.showerror("Ошибка", "Нет корректных строк для обработки!")
        return

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cur = conn.cursor()

        # создаём временную таблицу
        cur.execute("DROP TEMPORARY TABLE IF EXISTS tmp_accounts_new;")
        cur.execute("""
            CREATE TEMPORARY TABLE tmp_accounts_new (
                name   VARCHAR(255),
                damage BIGINT
            );
        """)

        # вставляем данные
        for name, dmg in rows:
            cur.execute("INSERT INTO tmp_accounts_new (name, damage) VALUES (%s, %s)", (name, dmg))

        # выбираем те, которых нет в NS.account
        cur.execute("""
            SELECT t.name, t.damage
            FROM tmp_accounts_new t
            LEFT JOIN NS.account a ON a.name = t.name
            WHERE a.id IS NULL;
        """)
        result = cur.fetchall()

        # выводим
        output_text.delete("1.0", tk.END)
        if result:
            for name, dmg in result:
                output_text.insert(tk.END, f"{name} ({dmg})\n")
        else:
            output_text.insert(tk.END, "Все аккаунты уже есть в базе.\n")

        cur.close()
        conn.close()

    except Exception as e:
        messagebox.showerror("Ошибка БД", str(e))


# === GUI ===
root = tk.Tk()
root.title("Проверка аккаунтов")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill="both", expand=True)

tk.Label(frame, text="Вставьте список аккаунтов:").pack(anchor="w")
input_text = tk.Text(frame, height=15, width=80)
input_text.pack(fill="both", expand=True, pady=5)

tk.Button(frame, text="Проверить", command=check_accounts).pack(pady=5)

tk.Label(frame, text="Результат (отсутствуют в NS.account):").pack(anchor="w")
output_text = tk.Text(frame, height=10, width=80, bg="#f5f5f5")
output_text.pack(fill="both", expand=True, pady=5)

root.mainloop()
