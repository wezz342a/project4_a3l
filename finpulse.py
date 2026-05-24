# FinPulse — Finance App
# Python + PyQt6 + SQLite + qtawesome + matplotlib

import sys
import sqlite3
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("QtAgg")

import qtawesome as qta
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLineEdit,
    QMessageBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QProgressBar,
    QStackedWidget,
    QScrollArea,
    QGridLayout,
    QDialog,
    QGraphicsDropShadowEffect,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# работа с базой данных
conn = sqlite3.connect("finpulse.db")
cursor = conn.cursor()

# таблица для транзакций
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    category TEXT,
    amount REAL,
    date TEXT
)
""")

# таблица для целей
cursor.execute("""
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    target REAL,
    saved REAL
)
""")

# настройки бюджета
cursor.execute("""
CREATE TABLE IF NOT EXISTS budget_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period TEXT,
    amount REAL
)
""")

conn.commit()


# стили интерфейса
STYLESHEET = """
QWidget {
    background-color: #0B1120;
    color: #F1F5F9;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}

QFrame {
    background-color: #111827;
    border-radius: 16px;
    border: 1px solid #1E293B;
}

QLabel {
    background: transparent;
    color: #F1F5F9;
}

QPushButton {
    background-color: #3B82F6;
    border: none;
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    min-height: 36px;
}

QPushButton:hover {
    background-color: #60A5FA;
}

QPushButton:pressed {
    background-color: #2563EB;
}

QPushButton#danger_btn {
    background-color: #EF4444;
}

QPushButton#danger_btn:hover {
    background-color: #F87171;
}

QPushButton#success_btn {
    background-color: #10B981;
    min-width: 100px;
}

QPushButton#success_btn:hover {
    background-color: #34D399;
}

QPushButton#secondary_btn {
    background-color: #475569;
    min-width: 100px;
}

QPushButton#secondary_btn:hover {
    background-color: #64748B;
}

QPushButton#sidebar_btn {
    background-color: transparent;
    text-align: left;
    padding: 10px 16px;
    border-radius: 12px;
}

QPushButton#sidebar_btn:hover {
    background-color: #1E293B;
}

QPushButton#sidebar_btn[active="true"] {
    background-color: #3B82F6;
}

QLineEdit, QComboBox {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 8px 12px;
    min-height: 32px;
    color: #F1F5F9;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #3B82F6;
}

QTableWidget {
    background-color: #111827;
    border: none;
    border-radius: 12px;
    gridline-color: transparent;
}

QTableWidget::item {
    padding: 12px;
    border-bottom: 1px solid #1E293B;
    color: #CBD5E1;
}

QTableWidget::item:selected {
    background-color: rgba(59, 130, 246, 0.2);
}

QHeaderView::section {
    background-color: #0F172A;
    border: none;
    padding: 12px;
    font-weight: 600;
    color: #94A3B8;
    font-size: 12px;
}

QProgressBar {
    border: none;
    background-color: #1E293B;
    border-radius: 8px;
    text-align: center;
    height: 28px;
    font-weight: 600;
}

QProgressBar::chunk {
    background-color: #3B82F6;
    border-radius: 8px;
}

