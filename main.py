# -*- coding: utf-8 -*-

import sys
from PyQt6 import QtWidgets
from lib.mainwindow import App


def main():
    app = QtWidgets.QApplication(sys.argv)

    ex = App()
    ex.showMaximized()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
