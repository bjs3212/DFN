from typing import List, TYPE_CHECKING
from PyQt6.QtCore import QObject
import numpy as np
import pyqtgraph as pg
import json, sys

if TYPE_CHECKING :
    from .Layer import Layerclass
    from .Graph import GraphDockWidget
    from .Sample import Sampleclass
    from .model import modelDockWidget
    from .ParameterController import ParameterControllerDockWidget
from .Calculator import CalculatorClass
from .CustomClass import OpticalItem, CustomListWidgetItem

MODEL_PLOT_RESOLUTION = 500 # Model의 광학상수 계산하여 plot할때 얼마나 조밀하게 plot할 것인지. 높을 수록 조밀하다.

class DataManager(QObject) :
    
    def __init__(self, main) :
        super().__init__(main)
        self.main = main
        self.Calculator = CalculatorClass(self)
        self.subscribes = []  # 데이터 매니저를 구독시킬 모든 윈도우 객체 참조
        self.datas : List[OpticalItem] = []
        self.Layers : List['Layerclass'] = []
        self.Samples : List['Sampleclass'] = []
        self.GraphDockWidgets : List['GraphDockWidget'] = []
        self.modelDockWidgets : List['modelDockWidget'] = []
        self.fitWindow = None
        self.parController : 'ParameterControllerDockWidget' = None


    def subscribe(self, subscribe) :
        self.subscribes.append(subscribe)

    def update_subscribes(self) :
        for subscribe in self.subscribes :
            subscribe.update()
        
    def subscribe_data(self, data : OpticalItem) :
        exist_dataNames = [data.name for data in self.datas]
        if data.name not in exist_dataNames:
            self.datas.append(data)
            
    def subscribe_Layer(self, Layer : 'Layerclass') :
        if Layer not in self.Layers :
            self.Layers.append(Layer)
            Layer.LayerParameterChanged.connect(self.update_model_graph)
            Layer.LayerNameChanged.connect(self.notify_LayerNameChanged)
            
    def subscribe_Sample(self, Sample : 'Sampleclass') :
        if not self.Samples :
            self.Samples.append(Sample)
            #self.subscribes.append(Layer)
            
    def subscribe_GraphDockWidget(self, Graph_DockWidget : 'GraphDockWidget') :
        if Graph_DockWidget not in self.GraphDockWidgets:
            self.GraphDockWidgets.append(Graph_DockWidget)
            self.subscribes.append(Graph_DockWidget)
            Graph_DockWidget.graphWidget.getViewBox().sigXRangeChanged.connect(self.update_model_graph)

    def subscribe_modelDockWidget(self, model_DockWidget : 'modelDockWidget') :
        if model_DockWidget not in self.modelDockWidgets:
            self.modelDockWidgets.append(model_DockWidget)
            #self.subscribes.append(model_DockWidget)

    def subscribe_ParController(self, parController : 'ParameterControllerDockWidget') :
        self.parController = parController
        
    def subscribe_fit(self, fit_window) :
        self.fitWindow = fit_window
        self.subscribes.append(fit_window)

    def setGraphCurves(self, GraphCurvesListWidgetItems : List[CustomListWidgetItem], GraphDockWidget_ : 'GraphDockWidget') :
        Graph_Curves : List[OpticalItem] = []

        vb = GraphDockWidget_.graphWidget.getViewBox()
        x_min, x_max = vb.viewRange()[0]
        x_for_simulation = np.linspace(x_min, x_max, MODEL_PLOT_RESOLUTION) # 시뮬레이션을 위한 x축 데이터 계산
        
        for item in GraphCurvesListWidgetItems : # CHISQ와 Multi는 아직 미구현.
            for data in self.datas :
                if item.name == data.name : Graph_Curves.append(data)
            for Layer in self.Layers :
                if item.name == Layer.name :
                    Layer_data = OpticalItem(name = Layer.name, x = x_for_simulation, dtype=item.dtype, curveType='Layer')
                    Layer_data.y = self.Calculator.getLayerSimulation(x=x_for_simulation, Layer=Layer, dtype=item.dtype)
                    # 다른건 다 Layer에서 받아오고 dtype만 item에서 받아옴
                    Graph_Curves.append(Layer_data)
            for Sample in self.Samples :
                if item.name == Sample.name :
                    Sample_data = OpticalItem(name = Sample.name, x = x_for_simulation, dtype=item.dtype, curveType='Sample')
                    Sample_data.y = self.Calculator.getSampleSimulation(x=x_for_simulation, Sample = Sample, dtype=item.dtype)
                    Graph_Curves.append(Sample_data)

        GraphDockWidget_.update_plot(Graph_Curves)

    def update_model_graph(self) :
        for GraphDockWidget in self.GraphDockWidgets :
            graphWidget = GraphDockWidget.graphWidget
            if graphWidget.listDataItems() == 0 : return # 현재 표시중인 그래프가 없을 경우 update X

            graphWidgetItems = [item for item in GraphDockWidget.GraphCurvesItems]
            isData_in_graphWidgetItems = [item.curveType == 'Data' for item in graphWidgetItems] # 그래프에 그린 선들 중 데이터가 있는지 bool타입으로 체크

            if False not in isData_in_graphWidgetItems : return # True밖에 없으면 데이터뿐인 것이므로 업데이트 x

            vb = graphWidget.getViewBox()
            x_min, x_max = vb.viewRange()[0]

            x = np.linspace(x_min, x_max, MODEL_PLOT_RESOLUTION)

            for optical_data in graphWidgetItems :
                ModelData = OpticalItem(name = optical_data.name, x = x, dtype=optical_data.dtype, curveType=optical_data.curveType) # dtype부분 데이터 여러개일때, 원하는 광학상수 얻고싶을때 수정 요함
                
                # ModelData.y 를 계산하기 위해 이름이 같은 Sample 혹은 Layer 오브젝트를 불러온다.
                if optical_data.curveType == 'Sample' :
                    for Sample in self.Samples : 
                        if Sample.name == optical_data.name : ModelData.y = self.Calculator.getSampleSimulation(x = ModelData.x, Sample = Sample, dtype=ModelData.dtype)
                elif optical_data.curveType == 'Layer' :
                    for Layer in self.Layers :
                        if Layer.name == optical_data.name : ModelData.y = self.Calculator.getLayerSimulation(x = ModelData.x, Layer=Layer, dtype=ModelData.dtype)
                
                graphWidget.getViewBox().enableAutoRange(x=False, y=False) # setData 메서드에 의한 xRange 조정으로 인해 무한루프가 생기는 것을 방지하기 위해 기능 off
                GraphDockWidget.update_model_line(ModelData)

    def notify_LayerNameChanged(self, oldName, newName) : # (레이어 이름 변경시 다른 객체들에 이름 변경사항 전달하는 함수)
        for GraphDockWidget in self.GraphDockWidgets :
            GraphCurvesItems = GraphDockWidget.GraphCurvesItems
            for i in range(len(GraphCurvesItems)) :
                if GraphCurvesItems[i].name == oldName :
                    GraphCurvesItems[i] = OpticalItem(name = newName,
                                                      dtype=GraphCurvesItems[i].dtype,
                                                      curveType=GraphCurvesItems[i].curveType,
                                                      x=GraphCurvesItems[i].x,
                                                      y=GraphCurvesItems[i].y,
                                                      xtype=GraphCurvesItems[i].xtype)
            GraphDockWidget.update_plot(GraphCurvesItems)
        
        for modelDockWidget in self.modelDockWidgets : #model Dockwidget의 이름 바꾸기
            if modelDockWidget.LayerName == oldName :
                modelDockWidget.setWindowTitle(newName)

            
    def getDatas(self) :
        return self.datas
    def getLayers(self) :
        return self.Layers
    def getSamples(self) :
        return self.Samples
    
    def getData_byName(self, name) :
        for data in self.datas :
            if data.name == name :
                return data
            
    def getModel_byName(self, name) :
        for Layer in self.Layers :
            if Layer.name == name :
                return Layer
        for Sample in self.Samples :
            if Sample.name == name :
                return Sample
            
    def save_layer_to_file(self, layer : 'Layerclass', filename):
        data = {
            "Einf": layer.Einf,
            "Thickness": layer.Thickness,
            "Params": layer.Params,
            "OscTypes": layer.OscTypes
        }
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)

    def load_layer_from_file(self, layer : 'Layerclass', filename):
        with open(filename, 'r') as file:
            data = json.load(file)
            layer.setEinf(data['Einf'])
            layer.setThickness(data['Thickness'])
            layer.setParams(data['Params'])
            layer.setOscTypes(data['OscTypes'])
            

    def setT0V(self, data) : # 임시 T(0V) 불러와서 나누는 용
        self.T0V = data
