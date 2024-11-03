import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableView

class CustomTableView(QTableView):
    def __init__(self):
        super().__init__()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            index = self.indexAt(event.position().toPoint())
            if index.isValid():
                item = self.model().itemFromIndex(index)
                item.setForeground(QColor("red"))  # 원하는 색으로 변경 가능
        super().mousePressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.table_view = CustomTableView()
        self.setCentralWidget(self.table_view)

        self.model = QStandardItemModel(5, 3)
        for row in range(5):
            for column in range(3):
                item = QStandardItem(f"Item {row},{column}")
                self.model.setItem(row, column, item)

        self.table_view.setModel(self.model)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
