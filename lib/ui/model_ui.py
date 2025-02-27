# Form implementation generated from reading ui file 'model_ui.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_modelDockWidget(object):
    def setupUi(self, modelDockWidget):
        modelDockWidget.setObjectName("modelDockWidget")
        modelDockWidget.resize(460, 387)
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.gridLayout = QtWidgets.QGridLayout(self.dockWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_AddOsc = QtWidgets.QPushButton(parent=self.dockWidgetContents)
        self.pushButton_AddOsc.setObjectName("pushButton_AddOsc")
        self.horizontalLayout.addWidget(self.pushButton_AddOsc)
        self.pushButton_RemoveOsc = QtWidgets.QPushButton(parent=self.dockWidgetContents)
        self.pushButton_RemoveOsc.setObjectName("pushButton_RemoveOsc")
        self.horizontalLayout.addWidget(self.pushButton_RemoveOsc)
        self.gridLayout.addLayout(self.horizontalLayout, 10, 0, 1, 2)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(parent=self.dockWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.tableView_Einf = ParamsTableView(parent=self.dockWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableView_Einf.sizePolicy().hasHeightForWidth())
        self.tableView_Einf.setSizePolicy(sizePolicy)
        self.tableView_Einf.setMinimumSize(QtCore.QSize(50, 50))
        self.tableView_Einf.setMaximumSize(QtCore.QSize(150, 50))
        self.tableView_Einf.setSizeIncrement(QtCore.QSize(50, 50))
        self.tableView_Einf.setBaseSize(QtCore.QSize(50, 50))
        self.tableView_Einf.setObjectName("tableView_Einf")
        self.tableView_Einf.horizontalHeader().setVisible(False)
        self.tableView_Einf.verticalHeader().setVisible(False)
        self.horizontalLayout_2.addWidget(self.tableView_Einf)
        self.label = QtWidgets.QLabel(parent=self.dockWidgetContents)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.tableView_Thickness = ParamsTableView(parent=self.dockWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableView_Thickness.sizePolicy().hasHeightForWidth())
        self.tableView_Thickness.setSizePolicy(sizePolicy)
        self.tableView_Thickness.setMaximumSize(QtCore.QSize(150, 50))
        self.tableView_Thickness.setObjectName("tableView_Thickness")
        self.tableView_Thickness.horizontalHeader().setVisible(False)
        self.tableView_Thickness.verticalHeader().setVisible(False)
        self.horizontalLayout_2.addWidget(self.tableView_Thickness)
        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 0, 1, 2)
        self.tableView_Params = ParamsTableView(parent=self.dockWidgetContents)
        self.tableView_Params.setObjectName("tableView_Params")
        self.gridLayout.addWidget(self.tableView_Params, 9, 0, 1, 1)
        modelDockWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(modelDockWidget)
        QtCore.QMetaObject.connectSlotsByName(modelDockWidget)

    def retranslateUi(self, modelDockWidget):
        _translate = QtCore.QCoreApplication.translate
        modelDockWidget.setWindowTitle(_translate("modelDockWidget", "DockWidget"))
        self.pushButton_AddOsc.setText(_translate("modelDockWidget", "Add"))
        self.pushButton_RemoveOsc.setText(_translate("modelDockWidget", "Remove"))
        self.label_2.setText(_translate("modelDockWidget", "Einf"))
        self.label.setText(_translate("modelDockWidget", "Thickness (nm)"))
from lib.ParamsTable import ParamsTableView
