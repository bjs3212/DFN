# -*- coding: utf-8 -*-

from PyQt6.QtCore import QObject, QEvent, Qt, pyqtSignal, QModelIndex
from PyQt6 import QtWidgets
from .ui.model_ui import Ui_modelDockWidget
from .ParamsTable import ParamsTableModel, FixedParamsTableModel
from typing import List, TYPE_CHECKING

if TYPE_CHECKING :
    from .Layer import Layerclass
    from .DataManager import DataManager

class TableViewEventFilter(QObject):
    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            print(f"Mouse Pressed at {event.pos()}")
        elif event.type() == QEvent.Type.MouseButtonRelease:
            print(f"Mouse Released at {event.pos()}")
        elif event.type() == QEvent.Type.MouseButtonDblClick:
            print(f"Mouse Double Clicked at {event.pos()}")
        elif event.type() == QEvent.Type.MouseMove:
            print(f"Mouse Moved at {event.pos()}")
        elif event.type() == QEvent.Type.KeyPress:
            print(f"Key Pressed: {event.key()}")
        elif event.type() == QEvent.Type.KeyRelease:
            print(f"Key Released: {event.key()}")
        return super().eventFilter(source, event)

# Fit에 필요한 변수들을 저장할 Table
class modelDockWidget(QtWidgets.QDockWidget, Ui_modelDockWidget):
    cellClicked = pyqtSignal(QModelIndex, QObject) 
    # ParController에 연결시켜서 idx와 tableView를 전달할 signal

    def __init__(self, parent=None, DataManager : 'DataManager' =None, LayerName = None):
        super().__init__(parent)
        self.setupUi(self)
        self.DataManager = DataManager
        self.initialize()
        self.LayerName = LayerName
        if LayerName : self.setWindowTitle(LayerName + ' model Dockwidget')
        self.pushButton_AddOsc.clicked.connect(self.add_Oscillator)
        self.pushButton_RemoveOsc.clicked.connect(self.remove_Oscillator)

        self.clicked_index = None #클릭된 index가 몇row 몇column인지 저장할 변수
        self.clicked_tableView = None #클릭된 셀이 어떤 tableView 소속인지 저장할 변수
        # 클릭 이벤트를 연결
        self.tableView_Params.clicked.connect(self.cellClicked_Params)
        self.tableView_Einf.clicked.connect(self.cellClicked_Einf)
        self.tableView_Thickness.clicked.connect(self.cellClicked_Thickness)
        # 클릭된 곳이 셀 위인지 검사하기 위한 이벤트 연결
        self.tableView_Params.selectionModel().selectionChanged.connect(self.selectionChanged_Params)
        self.tableView_Einf.selectionModel().selectionChanged.connect(self.selectionChanged_Einf)
        self.tableView_Thickness.selectionModel().selectionChanged.connect(self.selectionChanged_Thickness)
        
        self.tableView_Params.horizontalHeader().sectionClicked.connect(self.sort_by_header)


    def initialize(self) :
        self.tableView_Thickness_model = FixedParamsTableModel(self,data=[[2.]], vertical_header=['1'], horizontal_header=['Thickness'])
        self.tableView_Einf_model = FixedParamsTableModel(self,data=[[3.]], vertical_header=['1'], horizontal_header=['Einf'])
        self.tableView_Params_model = ParamsTableModel(self,data=[['Lorentzian', 100., 50., 10.]], vertical_header=['1'], horizontal_header=['OscType', 'w0', 'wp', 'gamma'])

        self.tableView_Thickness.setModel(self.tableView_Thickness_model)
        self.tableView_Einf.setModel(self.tableView_Einf_model)
        self.tableView_Params.setModel(self.tableView_Params_model)
        '''
        self.eventFilter = TableViewEventFilter()
        self.tableView_Einf.viewport().installEventFilter(self.eventFilter)
        self.tableView_Params.viewport().installEventFilter(self.eventFilter)
        '''

    def setWindowTitle(self, LayerName) : 
        self.LayerName = LayerName
        super().setWindowTitle(LayerName + ' model Dockwidget')

    def add_Oscillator(self):
        # Method to add a new oscillator row to the ParamsTableModel
        new_row = ['Lorentzian', 100., 100., 10.]  # Define default values for new row
        self.tableView_Params_model.addRow(new_row, self.clicked_index)

    def remove_Oscillator(self):
        self.tableView_Params_model.removeRow(self.clicked_index)


# 진짜 개짜치지만 clicked 이벤트를 오버라이딩하는 법을 몰라서 
# clicked로는 클릭된 tableView가 뭔지 전달이 불가한 상황
# 그래서 Einf, Thickness, Params마다 각각 함수를 다르게 매핑해서 전달할 tableView를 특정해놓았다
# 나중에 다른 방법을 찾으면 수정하자...

    def cellClicked_Params(self, index): # 셀 클릭시 클릭된 셀의 index 저장
        self.clicked_index = index
        self.cellClicked.emit(index, self.tableView_Params)
    def cellClicked_Einf(self, index): # 셀 클릭시 클릭된 셀의 index 저장
        self.clicked_index = index
        self.cellClicked.emit(index, self.tableView_Einf)
    def cellClicked_Thickness(self, index): # 셀 클릭시 클릭된 셀의 index 저장
        self.clicked_index = index
        self.cellClicked.emit(index, self.tableView_Thickness)

    def selectionChanged_Params(self, selected, deselected): # 셀 클릭 해제시 변수 초기화
        if not self.tableView_Params.selectionModel().hasSelection():
            self.clicked_index = None
            self.cellClicked.emit(QModelIndex(), self.tableView_Params)
    def selectionChanged_Einf(self, selected, deselected): # 셀 클릭 해제시 변수 초기화
        if not self.tableView_Einf.selectionModel().hasSelection():
            self.clicked_index = None
            self.cellClicked.emit(QModelIndex(), self.tableView_Einf)
    def selectionChanged_Thickness(self, selected, deselected): # 셀 클릭 해제시 변수 초기화
        if not self.tableView_Params.selectionModel().hasSelection():
            self.clicked_index = None
            self.cellClicked.emit(QModelIndex(), self.tableView_Thickness)

    def sort_by_header(self, logicalIndex):
        self.tableView_Params_model.sort_order = Qt.SortOrder.DescendingOrder if self.tableView_Params_model.sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        self.tableView_Params_model.sort(logicalIndex, self.tableView_Params_model.sort_order)
