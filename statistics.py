from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMainWindow, QWidget, QFileDialog, QDateEdit, QListWidget, QListWidgetItem, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from Models import Database, Account, Order, AccountInOrder

class DataFetcher:
    def __init__(self):
        self.db = Database()

    def parse_limit(self, limit_str):
        if not limit_str:
            return None
        limit_str = limit_str.lower().replace('k', '000')
        try:
            return float(limit_str)
        except ValueError:
            return None

    def fetch_data(self):
        session = self.db.session
        query = session.query(Order, AccountInOrder, Account).join(AccountInOrder, Order.id == AccountInOrder.order_id).join(Account, AccountInOrder.account_id == Account.id)
        rows = query.all()

        records = []
        for order, account_inorder, account in rows:
            record = {
                'order_id': order.id,
                'order_name': str(order.name),
                'order_date': datetime.strptime(order.date, '%d.%m.%Y'),
                'price': order.price,
                'limit': self.parse_limit(order.limit),
                'account_id': account.id,
                'account_name': account.name,
                'tg': account.tg,
                'damage': account_inorder.damage
            }
            record['final_damage'] = min(record['damage'], record['limit']) if record['limit'] is not None else record['damage']
            record['payment'] = record['final_damage'] / 1000 * record['price']
            records.append(record)
        df = pd.DataFrame(records)
        return df

class StatisticsCalculator:
    def __init__(self, df):
        self.df = df

    def filter_data(self, orders_selected, date_from, date_to):
        filtered_df = self.df.copy()
        if orders_selected:
            filtered_df = filtered_df[filtered_df['order_name'].isin(orders_selected)]
        filtered_df = filtered_df[(filtered_df['order_date'] >= pd.Timestamp(date_from)) & (filtered_df['order_date'] <= pd.Timestamp(date_to))]
        return filtered_df

    def total_stats(self, filtered_df):
        return {
            'total_damage': filtered_df['final_damage'].sum(),
            'total_payment': filtered_df['payment'].sum()
        }

    def leadership_income(self, filtered_df, percent):
        return (filtered_df['payment'] * percent / 100).sum()

    def monthly_aggregates(self, filtered_df):
        if filtered_df.empty:
            return pd.DataFrame(columns=['order_date', 'final_damage', 'payment'])
        grouped = filtered_df.groupby(filtered_df['order_date'].dt.to_period("M")).agg({
            'final_damage': 'sum',
            'payment': 'sum'
        }).reset_index()
        grouped['order_date'] = grouped['order_date'].dt.to_timestamp()
        return grouped

class StatsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clan Stats Analysis")
        self.setGeometry(100, 100, 1200, 700)

        self.fetcher = DataFetcher()
        self.df = self.fetcher.fetch_data()
        self.stats = StatisticsCalculator(self.df)

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)

        self.order_list = QListWidget(self)
        self.order_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        for _, row in self.df[['order_name', 'order_date']].drop_duplicates().sort_values('order_date').iterrows():
            display_text = f"{row['order_name']} ({row['order_date'].strftime('%d.%m.%Y')})"
            QListWidgetItem(display_text, self.order_list)
        main_layout.addWidget(self.order_list, 1)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        date_layout = QHBoxLayout()
        self.date_from = QDateEdit(self)
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QtCore.QDate.currentDate().addMonths(-1))
        date_layout.addWidget(QLabel("Дата с:"))
        date_layout.addWidget(self.date_from)

        self.date_to = QDateEdit(self)
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QtCore.QDate.currentDate())
        date_layout.addWidget(QLabel("Дата по:"))
        date_layout.addWidget(self.date_to)

        right_layout.addLayout(date_layout)

        btn_total = QPushButton("Показать общую статистику")
        btn_total.clicked.connect(self.show_total_stats)
        right_layout.addWidget(btn_total)

        btn_leadership = QPushButton("Рассчитать доход руководства")
        btn_leadership.clicked.connect(self.prompt_leadership_income)
        right_layout.addWidget(btn_leadership)

        btn_graph = QPushButton("Показать график")
        btn_graph.clicked.connect(self.plot_graph)
        right_layout.addWidget(btn_graph)

        btn_export = QPushButton("Экспортировать в CSV")
        btn_export.clicked.connect(self.export_to_csv)
        right_layout.addWidget(btn_export)

        self.stats_label = QLabel("Статистика")
        right_layout.addWidget(self.stats_label)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(self.canvas, 1)

        main_layout.addWidget(right_panel, 3)

        self.setCentralWidget(main_widget)

    def get_selected_data(self):
        orders_selected = []
        for item in self.order_list.selectedItems():
            text = item.text()
            order_name = text.split(' (')[0]
            orders_selected.append(order_name)
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()
        filtered_df = self.stats.filter_data(orders_selected, date_from, date_to)
        if filtered_df.empty:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "Нет данных для выбранных условий!")
        return filtered_df

    def show_total_stats(self):
        filtered_df = self.get_selected_data()
        if filtered_df.empty:
            return
        stats = self.stats.total_stats(filtered_df)
        text = f"Общий урон: {int(stats['total_damage']):,}\nОбщая выплата: {stats['total_payment']:.1f}"
        self.stats_label.setText(text)

    def prompt_leadership_income(self):
        filtered_df = self.get_selected_data()
        if filtered_df.empty:
            return
        percent, ok = QtWidgets.QInputDialog.getDouble(self, "Процент дохода руководства", "Введите процент:", 100, 0, 1000, 2)
        if ok:
            income = self.stats.leadership_income(filtered_df, percent)
            self.stats_label.setText(f"Доход руководства при {percent}%: {income:,.1f}")

    def plot_graph(self):
        filtered_df = self.get_selected_data()
        if filtered_df.empty:
            self.ax.clear()
            self.ax.set_title("Нет данных для отображения")
            self.canvas.draw()
            return
        self.ax.clear()
        grouped = self.stats.monthly_aggregates(filtered_df)
        if grouped.empty:
            self.ax.set_title("Нет данных для графика")
            self.canvas.draw()
            return
        self.ax.plot(grouped['order_date'], grouped['final_damage'], label='Урон')
        self.ax.plot(grouped['order_date'], grouped['payment'], label='Выплаты')
        self.ax.legend()
        self.ax.grid(True)
        self.ax.set_title("Урон и выплаты по месяцам")
        self.canvas.draw()

    def export_to_csv(self):
        filtered_df = self.get_selected_data()
        if filtered_df.empty:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить в CSV", filter="CSV files (*.csv)")
        if path:
            filtered_df.to_csv(path, index=False)
            QtWidgets.QMessageBox.information(self, "Экспорт", f"Сохранено в {path}")

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = StatsApp()
    window.show()
    sys.exit(app.exec_())
