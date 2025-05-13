import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

from cloudscraper import session

from Models import Database, AccountInOrder, Order, Account


class OrderStatsWindow:
    def __init__(self, root):
        self.root = tk.Toplevel(root)
        self.root.title("Статистика заказов")
        self.root.geometry("800x600")  # Можно задать начальные размеры окна

        # Основной фрейм
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Левая текстовая панель
        self.left_text = tk.Text(self.main_frame, wrap=tk.WORD, width=30)
        self.left_text.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Вкладки
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Добавляем вкладки
        self.create_account_tab()
        self.create_order_tab()
        self.create_account_inorder_tab()

        # Нижняя панель с кнопками
        self.button_panel = tk.Frame(self.main_frame)
        self.button_panel.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # Кнопки
        self.btn_add_csv = tk.Button(self.button_panel, text="Добавить csv", command=self.add_csv)
        self.btn_add_csv.pack(side=tk.LEFT, padx=5)

        self.btn_get_stats = tk.Button(self.button_panel, text="Получить статистику", command=self.get_stats)
        self.btn_get_stats.pack(side=tk.LEFT, padx=5)

        self.btn_calculate = tk.Button(self.button_panel, text="Рассчитать", command=self.calculate)
        self.btn_calculate.pack(side=tk.LEFT, padx=5)




    def create_table(self, parent, columns, data):
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=tk.CENTER)
        for row in data:
            tree.insert('', tk.END, values=row)
        tree.pack(fill=tk.BOTH, expand=True)

    def create_account_tab(self):
        tab_text = "Аккаунты"
        frame = None

        # Ищем существующую вкладку с именем "Аккаунты"
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == tab_text:
                frame = self.notebook.nametowidget(self.notebook.tabs()[i])
                break

        if frame is None:
            # Если не нашли — создаём новую
            frame = tk.Frame(self.notebook)
            self.notebook.add(frame, text=tab_text)

        # Очищаем содержимое вкладки
        for widget in frame.winfo_children():
            widget.destroy()

        # Загружаем данные из БД и отображаем
        accounts = Database.session.query(Account).all()
        data = [(a.id, a.name, a.tg) for a in accounts]
        self.create_table(frame, ["id", "name", "tg"], data)

        # Добавляем кнопку "Добавить аккаунт"
        tk.Button(frame, text="Добавить аккаунт", command=self.open_add_account_window).pack(pady=5)

    def create_order_tab(self):
        tab_text = "Заказы"
        frame = None

        # Ищем существующую вкладку с именем "Аккаунты"
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == tab_text:
                frame = self.notebook.nametowidget(self.notebook.tabs()[i])
                break

        if frame is None:
            # Если не нашли — создаём новую
            frame = tk.Frame(self.notebook)
            self.notebook.add(frame, text=tab_text)

        # Очищаем содержимое вкладки
        for widget in frame.winfo_children():
            widget.destroy()

        orders = Database.session.query(Order).all()
        data = [(o.id, o.name, o.date, o.price) for o in orders]
        self.create_table(frame, ["id", "name", "date", "price"], data)

        tk.Button(frame, text="Добавить заказ", command=self.open_add_order_window).pack(pady=5)

    def create_account_inorder_tab(self):
        frame = tk.Frame(self.notebook)
        self.notebook.add(frame, text="Урон по заказам")
        records = Database.session.query(AccountInOrder).all()
        data = [(r.id, r.account_id, r.order_id, r.damage) for r in records]
        self.create_table(frame, ["id", "account_id", "order_id", "damage"], data)

    def add_csv(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")],
            title="Выберите CSV-файл"
        )
        if file_path:
            print("Выбран файл:", file_path)
            self.left_text.insert(tk.END, file_path[file_path.rfind("/")+1:])
            return file_path

    def get_stats(self):
        # Заглушка
        pass

    def calculate(self):
        # Заглушка
        pass

    def open_add_account_window(self):
        def handle_new_account(account):
            print(f"Добавлен аккаунт: {account.name}, tg: {account.tg}")
                # Пересоздать содержимое
            self.create_account_tab()

        AddAccountWindow(self.root, on_save_callback=handle_new_account)

    def open_add_order_window(self):
        def handle_new_account(account):
            print(f"Добавлен заказ: {account.name}, date: {account.tg}, price: {account.price}")
                # Пересоздать содержимое
            self.create_order_tab()

        AddOrderWindow(self.root, on_save_callback=handle_new_account)

