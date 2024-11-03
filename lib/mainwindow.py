#from resources import Arrow_rc
from PyQt6.QtWidgets import QDockWidget, QListWidget, QToolBar, QMainWindow, QFileDialog, QInputDialog
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtCore import Qt, QSize
import pandas as pd
import numpy as np
import csv
import pyqtgraph as pg

from .Sample import SampleDockWidget
from .model import modelDockWidget
from .DataManager import DataManager
from .Graph import GraphDockWidget
from .Fit import FitDockWidget
from .ParameterController import ParameterControllerDockWidget
from .CustomClass import OpticalItem


FILE_FILTERS = [
    "Portable Network Graphics files (*.png)",
    "Text files (*.txt)",
    "Comma Separated Values (*.csv)",
    "All files (*)",
]

# 메인 윈도우가 될 App 클래스
class App(QMainWindow):
    # 추가할 것 : 메뉴 바
    def __init__(self):
        #self.data_manager = DataManager(self) # 모든 데이터들을 중앙관리할 Data Manager 선언
        
        super().__init__()
        self.DataManager = DataManager(self)

        self.SampleDockWidget = SampleDockWidget(self, DataManager=self.DataManager)
        self.SampleDockWidget.addedLayer.connect(self.updateLayerModelDockWidget)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.SampleDockWidget)
        self.DataManager.subscribe(self.SampleDockWidget)
        
        self.DataManager.subscribe_Sample(self.SampleDockWidget.Sample)
        self.DataManager.subscribe_Layer(self.SampleDockWidget.Sample.Layers[0])
        
        self.FitDockWidget = FitDockWidget(self, self.DataManager)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.FitDockWidget)

        self.GraphDockWidget = GraphDockWidget(self, DataManager=self.DataManager)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.GraphDockWidget)
        self.DataManager.subscribe_GraphDockWidget(self.GraphDockWidget)

        self.ParControllerDockWidget = ParameterControllerDockWidget(self, DataManager=self.DataManager)
        self.DataManager.subscribe_ParController(self.ParControllerDockWidget)



        self.updateLayerModelDockWidget()
        self.setToolBar()

    def updateLayerModelDockWidget(self) :
        if self.SampleDockWidget :
            for LayerWidget in self.SampleDockWidget.LayerWidgets :
                self.DataManager.subscribe_Layer(LayerWidget.Layer)
                self.DataManager.subscribe_modelDockWidget(LayerWidget.LayerModelDockWidget)
                self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, LayerWidget.LayerModelDockWidget)
                self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.ParControllerDockWidget) # ParController를 항상 맨 오른쪽에 두기 위해
                LayerWidget.LayerModelDockWidget.cellClicked.connect(self.ParControllerDockWidget.setCurrent)

    def setToolBar(self) :
        toolbar = QToolBar("Default ToolBar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        action_LoadFile = QAction("Load File", self)
        action_LoadFile.setStatusTip("Load Data File")
        action_LoadFile.triggered.connect(self.loadDataFile)
        toolbar.addAction(action_LoadFile)

        action_ExportGraph = QAction("Export Graph", self)
        action_ExportGraph.setStatusTip("Export Graph Lines to csv file")
        action_ExportGraph.triggered.connect(self.exportData)
        toolbar.addAction(action_ExportGraph)

        action_AddGraph = QAction("Add Graph", self)
        action_AddGraph.setStatusTip("Add Graph Dock Widget")
        action_AddGraph.triggered.connect(self.AddGraph)
        toolbar.addAction(action_AddGraph)

        action_LoadT = QAction("Load devide T data", self) # 임시. T(0V) 를 로드해서 T 그릴때 나눠준다
        action_LoadT.setStatusTip("Load devide T data")
        action_LoadT.triggered.connect(self.LoadT)
        toolbar.addAction(action_LoadT)
        
    def loadDataFile(self):
        caption = "Load Data file"
        initial_dir = ""  # Empty uses current folder.
        initial_filter = FILE_FILTERS[3]  # Select one from the list.

        dialog = QFileDialog()
        dialog.setWindowTitle(caption)
        dialog.setDirectory(initial_dir)
        dialog.setNameFilters(FILE_FILTERS)
        dialog.selectNameFilter(initial_filter)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.exec()

        for fileName in dialog.selectedFiles() :
            if fileName: # 파일 타입에 따라 다르게 받는 것 구현 예정
                if 'csv' in fileName.split('/')[-1] : dataDF = pd.read_csv(fileName, delimiter=',')
                else : dataDF = pd.read_csv(fileName, delimiter=r'[\s\t]+', engine='python') # 구분자를 탭문자 혹은 공백문자로
                # 첫 번째 열은 X축, 나머지 열은 Y축 데이터로 생각한다.
                data = OpticalItem()
                data.name = fileName.split('/')[-1] # 파일 명을 data의 명으로
                data.dtype = self.getDataType()
                data.curveType = 'Data'
                data.Ndata = dataDF.shape[1]
                keys = dataDF.keys()
                data.x = dataDF[keys[0]]
                data.x = np.array(data.x).flatten()
                data.y = dataDF[keys[1:]] # y데이터가 2개 이상인 경우 수정 예정
                data.y = np.array(data.y.T).flatten()
                self.DataManager.subscribe_data(data)
        self.DataManager.update_subscribes()


    def getDataType(self):
        title = "Select the Type of Data"
        label = "Select the Data Type from the list"
        DataTypes = ['T', 'R', 'E1', 'E2', 'S1', 'S2', 'n', 'k', 'Psi', 'Delta', 'TdT']
        initial_selection = 0  # orange, indexed from 0
        selected_DataType, ok = QInputDialog.getItem(
            self,
            title,
            label,
            DataTypes,
            current=initial_selection,
            editable=False,
        )
        return selected_DataType

    def get_folder(self):
        caption = "Select folder"
        initial_dir = ""  # Empty uses current folder.

        dialog = QFileDialog()
        dialog.setWindowTitle(caption)
        dialog.setDirectory(initial_dir)
        dialog.setFileMode(QFileDialog.FileMode.Directory)

        ok = dialog.exec()
        print(
            "Result:",
            ok,
            dialog.selectedFiles(),
            dialog.selectedNameFilter(),
        )

    def exportData(self):
        EXPORT_RESOLUTION = 10000
        # Get the data from the plot
        '''graphWidget = self.GraphDockWidget.graphWidget
        
        dataset = {}

        graphItems = graphWidget.items()
        index_item = 1
        for item in graphItems :
            if isinstance(item, pg.PlotDataItem):
                dataset[f'X{index_item}'] = item.getData()[0]
                dataset[f'Y{index_item}'] = item.getData()[1]
                print(item.name())
                index_item += 1'''
        
        dataset = {}
        index_item = 1
        for item in self.GraphDockWidget.GraphCurvesItems :
            xmin = min(item.x)
            xmax = max(item.x)
            x = np.linspace(xmin, xmax, EXPORT_RESOLUTION)
            print(item.name)
            if item.curveType == 'Layer' :
                Layer = self.DataManager.getModel_byName(item.name)
                y = self.DataManager.Calculator.getLayerSimulation(x, Layer, item.dtype)
            elif item.curveType == 'Sample' :
                Sample = self.DataManager.getModel_byName(item.name)
                y = self.DataManager.Calculator.getSampleSimulation(x, Sample, item.dtype)
            else : 
                x = item.x
                y = item.y
            dataset[f'X{index_item}'] = x
            dataset[f'Y{index_item}'] = y
            index_item += 1
        
        df_dataset = pd.DataFrame(dataset)
        
        
        caption = "Save As"
        initial_dir = ""  # Empty uses current folder.
        initial_filter = FILE_FILTERS[3]  # Select one from the list.

        dialog = QFileDialog()
        dialog.setWindowTitle(caption)
        dialog.setDirectory(initial_dir)
        dialog.setNameFilters(FILE_FILTERS)
        dialog.selectNameFilter(initial_filter)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)

        ok = dialog.exec()
        print(
            "Result:",
            ok,
            dialog.selectedFiles(),
            dialog.selectedNameFilter(),
        )

        df_dataset.to_csv(dialog.selectedFiles()[0]+'.csv', index=False)
    def AddGraph(self) : 
        AddedGraphDockWidget = GraphDockWidget(self, DataManager=self.DataManager)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, AddedGraphDockWidget)
        self.DataManager.subscribe_GraphDockWidget(AddedGraphDockWidget)

    def LoadT(self) : # 임시. T(0V) 불러와서 나누는 용
        caption = "Load T file"
        initial_dir = ""  # Empty uses current folder.
        initial_filter = FILE_FILTERS[3]  # Select one from the list.

        dialog = QFileDialog()
        dialog.setWindowTitle(caption)
        dialog.setDirectory(initial_dir)
        dialog.setNameFilters(FILE_FILTERS)
        dialog.selectNameFilter(initial_filter)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.exec()

        for fileName in dialog.selectedFiles() :
            if fileName: # 파일 타입에 따라 다르게 받는 것 구현 예정
                if 'csv' in fileName.split('/')[-1] : dataDF = pd.read_csv(fileName, delimiter=',')
                else : dataDF = pd.read_csv(fileName, delimiter=r'[\s\t]+', engine='python') # 구분자를 탭문자 혹은 공백문자로
                # 첫 번째 열은 X축, 나머지 열은 Y축 데이터로 생각한다.
                data = OpticalItem()
                data.name = fileName.split('/')[-1] # 파일 명을 data의 명으로
                data.dtype = self.getDataType()
                data.curveType = 'Data'
                data.Ndata = dataDF.shape[1]
                keys = dataDF.keys()
                data.x = dataDF[keys[0]]
                data.x = np.array(data.x).flatten()
                data.y = dataDF[keys[1:]] # y데이터가 2개 이상인 경우 수정 예정
                data.y = np.array(data.y.T).flatten()
                self.DataManager.setT0V(data)