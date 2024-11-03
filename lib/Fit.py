from PyQt6.QtWidgets import QDockWidget, QDialog, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from .ui.fit_ui import Ui_FitDockWidget
from .ui.AddFit_dialog_ui import Ui_AddFit_Dialog
from itertools import groupby
from typing import List, TYPE_CHECKING
from scipy.optimize import minimize

if TYPE_CHECKING :
    from .DataManager import DataManager
    from .Layer import Layerclass
    from .Sample import Sampleclass
from .CustomClass import OpticalItem, CustomListWidgetItem, DataListWidgetItem, LayerListWidgetItem, SampleListWidgetItem, FitListWidgetItem


'''class FitWorker(QThread):
    update_signal = pyqtSignal(str)  # UI 업데이트를 위한 신호
    finished_signal = pyqtSignal(bool)  # 작업 완료 신호

    def __init__(self, fitDockWidget):
        super().__init__()
        self.fitDockWidget = fitDockWidget

    def run(self):
        result_message, success = self.fitDockWidget.doFit()
        self.finished_signal.emit(success)
        self.update_signal.emit(result_message)


class FitDockWidget(QDockWidget, Ui_FitDockWidget) :
    
    def __init__(self, parent=None, DataManager : 'DataManager' =None) :
        super().__init__(parent)
        self.DataManager = DataManager
        self.setupUi(self)
        self.AddFit_Dialog = AddFit_Dialog(self, self.DataManager)
        self.thread_fit = None

        self.pushButton_AddFit.clicked.connect(self.open_AddFit_Dialog)
        self.pushButton_DeleteFit.clicked.connect(self.delete_SelectedFitItem)
        self.pushButton_Fit.clicked.connect(self.start_fit)

    def open_AddFit_Dialog(self) :
        # GraphSetDialog를 열면서, 현재 로드된 데이터와 생성된 Layer, Sample들이 뭐가 있는지를 GraphSetDialog에 알려준다.
        Datas = self.DataManager.getDatas()
        Layers = self.DataManager.getLayers()
        Samples = self.DataManager.getSamples()

        Sample_OpticalItems =[OpticalItem(name = Sample.name, dtype='any', curveType='Sample') for Sample in Samples]
        Layers_OpticalItems =[OpticalItem(name = Layer.name, dtype='any', curveType='Layer') for Layer in Layers]

        DataListWidgetItems : List[CustomListWidgetItem] = []
        ModelListWidgetItems : List[CustomListWidgetItem] = []
        for Data in Datas :
            DataListWidgetItems.append(DataListWidgetItem(Data))
        for Layer in Layers_OpticalItems :
            ModelListWidgetItems.append(LayerListWidgetItem(Layer))
        for Sample in Sample_OpticalItems :
            ModelListWidgetItems.append(SampleListWidgetItem(Sample))

        self.AddFit_Dialog.insert_Datas_and_Models(DataListWidgetItems, ModelListWidgetItems)
        self.AddFit_Dialog.show()

    def setFitItems(self,FitItems) :
        for item in FitItems :
            self.listWidget_FitItems.addItem(item)

    def delete_SelectedFitItem(self) :
        for item in self.listWidget_FitItems.selectedItems() :
            self.listWidget_FitItems.takeItem(self.listWidget_FitItems.row(item))

    def start_fit(self):
        self.thread_fit = FitWorker(self)
        self.thread_fit.update_signal.connect(self.update_log)
        self.thread_fit.finished_signal.connect(self.fit_finished)
        self.thread_fit.start()

    def update_log(self, message):
        self.textEdit_FitLog.append(message)

    def fit_finished(self, success):
        if success:
            self.textEdit_FitLog.append('Fit Successed')
        else:
            self.textEdit_FitLog.append('Fit Failed.')

    def doFit(self) :
        from .Sample import Sampleclass
        from .Layer import Layerclass

        if self.listWidget_FitItems.count() == 0 : return # fititem이 없을 경우 아무것도 하지 않는다.
        fitSets = []
        FitItems = [self.listWidget_FitItems.item(i) for i in range(self.listWidget_FitItems.count())]
        for item in FitItems :
            fitData = None
            fitModel = None
            for data in self.DataManager.getDatas() :
                if item.fitDataName == data.name :
                    fitData = data
            for model in self.DataManager.getLayers() + self.DataManager.getSamples() :
                if item.fitModelName == model.name :
                    fitModel = model
                    fitModel.cache_Dielectric_Func(fitData.x) 
                    # Fit과정을 빨리 하기 위해 미리 Dielectric func를 캐싱한다.
            fitSets.append( (fitModel, fitData) )

        fitGroups = [] # Model을 기준으로 Model을 fit할 데이터들과 함께 묶는다. 한꺼번에 MSE를 계산하기 위함.
        fitSets.sort(key = lambda x : x[0].name)
        for model_name, group in groupby(fitSets, key=lambda x:x[0].name) :
            model_instance = None
            data_list = []
            for model, data in group :
                model_instance = model
                data_list.append(data)
            if isinstance(model_instance, Sampleclass) : fitGroups.insert(0,(model_instance, data_list))
            elif isinstance(model_instance, Layerclass) : fitGroups.append((model_instance, data_list))
            # Sampleclass의 경우 fitGroups의 맨 앞쪽에 배치
        # fitGroups 내에 Sample과 Layer가 있을 것.
        # Sample 내에 Layer가 포함되어 있으므로 Sample 내의 parameter조정은 Layer의 parameter 조정을 포함한다.
        # 따라서 Sample내에 Layer가 포함되어 있으면 Layer의 파라미터를 중복으로 받지 말것.
        # 이를 위해
        # 1. fitGroups에 Sampleclass가 있는지 검사해서 있으면 가져오기.
        # 2. Sampleclass가 있는 경우 fitGroups에 Sample내의 Layer가 있으면 제외
        # 3. Sampleclass가 없으면 Layer도 가져오기
        # 4. 가져온 것들에서 AdjustableParams를 다 가져와서 합친다
        # 5. 가져온 model들을 같이 MSE구하는 함수에 넘겨서 해당 model들에 adjustable params를 집어넣고 MSE구하게 하자
        # 이를 위해 fitGroups에 Sampleclass가 앞의 인덱스로 오도록 할 필요가 있음

        Models_to_Adjust = [] # 같은 adjustable한 parameter를 공유하지 않는 모델들의 모음
        Duplicated_Layers = [] # 중복되는 레이어들. Sample을 fit하는 경우 Sample내의 Layer들을 담아 중복되는지 검사할 리스트
        adjustable_params = [] # 조정 가능한 parameter들을 담을 리스트
        for fitGroup in fitGroups :
            model, datas = fitGroup
            if isinstance(model, Sampleclass) and (model not in Models_to_Adjust) : 
                Models_to_Adjust.append(model)
                Duplicated_Layers.extend(model.getLayers())
                adjustable_params.extend(model.getAllAdjustableParams_flattened())
            elif isinstance(model, Layerclass) and (model not in Duplicated_Layers) :
                Models_to_Adjust.append(model)
                adjustable_params.extend(model.getAllAdjustableParams_flattened())

        callback_for_Fit = self.create_callback_for_Fit(fitGroups, Models_to_Adjust, weight=1.)
        result=minimize(self.DataManager.Calculator.getfitGroupsMSE_with_adjustable_params, adjustable_params, args=(fitGroups, Models_to_Adjust, 1.), callback=callback_for_Fit)

        for fitSet in fitSets :
            model, data = fitSet
            model.remove_cached_Dielectric_Funcs()
            # 피팅이 끝났으므로 캐싱해둔 Dielectric func를 모두 제거한다.
        print('Fit Over')
        return result.message, result.success


    def create_callback_for_Fit(self, fitGroups, Models_to_Adjust, weight) :
        iteration_count = [0]

        def callback_update_iteration() : # 표시되는 iteration 수를 업데이트
            iteration_count[0] += 1
            self.lineEdit_Iteration.clear()
            self.lineEdit_Iteration.setText(str(iteration_count[0]))
        
        def callback_replace_adjustable_params(adjusted_Params) :
            self.DataManager.Calculator.Adjust_Params_of_fitGroups(adjusted_Params, Models_to_Adjust)

        def callback_update_MSE() : # 표시되는 MSE를 업데이트
            MSE = self.DataManager.Calculator.getTotalMSE_fitGroups(fitGroups, weight)
            self.lineEdit_MSE.clear()
            self.lineEdit_MSE.setText(str(MSE))

        def callback(adjusted_Params) :
            callback_update_iteration()
            callback_replace_adjustable_params(adjusted_Params)
            callback_update_MSE()
        
        return callback'''
        


