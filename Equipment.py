import sys
import psycopg2
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit,
    QHeaderView, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette, QIcon


class EquipmentApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система учета оборудования на производстве")
        self.setGeometry(100, 100, 900, 650)

        # Цветовая схема для промышленного приложения
        self.industrial_blue = QColor(0, 90, 141)  # Основной синий цвет
        self.industrial_light = QColor(240, 244, 248)  # Светлый фон
        self.industrial_white = QColor(255, 255, 255)  # Белый
        self.industrial_red = QColor(200, 16, 46)  # Для предупреждений
        self.industrial_green = QColor(0, 128, 0)  # Для статуса "работает"
        self.industrial_gray = QColor(128, 128, 128)  # Для статуса "Списано"

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
            QLineEdit {{
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

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок
        title_label = QLabel("Учет оборудования на производстве")
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
        self.delete_btn.clicked.connect(self.delete_equipment)
        self.refresh_btn.clicked.connect(self.load_data)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)

        # Таблица с данными
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Название оборудования", "Статус"])
        self.table.setColumnHidden(0, True)  # Скрываем столбец ID

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
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

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
        """Загрузка данных из таблицы equipment с учетом статусов ремонтов и списаний"""
        if not hasattr(self, 'cursor') or not self.cursor:
            print("Курсор не инициализирован")
            return

        try:
            self.cursor.execute("""
                SELECT e.equipmentid, e.name, 
                       CASE 
                           WHEN EXISTS (
                               SELECT 1 FROM writeoffact w 
                               WHERE w.equipmentid = e.equipmentid
                           ) THEN 'Списано'
                           WHEN EXISTS (
                               SELECT 1 FROM repair r 
                               JOIN repairstatus rs ON r.repairstatusid = rs.repairstatusid
                               WHERE r.equipmentid = e.equipmentid 
                               AND rs.statusname = 'В процессе'
                           ) THEN 'На ремонте'
                           ELSE 'Исправен'
                       END as status
                FROM equipment e
                ORDER BY e.equipmentid
            """)
            data = self.cursor.fetchall()

            self.table.setRowCount(len(data))
            for row_idx, row in enumerate(data):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    # Подсветка статуса цветом
                    if col_idx == 2:  # Столбец статуса
                        if value == "Исправен":
                            item.setForeground(self.industrial_green)
                        elif value == "На ремонте":
                            item.setForeground(self.industrial_red)
                        elif value == "Списано":
                            item.setForeground(self.industrial_gray)
                        else:
                            item.setForeground(QColor(53, 59, 72))

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
        """Диалог добавления нового оборудования"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить оборудование")
        dialog.setFixedSize(400, 250)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        name_input = QLineEdit()
        name_input.setPlaceholderText("Введите название оборудования")

        status_input = QLineEdit()
        status_input.setPlaceholderText("Введите статус (например, работает, ремонт)")
        status_input.setVisible(False)  # Скрываем поле статуса, так как он определяется автоматически

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Добавить")
        cancel_btn = QPushButton("Отмена")

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Название оборудования:", name_input)
        layout.addRow(btn_box)

        def add_equipment():
            name = name_input.text().strip()

            if not name:
                QMessageBox.warning(dialog, "Ошибка", "Введите название оборудования")
                return

            try:
                self.cursor.execute(
                    "INSERT INTO equipment (name) VALUES (%s) RETURNING equipmentid",
                    (name,))
                new_id = self.cursor.fetchone()[0]
                self.conn.commit()

                row_pos = self.table.rowCount()
                self.table.insertRow(row_pos)

                # Добавляем данные в таблицу
                for col_idx, value in enumerate([new_id, name, "Исправен"]):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    if col_idx == 2:  # Подсветка статуса
                        item.setForeground(self.industrial_green)

                    self.table.setItem(row_pos, col_idx, item)

                dialog.close()

            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить оборудование:\n{str(e)}")

        ok_btn.clicked.connect(add_equipment)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def show_edit_dialog(self):
        """Диалог редактирования оборудования"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите оборудование для редактирования")
            return

        row = selected_items[0].row()
        equip_id = int(self.table.item(row, 0).text())
        current_name = self.table.item(row, 1).text()
        current_status = self.table.item(row, 2).text()

        # Запрещаем редактирование списанного оборудования
        if current_status == "Списано":
            QMessageBox.warning(self, "Ошибка", "Нельзя редактировать списанное оборудование")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать оборудование")
        dialog.setFixedSize(400, 250)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        name_input = QLineEdit(current_name)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Название оборудования:", name_input)
        layout.addRow(btn_box)

        def update_equipment():
            new_name = name_input.text().strip()

            if not new_name:
                QMessageBox.warning(dialog, "Ошибка", "Введите название оборудования")
                return

            try:
                self.cursor.execute(
                    "UPDATE equipment SET name = %s WHERE equipmentid = %s",
                    (new_name, equip_id))
                self.conn.commit()

                # Обновляем таблицу
                self.table.item(row, 1).setText(new_name)
                dialog.close()

            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось обновить оборудование:\n{str(e)}")

        ok_btn.clicked.connect(update_equipment)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def delete_equipment(self):
        """Удаление выбранного оборудования"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите оборудование для удаления")
            return

        row = selected_items[0].row()
        equip_id = int(self.table.item(row, 0).text())
        equip_name = self.table.item(row, 1).text()
        equip_status = self.table.item(row, 2).text()

        # Запрещаем удаление списанного оборудования через это приложение
        if equip_status == "Списано":
            QMessageBox.warning(self, "Ошибка", "Списанное оборудование нельзя удалить. Удалите сначала акт списания.")
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить оборудование '{equip_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Сначала удаляем связанные записи о ремонтах
                self.cursor.execute(
                    "DELETE FROM repair WHERE equipmentid = %s",
                    (equip_id,))

                # Затем удаляем само оборудование
                self.cursor.execute(
                    "DELETE FROM equipment WHERE equipmentid = %s",
                    (equip_id,))
                self.conn.commit()
                self.table.removeRow(row)
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить оборудование:\n{str(e)}")

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
    window = EquipmentApp()
    window.show()
    sys.exit(app.exec())