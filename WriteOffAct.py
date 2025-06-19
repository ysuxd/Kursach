import sys
import psycopg2
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit, QDateEdit,
    QHeaderView, QDialog, QFormLayout, QComboBox, QTextEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QPalette


class WriteOffApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система учета актов списания оборудования")
        self.setGeometry(100, 100, 1000, 700)

        # Цветовая схема
        self.industrial_blue = QColor(0, 90, 141)
        self.industrial_light = QColor(240, 244, 248)
        self.industrial_white = QColor(255, 255, 255)
        self.industrial_red = QColor(220, 53, 69)  # Для акцента на списании

        # Установка стиля приложения
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.industrial_light.name()};
            }}
            QTableWidget {{
                background-color: {self.industrial_white.name()};
                border: 1px solid #d1d8e0;
                border-radius: 5px;
                gridline-color: #d1d8e0;
                font-size: 14px;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background-color: {self.industrial_blue.name()};
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
            QPushButton {{
                background-color: {self.industrial_blue.name()};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                font-size: 14px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {self.industrial_blue.darker(110).name()};
            }}
            QPushButton:pressed {{
                background-color: {self.industrial_blue.darker(120).name()};
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
            }}
            QLineEdit, QComboBox, QDateEdit, QTextEdit {{
                border: 1px solid #d1d8e0;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }}
            QDialog {{
                background-color: {self.industrial_light.name()};
            }}
        """)

        # Настройка цветовой палитры
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, self.industrial_light)
        palette.setColor(QPalette.ColorRole.Base, self.industrial_white)
        palette.setColor(QPalette.ColorRole.Highlight, self.industrial_blue)
        self.setPalette(palette)

        self.conn = None
        self.cursor = None
        self.connect_to_db()
        self.setup_ui()
        self.load_data()
        self.load_equipment()

    def connect_to_db(self):
        """Подключение к базе данных"""
        try:
            self.conn = psycopg2.connect(
                dbname='kurs',
                user='postgres',
                password='123',
                host='localhost'
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к БД: {str(e)}")
            sys.exit(1)

    def load_equipment(self):
        """Загрузка списка оборудования для комбобокса"""
        try:
            self.cursor.execute("SELECT equipmentid, name FROM equipment ORDER BY name")
            self.equipment_list = self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при загрузке оборудования: {e}")
            self.equipment_list = []

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок
        title_label = QLabel("Учет актов списания оборудования")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {self.industrial_blue.name()};
                padding: 10px;
            }}
        """)
        layout.addWidget(title_label)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.add_btn = QPushButton("Добавить")
        self.edit_btn = QPushButton("Редактировать")
        self.delete_btn = QPushButton("Удалить")
        self.refresh_btn = QPushButton("Обновить")

        for btn in [self.add_btn, self.edit_btn, self.delete_btn, self.refresh_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.add_btn.clicked.connect(self.show_add_dialog)
        self.edit_btn.clicked.connect(self.show_edit_dialog)
        self.delete_btn.clicked.connect(self.delete_writeoff)
        self.refresh_btn.clicked.connect(self.load_data)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)

        # Таблица с данными
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "ID оборудования", "Оборудование", "Дата списания", "Причина списания"])
        self.table.setColumnHidden(0, True)  # Скрываем столбец ID
        self.table.setColumnHidden(1, True)  # Скрываем столбец ID оборудования

        # Настройка внешнего вида таблицы
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #c0c0c0;
                gridline-color: #c0c0c0;
            }
            QHeaderView::section {
                background-color: #005A8D;
                color: white;
                padding: 8px;
                border: 1px solid #c0c0c0;
                font-weight: bold;
            }
            QTableWidget::item {
                border-right: 1px solid #c0c0c0;
                border-bottom: 1px solid #c0c0c0;
                padding: 8px;
            }
        """)

        # Настройка размеров столбцов
        header = self.table.horizontalHeader()
        header.setDefaultSectionSize(200)
        header.setMinimumSectionSize(150)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Название оборудования
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Дата
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Причина

        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f5f5f5;
            }
            QTableWidget::item[column="4"] {
                color: #dc3545;  /* Красный цвет для причины списания */
            }
        """)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)

    def load_data(self):
        """Загрузка данных об актах списания с объединением таблиц"""
        if not hasattr(self, 'cursor') or not self.cursor:
            print("Курсор не инициализирован")
            return

        try:
            query = """
                SELECT w.writeoffactid, w.equipmentid, e.name, 
                       w.writeoffdate, w.reason
                FROM writeoffact w
                LEFT JOIN equipment e ON w.equipmentid = e.equipmentid
                ORDER BY w.writeoffdate DESC
            """
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            self.table.setRowCount(len(data))
            for row_idx, row in enumerate(data):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    # Окрашиваем причину списания в красный
                    if col_idx == 4:  # Причина списания
                        item.setForeground(self.industrial_red)

                    self.table.setItem(row_idx, col_idx, item)

            print(f"Загружено {len(data)} записей")

        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            QMessageBox.critical(
                self,
                "Ошибка загрузки",
                f"Не удалось загрузить данные из базы:\n{str(e)}"
            )

    def show_add_dialog(self):
        """Диалог добавления нового акта списания"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить акт списания")
        dialog.setFixedSize(500, 400)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Комбобокс для выбора оборудования
        equipment_combo = QComboBox()
        for equip_id, equip_name in self.equipment_list:
            equipment_combo.addItem(equip_name, equip_id)

        # Поля для ввода данных
        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.currentDate())
        date_input.setDisplayFormat("dd.MM.yyyy")

        reason_input = QTextEdit()
        reason_input.setMaximumHeight(100)
        reason_input.setPlaceholderText("Введите причину списания...")

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Добавить")
        cancel_btn = QPushButton("Отмена")

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        # Добавляем элементы в форму
        layout.addRow("Оборудование:", equipment_combo)
        layout.addRow("Дата списания:", date_input)
        layout.addRow("Причина списания:", reason_input)
        layout.addRow(btn_box)

        def add_writeoff():
            # Получаем данные из формы
            equip_id = equipment_combo.currentData()
            date = date_input.date().toString("yyyy-MM-dd")
            reason = reason_input.toPlainText()

            # Валидация данных
            if not all([equip_id, date, reason]):
                QMessageBox.warning(dialog, "Ошибка", "Заполните все обязательные поля")
                return

            try:
                self.cursor.execute(
                    """INSERT INTO writeoffact 
                    (equipmentid, writeoffdate, reason) 
                    VALUES (%s, %s, %s) 
                    RETURNING writeoffactid""",
                    (equip_id, date, reason))

                new_id = self.cursor.fetchone()[0]
                self.conn.commit()

                # Добавляем новую строку в таблицу
                row_pos = self.table.rowCount()
                self.table.insertRow(row_pos)

                # Получаем названия для отображения
                equip_name = equipment_combo.currentText()

                # Заполняем таблицу
                columns = [
                    str(new_id), str(equip_id), equip_name,
                    date_input.date().toString("dd.MM.yyyy"),
                    reason
                ]

                for col_idx, value in enumerate(columns):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    # Окрашиваем причину списания в красный
                    if col_idx == 4:  # Причина списания
                        item.setForeground(self.industrial_red)

                    self.table.setItem(row_pos, col_idx, item)

                dialog.close()

            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить акт списания:\n{str(e)}")

        ok_btn.clicked.connect(add_writeoff)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def show_edit_dialog(self):
        """Диалог редактирования акта списания"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите акт списания для редактирования")
            return

        row = selected_items[0].row()
        writeoff_id = int(self.table.item(row, 0).text())
        equip_id = int(self.table.item(row, 1).text())
        current_equip_name = self.table.item(row, 2).text()
        current_date = QDate.fromString(self.table.item(row, 3).text(), "dd.MM.yyyy")
        current_reason = self.table.item(row, 4).text()

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать акт списания")
        dialog.setFixedSize(500, 400)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Комбобокс для выбора оборудования
        equipment_combo = QComboBox()
        current_equip_index = 0
        for i, (e_id, e_name) in enumerate(self.equipment_list):
            equipment_combo.addItem(e_name, e_id)
            if e_id == equip_id:
                current_equip_index = i
        equipment_combo.setCurrentIndex(current_equip_index)

        # Поля для ввода данных
        date_input = QDateEdit(current_date)
        date_input.setCalendarPopup(True)
        date_input.setDisplayFormat("dd.MM.yyyy")

        reason_input = QTextEdit()
        reason_input.setMaximumHeight(100)
        reason_input.setText(current_reason)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        # Добавляем элементы в форму
        layout.addRow("Оборудование:", equipment_combo)
        layout.addRow("Дата списания:", date_input)
        layout.addRow("Причина списания:", reason_input)
        layout.addRow(btn_box)

        def update_writeoff():
            # Получаем данные из формы
            new_equip_id = equipment_combo.currentData()
            new_date = date_input.date().toString("yyyy-MM-dd")
            new_reason = reason_input.toPlainText()

            # Валидация данных
            if not all([new_equip_id, new_date, new_reason]):
                QMessageBox.warning(dialog, "Ошибка", "Заполните все обязательные поля")
                return

            try:
                self.cursor.execute(
                    """UPDATE writeoffact SET 
                    equipmentid = %s, 
                    writeoffdate = %s, 
                    reason = %s
                    WHERE writeoffactid = %s""",
                    (new_equip_id, new_date, new_reason, writeoff_id))

                self.conn.commit()

                # Обновляем таблицу
                new_equip_name = equipment_combo.currentText()

                self.table.item(row, 1).setText(str(new_equip_id))
                self.table.item(row, 2).setText(new_equip_name)
                self.table.item(row, 3).setText(date_input.date().toString("dd.MM.yyyy"))

                reason_item = self.table.item(row, 4)
                reason_item.setText(new_reason)
                reason_item.setForeground(self.industrial_red)

                dialog.close()

            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось обновить акт списания:\n{str(e)}")

        ok_btn.clicked.connect(update_writeoff)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def delete_writeoff(self):
        """Удаление выбранного акта списания"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите акт списания для удаления")
            return

        row = selected_items[0].row()
        writeoff_id = int(self.table.item(row, 0).text())
        equip_name = self.table.item(row, 2).text()
        date = self.table.item(row, 3).text()

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить акт списания для '{equip_name}' от {date}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cursor.execute(
                    "DELETE FROM writeoffact WHERE writeoffactid = %s",
                    (writeoff_id,))
                self.conn.commit()
                self.table.removeRow(row)
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить акт списания:\n{str(e)}")

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = WriteOffApp()
    window.show()
    sys.exit(app.exec())