QProgressBar[danger="true"]::chunk {
    background-color: #EF4444;
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: #111827;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}
"""


# тень для карточек
def add_shadow(widget, blur=20, offset_y=5, opacity=60):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(offset_y)
    shadow.setColor(QColor(0, 0, 0, opacity))
    widget.setGraphicsEffect(shadow)


# диалог создания новой цели
class AddGoalDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Новая цель")
        self.setFixedSize(400, 420)
        self.setStyleSheet(STYLESHEET)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(15)

        title = QLabel("Новая цель")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #3B82F6;")

        layout.addWidget(title)

        layout.addWidget(QLabel("Название"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Например: Новая машина")
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("Целевая сумма (руб.)"))
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("500000")
        layout.addWidget(self.target_input)

        layout.addWidget(QLabel("Накоплено (руб.)"))
        self.saved_input = QLineEdit()
        self.saved_input.setPlaceholderText("0")
        layout.addWidget(self.saved_input)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("secondary_btn")
        self.cancel_btn.setMinimumHeight(36)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setObjectName("success_btn")
        self.ok_btn.setMinimumHeight(36)
        self.ok_btn.clicked.connect(self.save_goal)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def save_goal(self):
        title = self.title_input.text()
        target_text = self.target_input.text().replace(" ", "")
        saved_text = self.saved_input.text().replace(" ", "")

        if not title or not target_text:
            QMessageBox.warning(self, "Ошибка", "Заполните название и сумму")
            return

        try:
            target = float(target_text)
            saved = float(saved_text) if saved_text else 0
            if target <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректные суммы")
            return

        cursor.execute("INSERT INTO goals(title, target, saved) VALUES (?, ?, ?)", (title, target, saved))
        conn.commit()
        self.accept()


# главное окно приложения
class FinPulse(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("FinPulse")
        self.resize(1400, 850)
        self.setStyleSheet(STYLESHEET)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        self.setLayout(self.main_layout)

        # верхняя панель с заголовком и поиском
        header = QHBoxLayout()
        
        title = QLabel("FinPulse")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #3B82F6;")

        # поле поиска
        search_frame = QFrame()
        search_frame.setFixedWidth(280)
        search_frame.setStyleSheet("background-color: #1E293B; border-radius: 20px;")
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(12, 6, 12, 6)
        search_icon = QLabel()
        search_icon.setPixmap(qta.icon("fa5s.search").pixmap(14, 14))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        self.search_input.setStyleSheet("border: none; background: transparent; padding: 0;")
        self.search_input.textChanged.connect(self.search_transactions)
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_input)
        search_frame.setLayout(search_layout)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(search_frame)

        self.main_layout.addLayout(header)

        # основное содержимое
        content = QHBoxLayout()
        content.setSpacing(20)

        # боковое меню
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #111827; border-radius: 16px;")
        
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(8)
        
        self.home_btn = QPushButton(qta.icon("fa5s.home"), "  Главная")
        self.home_btn.setObjectName("sidebar_btn")
        self.home_btn.setProperty("active", True)
        self.home_btn.setMinimumHeight(44)
        
        self.transactions_btn = QPushButton(qta.icon("fa5s.wallet"), "  Транзакции")
        self.transactions_btn.setObjectName("sidebar_btn")
        self.transactions_btn.setProperty("active", False)
        self.transactions_btn.setMinimumHeight(44)
        
        self.goals_btn = QPushButton(qta.icon("fa5s.bullseye"), "  Цели")
        self.goals_btn.setObjectName("sidebar_btn")
        self.goals_btn.setProperty("active", False)
        self.goals_btn.setMinimumHeight(44)
        
        self.analytics_btn = QPushButton(qta.icon("fa5s.chart-line"), "  Аналитика")
        self.analytics_btn.setObjectName("sidebar_btn")
        self.analytics_btn.setProperty("active", False)
        self.analytics_btn.setMinimumHeight(44)
        
        sidebar_layout.addWidget(self.home_btn)
        sidebar_layout.addWidget(self.transactions_btn)
        sidebar_layout.addWidget(self.goals_btn)
        sidebar_layout.addWidget(self.analytics_btn)
        sidebar_layout.addStretch()
        
        sidebar.setLayout(sidebar_layout)
        
        # переключение страниц
        self.stack = QStackedWidget()
        
        self.dashboard_tab = QWidget()
        self.transactions_tab = QWidget()
        self.goals_tab = QWidget()
        self.analytics_tab = QWidget()
        
        self.stack.addWidget(self.dashboard_tab)
        self.stack.addWidget(self.transactions_tab)
        self.stack.addWidget(self.goals_tab)
        self.stack.addWidget(self.analytics_tab)
        
        self.home_btn.clicked.connect(lambda: self.switch_page(0))
        self.transactions_btn.clicked.connect(lambda: self.switch_page(1))
        self.goals_btn.clicked.connect(lambda: self.switch_page(2))
        self.analytics_btn.clicked.connect(lambda: self.switch_page(3))
        
        content.addWidget(sidebar)
        content.addWidget(self.stack, 1)
        
        self.main_layout.addLayout(content)

        # создаем все страницы
        self.build_dashboard()
        self.build_transactions()
        self.build_goals()
        self.build_analytics()

        self.load_transactions()
        self.update_all()

    def closeEvent(self, event):
        conn.close()
        event.accept()

    # поиск по транзакциям
    def search_transactions(self, text):
        if not text:
            self.load_transactions()
            return
        
        cursor.execute("""
            SELECT * FROM transactions 
            WHERE category LIKE ? OR CAST(amount AS TEXT) LIKE ? OR type LIKE ?
            ORDER BY id DESC
        """, (f'%{text}%', f'%{text}%', f'%{text}%'))
        
        data = cursor.fetchall()
        
        self.table.clearSpans()
        
        if not data:
            self.table.setRowCount(1)
            self.table.setSpan(0, 0, 1, 5)
            empty_item = QTableWidgetItem("📭 Нет транзакций")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_item.setForeground(QColor("#94A3B8"))
            self.table.setItem(0, 0, empty_item)
            return
        
        self.table.setRowCount(len(data))
        
        for row_index, row_data in enumerate(data):
            for col_index, item in enumerate(row_data):
                if col_index == 4 and isinstance(item, str) and '-' in item:
                    try:
                        date_obj = datetime.strptime(item, "%Y-%m-%d")
                        display_item = date_obj.strftime("%d.%m.%Y")
                    except:
                        display_item = item
                else:
                    display_item = str(item)
                
                cell = QTableWidgetItem(display_item)
                
                if col_index == 3:
                    if row_data[1] == "Доход":
                        cell.setForeground(QColor("#10B981"))
                    else:
                        cell.setForeground(QColor("#EF4444"))
                
                self.table.setItem(row_index, col_index, cell)
        
        self.table.setColumnWidth(0, 60)

    # переключение между вкладками
    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        
        buttons = [self.home_btn, self.transactions_btn, self.goals_btn, self.analytics_btn]
        for i, btn in enumerate(buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # главная страница с карточками и бюджетом
    def build_dashboard(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        self.dashboard_tab.setLayout(layout)

        cards_grid = QGridLayout()
        cards_grid.setSpacing(20)

        self.income_card = self.create_card("📈 Доходы", "0 руб.", "#10B981")
        self.expense_card = self.create_card("📉 Расходы", "0 руб.", "#EF4444")
        self.balance_card = self.create_card("💰 Баланс", "0 руб.", "#3B82F6")

        cards_grid.addWidget(self.income_card, 0, 0)
        cards_grid.addWidget(self.expense_card, 0, 1)
        cards_grid.addWidget(self.balance_card, 0, 2)

        layout.addLayout(cards_grid)

        # блок бюджета
        budget_frame = QFrame()
        budget_frame.setMaximumWidth(500)
        add_shadow(budget_frame)

        budget_layout = QVBoxLayout()
        budget_layout.setContentsMargins(24, 24, 24, 24)
        budget_layout.setSpacing(15)

        budget_frame.setLayout(budget_layout)

        budget_title = QLabel("📊 Бюджет")
        budget_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))

        self.budget_period = QComboBox()
        self.budget_period.addItems(["Неделя", "Месяц", "Год"])
        self.budget_period.currentTextChanged.connect(self.update_budget)

        self.budget_amount = QLineEdit()
        self.budget_amount.setPlaceholderText("Сумма бюджета")

        set_budget_btn = QPushButton("Установить")
        set_budget_btn.setMaximumWidth(150)
        set_budget_btn.clicked.connect(self.set_budget)

        self.budget_progress = QProgressBar()
        self.budget_progress.setFormat("")
        self.budget_progress.setProperty("danger", False)

        budget_layout.addWidget(budget_title)
        budget_layout.addWidget(self.budget_period)
        budget_layout.addWidget(self.budget_amount)
        budget_layout.addWidget(set_budget_btn)
        budget_layout.addWidget(self.budget_progress)

        layout.addWidget(budget_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    # создание карточки для дашборда
    def create_card(self, title, value, color):
        card = QFrame()
        card.setMinimumHeight(130)
        add_shadow(card)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(8)

        card.setLayout(layout)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #94A3B8; font-size: 14px;")

        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()

        card.value_label = value_label
        return card

    # страница с транзакциями
    def build_transactions(self):
        root = QHBoxLayout()
        root.setSpacing(20)

        self.transactions_tab.setLayout(root)

        # левая панель - форма добавления
        left_panel = QFrame()
        left_panel.setMaximumWidth(320)
        add_shadow(left_panel)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)

        left_panel.setLayout(left_layout)

        panel_title = QLabel("➕ Добавить")
        panel_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Все", "Доходы", "Расходы"])
        self.filter_combo.currentTextChanged.connect(self.load_transactions)

        self.type_box = QComboBox()
        self.type_box.addItems(["Доход", "Расход"])
        self.type_box.currentTextChanged.connect(self.update_categories)

        self.category_box = QComboBox()
        self.update_categories()

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Сумма")

        add_btn = QPushButton(qta.icon("fa5s.check"), "  Добавить")
        add_btn.setObjectName("success_btn")
        add_btn.clicked.connect(self.add_transaction)

        delete_btn = QPushButton(qta.icon("fa5s.trash"), "  Удалить")
        delete_btn.setObjectName("danger_btn")
        delete_btn.clicked.connect(self.delete_transaction)

        left_layout.addWidget(panel_title)
        left_layout.addWidget(QLabel("Фильтр"))
        left_layout.addWidget(self.filter_combo)
        left_layout.addSpacing(10)
        left_layout.addWidget(QLabel("Тип"))
        left_layout.addWidget(self.type_box)
        left_layout.addWidget(QLabel("Категория"))
        left_layout.addWidget(self.category_box)
        left_layout.addWidget(QLabel("Сумма"))
        left_layout.addWidget(self.amount_input)
        left_layout.addSpacing(15)
        left_layout.addWidget(add_btn)
        left_layout.addWidget(delete_btn)
        left_layout.addStretch()

        # правая панель - таблица
        right_panel = QFrame()
        add_shadow(right_panel)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(20, 20, 20, 20)

        right_panel.setLayout(right_layout)

        table_title = QLabel("📋 История")
        table_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Тип", "Категория", "Сумма", "Дата"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        right_layout.addWidget(table_title)
        right_layout.addSpacing(10)
        right_layout.addWidget(self.table)

        root.addWidget(left_panel)
        root.addWidget(right_panel)

    # обновление категорий в зависимости от типа
    def update_categories(self):
        self.category_box.clear()

        if self.type_box.currentText() == "Доход":
            categories = ["Зарплата", "Фриланс", "Инвестиции", "Подарок", "Возврат", "Другое"]
        else:
            categories = ["Еда", "Транспорт", "Развлечения", "Покупки", "Коммунальные", 
                         "Здоровье", "Кафе", "Подписки", "Образование", "Другое"]

        self.category_box.addItems(categories)

    # добавление новой транзакции
    def add_transaction(self):
        try:
            amount = float(self.amount_input.text().replace(",", "."))
            if amount <= 0:
                raise ValueError
        except:
            QMessageBox.warning(self, "Ошибка", "Введите сумму")
            return

        current_date = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("""
            INSERT INTO transactions(type, category, amount, date)
            VALUES (?, ?, ?, ?)
        """, (
            self.type_box.currentText(),
            self.category_box.currentText(),
            amount,
            current_date
        ))

        conn.commit()
        self.amount_input.clear()
        self.load_transactions()
        self.update_all()

    # удаление выбранной транзакции
    def delete_transaction(self):
        row = self.table.currentRow()

        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите транзакцию")
            return

        transaction_id = int(self.table.item(row, 0).text())

        reply = QMessageBox.question(self, "Удалить?", "Удалить эту транзакцию?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            cursor.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))
            conn.commit()
            self.load_transactions()
            self.update_all()

    # загрузка транзакций в таблицу
    def load_transactions(self):
        filter_type = self.filter_combo.currentText()

        if filter_type == "Доходы":
            cursor.execute("SELECT * FROM transactions WHERE type='Доход' ORDER BY id DESC")
        elif filter_type == "Расходы":
            cursor.execute("SELECT * FROM transactions WHERE type='Расход' ORDER BY id DESC")
        else:
            cursor.execute("SELECT * FROM transactions ORDER BY id DESC")

        data = cursor.fetchall()
        
        self.table.clearSpans()

        if not data:
            self.table.setRowCount(1)
            self.table.setSpan(0, 0, 1, 5)
            empty_item = QTableWidgetItem("📭 Нет транзакций")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_item.setForeground(QColor("#94A3B8"))
            self.table.setItem(0, 0, empty_item)
            return

        self.table.setRowCount(len(data))

        for row_index, row_data in enumerate(data):
            for col_index, item in enumerate(row_data):
                if col_index == 4 and isinstance(item, str) and '-' in item:
                    try:
                        date_obj = datetime.strptime(item, "%Y-%m-%d")
                        display_item = date_obj.strftime("%d.%m.%Y")
                    except:
                        display_item = item
                else:
                    display_item = str(item)
                
                cell = QTableWidgetItem(display_item)
                
                if col_index == 3:
                    if row_data[1] == "Доход":
                        cell.setForeground(QColor("#10B981"))
                    else:
                        cell.setForeground(QColor("#EF4444"))
                
                self.table.setItem(row_index, col_index, cell)

        self.table.setColumnWidth(0, 60)

    # обновление статистики на дашборде
    def update_stats(self):
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='Доход'")
        income = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='Расход'")
        expense = cursor.fetchone()[0]

        balance = income - expense

        self.income_card.value_label.setText(f"{income:,.0f} руб.")
        self.expense_card.value_label.setText(f"{expense:,.0f} руб.")
        self.balance_card.value_label.setText(f"{balance:,.0f} руб.")

    # получение лимита бюджета
    def get_budget_limit(self):
        period = self.budget_period.currentText()
        
        if period == "Неделя":
            days = 7
        elif period == "Год":
            days = 365
        else:
            days = 30

        cursor.execute("SELECT amount FROM budget_settings WHERE period=?", (period,))
        result = cursor.fetchone()

        if result:
            return result[0], days
        return None, days

    # установка бюджета
    def set_budget(self):
        try:
            amount = float(self.budget_amount.text().replace(",", "."))
            if amount <= 0:
                raise ValueError
        except:
            QMessageBox.warning(self, "Ошибка", "Введите сумму")
            return

        period = self.budget_period.currentText()

        cursor.execute("DELETE FROM budget_settings WHERE period=?", (period,))
        cursor.execute("INSERT INTO budget_settings(period, amount) VALUES (?, ?)", (period, amount))

        conn.commit()
        self.budget_amount.clear()
        self.update_budget()
        QMessageBox.information(self, "Готово", f"Бюджет на {period.lower()} установлен")

    # обновление прогресса бюджета
    def update_budget(self):
        budget, days = self.get_budget_limit()

        if not budget:
            self.budget_progress.setValue(0)
            self.budget_progress.setFormat("")
            return

        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM transactions 
            WHERE type='Расход' AND date >= ?
        """, (start_date,))
        expense = cursor.fetchone()[0]

        percent = int((expense / budget) * 100) if budget > 0 else 0
        display_percent = min(percent, 100)

        self.budget_progress.setValue(display_percent)
        self.budget_progress.setFormat(f"{expense:,.0f} / {budget:,.0f} руб. ({percent}%)")
        self.budget_progress.setProperty("danger", percent > 100)
        self.budget_progress.style().unpolish(self.budget_progress)
        self.budget_progress.style().polish(self.budget_progress)

    # страница аналитики с графиком
    def build_analytics(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        self.analytics_tab.setLayout(layout)

        frame = QFrame()
        add_shadow(frame)
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(24, 24, 24, 24)
        frame.setLayout(frame_layout)

        title = QLabel("📊 Расходы по категориям")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))

        self.figure = Figure(facecolor="#111827", figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: transparent; border-radius: 16px;")

        frame_layout.addWidget(title)
        frame_layout.addWidget(self.canvas)

        layout.addWidget(frame)

    # обновление круговой диаграммы
    def update_chart(self):
        cursor.execute("""
            SELECT category, SUM(amount)
            FROM transactions
            WHERE type='Расход'
            GROUP BY category
            ORDER BY SUM(amount) DESC
        """)

        data = cursor.fetchall()

        categories = [x[0] for x in data]
        amounts = [x[1] for x in data]

        self.figure.clear()

        if amounts:
            colors = ["#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#EF4444", 
                     "#EC4899", "#06B6D4", "#6366F1", "#14B8A6", "#F97316"]
            
            ax = self.figure.add_subplot(111)
            ax.set_facecolor("#111827")
            
            wedges, texts, autotexts = ax.pie(
                amounts,
                labels=categories,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors[:len(categories)],
                wedgeprops={"width": 0.4, "edgecolor": "#111827", "linewidth": 2},
                textprops={"color": "white", "fontsize": 10}
            )
            
            for autotext in autotexts:
                autotext.set_color("white")
                autotext.set_fontsize(10)
            
            legend = ax.legend(wedges, categories, title="Категории", 
                              loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
                              facecolor="#1E293B", edgecolor="#334155", 
                              labelcolor="white")
            legend.get_title().set_color("white")
            
            total = sum(amounts)
            ax.text(0, 0, f"Всего\n{total:,.0f} руб.", 
                   ha='center', va='center', fontsize=12, 
                   color='white', fontweight='bold')
            
            ax.set_aspect('equal')
        else:
            ax = self.figure.add_subplot(111)
            ax.set_facecolor("#111827")
            ax.text(0.5, 0.5, "Нет данных", 
                   color="#94A3B8", ha="center", va="center", fontsize=14)
            ax.axis('off')

        self.canvas.draw()

    # страница целей
    def build_goals(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        self.goals_tab.setLayout(layout)

        header = QHBoxLayout()
        title = QLabel("🎯 Финансовые цели")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        
        add_goal_btn = QPushButton(qta.icon("fa5s.plus"), "  Новая цель")
        add_goal_btn.setMaximumWidth(150)
        add_goal_btn.setObjectName("success_btn")
        add_goal_btn.clicked.connect(self.show_add_goal_dialog)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_goal_btn)
        
        layout.addLayout(header)

        self.goals_scroll = QScrollArea()
        self.goals_scroll.setWidgetResizable(True)
        self.goals_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.goals_container = QWidget()
        self.goals_layout = QVBoxLayout(self.goals_container)
        self.goals_layout.setSpacing(15)
        self.goals_layout.addStretch()
        
        self.goals_scroll.setWidget(self.goals_container)
        layout.addWidget(self.goals_scroll)

        self.load_goals()

    def show_add_goal_dialog(self):
        dialog = AddGoalDialog()
        if dialog.exec():
            self.load_goals()

    # загрузка всех целей
    def load_goals(self):
        for i in reversed(range(self.goals_layout.count())):
            widget = self.goals_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        cursor.execute("SELECT id, title, target, saved FROM goals")
        goals = cursor.fetchall()

        if not goals:
            empty_label = QLabel("🎯 Нет целей. Нажмите 'Новая цель'")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #94A3B8; padding: 40px;")
            self.goals_layout.addWidget(empty_label)
            return

        for goal_id, title, target, saved in goals:
            card = self.create_goal_card(goal_id, title, target, saved)
            self.goals_layout.insertWidget(self.goals_layout.count() - 1, card)

    # создание карточки цели
    def create_goal_card(self, goal_id, title, target, saved):
        card = QFrame()
        card.setMinimumHeight(140)
        add_shadow(card)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setObjectName("danger_btn")
        delete_btn.clicked.connect(lambda: self.delete_goal(goal_id))
        
        header.addWidget(title_label)
        header.addStretch()
        header.addWidget(delete_btn)

        percent = int((saved / target) * 100) if target > 0 else 0
        progress = QProgressBar()
        progress.setValue(min(percent, 100))
        progress.setFormat(f"{saved:,.0f} / {target:,.0f} руб. ({percent}%)")

        add_layout = QHBoxLayout()
        add_input = QLineEdit()
        add_input.setPlaceholderText("Сумма")
        
        add_btn = QPushButton("Пополнить")
        add_btn.setObjectName("success_btn")
        add_btn.setMaximumWidth(120)
        add_btn.clicked.connect(lambda: self.add_to_goal(goal_id, add_input, target))
        
        add_layout.addWidget(add_input)
        add_layout.addWidget(add_btn)

        layout.addLayout(header)
        layout.addWidget(progress)
        layout.addLayout(add_layout)

        card.setLayout(layout)
        return card

    # добавление суммы к цели
    def add_to_goal(self, goal_id, input_widget, target):
        try:
            amount = float(input_widget.text().replace(",", "."))
            if amount <= 0:
                raise ValueError
                
            cursor.execute("SELECT saved FROM goals WHERE id=?", (goal_id,))
            saved = cursor.fetchone()[0]
            new_saved = min(saved + amount, target)
            cursor.execute("UPDATE goals SET saved=? WHERE id=?", (new_saved, goal_id))
            conn.commit()
            
            input_widget.clear()
            self.load_goals()
            QMessageBox.information(self, "Готово", f"Добавлено {amount:,.0f} руб.")
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите сумму")

    # удаление цели
    def delete_goal(self, goal_id):
        reply = QMessageBox.question(self, "Удалить?", "Удалить эту цель?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            cursor.execute("DELETE FROM goals WHERE id=?", (goal_id,))
            conn.commit()
            self.load_goals()

    # обновление всего приложения
    def update_all(self):
        self.update_stats()
        self.update_budget()
        self.update_chart()


# запуск программы
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = FinPulse()
    window.show()

    sys.exit(app.exec())