class FitWorker(QThread):
    update_signal = pyqtSignal(list, list, list)  # UI 업데이트를 위한 신호
    finished_signal = pyqtSignal(object)  # 작업 완료 신호

    def __init__(self, fitDockWidget, DataManager : 'DataManager'):
        super().__init__()
        self.fitDockWidget = fitDockWidget
        self.DataManager = DataManager
        self.adjustable_params = None
        self.fitGroups = None
        self.Models_to_Adjust = None

    def fit(self, adjustable_params, fitGroups, Models_to_Adjust):
        self.adjustable_params = adjustable_params
        self.fitGroups = fitGroups
        self.Models_to_Adjust = Models_to_Adjust
        self.start()  # QThread의 start() 메서드를 호출하여 스레드를 시작

    def run(self):
        callback_for_Fit = self.create_callback_for_Fit(self.fitGroups, self.Models_to_Adjust, weight=1.)
        options = {
            'maxiter': 100,    # 최대 반복 횟수
            'disp': True,       # 최적화 과정 출력 여부
        }
        result = minimize(
            self.DataManager.Calculator.getfitGroupsMSE_with_adjustable_params, 
            self.adjustable_params, 
            args=(self.fitGroups, self.Models_to_Adjust, 1.), 
            callback=callback_for_Fit,
            options=options
        )
        self.finished_signal.emit(result)

    def create_callback_for_Fit(self, fitGroups, Models_to_Adjust, weight):
        def callback_update_adjustable_params(adjustable_params):
            self.update_signal.emit(adjustable_params, Models_to_Adjust, fitGroups)

        def callback(adjusted_Params):
            callback_update_adjustable_params(adjusted_Params)

        return callback


