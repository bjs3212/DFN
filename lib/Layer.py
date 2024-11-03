import sys
import os
import pandas as pd
import numpy as np
import copy
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog
from PyQt6.QtCore import QObject, Qt, pyqtSignal
from typing import List, TYPE_CHECKING


if TYPE_CHECKING :
    from .DataManager import DataManager
from .model import modelDockWidget
from .ui.Layer_ui import Ui_LayerWidget
from .ParamsTable import ParamsTableModel
from .CustomClass import OpticalItem

FILE_FILTERS = [
    "Portable Network Graphics files (*.png)",
    "Text files (*.txt)",
    "Comma Separated Values (*.csv)",
    "JSON Files (*.json)",
    "All files (*)",
]


class Layerclass(QObject) : # 각 Layer의 optical model의 parameter를 저장할 class 선언

    LayerParameterChanged = pyqtSignal(object, object) # 이 시그널에선 Layer의 이름, Layer에서 변경된 부분을 emit할 예정
    LayerNameChanged = pyqtSignal(str, str) # LayerName이 바뀐 경우, (oldname, newname) 을 emit

    def __init__(self, parent=None, DataManager : 'DataManager' =None, name='Layername', 
                 ThicknessTableModel : ParamsTableModel = None, 
                 EinfTableModel : ParamsTableModel = None, 
                 ParamsTableModel : ParamsTableModel = None,
                 isVacuum = False,
                 isCoherent = True):
        super().__init__(parent)
        self.DataManager = DataManager
        self.name = name
        self.ThicknessTableModel = ThicknessTableModel
        self.EinfTableModel = EinfTableModel
        self.ParamsTableModel = ParamsTableModel
        self.updating_from_model = True
        
        # set Default Parameters
        self.Thickness = 3.
        self.Einf = 3.
        self.Params = [[100., 50., 10.]] 
        self.OscTypes = ['Lorentzian']
        self.OscTypes_Params = self.combine_osc_params(self.OscTypes, self.Params)
        self.isAdjustableThickenss = True
        self.isAdjustableEinf = True
        self.isAdjustableParams = [[True for data in data_row] for data_row in self.Params] # 피팅에 쓸 파라미터인지 확인하는 bool list
        self.isVacuum = isVacuum # Vacuum layer가 필요할때. 기본 값은 False
        self.isCoherent = isCoherent # Coherent 인지 inCoherent 인지. 기본 값은 True
        self.isFixedLayer = False # n, k를 불러온 값으로 고정시킨 Layer인지. 기본 값은 False
        self.cached_interpolated_Dielectric_Funcs : List[OpticalItem] = [] 
        # 미리 계산해서 캐싱해둔 Dielectric func들을 저장할 변수

        self.setThickness(self.Thickness)
        self.setEinf(self.Einf)
        self.setParams(self.Params)
        self.setOscTypes(self.OscTypes)

        # Connect signals to slots
        if self.ThicknessTableModel:
            self.ThicknessTableModel.dataChanged.connect(self.update_thickness_from_table)
        if self.EinfTableModel:
            self.EinfTableModel.dataChanged.connect(self.update_einf_from_table)
        if self.ParamsTableModel:
            self.ParamsTableModel.dataChanged.connect(self.update_params_from_table)
            self.ParamsTableModel.tableChanged.connect(self.update_params_from_table)

    def setThicknessTableModel(self, ThicknessTableModel) :
        self.ThicknessTableModel = ThicknessTableModel
    def setEinfTabelModel(self, EinfTableModel) :
        self.EinfTableModel = EinfTableModel
    def setParamsTableModel(self, ParamsTableModel) :
        self.ParamsTableModel = ParamsTableModel

    def getThickness(self) :
        return self.Thickness
    def getEinf(self) :
        return self.Einf
    def getParams(self) :
        return self.Params[:]
    def getParams_flattened(self) :
        return [Param for Params_row in self.Params for Param in Params_row]
    def getAllParams(self) : 
        return [self.Thickness] + [self.Einf] + self.getParams_flattened()
    def getAll_isAdjustable_flattened(self) :
        # isAdjustable 변수들을 flatten 하여 반환. (두께, Einf, 나머지파라미터들) 순서
        isAdjustables = []
        isAdjustables.append(self.isAdjustableThickenss)
        isAdjustables.append(self.isAdjustableEinf)
        isAdjustables.extend([isAdjustable for isAdjustable_row in self.isAdjustableParams for isAdjustable in isAdjustable_row])
        return isAdjustables

    def getOscTypes(self) :
        return self.OscTypes[:]
    def getAllAdjustableParams_flattened(self) : #Thickness, Einf를 포함한 모든 파라미터들중 조정 가능한 파라미터를 전달한다.
        AdjustableParams = []
        AdjustableParams_osc = [self.Params[i][j] for i in range(len(self.Params)) for j in range(len(self.Params[i])) if self.isAdjustableParams[i][j]]
        # 오실레이터의 parameter들중 조정가능한것들
        if self.isAdjustableThickenss : AdjustableParams.append(self.Thickness)
        if self.isAdjustableEinf : AdjustableParams.append(self.Einf)
        AdjustableParams.extend(AdjustableParams_osc)

        return AdjustableParams

        
    
    def setName(self, newName) :
        oldName = self.name
        self.name = newName
        self.LayerNameChanged.emit(oldName, newName)
        
    def setThickness(self, Thickness):
        self.Thickness = Thickness
        if self.ThicknessTableModel:
            self.updating_from_model = False
            index = self.ThicknessTableModel.index(0, 0)
            self.ThicknessTableModel.setData(index, Thickness, Qt.ItemDataRole.EditRole)
            self.updating_from_model = True
        self.LayerParameterChanged.emit(self.name, 'Thickness')

    def setEinf(self, Einf):
        self.Einf = Einf
        if self.EinfTableModel:
            self.updating_from_model = False
            index = self.EinfTableModel.index(0, 0)
            self.EinfTableModel.setData(index, Einf, Qt.ItemDataRole.EditRole)
            self.updating_from_model = True
        self.LayerParameterChanged.emit(self.name, 'Einf')

    def setParams(self, Params):
        self.Params = Params
        if self.ParamsTableModel:
            self.updating_from_model = False

            row_count = self.ParamsTableModel.rowCount()
            col_count = self.ParamsTableModel.columnCount()
            # Params의 크기에 맞추어 row와 column을 추가
            if len(Params) > row_count:
                self.ParamsTableModel.insertRows(row_count, len(Params) - row_count)
            
            if len(Params) > 0 and len(Params[0]) > (col_count - 1): # OscType 칸 제외하기 위해 -1
                self.ParamsTableModel.insertColumns(col_count, len(Params[0]) - (col_count - 1))

            for row in range(len(Params)):
                for col in range(len(Params[row])):
                    index = self.ParamsTableModel.index(row, col+1) # +1 은 OscType칸을 제외하기 위해서
                    self.ParamsTableModel.setData(index, Params[row][col], Qt.ItemDataRole.EditRole)
            self.updating_from_model = True
        self.LayerParameterChanged.emit(self.name, 'Params')

    def setOscTypes(self, OscTypes):
        self.OscTypes = OscTypes
        OscTypes_Params = self.combine_osc_params(self.OscTypes, self.Params)
        if self.ParamsTableModel:

            row_count = self.ParamsTableModel.rowCount()
            col_count = self.ParamsTableModel.columnCount()
            # Params의 크기에 맞추어 row와 column을 추가
            if len(OscTypes_Params) > row_count:
                self.ParamsTableModel.insertRows(row_count, len(OscTypes_Params) - row_count)
            
            if len(OscTypes_Params) > 0 and len(OscTypes_Params[0]) > (col_count - 1): # OscType 칸 제외하기 위해 -1
                self.ParamsTableModel.insertColumns(col_count, len(OscTypes_Params[0]) - (col_count - 1))

            for row in range(len(OscTypes_Params)):
                for col in range(len(OscTypes_Params[row])):
                    index = self.ParamsTableModel.index(row, col)
                    self.ParamsTableModel.setData(index, OscTypes_Params[row][col], Qt.ItemDataRole.EditRole)
        self.LayerParameterChanged.emit(self.name, 'OscTypes')

    def replace_Adjustable_Parameters(self, new_adjustable_params) :
        isAdjustable = self.getAll_isAdjustable_flattened()
        original_params = self.getAllParams()
        params = []
        j = 0
        for i in range(len(isAdjustable)) :
            if isAdjustable[i] :
                params.append(new_adjustable_params[j])
                j += 1
            else :
                params.append(original_params[i])
        
        Thickness = params[0]
        Einf = params[1]
        osc_params = []

        i=0
        for OscType in self.OscTypes :
            params_osconly = params[2:]
            OscParameterNum = self.DataManager.Calculator.getOscParameterNumber(OscType)
            osc_params.append(params_osconly[i:i+OscParameterNum])
            i = i+OscParameterNum

        self.setThickness(Thickness)
        self.setEinf(Einf)
        self.setParams(osc_params)

    def replace_Adjustable_Parameters_NOT_Change_UI(self, new_adjustable_params) :
        # fitting시 계산의 속도 향상을 위해 UI단과 통신하지 않으면서 parameter만 갈아끼우는 메서드
        # 위 replace_Adjustalbe_Parameters 와 똑같지만 set 메서드들을 이용하지 않고 직접 parameter를 바꿔준다
        isAdjustable = self.getAll_isAdjustable_flattened()
        original_params = self.getAllParams()
        params = []
        j = 0
        for i in range(len(isAdjustable)) :
            if isAdjustable[i] :
                params.append(new_adjustable_params[j])
                j += 1
            else :
                params.append(original_params[i])
        
        Thickness = params[0]
        Einf = params[1]
        osc_params = []

        i=0
        for OscType in self.OscTypes :
            params_osconly = params[2:]
            OscParameterNum = self.DataManager.Calculator.getOscParameterNumber(OscType)
            osc_params.append(params_osconly[i:i+OscParameterNum])
            i = i+OscParameterNum
        # ---- 여기부터 위 메서드와 다름 ----

        self.Thickness = Thickness
        self.Einf = Einf
        self.Params = osc_params

    def setFixedDielectricFunc(self, DielectricFunc_data : OpticalItem) :
        x = DielectricFunc_data.x
        e1 = np.array(DielectricFunc_data.y['E1'])
        e2 = np.array(DielectricFunc_data.y['E2'])
        self.e1 = OpticalItem(name=self.name+' E1', dtype='E1', curveType='Layer', x=x, y=e1)
        self.e2 = OpticalItem(name=self.name+' E2', dtype='E2', curveType='Layer', x=x, y=e2)
        self.isFixedLayer = True
        self.isAdjustableEinf = False
        self.isAdjustableParams = [[False for isAdjustable in isAdjustable_row] for isAdjustable_row in self.isAdjustableParams]

    def cache_Dielectric_Func(self, x) : 
        # Dielectric func를 고정시킨 Layer일때
        # 받은 x축으로부터 Dielectric func를 interpolate해서 캐싱해둔다.
        if self.isFixedLayer == False : return # FixedLayer일 경우에만 함수 실행
        e1 = self.DataManager.Calculator.interpolate_or_extrapolate(self.e1.x, self.e1.y, new_x=x)
        e2 = self.DataManager.Calculator.interpolate_or_extrapolate(self.e2.x, self.e2.y, new_x=x, fill_value=0.)
        e = OpticalItem(x = x , y=e1 + 1j*e2)
        self.cached_interpolated_Dielectric_Funcs.append(e)
    
    def remove_cached_Dielectric_Funcs(self) : 
        self.cached_interpolated_Dielectric_Funcs = []

    def switchisCoherent(self) : # isCoherent를 True면 False로, False면 True로 switch하는 함수
        if self.isCoherent == True : self.isCoherent = False
        else : self.isCoherent = True

    def combine_osc_params(self, osc_types, params):
        return [[osc_type] + param for osc_type, param in zip(osc_types, params)]
    
    def split_osc_params(self, OscTypes_Params):
        OscTypes = [item[0] for item in OscTypes_Params]
        Params = [item[1:] for item in OscTypes_Params]
        return (OscTypes, Params)

    def update_thickness_from_table(self, top_left, bottom_right, roles):
        if self.updating_from_model:
            self.Thickness = self.ThicknessTableModel.data(top_left, Qt.ItemDataRole.EditRole)
            self.isAdjustableThickenss = self.ThicknessTableModel.getisAdjustable()[0][0]
            self.LayerParameterChanged.emit(self.name, 'Thickness')

    def update_einf_from_table(self, top_left, bottom_right, roles):
        if self.updating_from_model:
            self.Einf = self.EinfTableModel.data(top_left, Qt.ItemDataRole.EditRole)
            self.isAdjustableEinf = self.EinfTableModel.getisAdjustable()[0][0]
            self.LayerParameterChanged.emit(self.name, 'Einf')

    def update_params_from_table(self, top_left=None, bottom_right=None, roles=None): 
        # dataChanged signal을 편집하기 귀찮아서 그냥 인수를 받게 했지만 self 이외 인수는 필요없다.
        if self.updating_from_model:
            Table_vars = self.ParamsTableModel.getData()
            OscTypes_Params = []
            for row in Table_vars :
                # 각 row의 0번째는 OscType이고, 나머지는 Parameter들인데, column수가 각 OscType의 변수보다 많을 수 있으므로 적당히 slice한다.
                OscType = row[0]
                num_params_Osc = self.DataManager.Calculator.getOscParameterNumber(OscType)
                Params = row[1:1+num_params_Osc]
                OscTypes_Params.append([OscType] + Params)
            self.OscTypes_Params = OscTypes_Params
            self.OscTypes, self.Params = self.split_osc_params(self.OscTypes_Params)

            isAdjustableParams = []
            isAdjustableParams_Table = self.ParamsTableModel.getisAdjustable()
            for i in range(len(isAdjustableParams_Table)) :
                # 테이블에서 가져온 isAdjustable을 각 OscType에 맞게 필요한 길이만큼만 자른다. (column수 > params수 여서 길이가 다를 수 있기 때문)
                num_params_Osc = self.DataManager.Calculator.getOscParameterNumber(self.OscTypes[i])
                if num_params_Osc < len(isAdjustableParams_Table[i]) : # Osc의 params수가 Table에서 가져온 isAdjustable 수 보다 작은경우
                    isAdjustableParams.append(isAdjustableParams_Table[i][:num_params_Osc])
                else : isAdjustableParams.append(isAdjustableParams_Table[i])
                
            self.isAdjustableParams = isAdjustableParams
            self.LayerParameterChanged.emit(self.name, 'OscTypes_Params')

    def update(self) : # 개발예정
        return
    
    def __deepcopy__(self, memo):
        # Layer객체를 deep copy하여 반환하는 메서드
        # Create a new instance
        new_copy = Layerclass(parent=None, DataManager=self.DataManager, name=self.name,
                              isVacuum=self.isVacuum, isCoherent=self.isCoherent)
        
        # Copy simple attributes
        new_copy.Thickness = self.Thickness
        new_copy.Einf = self.Einf
        new_copy.Params = copy.deepcopy(self.Params, memo)
        new_copy.OscTypes = copy.deepcopy(self.OscTypes, memo)
        new_copy.OscTypes_Params = copy.deepcopy(self.OscTypes_Params, memo)
        new_copy.isAdjustableThickenss = self.isAdjustableThickenss
        new_copy.isAdjustableEinf = self.isAdjustableEinf
        new_copy.isAdjustableParams = copy.deepcopy(self.isAdjustableParams, memo)
        new_copy.isVacuum = self.isVacuum
        new_copy.isCoherent = self.isCoherent
        new_copy.isFixedLayer = self.isFixedLayer
        if new_copy.isFixedLayer :
            new_copy.e1 = self.e1
            new_copy.e2 = self.e2
            new_copy.cached_interpolated_Dielectric_Funcs = self.cached_interpolated_Dielectric_Funcs

        return new_copy
    
    def __repr__(self):
        return (f"Layer(Einf={self.Einf}, Thickness={self.Thickness}, "
                f"Params={self.Params}, OscTypes={self.OscTypes})")
        
