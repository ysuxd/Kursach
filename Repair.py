import sys
import psycopg2
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit, QDateEdit,
    QHeaderView, QDialog, QFormLayout, QComboBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QPalette, QIcon


class RepairApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система учета ремонтов оборудования")
        self.setGeometry(100, 100, 1000, 700)

        # Промышленная цветовая схема
        self.industrial_blue = QColor(0, 90, 141)
        self.industrial_light = QColor(240, 244, 248)
        self.industrial_white = QColor(255, 255, 255)
        self.industrial_green = QColor(0, 128, 0)

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
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {{
                border: 1px solid #d1d8e0;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }}
            QDialog {{
                background-color: {self.industrial_light.name()};
            }}
        """)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, self.industrial_light)
        palette.setColor(QPalette.ColorRole.Base, self.industrial_white)
        palette.setColor(QPalette.ColorRole.Highlight, self.industrial_blue)
        self.setPalette(palette)

        self.conn = None
        self.cursor = None
        self.connect_to_db()
        self.setup_ui()
        self.load_equipment()
        self.load_repair_statuses()
        self.load_data()

    def connect_to_db(self):
        """Подключение к базе данных"""
        try:
            self.conn = psycopg2.connect(
                dbname='kurs',
                user='postgres',
                password='123',
                host='localhost'
            )
            self.conn.autocommit = True  # Включаем autocommit для избежания проблем с транзакциями
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

    def load_repair_statuses(self):
        """Загрузка списка статусов ремонта из таблицы repairstatus"""
        try:
            self.cursor.execute("SELECT statusname FROM repairstatus ORDER BY reparstatusid")
            self.repair_statuses = [status[0] for status in self.cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка при загрузке статусов ремонта: {e}")
            self.repair_statuses = ["Завершён", "В процессе", "Отменён"]

    def update_equipment_status(self, equipment_id, repair_status):
        """Обновляет статус оборудования в зависимости от статуса ремонта"""
        try:
            if repair_status == "В процессе":
                new_status = "На ремонте"
            else:
                self.cursor.execute(
                    """SELECT COUNT(*) FROM repair r 
                    JOIN repairstatus rs ON r.repairstatusid = rs.repairstatusid
                    WHERE r.equipmentid = %s AND rs.statusname = 'В процессе'""",
                    (equipment_id,))
                active_repairs = self.cursor.fetchone()[0]
                new_status = "На ремонте" if active_repairs > 0 else "Исправен"

            self.cursor.execute(
                "UPDATE equipment SET status = %s WHERE equipmentid = %s",
                (new_status, equipment_id))
            return True
        except Exception as e:
            print(f"Ошибка при обновлении статуса оборудования: {e}")
            return False

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_label = QLabel("Учет ремонтов оборудования")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {self.industrial_blue.name()};
                padding: 10px;
            }}
        """)
        layout.addWidget(title_label)

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
        self.delete_btn.clicked.connect(self.delete_repair)
        self.refresh_btn.clicked.connect(self.load_data)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "ID оборудования", "Оборудование", "Дата ремонта", "Стоимость ремонта", "Статус"])
        self.table.setColumnHidden(0, True)
        self.table.setColumnHidden(1, True)

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

        header = self.table.horizontalHeader()
        header.setDefaultSectionSize(150)
        header.setMinimumSectionSize(100)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f5f5f5;
            }
        """)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)

    def load_data(self):
        """Загрузка данных о ремонтах с объединением таблиц"""
        try:
            query = """
                SELECT r.repairid, r.equipmentid, e.name, 
                       r.repairdate, r.repairprice, rs.statusname
                FROM repair r
                LEFT JOIN equipment e ON r.equipmentid = e.equipmentid
                LEFT JOIN repairstatus rs ON r.repairstatusid = rs.repairstatusid
                ORDER BY r.repairdate DESC
            """
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            self.table.setRowCount(len(data))
            for row_idx, row in enumerate(data):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    if col_idx == 5:
                        if value == "Завершён":
                            item.setBackground(QColor(144, 238, 144))
                        elif value == "В процессе":
                            item.setBackground(QColor(255, 255, 153))
                        elif value == "Отменён":
                            item.setBackground(QColor(255, 182, 193))

                    self.table.setItem(row_idx, col_idx, item)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка загрузки",
                f"Не удалось загрузить данные из базы:\n{str(e)}"
            )

    def show_add_dialog(self):
        """Диалог добавления нового ремонта"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить запись о ремонте")
        dialog.setFixedSize(500, 400)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        equipment_combo = QComboBox()
        for equip_id, equip_name in self.equipment_list:
            equipment_combo.addItem(equip_name, equip_id)

        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.currentDate())
        date_input.setDisplayFormat("dd.MM.yyyy")

        price_input = QDoubleSpinBox()
        price_input.setRange(0, 9999999)
        price_input.setDecimals(2)
        price_input.setPrefix("₽ ")

        status_combo = QComboBox()
        status_combo.addItems(self.repair_statuses)
        status_combo.setCurrentText("В процессе")

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Добавить")
        cancel_btn = QPushButton("Отмена")

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Оборудование:", equipment_combo)
        layout.addRow("Дата ремонта:", date_input)
        layout.addRow("Стоимость ремонта:", price_input)
        layout.addRow("Статус ремонта:", status_combo)
        layout.addRow(btn_box)

        def add_repair():
            equip_id = equipment_combo.currentData()
            date = date_input.date().toString("yyyy-MM-dd")
            price = price_input.value()
            status = status_combo.currentText()

            if not all([equip_id, date, status]):
                QMessageBox.warning(dialog, "Ошибка", "Заполните все обязательные поля")
                return

            try:
                self.cursor.execute(
                    "SELECT repairstatusid FROM repairstatus WHERE statusname = %s",
                    (status,))
                status_id = self.cursor.fetchone()[0]

                self.cursor.execute(
                    """INSERT INTO repair 
                    (equipmentid, repairdate, repairprice, repairstatusid) 
                    VALUES (%s, %s, %s, %s) 
                    RETURNING repairid""",
                    (equip_id, date, price, status_id))

                new_id = self.cursor.fetchone()[0]
                self.update_equipment_status(equip_id, status)

                row_pos = self.table.rowCount()
                self.table.insertRow(row_pos)

                equip_name = equipment_combo.currentText()
                columns = [
                    str(new_id), str(equip_id), equip_name,
                    date_input.date().toString("dd.MM.yyyy"),
                    f"{price:.2f} ₽",
                    status
                ]

                for col_idx, value in enumerate(columns):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    if col_idx == 5:
                        if value == "Завершён":
                            item.setBackground(QColor(144, 238, 144))
                        elif value == "В процессе":
                            item.setBackground(QColor(255, 255, 153))
                        elif value == "Отменён":
                            item.setBackground(QColor(255, 182, 193))

                    self.table.setItem(row_pos, col_idx, item)

                dialog.close()

            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить запись о ремонте:\n{str(e)}")

        ok_btn.clicked.connect(add_repair)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def show_edit_dialog(self):
        """Диалог редактирования записи о ремонте"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите запись о ремонте для редактирования")
            return

        row = selected_items[0].row()
        repair_id = int(self.table.item(row, 0).text())
        equip_id = int(self.table.item(row, 1).text())
        current_equip_name = self.table.item(row, 2).text()
        current_date = QDate.fromString(self.table.item(row, 3).text(), "dd.MM.yyyy")
        current_price = float(self.table.item(row, 4).text().split()[0])
        current_status = self.table.item(row, 5).text()

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать запись о ремонте")
        dialog.setFixedSize(500, 400)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        equipment_combo = QComboBox()
        current_equip_index = 0
        for i, (e_id, e_name) in enumerate(self.equipment_list):
            equipment_combo.addItem(e_name, e_id)
            if e_id == equip_id:
                current_equip_index = i
        equipment_combo.setCurrentIndex(current_equip_index)

        date_input = QDateEdit(current_date)
        date_input.setCalendarPopup(True)
        date_input.setDisplayFormat("dd.MM.yyyy")

        price_input = QDoubleSpinBox()
        price_input.setRange(0, 9999999)
        price_input.setDecimals(2)
        price_input.setPrefix("₽ ")
        price_input.setValue(current_price)

        status_combo = QComboBox()
        status_combo.addItems(self.repair_statuses)
        status_combo.setCurrentText(current_status)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Оборудование:", equipment_combo)
        layout.addRow("Дата ремонта:", date_input)
        layout.addRow("Стоимость ремонта:", price_input)
        layout.addRow("Статус ремонта:", status_combo)
        layout.addRow(btn_box)

        def update_repair():
            new_equip_id = equipment_combo.currentData()
            new_date = date_input.date().toString("yyyy-MM-dd")
            new_price = price_input.value()
            new_status = status_combo.currentText()

            if not all([new_equip_id, new_date, new_status]):
                QMessageBox.warning(dialog, "Ошибка", "Заполните все обязательные поля")
                return

            try:
                self.cursor.execute(
                    "SELECT repairstatusid FROM repairstatus WHERE statusname = %s",
                    (new_status,))
                new_status_id = self.cursor.fetchone()[0]

                self.cursor.execute(
                    """SELECT rs.statusname 
                    FROM repair r
                    JOIN repairstatus rs ON r.repairstatusid = rs.repairstatusid
                    WHERE r.repairid = %s""",
                    (repair_id,))
                old_status = self.cursor.fetchone()[0]

                self.cursor.execute(
                    """UPDATE repair SET 
                    equipmentid = %s, 
                    repairdate = %s, 
                    repairprice = %s,
                    repairstatusid = %s
                    WHERE repairid = %s""",
                    (new_equip_id, new_date, new_price, new_status_id, repair_id))

                if old_status != new_status:
                    self.update_equipment_status(new_equip_id, new_status)

                new_equip_name = equipment_combo.currentText()

                self.table.item(row, 1).setText(str(new_equip_id))
                self.table.item(row, 2).setText(new_equip_name)
                self.table.item(row, 3).setText(date_input.date().toString("dd.MM.yyyy"))
                self.table.item(row, 4).setText(f"{new_price:.2f} ₽")

                status_item = self.table.item(row, 5)
                status_item.setText(new_status)

                if new_status == "Завершён":
                    status_item.setBackground(QColor(144, 238, 144))
                elif new_status == "В процессе":
                    status_item.setBackground(QColor(255, 255, 153))
                elif new_status == "Отменён":
                    status_item.setBackground(QColor(255, 182, 193))

                dialog.close()

            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось обновить запись о ремонте:\n{str(e)}")

        ok_btn.clicked.connect(update_repair)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def delete_repair(self):
        """Удаление выбранной записи о ремонте"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите запись о ремонте для удаления")
            return

        row = selected_items[0].row()
        repair_id = int(self.table.item(row, 0).text())
        equip_id = int(self.table.item(row, 1).text())
        equip_name = self.table.item(row, 2).text()
        date = self.table.item(row, 3).text()

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить запись о ремонте для '{equip_name}' от {date}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cursor.execute(
                    """SELECT rs.statusname 
                    FROM repair r
                    JOIN repairstatus rs ON r.repairstatusid = rs.repairstatusid
                    WHERE r.repairid = %s""",
                    (repair_id,))
                status = self.cursor.fetchone()[0]

                self.cursor.execute(
                    "DELETE FROM repair WHERE repairid = %s",
                    (repair_id,))

                if status == "В процессе":
                    self.update_equipment_status(equip_id, "Завершён")

                self.table.removeRow(row)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись о ремонте:\n{str(e)}")

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
    window = RepairApp()
    window.show()
    sys.exit(app.exec())