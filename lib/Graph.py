from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QApplication
import pyqtgraph as pg  # import PyQtGraph after Qt
from typing import List, TYPE_CHECKING
import sys

if TYPE_CHECKING :
    from .DataManager import DataManager
from .CustomClass import OpticalItem, DataListWidgetItem, LayerListWidgetItem, SampleListWidgetItem, CHISQListWidgetItem, MultiListWidgetItem, CustomListWidgetItem
from .ui.graph_set_dialog_ui import Ui_GraphSetDialog


# PyQtGraph 전역 설정 변경
pg.setConfigOptions(
    background='w',    # 배경색 (white)
    foreground='k',    # 전경색 (black)
    antialias=True     # 안티앨리어싱 활성화
)

class DoubleClickFilter(QtCore.QObject):
    def __init__(self, parent=None, double_click_callback=None):
        super().__init__(parent)
        self.double_click_callback = double_click_callback

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.MouseButtonDblClick:
            if isinstance(obj, pg.PlotWidget):
                if self.double_click_callback:
                    self.double_click_callback()
                    return True
        return super().eventFilter(obj, event)

class GraphDockWidget(QtWidgets.QDockWidget):
    def __init__(self, parent=None, DataManager : 'DataManager' = None):
        super().__init__(parent)
        self.setObjectName('Graph')
        self.setWindowTitle('Graph')
        self.DataManager = DataManager
        self.GraphSetDialog = GraphSetDialog(self, DataManager=self.DataManager)
        self.GraphCurvesItems : List[OpticalItem] = []  #현재 그래프에 어떤 객체가 그려져있는지 저장할 리스트 생성.

        self.graphWidget = pg.PlotWidget()
        self.setWidget(self.graphWidget)
        self.setDefaultGraphDesign()

        self.default_pen = pg.mkPen(color=(255, 0, 0), width=2)
        self.default_colorpalette = [
            (255, 0, 0),  # red
            (0, 255, 0),  # green
            (0, 0, 255),  # blue
            (255, 255, 0),  # yellow
            (255, 0, 255),  # magenta
            (0, 255, 255)  # cyan
        ]

        # 그래프 더블클릭시 발생할 이벤트 처리하는 필터와 이벤트 발생시 실행할 함수 (그래프설정) 전달
        doubleClickFilter = DoubleClickFilter(self, double_click_callback=self.open_GraphSetDialog)
        self.graphWidget.installEventFilter(doubleClickFilter)

    def setDefaultGraphDesign(self):
        # PlotItem 객체 가져오기
        plotItem = self.graphWidget.getPlotItem()

        # 축 스타일 설정
        axisPen = pg.mkPen(color='k', width=2)  # 축선 스타일
        for axis in ['left', 'bottom', 'right', 'top']:
            plotItem.getAxis(axis).setPen(axisPen)

        # 우측과 상단 축 활성화
        plotItem.showAxis('right')
        plotItem.showAxis('top')

        # 레전드 추가 및 이동 가능 설정
        self.legend = pg.LegendItem((100, 60), offset=(70, 30))  # 크기 설정 및 위치 초기화
        self.legend.setParentItem(plotItem)

    def update_plot(self, datas : List[OpticalItem]):
        self.graphWidget.clear()
        self.legend.clear()  # 레전드 초기화

        for index, data in enumerate(datas):
            color = self.default_colorpalette[index % len(self.default_colorpalette)]
            pen = data.pen if hasattr(data, 'pen') else pg.mkPen(color=color, width=2)
            lineName = '['+data.dtype+'] '+data.name # 표시하는 선의 이름을 예시 : [E1] dataname 과 같이 정의
            plotItem = self.graphWidget.plot(
                data.x, data.y, pen=pen, name=lineName
            )
            self.legend.addItem(plotItem, lineName)
        self.GraphCurvesItems = datas

    def update_model_line(self, data : OpticalItem) : 
        if data.curveType == 'Data' : return # Data일땐 실행 X. 시뮬레이션하는 모델만 update시키는 함수.
        model_line = None
        items = self.graphWidget.items()
        for item in items:
            if isinstance(item, pg.PlotDataItem) and ( data.name in item.name() ) and ( data.dtype in item.name() ):
                # data의 이름 (LayerName 혹은 SampleName)이 Line 이름에 들어가있고, dtype도 들어간 경우 (즉 dtype과 name이 item과 같을 때)
                model_line = item
                model_line.setData(data.x, data.y)
        
        if model_line == None : # 위에서 if문에 한번도 통과 못한 경우
            # 현재 Model 의 line이 너무 빠르게 업데이트돼서 (추정) 중간에 사라지는 바람에 else문으로 연결되는 문제가 있는듯?
            #raise ValueError('Ther is No data named {}'.format(data.name))
            print('There is no model curve named {}'.format(data.name))

    def update(self) :
        print('GraphWindow updated')
        return

    def open_GraphSetDialog(self) :
        # GraphSetDialog를 열면서, 현재 로드된 데이터와 생성된 Layer, Sample들이 뭐가 있는지를 GraphSetDialog에 알려준다.
        Datas = self.DataManager.getDatas()
        Layers = self.DataManager.getLayers()
        Samples = self.DataManager.getSamples()
        DataTypeTexts = self.GraphSetDialog.getDataTypeTexts()
        Layers_OpticalItems : List[OpticalItem] = []
        Sample_OpticalItems : List[OpticalItem] = []
        for DataTypeText in DataTypeTexts :
            if DataTypeText == 'All' : continue
            elif DataTypeText == 'R' or DataTypeText == 'T' or DataTypeText == 'Psi' or DataTypeText == 'Delta' or DataTypeText == 'TdT': 
                Sample_OpticalItems = Sample_OpticalItems + [OpticalItem(name = Sample.name, dtype=DataTypeText, curveType='Sample') for Sample in Samples]
            else :
                Layers_OpticalItems = Layers_OpticalItems + [OpticalItem(name = Layer.name, dtype=DataTypeText, curveType='Layer') for Layer in Layers]
        
        OpticalItems = Datas + Layers_OpticalItems + Sample_OpticalItems
        ListWidgetItems : List[CustomListWidgetItem] = []
        for item in OpticalItems :
            if item.curveType == 'Data' : ListWidgetItems.append(DataListWidgetItem(item))
            elif item.curveType == 'Sample' : ListWidgetItems.append(SampleListWidgetItem(item))
            elif item.curveType == 'Layer' : ListWidgetItems.append(LayerListWidgetItem(item))
            elif item.curveType == 'CHISQ' : ListWidgetItems.append(CHISQListWidgetItem(item))
            elif item.curveType == 'Multi' : ListWidgetItems.append(MultiListWidgetItem(item))
            else : raise ValueError("This item has no curveType : {}".format(item.curveType))
            
        self.GraphSetDialog.insertListWidgetItems(ListWidgetItems)
        self.GraphSetDialog.show()
        

    def show_line_style_dialog(self):
        items = [GraphCurveItem.name for GraphCurveItem in self.GraphCurveItems]
        item, ok = QtWidgets.QInputDialog.getItem(self, "Select Data", "Choose data to style:", items, 0, False)
        if ok and item:
            selected_data = next((data for data in self.GraphCurveItems if data.name == item), None)
            if selected_data:
                color = QtWidgets.QColorDialog.getColor()
                if color.isValid():
                    r, g, b = color.red(), color.green(), color.blue()
                else:
                    r, g, b = 255, 0, 0

                width, ok = QtWidgets.QInputDialog.getInt(self, "Line Width", "Enter new line width:", min=1, max=10)
                if not ok:
                    width = 2

                selected_data.pen = pg.mkPen(color=(r, g, b), width=width)
                self.update_plot(self.GraphCurveItems)



