from PyQt6.QtWidgets import QDockWidget, QTableView
from PyQt6.QtCore import Qt, QModelIndex
from typing import TYPE_CHECKING

if TYPE_CHECKING : 
    from .DataManager import DataManager
from .ui.ParController_ui import Ui_ParContollerDockWidget

class ParameterControllerDockWidget(QDockWidget, Ui_ParContollerDockWidget) :
    def __init__(self, parent=None, DataManager : 'DataManager'=None) :
        super().__init__(parent)
        self.setupUi(self)
        self.DataManager = DataManager
        self.initialize()

    def initialize(self) :
        self.ParController_verticalSlider.sliderMoved.connect(self.slider_moved)
        self.ParController_verticalSlider.sliderReleased.connect(self.slider_released)
        self.current_tableView : QTableView = None
        self.current_index : QModelIndex = None
        self.currentVal = None

        # 일단 slider가 exponential하게 변화시키도록 하자
        min_power = -100 # 최소 지수
        max_power = 100 # 최대 지수
        self.ParController_verticalSlider.setMinimum(min_power)
        self.ParController_verticalSlider.setMaximum(max_power)
        self.ParController_verticalSlider.setValue(0)
    
    def slider_moved(self, value): # slider가 움직이는 도중에 계속해서 Model에 값을 할당
        if self.currentVal :
            V = self.currentVal
            if V == 0 : V = 1
            base = 1.025 # 지수의 밑이 될 수
            value = V*(base**value)
            tableViewModel = self.current_tableView.model()
            tableViewModel.setData(self.current_index, value, Qt.ItemDataRole.EditRole)

    def slider_released(self) :
        min_power = -100 # 최소 지수
        max_power = 100 # 최대 지수
        self.ParController_verticalSlider.setMinimum(min_power)
        self.ParController_verticalSlider.setMaximum(max_power)
        self.ParController_verticalSlider.setValue(0)
        if self.currentVal :
            self.currentVal = self.current_index.data(role = Qt.ItemDataRole.DisplayRole)

    def setCurrent(self, index : QModelIndex, tableView : QTableView) :
        self.current_tableView = tableView
        self.current_index = index
        if index.isValid() : self.currentVal = index.data(role=Qt.ItemDataRole.DisplayRole)
        if isinstance(self.currentVal, str) : # 클릭한 cell이 문자열 셀일경우
            self.clearCurrent()

    def clearCurrent(self) :
        self.current_tableView = None
        self.current_index = None
        self.currentVal = None