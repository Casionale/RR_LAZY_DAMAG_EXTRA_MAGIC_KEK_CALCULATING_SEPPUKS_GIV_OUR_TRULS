import tkinter as tk
from tkinter import filedialog, messagebox
import csv
import os
from collections import defaultdict

from Models import Database, Account


def process_csv_files(file_paths):
    grouped_data = defaultdict(list)

    for file_path in file_paths:
        filename = os.path.splitext(os.path.basename(file_path))[0]
        try:
            with open(file_path, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, delimiter=';')
                for row in reader:
                    tg = row['tg']
                    grouped_data[tg].append({
                        'filename': filename,
                        'account': row['Аккаунт'],
                        'url': row['url'],
                        'payment': int(row['Плата'])
                    })
        except Exception as e:
            messagebox.showerror("Ошибка чтения файла", f"{file_path}:\n{e}")
            continue

    # Формируем табличный вывод с табуляцией
    output = []
    for tg, entries in grouped_data.items():
        url_by_tg = get_payment_acc_ny_tg(tg)
        output.append(f"{tg}\t{ url_by_tg if url_by_tg is not None else entries[0]['url'] }")
        output.append("Файл\tАккаунт\tПлата")
        for entry in entries:
            output.append(f"{entry['filename']}\t{entry['account']}\t{entry['payment']}")
        output.append(f"\tИТОГО:\t{sum(e['payment'] for e in entries)}\n")
    return "\n".join(output)


def select_files():
    file_paths = filedialog.askopenfilenames(
        title="Выберите CSV-файлы",
        filetypes=[("CSV files", "*.csv")]
    )
    if file_paths:
        result = process_csv_files(file_paths)
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, result)


def copy_to_clipboard():
    data = output_text.get(1.0, tk.END)
    root.clipboard_clear()
    root.clipboard_append(data)
    messagebox.showinfo("Готово", "Результат скопирован в буфер обмена!\nВставь в Excel или Google Таблицы.")

def get_payment_acc_ny_tg(tg):
    account = Database.session.query(Account).filter_by(tg=tg, payable=True).first()
    if account is None:
        return None
    return account.url


# Создание окна
root = tk.Tk()
root.title("Группировка CSV по Telegram")

frame = tk.Frame(root)
frame.pack(pady=10)

select_button = tk.Button(frame, text="Выбрать CSV-файлы", command=select_files)
select_button.pack(side=tk.LEFT, padx=5)

copy_button = tk.Button(frame, text="Копировать в буфер", command=copy_to_clipboard)
copy_button.pack(side=tk.LEFT, padx=5)

output_text = tk.Text(root, wrap=tk.NONE, height=25, width=100)
output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

root.mainloop()
