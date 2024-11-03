import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QDockWidget, QTextEdit
from PyQt6.QtCore import QSettings, Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DockWidget Example")

        # 중앙 위젯 설정
        central_widget = QTextEdit("Central Widget")
        self.setCentralWidget(central_widget)

        # DockWidget 설정
        self.dock1 = QDockWidget("Dock 1", self)
        self.dock1.setObjectName("Dock1")  # Object name 설정
        self.dock1.setWidget(QTextEdit("Dock 1 Content"))
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock1)

        self.dock2 = QDockWidget("Dock 2", self)
        self.dock2.setObjectName("Dock2")  # Object name 설정
        self.dock2.setWidget(QTextEdit("Dock 2 Content"))
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock2)

        # 창 크기와 위치를 저장 및 복원하는 메서드 호출
        self.load_settings()

    def closeEvent(self, event):
        # 창이 닫힐 때 설정을 저장
        self.save_settings()
        super().closeEvent(event)

    def save_settings(self):
        # QSettings 객체 생성
        settings = QSettings("YourCompany", "YourApp")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    def load_settings(self):
        # QSettings 객체 생성
        settings = QSettings("YourCompany", "YourApp")
        geometry = settings.value("geometry")
        windowState = settings.value("windowState")
        if geometry is not None:
            self.restoreGeometry(geometry)
        if windowState is not None:
            self.restoreState(windowState)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())