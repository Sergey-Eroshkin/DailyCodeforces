import os
import sys
from PySide6.QtCore import QObject, QThread, Signal, Slot, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QAbstractScrollArea,
    QComboBox,
    QListView,
)

# Логику забираем напрямую из существующего модуля
from app.main import get_recommendations

ICON_PATH = os.path.join(os.path.dirname(__file__), "app_icon.png")


class RecommendationWorker(QObject):
    """Отдельный поток для сетевых вызовов Codeforces."""

    finished = Signal(list)
    error = Signal(str)

    def __init__(self, handle: str, limit: int):
        super().__init__()
        self.handle = handle
        self.limit = limit

    @Slot()
    def run(self):
        try:
            tasks = get_recommendations(self.handle, self.limit)
            if not tasks:
                self.error.emit("Не удалось подобрать задачи.")
                return
            self.finished.emit(tasks)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Daily Codeforces")
        self.setWindowIcon(QIcon(ICON_PATH))

        self.handle_input = QLineEdit()
        self.handle_input.setPlaceholderText("Введите handle")

        self.count_input = QSpinBox()
        self.count_input.setRange(1, 20)
        self.count_input.setValue(3)

        self.fetch_button = QPushButton("Подобрать задачи")
        self.fetch_button.clicked.connect(self.on_fetch_clicked)

        self.status_label = QLabel()
        self.status_label.setText("Готово")

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Задача", "Контест", "Рейтинг", "Теги", "Ссылка"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setWordWrap(False)
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.table.cellActivated.connect(self.on_cell_activated)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Handle:"))
        controls.addWidget(self.handle_input)
        controls.addWidget(QLabel("Количество:"))
        controls.addWidget(self.count_input)
        controls.addWidget(self.fetch_button)

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(self.table)
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.apply_styles()

        self.thread: QThread | None = None
        self.worker: RecommendationWorker | None = None

    def apply_styles(self):
        self.setStyleSheet(
            """
            QWidget {
                font-family: 'Segoe UI';
                font-size: 12pt;
            }
            QLineEdit, QPushButton, QTableWidget {
                padding: 6px;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
            }
            QPushButton {
                background-color: #2d89ef;
                color: white;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #a0a0a0;
            }
            QComboBox#tagCombo {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 4px 8px;
                background: #f4f6fb;
            }
            QComboBox#tagCombo::drop-down {
                border: none;
                width: 18px;
            }
            QComboBox#tagCombo QAbstractItemView {
                border: 1px solid #d0d0d0;
                selection-background-color: #e5f1ff;
                selection-color: #000000;
                background: #ffffff;
                padding: 4px;
            }
            QComboBox#tagCombo QAbstractItemView::item {
                margin: 2px;
                padding: 4px 8px;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                background: #f9fafc;
            }
            """
        )

    @Slot()
    def on_fetch_clicked(self):
        handle = self.handle_input.text().strip()
        if not handle:
            self.status_label.setText("Укажите handle.")
            return
        limit = self.count_input.value()

        self.fetch_button.setEnabled(False)
        self.status_label.setText("Загрузка...")
        self.table.setRowCount(0)

        self.thread = QThread()
        self.worker = RecommendationWorker(handle, limit)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @Slot(list)
    def on_finished(self, tasks: list):
        self.fetch_button.setEnabled(True)
        self.status_label.setText("Готово")

        self.table.setRowCount(len(tasks))
        for row, item in enumerate(tasks):
            name = item.get("name", "")
            contest = item.get("contest", "")
            rating = str(item.get("rating", ""))
            tags = ", ".join(item.get("tags", []))
            link = item.get("link", "")
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(contest))
            self.table.setItem(row, 2, QTableWidgetItem(rating))
            tags_combo = QComboBox()
            tags_combo.setObjectName("tagCombo")
            tags_combo.setView(QListView())
            tags_combo.setEditable(False)
            tag_list = item.get("tags", [])
            if tag_list:
                tags_combo.addItems(tag_list)
            else:
                tags_combo.addItem("—")
            self.table.setCellWidget(row, 3, tags_combo)
            self.table.setItem(row, 4, QTableWidgetItem(link))

    @Slot(str)
    def on_error(self, message: str):
        self.fetch_button.setEnabled(True)
        self.status_label.setText(f"Ошибка: {message}")

    @Slot(int, int)
    def on_cell_activated(self, row: int, column: int):
        """Открываем ссылку при клике по ячейке столбца 'Ссылка'."""
        if column != 4:
            return
        item = self.table.item(row, column)
        if not item:
            return
        link = item.text().strip()
        if link:
            QDesktopServices.openUrl(QUrl(link))


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_PATH))
    window = MainWindow()
    window.resize(700, 400)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

