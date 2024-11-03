from PyQt6.QtWidgets import QDockWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import pyqtSignal, QObject
from typing import List, TYPE_CHECKING
import copy

if TYPE_CHECKING :
    from .DataManager import DataManager
from .Layer import LayerWidget, Layerclass
from .ui.Sample_ui import Ui_Sample

class Sampleclass(QObject) : # 여러 Layer들을 갖는 Sample 클래스
    def __init__(self, parent=None, DataManager : 'DataManager' = None) :
        super().__init__(parent)
        self.DataManager = DataManager
        self.Layers : List[Layerclass] = []
        self.name = 'Sample'
    
    def setName(self, name) :
        self.name = name

    def addLayer(self, Layer : Layerclass) :
        if Layer not in self.Layers :
            self.Layers.insert(0, Layer)
    
    def getLayers(self) :
        return self.Layers[:]
    
    def getAllParams_flattened(self) :
        # 각 Layer의 두께, Einf, OscParams를 포함한 모든 파라미터들을 flatten해서 반환
        # [Layer#0 두께, Layer#0 Einf, Layer#0 Param, ... , Layer#N 두께, Layer#N Einf, Layer#N Param] 의 식으로 반환
        # Calculator의 getSampleSimulation을 이용하기 위함

        Params = []
        for Layer in self.Layers :
            Params.append(Layer.getThickness())
            Params.append(Layer.getEinf())
            Params.extend(Layer.getParams_flattened())

        return Params
    
    def getAllAdjustableParams_flattened(self) :
        # Adjustable한 모든 파라미터들 반환하는 함수
        Params = []
        for Layer in self.Layers :
            Params.extend(Layer.getAllAdjustableParams_flattened())
        return Params
    
    def getAll_isAdjustable_flattened(self) :
        # 각 Layer의 두께, Einf, OscParams를 포함한 모든 파라미터들의 isAdjustable 여부를 flatten해서 반환
        # [Layer#0 두께, Layer#0 Einf, Layer#0 Param, ... , Layer#N 두께, Layer#N Einf, Layer#N Param] 의 식으로 반환
        # Calculator의 getSampleSimulation을 이용하기 위함

        isAdjustables = []
        for Layer in self.Layers :
            isAdjustables.extend(Layer.getAll_isAdjustable_flattened())

        return isAdjustables
    
    def replace_Adjustable_Parameters(self, new_adjustable_params) :
        # Layer들의 기존의 Params들중 Adjustable한 것들을 new로 갈아끼운다.
        Layers = self.getLayers()
        Layers_paramGroup = []
        i = 0
        for Layer in Layers :
            num_adjustable_params_Layer = len(Layer.getAllAdjustableParams_flattened())
            new_adjustable_params_Layer = new_adjustable_params[i:i+num_adjustable_params_Layer]
            Layer.replace_Adjustable_Parameters(new_adjustable_params_Layer)
            i += num_adjustable_params_Layer

    def replace_Adjustable_Parameters_NOT_Change_UI(self, new_adjustable_params) :
        # fitting시 계산의 속도 향상을 위해 UI단과 통신하지 않으면서 parameter만 갈아끼우는 메서드
        # 위 replace_Adjustalbe_Parameters 와 똑같지만 set 메서드들을 이용하지 않고 직접 parameter를 바꿔준다
        Layers = self.getLayers()
        Layers_paramGroup = []
        i = 0
        for Layer in Layers :
            num_adjustable_params_Layer = len(Layer.getAllAdjustableParams_flattened())
            new_adjustable_params_Layer = new_adjustable_params[i:i+num_adjustable_params_Layer]
            Layer.replace_Adjustable_Parameters_NOT_Change_UI(new_adjustable_params_Layer) # 여기만 다름
            i += num_adjustable_params_Layer

    def cache_Dielectric_Func(self, x) : 
        # Sample 내 Layer들에 대해 fixed dielectric func인 경우 주어진 x축에 대해 interpolate하여 caching합니다
        for Layer in self.Layers :
            Layer.cache_Dielectric_Func(x)

    def remove_cached_Dielectric_Funcs(self) : 
        # Sample 내 Layer들에 대해 캐싱된 Dielectric func들을 모두 제거합니다.
        for Layer in self.Layers :
            Layer.remove_cached_Dielectric_Funcs()

    def __deepcopy__(self, memo):
        # Layer객체를 deep copy하여 반환하는 메서드
        # Create a new instance
        new_copy = Sampleclass(parent=None, DataManager=self.DataManager)
        new_copy.setName(self.name)
        
        # Copy simple attributes
        for Layer in self.Layers :
            copied_Layer = copy.deepcopy(Layer)
            new_copy.addLayer(copied_Layer)

        return new_copy

class SampleDockWidget(QDockWidget, Ui_Sample):

    addedLayer = pyqtSignal(object)

    def __init__(self, parent=None, DataManager : 'DataManager' = None):
        super().__init__(parent)
        self.DataManager = DataManager
        
        # Load the UI for Sample
        self.setupUi(self)
        self.initialize()

    def initialize(self) :
        self.LayerWidgets : List[LayerWidget] = []
        self.Sample = Sampleclass(self, DataManager = self.DataManager)

        # Find the layout and button in the loaded UI
        self.verticalLayout_SampleStructure = self.findChild(QVBoxLayout, 'verticalLayout_SampleStructure')
        self.pushButton_AddLayer = self.findChild(QPushButton, 'pushButton_AddLayer')

        # Connect the button click to the add_layer method
        self.pushButton_AddLayer.clicked.connect(self.AddLayer)
        self.AddLayer(name='Substrate')

    def AddLayer(self, name = None):
        # Load the Layer UI from the ui folder
        LayerName = name
        if not name : 
            i = 1
            while i < 100 : 
                LayerName = 'Layer # '+str(i)
                if LayerName not in [Layer.name for Layer in self.DataManager.getLayers()] : break
                i=i+1
    
        LayerWidget_ = LayerWidget(self, name = LayerName, DataManager=self.DataManager)

        self.LayerWidgets.append(LayerWidget_)
        self.Sample.addLayer(LayerWidget_.Layer)
        self.verticalLayout_SampleStructure.insertWidget(0, LayerWidget_)
        self.addedLayer.emit(LayerWidget_)


    def update(self) :
        print('SampleWindow updated')
        return