class GraphSetDialog(QtWidgets.QDialog, Ui_GraphSetDialog) :
    
    def __init__(self, parent = None, DataManager : 'DataManager' = None) :
        super().__init__(parent)
        self.DataManager = DataManager
        self.setupUi(self)
        self.radioButton_CurveType_All.setChecked(True)
        self.radioButton_Quantity_All.setChecked(True)
        self.pushButton_SetLineColor.setEnabled(False) # 디폴트로 그래프 선 세팅은 비활성화
        self.lineEdit_LineWidth.setEnabled(False)
        

        self.ListWidgetItems : List[CustomListWidgetItem] = []

        self.pushButton_MoveToGraph.clicked.connect(self.moveSelectedItems_to_Graph)
        self.pushButton_RemoveFromGraph.clicked.connect(self.removeSelectedItems_from_Graph)
        self.buttonGroup_CurveType.buttonClicked.connect(self.displayItems)
        self.buttonGroup_DataType.buttonClicked.connect(self.displayItems)

    def insertListWidgetItems(self, items) :
        self.ListWidgetItems = items
    
    def insertListWidgetItems_to_Available_curves_Listwidget(self, curveType, dtype) :
        while self.listWidget_Available_curves.count() > 0: # clear()메서드를 쓰면 WidgetItem들이 제거되므로 
            self.listWidget_Available_curves.takeItem(0) # 제거되지 않으면서 listwidget에서 없애기 위함
        isAllofItems = False
        isAllofCurveType_but_NotAllofDtype = False
        isNotAllofCurveType_but_AllofDtype = False
        if curveType == 'All' :
            if dtype == 'All' : isAllofItems = True # 둘다 All 체크면 모든 아이템을 담는다
            else : isAllofCurveType_but_NotAllofDtype = True # Dtpye만 All이 아닐 경우
        else :
            if dtype == 'All' : isNotAllofCurveType_but_AllofDtype = True # Dtype만 All일 경우

        if isAllofItems : # 모든 아이템을 담아야 하는 경우
            for item in self.ListWidgetItems :
                self.listWidget_Available_curves.addItem(item)

        elif isAllofCurveType_but_NotAllofDtype : # curveType은 상관없지만 Dtype을 가려받는 경우
            for item in self.ListWidgetItems :
                if item.dtype == dtype :
                    self.listWidget_Available_curves.addItem(item)
        
        elif isNotAllofCurveType_but_AllofDtype : # Dtype은 상관없지만 curveType을 가려받는 경우
            for item in self.ListWidgetItems :
                if item.curveType == curveType :
                    self.listWidget_Available_curves.addItem(item)
        
        else : # curveType과 dtype 모두 특정한 경우
            for item in self.ListWidgetItems :
                if (item.curveType == curveType) and (item.dtype == dtype) :
                    self.listWidget_Available_curves.addItem(item)
        
    def moveSelectedItems_to_Graph(self):
        selected_items = self.listWidget_Available_curves.selectedItems()
        for item in selected_items:
            self.listWidget_Available_curves.takeItem(self.listWidget_Available_curves.row(item))
            self.listWidget_Graph_curves.addItem(item)

    def removeSelectedItems_from_Graph(self):
        selected_items = self.listWidget_Graph_curves.selectedItems()
        for item in selected_items:
            self.listWidget_Graph_curves.takeItem(self.listWidget_Graph_curves.row(item))
            self.listWidget_Available_curves.addItem(item)

    def getDataTypeTexts(self) :
        DataTypeTexts = []
        for Button in self.buttonGroup_DataType.buttons() :
            DataTypeTexts.append(Button.text())
        return DataTypeTexts
    
    def showEvent(self, event):
        super().showEvent(event)
        self.displayItems()

    def displayItems(self) :
        CurveTypeButton = self.buttonGroup_CurveType.checkedButton()
        DataTypeButton = self.buttonGroup_DataType.checkedButton()
        CurveType = CurveTypeButton.text()
        DataType = DataTypeButton.text()
        self.insertListWidgetItems_to_Available_curves_Listwidget(curveType = CurveType, dtype = DataType)
        
    def accept(self) :
        GraphCurves_ListWidgetItems = [self.listWidget_Graph_curves.item(i) for i in range(self.listWidget_Graph_curves.count())]
        self.DataManager.setGraphCurves(GraphCurvesListWidgetItems = GraphCurves_ListWidgetItems,
                                        GraphDockWidget_=self.parent())
        super().accept()