class FitDockWidget(QDockWidget, Ui_FitDockWidget):

    def __init__(self, parent=None, DataManager : 'DataManager' = None):
        super().__init__(parent)
        self.DataManager = DataManager
        self.setupUi(self)
        self.AddFit_Dialog = AddFit_Dialog(self, self.DataManager)
        self.thread_fit = FitWorker(self, DataManager=self.DataManager)
        self.thread_fit.update_signal.connect(self.update_params_and_iteration_MSE)
        self.thread_fit.finished_signal.connect(self.fit_finished)

        self.pushButton_AddFit.clicked.connect(self.open_AddFit_Dialog)
        self.pushButton_DeleteFit.clicked.connect(self.delete_SelectedFitItem)
        self.pushButton_Fit.clicked.connect(self.start_Fit)

        self.iteration_count = 0  # fit 반복 횟수
        self.fitSets = []  # fit할 묶음 (Model, Data) 들의 List

    def open_AddFit_Dialog(self) :
        # GraphSetDialog를 열면서, 현재 로드된 데이터와 생성된 Layer, Sample들이 뭐가 있는지를 GraphSetDialog에 알려준다.
        Datas = self.DataManager.getDatas()
        Layers = self.DataManager.getLayers()
        Samples = self.DataManager.getSamples()

        Sample_OpticalItems =[OpticalItem(name = Sample.name, dtype='any', curveType='Sample') for Sample in Samples]
        Layers_OpticalItems =[OpticalItem(name = Layer.name, dtype='any', curveType='Layer') for Layer in Layers]

        DataListWidgetItems : List[CustomListWidgetItem] = []
        ModelListWidgetItems : List[CustomListWidgetItem] = []
        for Data in Datas :
            DataListWidgetItems.append(DataListWidgetItem(Data))
        for Layer in Layers_OpticalItems :
            ModelListWidgetItems.append(LayerListWidgetItem(Layer))
        for Sample in Sample_OpticalItems :
            ModelListWidgetItems.append(SampleListWidgetItem(Sample))

        self.AddFit_Dialog.insert_Datas_and_Models(DataListWidgetItems, ModelListWidgetItems)
        self.AddFit_Dialog.show()

    def setFitItems(self,FitItems) :
        for item in FitItems :
            self.listWidget_FitItems.addItem(item)

    def delete_SelectedFitItem(self) :
        for item in self.listWidget_FitItems.selectedItems() :
            self.listWidget_FitItems.takeItem(self.listWidget_FitItems.row(item))

    def update_log(self, message):
        self.textEdit_FitLog.append(message)

    def fit_finished(self, result): # fit이 종료되면 실행될 메서드
        for fitSet in self.fitSets :
            model, data = fitSet
            model.remove_cached_Dielectric_Funcs()
            # 피팅이 끝났으므로 캐싱해둔 Dielectric func를 모두 제거한다.

        self.update_log(result.message)
        if result.success:
            self.update_log('Fit Successed')
        else:
            self.update_log('Fit Failed.')

        # iteration count와 fitSets 초기화
        self.iteration_count = 0 
        self.fitSets = []

    def start_Fit(self):
        from .Sample import Sampleclass
        from .Layer import Layerclass

        if self.listWidget_FitItems.count() == 0:
            return  # fititem이 없을 경우 아무것도 하지 않는다.
        
        fitSets = []
        FitItems = [self.listWidget_FitItems.item(i) for i in range(self.listWidget_FitItems.count())]
        for item in FitItems:
            fitData = None
            fitModel = None
            for data in self.DataManager.getDatas():
                if item.fitDataName == data.name:
                    fitData = data
            for model in self.DataManager.getLayers() + self.DataManager.getSamples():
                if item.fitModelName == model.name:
                    fitModel = model
                    fitModel.cache_Dielectric_Func(fitData.x) 
            fitSets.append((fitModel, fitData))

        self.fitSets = fitSets

        fitGroups = []
        fitSets.sort(key=lambda x: x[0].name)
        for model_name, group in groupby(fitSets, key=lambda x: x[0].name):
            model_instance = None
            data_list = []
            for model, data in group:
                model_instance = model
                data_list.append(data)
            if isinstance(model_instance, Sampleclass):
                fitGroups.insert(0, (model_instance, data_list))
            elif isinstance(model_instance, Layerclass):
                fitGroups.append((model_instance, data_list))

        Models_to_Adjust = []
        Duplicated_Layers = []
        adjustable_params = []
        for fitGroup in fitGroups:
            model, datas = fitGroup
            if isinstance(model, Sampleclass) and (model not in Models_to_Adjust):
                Models_to_Adjust.append(model)
                Duplicated_Layers.extend(model.getLayers())
                adjustable_params.extend(model.getAllAdjustableParams_flattened())
            elif isinstance(model, Layerclass) and (model not in Duplicated_Layers):
                Models_to_Adjust.append(model)
                adjustable_params.extend(model.getAllAdjustableParams_flattened())

        self.thread_fit.fit(adjustable_params, fitGroups, Models_to_Adjust)

    def update_params_and_iteration_MSE(self, adjustable_params, Models_to_Adjust, fitGroups):
        # fit의 iteration이 돌 때 마다 실행될 메서드
        # 새로운 adjustable한 params를 받아서 각 Layer들에 전달하여 갈아끼운다
        # 그리고 iteration 횟수 및 MSE 계산하여 UI에 표시
        self.DataManager.Calculator.Adjust_Params_of_fitGroups(adjustable_params, Models_to_Adjust)

        MSE = self.DataManager.Calculator.getTotalMSE_fitGroups(fitGroups, weight=1.)
        self.lineEdit_MSE.clear()
        self.lineEdit_MSE.setText(str(MSE))

        self.iteration_count += 1
        self.lineEdit_Iteration.clear()
        self.lineEdit_Iteration.setText(str(self.iteration_count))


