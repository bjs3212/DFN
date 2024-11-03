import sys
from PyQt6.QtWidgets import QApplication, QTableView, QMainWindow, QVBoxLayout, QWidget, QStyledItemDelegate, QLineEdit
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt
import re

class ScientificNotationDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        text = editor.text()
        if self.is_valid_number(text):
            model.setData(index, float(text), Qt.ItemDataRole.EditRole)
        else:
            editor.setText(str(index.model().data(index, Qt.ItemDataRole.EditRole)))

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def is_valid_number(self, text):
        # Check if the text is a valid scientific notation number
        regex = re.compile(r'^-?\d+(\.\d+)?(e-?\d+)?$', re.IGNORECASE)
        return bool(regex.match(text))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.table = QTableView()
        self.model = QStandardItemModel(5, 3)
        
        for row in range(5):
            for column in range(3):
                value = 1 / (10 ** (row + column + 1))
                item = QStandardItem(f"{value:.9e}")
                self.model.setItem(row, column, item)
        
        self.table.setModel(self.model)
        self.table.setItemDelegate(ScientificNotationDelegate())
        
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()