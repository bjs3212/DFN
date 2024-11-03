import json
import sys

class Layer:
    def __init__(self, einf=0.0, thickness=0.0, params=None, osc_types=None, table_view=None):
        self.Einf = einf
        self.Thickness = thickness
        self.Params = params if params is not None else []
        self.OscTypes = osc_types if osc_types is not None else []
        self.table_view = table_view

    def setEinf(self, einf):
        self.Einf = einf
        self.update_table_view()

    def setThickness(self, thickness):
        self.Thickness = thickness
        self.update_table_view()

    def setParams(self, params):
        self.Params = params
        self.update_table_view()

    def setOscTypes(self, osc_types):
        self.OscTypes = osc_types
        self.update_table_view()

    def update_table_view(self):
        if self.table_view is not None:
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(['Property', 'Value'])

            items = [
                QStandardItem("Einf"), QStandardItem(str(self.Einf)),
                QStandardItem("Thickness"), QStandardItem(str(self.Thickness)),
                QStandardItem("Params"), QStandardItem(str(self.Params)),
                QStandardItem("OscTypes"), QStandardItem(str(self.OscTypes))
            ]
            for i in range(0, len(items), 2):
                model.appendRow(items[i:i+2])

            self.table_view.setModel(model)

    def __repr__(self):
        return (f"Layer(Einf={self.Einf}, Thickness={self.Thickness}, "
                f"Params={self.Params}, OscTypes={self.OscTypes})")



# PyQt 예제 사용법
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTableView
from PyQt6.QtGui import QStandardItem, QStandardItemModel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Layer Example")
        self.resize(400, 300)

        self.table_view = QTableView()

        self.layer = Layer(einf=2.5, thickness=100.0, params=[1, 2, 3], osc_types=["type1", "type2"], table_view=self.table_view)
        self.layer.update_table_view()

        layout = QVBoxLayout()
        layout.addWidget(self.table_view)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Test saving and loading
        save_layer_to_file(self.layer, "layer_data.json")
        loaded_layer = load_layer_from_file("layer_data.json")
        print("Loaded Layer:", loaded_layer)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())