import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

from Models import Database, AccountInOrder, Order, Account
from StatUtils import StatUtils


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
        data = [(a.id, a.name, a.tg, a.url) for a in accounts]
        self.create_table(frame, ["id", "name", "tg", "url"], data)

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
            frame = tk.Frame(self.notebook, name="order_tab")
            self.notebook.add(frame, text=tab_text)

        # Очищаем содержимое вкладки
        for widget in frame.winfo_children():
            widget.destroy()

        orders = Database.session.query(Order).all()
        data = [(o.id, o.name, o.date, o.price, o.limit) for o in orders]
        self.create_table(frame, ["id", "name", "date", "price", "limit"], data)

        tk.Button(frame, text="Добавить заказ", command=self.open_add_order_window).pack(pady=5)

        tk.Button(frame, text="Рассчитать оплату", command=self.open_calculate_cash_window).pack(pady=5)

    def create_account_inorder_tab(self):
        tab_text = "Урон по заказам"
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

        records = Database.session.query(AccountInOrder).all()
        data = [(r.id, r.account_id, r.order_id, r.damage) for r in records]
        self.create_table(frame, ["id", "account_id", "order_id", "damage"], data)

        tk.Button(frame, text="Добавить из csv файла", command=self.open_add_accountinorder_window).pack(pady=5)

    def get_stats(self):
        order_list = []
        tree = self.notebook.children['order_tab'].children['!treeview']
        for selected_item in tree.selection():
            item = tree.item(selected_item)
            order_list.append(Database.session.query(Order).filter_by(id=item['values'][0]).first())
        info = StatUtils.order_participants(order_list)
        if info == 0:
            messagebox.showinfo('Просмотри файлы')
        else:
            messagebox.showerror('Ошибка!')

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
        def handle_new_order(order):
            print(f"Добавлен заказ: {order.name}, date: {order.date}, price: {order.price}")
                # Пересоздать содержимое
            self.create_order_tab()

        AddOrderWindow(self.root, on_save_callback=handle_new_order)

    def open_add_accountinorder_window(self):
        def handle_csv_upload(file_path):
            print("Путь к выбранному файлу:", file_path)
            self.add_account_in_order(file_path)
                # Пересоздать содержимое
            self.create_account_inorder_tab()

        AddAccountInOrderWindow(self.root, on_file_selected=handle_csv_upload)

    def add_account_in_order(self, file_path):
        content = []
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';', quotechar='|')

            for row in reader:
                content.append([row[0],row[1]])

        order_name = file_path[file_path.rfind(" ")+1:].replace(".csv", "")
        session = Database.session

        try:
            for member in content:
                account = session.query(Account).filter_by(name=member[0]).first()
                order = session.query(Order).filter_by(name=order_name).first()

                new_account_in_order = AccountInOrder(account_id=account.id, order_id=order.id, damage=float(member[1]))

                session.add(new_account_in_order)
        except Exception as e:
            messagebox.showerror("Ошибка БД!", str(e))
        finally:
            session.commit()
            messagebox.showinfo("Все участники добавлены в заказ!")



    def open_calculate_cash_window(self):

        def handle_payment_calc(order, participants, mode, covered_by):
            print("Заказ:", order.name)
            print("Участники:", [a.name for a in participants])
            print("Режим:", mode)
            if mode == "covered":
                print("За чей счёт:", [a.name for a in covered_by])
            self.calculate_cash(order, participants, mode, covered_by)

        PaymentCalcWindow(self.root, handle_payment_calc)

    def calculate_cash(self, order, participants, mode, covered_by):
        session = Database.session
        covered_count = len(covered_by)

        cashlist = [('Аккаунт', 'tg', 'Дамаг учтён.', 'Плата')]

        for p in participants:
            ainord = session.query(AccountInOrder).filter_by(account_id=p.id, order_id=order.id).first()
            if p not in covered_by:
                row = (p.name, p.tg, int(ainord.damage), int(ainord.damage * order.price))
            else:
                messagebox.showwarning('Не реализовано!')
            cashlist.append(row)

        with open(f'{order.name} выплаты.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_NONE)
            writer.writerows(cashlist)


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

        tk.Label(self.top, text="Лимит (Например 1kkk):").pack(anchor='w', padx=10, pady=(10, 0))
        self.limit_entry = tk.Entry(self.top)
        self.limit_entry.pack(fill=tk.X, padx=10)

        # Кнопка сохранить
        tk.Button(self.top, text="Сохранить", command=self.save).pack(pady=10)

    def save(self):
        name = self.name_entry.get().strip()
        date = self.date_entry.get().strip()
        price = self.price_entry.get().strip()
        limit = self.limit_entry.get().strip()

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
            order = Order(name=name, date=date, price=float(price), limit=limit)
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

class AddAccountInOrderWindow:
    def __init__(self, master, on_file_selected):
        """
        :param master: родительское окно
        :param on_file_selected: функция, которая принимает путь к выбранному CSV файлу
        """
        self.on_file_selected = on_file_selected

        self.top = tk.Toplevel(master)
        self.top.title("Загрузка CSV")
        self.top.geometry("300x100")
        self.top.resizable(False, False)
        self.top.grab_set()

        tk.Label(self.top, text="Выберите CSV-файл:").pack(pady=(10, 5))

        tk.Button(self.top, text="Загрузить CSV", command=self.load_csv).pack(pady=5)

    def load_csv(self):
        file_path = filedialog.askopenfilename(
            title="Выберите CSV файл",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")]
        )

        if file_path:
            try:
                self.on_file_selected(file_path)
                self.top.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обработать файл:\n{e}")

class PaymentCalcWindow:
    def __init__(self, master, on_calculate):
        """
        :param master: родительское окно
        :param on_calculate: функция (order: Order, participants: list[Account], mode: str, covered_by: list[Account])
        """
        self.on_calculate = on_calculate
        self.top = tk.Toplevel(master)
        self.top.title("Рассчёт оплаты")
        self.top.geometry("500x500")
        self.top.grab_set()
        self.session = Database.session

        # --- Комбобокс заказов ---
        tk.Label(self.top, text="Выберите заказ:").pack(pady=5)
        self.order_combobox = ttk.Combobox(self.top, state="readonly")
        self.order_combobox.pack(fill='x', padx=10)
        self.order_combobox.bind("<<ComboboxSelected>>", self.on_order_selected)

        # --- Участники заказа ---
        tk.Label(self.top, text="Участники заказа:").pack(pady=5)
        self.participants_listbox = tk.Listbox(self.top, selectmode=tk.MULTIPLE, height=6)
        self.participants_listbox.pack(fill='both', padx=10, pady=5, expand=True)

        # --- Радиокнопки режима ---
        self.mode_var = tk.StringVar(value="nolimit")
        frame_mode = tk.Frame(self.top)
        frame_mode.pack(pady=5)
        tk.Radiobutton(frame_mode, text="БЕЗ ЛИМИТА", variable=self.mode_var, value="nolimit", command=self.on_mode_changed).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(frame_mode, text="ПЕРЕЛИВ ЗА СЧЁТ", variable=self.mode_var, value="covered", command=self.on_mode_changed).pack(side=tk.LEFT, padx=10)

        # --- Список "за чей счёт" ---
        self.covered_listbox_label = tk.Label(self.top, text="Выберите, за чей счёт:")
        self.covered_listbox = tk.Listbox(self.top, selectmode=tk.MULTIPLE, height=4)

        # --- Кнопка "Рассчитать" ---
        tk.Button(self.top, text="Рассчитать", command=self.calculate).pack(pady=10)

        # --- Данные ---
        self.orders = []  # список Order
        self.order_map = {}  # название -> Order
        self.current_accounts = []

        self.load_orders()

    def load_orders(self):
        orders = self.session.query(Order).join(AccountInOrder).distinct().all()
        self.orders = orders
        names = [f"{o.id}: {o.name}" for o in orders]
        self.order_map = {f"{o.id}: {o.name}": o for o in orders}
        self.order_combobox["values"] = names

    def on_order_selected(self, event=None):
        selection = self.order_combobox.get()
        order = self.order_map.get(selection)
        if not order:
            return

        # Получаем всех участников этого заказа
        links = self.session.query(AccountInOrder).filter_by(order_id=order.id).all()
        account_ids = [l.account_id for l in links]
        self.current_accounts = self.session.query(Account).filter(Account.id.in_(account_ids)).all()

        self.update_participants_list()

    def update_participants_list(self):
        self.participants_listbox.delete(0, tk.END)
        for acc in self.current_accounts:
            self.participants_listbox.insert(tk.END, f"{acc.id}: {acc.name}")

        self.covered_listbox.delete(0, tk.END)
        for acc in self.current_accounts:
            self.covered_listbox.insert(tk.END, f"{acc.id}: {acc.name}")

    def on_mode_changed(self):
        if self.mode_var.get() == "covered":
            self.covered_listbox_label.pack(pady=5)
            self.covered_listbox.pack(fill='both', padx=10)
        else:
            self.covered_listbox_label.pack_forget()
            self.covered_listbox.pack_forget()

    def calculate(self):
        selection = self.order_combobox.get()
        order = self.order_map.get(selection)
        if not order:
            messagebox.showwarning("Ошибка", "Выберите заказ.")
            return

        # Получаем всех участников заказа
        participants = (
            self.session.query(Account)
            .join(AccountInOrder, Account.id == AccountInOrder.account_id)
            .filter(AccountInOrder.order_id == order.id)
            .all()
        )
        mode = self.mode_var.get()
        covered_by = []

        if mode == "covered":
            covered_idxs = self.covered_listbox.curselection()
            if not covered_idxs:
                messagebox.showwarning("Ошибка", "Выберите, за чей счёт.")
                return
            covered_by = [self.current_accounts[i] for i in covered_idxs]

        self.on_calculate(order, participants, mode, covered_by)
        self.top.destroy()