class LayerWidget(QWidget, Ui_LayerWidget):
    def __init__(self, parent=None, DataManager : 'DataManager' =None, name=None):
        super(LayerWidget, self).__init__()
        
        # Load the UI for Sample
        self.setupUi(self)
        self.DataManager = DataManager
        self.LayerModelDockWidget = modelDockWidget(parent=self, DataManager=self.DataManager)

        self.Layer = Layerclass(parent=self, DataManager=self.DataManager, name=name,
                           ThicknessTableModel=self.LayerModelDockWidget.tableView_Thickness_model,
                           EinfTableModel=self.LayerModelDockWidget.tableView_Einf_model,
                           ParamsTableModel=self.LayerModelDockWidget.tableView_Params_model)

        # Layer 이름 설정
        if name : 
            self.label_LayerName.setText(name)
            self.LayerModelDockWidget.setWindowTitle(name)
        
        # Find the layout and button in the loaded UI
        self.pushButton_DeleteLayer = self.findChild(QPushButton, 'pushButton_DeleteLayer')
        self.pushButton_SetLayer = self.findChild(QPushButton, 'pushButton_SetLayer')

        # Connect the button click to the add_layer method
        self.pushButton_DeleteLayer.clicked.connect(self.delete_layer)
        self.pushButton_SetLayer.clicked.connect(self.set_layer)
        self.pushButton_isCoherent.clicked.connect(self.switch_isCoherent)
        self.pushButton_SaveLayer.clicked.connect(self.save_layer)
        self.pushButton_LoadLayer.clicked.connect(self.load_layer)

        #라벨 변경 시그널을 연결한다
        self.label_LayerName.editingFinished.connect(self.setLayerName)
        

    def delete_layer(self):
        # Remove the widget from its parent layout and delete it
        self.setParent(None)
        self.LayerModelDockWidget.setParent(None)
        self.LayerModelDockWidget.deleteLater()
        self.deleteLater()

    def set_layer(self): # 임시로 e1,e2 불러와서 고정시키는 함수로 쓴다.
        caption = "Load material (e1, e2) file"
        initial_dir = ""  # Empty uses current folder.
        initial_filter = FILE_FILTERS[-1]  # Select one from the list.

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
                data.dtype = 'e1e2'
                data.curveType = 'Data'
                data.Ndata = dataDF.shape[1]
                keys = dataDF.keys()
                data.x = dataDF[keys[0]]
                data.x = np.array(data.x).flatten()
                data.y = dataDF[keys[1:]] # y데이터가 2개 이상인 경우 수정 예정
                self.Layer.setFixedDielectricFunc(data)
        return
    
    def save_layer(self) : 
        caption = "Save Layer Parameters to file"
        initial_dir = ""  # Empty uses current folder.
        initial_filter = "JSON Files (*.json)"  # Select one from the list.

        dialog = QFileDialog()
        dialog.setWindowTitle(caption)
        dialog.setDirectory(initial_dir)
        dialog.setNameFilters(["JSON Files (*.json)"])
        dialog.selectNameFilter(initial_filter)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        #dialog.exec()
        fileName, _ = dialog.getSaveFileName(self)
        #fileName = dialog.selectedFiles()[0]
        self.DataManager.save_layer_to_file(self.Layer, fileName)

    def load_layer(self) :
        caption = "Load Layer Parameters to file"
        initial_dir = ""  # Empty uses current folder.
        initial_filter = "JSON Files (*.json)"  # Select one from the list.

        dialog = QFileDialog()
        dialog.setWindowTitle(caption)
        dialog.setDirectory(initial_dir)
        dialog.setNameFilters(["JSON Files (*.json)"])
        dialog.selectNameFilter(initial_filter)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.exec()

        fileName = dialog.selectedFiles()[0]
        self.DataManager.load_layer_from_file(self.Layer, fileName)
    
    def switch_isCoherent(self) :
        self.Layer.switchisCoherent()
        if self.pushButton_isCoherent.isChecked() & (self.Layer.isCoherent==False) : self.pushButton_isCoherent.setText("Coherence : Off")
        else : self.pushButton_isCoherent.setText("Coherence : On")
        self.DataManager.update_model_graph()
        
    
    def setLayerName(self, newName) :
        self.Layer.setName(newName)
        