class AddFit_Dialog(QDialog, Ui_AddFit_Dialog) :
    def __init__(self, parent=None, DataManager : 'DataManager' = None) :
        super().__init__(parent)
        self.DataManager = DataManager
        self.setupUi(self)

    def insert_Datas_and_Models(self, DataListWidgetItems, ModelListWidgetItems) :
        self.listWidget_Datas.clear()
        self.listWidget_Models.clear()
        for item in DataListWidgetItems :
            self.listWidget_Datas.addItem(item)
        for item in ModelListWidgetItems :
            self.listWidget_Models.addItem(item)

    def accept(self) :
        FitItems = []
        if not self.listWidget_Datas.selectedItems() :  #선택된 데이터 아이템이 없을 때 아무것도 안함
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle('Warning')
            msg.setText('You must select at least one data item.')
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            return
        
        for selectedData in self.listWidget_Datas.selectedItems() :
            for selectedModel in self.listWidget_Models.selectedItems() :
                dataName = selectedData.name
                modelName = selectedModel.name
                name = selectedData.name + ' - ' + selectedModel.name
                FitItem = FitListWidgetItem(name, selectedData.dtype, fitDataName=dataName, fitModelName=modelName)
                FitItems.append(FitItem)
        FitDockWidget = self.parent()
        FitDockWidget.setFitItems(FitItems)
        super().accept()

    