class AddAccountWindow:
    def __init__(self, master, on_save_callback=None):
        self.top = tk.Toplevel(master)
        self.top.title("Добавить аккаунт")
        self.top.geometry("300x150")
        self.top.resizable(False, False)
        self.top.grab_set()  # Модальное окно

        self.on_save_callback = on_save_callback

        # Метки и поля ввода
        tk.Label(self.top, text="Имя:").pack(anchor='w', padx=10, pady=(10, 0))
        self.name_entry = tk.Entry(self.top)
        self.name_entry.pack(fill=tk.X, padx=10)

        tk.Label(self.top, text="Telegram:").pack(anchor='w', padx=10, pady=(10, 0))
        self.tg_entry = tk.Entry(self.top)
        self.tg_entry.pack(fill=tk.X, padx=10)

        # Кнопка сохранить
        tk.Button(self.top, text="Сохранить", command=self.save).pack(pady=10)

    def save(self):
        name = self.name_entry.get().strip()
        tg = self.tg_entry.get().strip()

        if not name or not tg:
            messagebox.showwarning("Ошибка", "Поля не должны быть пустыми")
            return

        session = Database.session

        try:
            # Проверка, есть ли уже аккаунт с таким Telegram
            existing = session.query(Account).filter_by(name=name).first()
            if existing:
                messagebox.showerror("Ошибка", f"Пользователь с именем '{name}' уже существует")
                return

            # Создание и сохранение аккаунта
            account = Account(name=name, tg=tg)
            session.add(account)
            session.commit()

            messagebox.showinfo("Успешно", "Аккаунт добавлен")

            if self.on_save_callback:
                self.on_save_callback(account)

            self.top.destroy()

        except Exception as e:
            session.rollback()
            messagebox.showerror("Ошибка БД", str(e))
        finally:
            session.close()

class AddOrderWindow:
    def __init__(self, master, on_save_callback=None):
        self.top = tk.Toplevel(master)
        self.top.title("Добавить заказ")
        self.top.geometry("300x250")
        self.top.resizable(False, False)
        self.top.grab_set()  # Модальное окно

        self.on_save_callback = on_save_callback

        # Метки и поля ввода
        tk.Label(self.top, text="Имя:").pack(anchor='w', padx=10, pady=(10, 0))
        self.name_entry = tk.Entry(self.top)
        self.name_entry.pack(fill=tk.X, padx=10)

        tk.Label(self.top, text="Дата DD.MM.YYYY:").pack(anchor='w', padx=10, pady=(10, 0))
        self.date_entry = tk.Entry(self.top)
        self.date_entry.pack(fill=tk.X, padx=10)

        tk.Label(self.top, text="Цена:").pack(anchor='w', padx=10, pady=(10, 0))
        self.price_entry = tk.Entry(self.top)
        self.price_entry.pack(fill=tk.X, padx=10)

        # Кнопка сохранить
        tk.Button(self.top, text="Сохранить", command=self.save).pack(pady=10)

    def save(self):
        name = self.name_entry.get().strip()
        date = self.date_entry.get().strip()
        price = self.price_entry.get().strip()

        if not name or not date or not price:
            messagebox.showwarning("Ошибка", "Поля не должны быть пустыми")
            return

        session = Database.session

        try:
            # Проверка, есть ли
            existing = session.query(Order).filter_by(name=name).first()
            if existing:
                messagebox.showerror("Ошибка", f"Заказ с именем '{name}' уже существует")
                return

            # Создание и сохранение аккаунта
            order = Order(name=name, date=date, price=float(price))
            session.add(order)
            session.commit()

            messagebox.showinfo("Успешно", "Заказ добавлен")

            if self.on_save_callback:
                self.on_save_callback(order)

            self.top.destroy()

        except Exception as e:
            session.rollback()
            messagebox.showerror("Ошибка БД", str(e))
        finally:
            session.close()