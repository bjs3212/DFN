from .OpticalFunctions import drude, local_drude, lorentzian, to_refraction_index, to_sigma, Tauc_Lorentz
from PyQt6.QtCore import QObject
import numpy as np
from typing import List, TYPE_CHECKING
from scipy.interpolate import interp1d
import copy

if TYPE_CHECKING :
    from .Sample import Sampleclass
    from .Layer import Layerclass
    from .CustomClass import OpticalItem
from .Layer import Layerclass
from .smmo import make_config, make_layer, SMMO


class CalculatorClass(QObject) :
    def __init__(self, parent=None) :
        super().__init__(parent)
        self.DataManager = parent

    def getDielectricFunc(self, x, Layer : 'Layerclass') :
        if Layer.isVacuum : return np.full_like(x, 1., dtype=np.complex128)
        elif Layer.isFixedLayer : 
            if Layer.cached_interpolated_Dielectric_Funcs : # 캐싱된 유전함수가 있으면
                for e in Layer.cached_interpolated_Dielectric_Funcs : # 그 유전함수들중 같은 x축을 갖는게 있는지 검사
                    x_cached = e.x
                    if np.array_equal(x_cached[:10], x[:10]) :  # 시간절약을 위해 첫 10개 element만 같은지 검사
                        return e.y
                    # Layer에 이미 캐싱된 유전함수가 있고 그 유전함수의 x축이 제공된 x축과 같으면 이미 계산된걸 반환하고, 
                    # 아니면 새로 interpolation 하여 계산하고 새로 캐싱합니다.
            e1 = self.interpolate_or_extrapolate(Layer.e1.x, Layer.e1.y, new_x=x)
            e2 = self.interpolate_or_extrapolate(Layer.e2.x, Layer.e2.y, new_x=x, fill_value=0.)
            e = e1 + 1j*e2
            return e
        # 진공도, e1e2 고정된 Layer도 아니면 parameter들로 계산
        Params = Layer.Params
        OscTypes = Layer.OscTypes
        Einf = np.full_like(x, Layer.Einf, dtype=np.complex128)
        e = Einf
        for i in range(len(Params)) :
            if OscTypes[i] == 'Drude' :
                w0, wp, gamma = Params[i]
                e += drude(x, wp, gamma)
            elif OscTypes[i] == 'Lorentzian' :
                w0, wp, gamma = Params[i]
                e += lorentzian(x, w0, wp, gamma)
            elif OscTypes[i] == 'LocalizedDrude' :
                C, wp, gamma = Params[i]
                e += local_drude(x, C, wp, gamma)
            elif OscTypes[i] == 'Tauc-Lorentz' :
                w0, wg, A, C = Params[i]
                e += Tauc_Lorentz(x, w0, wg, A, C)
        return e
    
    def getDielectricFunc_withParams(self, x, Einf, Params, OscTypes) :
        Einf = np.full_like(x, Einf, dtype=np.complex128)
        e = Einf
        for i in range(len(Params)) :
            w0, wp, gamma = Params[i]
            if OscTypes[i] == 'Drude' :
                e += drude(x, wp, gamma)
            elif OscTypes[i] == 'Lorentzian' :
                e += lorentzian(x, w0, wp, gamma)
            elif OscTypes[i] == 'LocalizedDrude' :
                e += local_drude(x, w0, wp, gamma)
        return e
        
    def getLayerSimulation(self, x, Layer : 'Layerclass', dtype) :
        Dielectric_Func = self.getDielectricFunc(x, Layer)

        if dtype == 'S1' :
            Optical_Conductivity = to_sigma(x, Dielectric_Func)
            return Optical_Conductivity.real
        elif dtype == 'S2' :
            Optical_Conductivity = to_sigma(x, Dielectric_Func)
            return Optical_Conductivity.imag
        elif dtype == 'E1' :
            return Dielectric_Func.real
        elif dtype == 'E2' :
            return Dielectric_Func.imag
        elif dtype == 'n' :
            Refractive_Index = to_refraction_index(x, Dielectric_Func)
            return Refractive_Index.real
        elif dtype == 'k' :
            Refractive_Index = to_refraction_index(x, Dielectric_Func)
            return Refractive_Index.imag
        
        else : raise ValueError("Received wrong dtype for Layer : {}".format(dtype))
        

    def getLayerSimulation_withParams(self, Params, OscTypes, x_data, y_data, dtype) :
        # Params의 0번째는 Thickness, 1번째는 Einf, 나머지는 Oscillator의 parameter들로 한다.
        # 각 Oscillator가 3개가 아닌 다른 갯수의 파라미터를 갖는경우는 나중에 추가하자.

        
        Thickness = Params[0]
        Einf = Params[1]
        osc_params = []

        i=0
        for OscType in OscTypes :
            params = Params[2:]
            OscParameterNum = self.getOscParameterNumber(OscType)
            osc_params.append(params[i:i+OscParameterNum])
            i = i+OscParameterNum

        Dielectric_Func = self.getDielectricFunc_withParams(x_data, Einf=Einf, Params=osc_params, OscTypes=OscTypes)

        if dtype == 'S1' :
            Optical_Conductivity = to_sigma(x_data, Dielectric_Func)
            return Optical_Conductivity.real
        elif dtype == 'S2' :
            Optical_Conductivity = to_sigma(x_data, Dielectric_Func)
            return Optical_Conductivity.imag
        elif dtype == 'E1' :
            return Dielectric_Func.real
        elif dtype == 'E2' :
            return Dielectric_Func.imag
        elif dtype == 'n' :
            Refractive_Index = to_refraction_index(x_data, Dielectric_Func)
            return Refractive_Index.real
        elif dtype == 'k' :
            Refractive_Index = to_refraction_index(x_data, Dielectric_Func)
            return Refractive_Index.imag
        
        else : raise ValueError("Received wrong dtype for Layer : {}".format(dtype))

    def getLayerMSE_withAdjustableParams(self, adjustable_Params, original_params, isAdjustable, OscTypes, datas : List['OpticalItem'], weight) :
        params = []
        MSE = 0.

        j = 0
        for i in range(len(isAdjustable)) :
            if isAdjustable[i] :
                params.append(adjustable_Params[j])
                j += 1
            else :
                params.append(original_params[i])
        
        for data in datas :
            x = data.x
            y = data.y
            simulated = self.getLayerSimulation_withParams(Params=params, OscTypes=OscTypes, x_data=x, y_data=y, dtype=data.dtype)
            MSE += np.sum((simulated-y)**2)*weight

        return MSE
    
    def getLayerMSE(self, datas: List['OpticalItem'], Layer:'Layerclass', weight) :
        MSE = 0.
        for data in datas :
            simulated = self.getLayerSimulation(data.x, Layer, data.dtype)
            MSE += np.sum((simulated-data.y)**2)*weight
        return MSE


    def getSampleSimulation(self, x, Sample : 'Sampleclass', dtype,
                            polarization = 's', incidence = 0.) : # 임시로 입사각 70도
        SampleLayers = Sample.getLayers()[:]
        VacuumLayer = Layerclass(name = 'Vacuum', isVacuum=True, isCoherent=True)
        VacuumLayer.setThickness(0.)
        SampleLayers.insert(0, VacuumLayer)
        SampleLayers.append(VacuumLayer) # Layer의 처음과 끝에 진공 Layer를 넣어준다

        Layers = []
        for Layer in SampleLayers :
            N_Layer = to_refraction_index(x, self.getDielectricFunc(x, Layer))#-np.sin(incidence*np.pi/180)**2) # N = np.sqrt(e-sin(theta)^2)
            smmo_converted_layer = make_layer(n = N_Layer.real, k = N_Layer.imag,
                                thickness=Layer.Thickness, coherence=Layer.isCoherent)
            Layers.append(smmo_converted_layer)

        config_s = make_config(wavenumber=x, incidence=70., polarization='s') # 임시로 입사각 70도로 고정해둔다. 추후 입사각 넣도록 구현할 예정
        config_p = make_config(wavenumber=x, incidence=70., polarization='p')
        output_s = SMMO(Layers, config_s)
        output_p = SMMO(Layers, config_p)


        config = make_config(wavenumber=x, incidence=incidence, polarization=polarization)
        output = SMMO(Layers, config)

        if dtype == 'T' : return output()['T']
        elif dtype=='TdT' :
            # ------- 임시로 T(0V)로 나눠주기 위함 -------
            T0V = self.DataManager.T0V
            T0V_y = self.interpolate_or_extrapolate(T0V.x, T0V.y, new_x=x)
            return output()['T']/T0V_y
        elif dtype == 'R' : return output()['R']
        elif dtype == 'Psi' :
            S_s = output_s.get_smatrix_components(Layers)
            S_p = output_p.get_smatrix_components(Layers)
            r_s = S_s[2]
            r_p = S_p[2]
            rho = r_p/r_s
            return 180/np.pi*np.arctan(abs(rho))
        elif dtype == 'Delta' :
            S_s = output_s.get_smatrix_components(Layers)
            S_p = output_p.get_smatrix_components(Layers)
            r_s = S_s[2]
            r_p = S_p[2]
            rho = r_p/r_s
            return np.angle(rho, deg=True)

        
        else : raise ValueError("Received wrong dtype for Sample : {}".format(dtype))

    def getSampleSimulation_withParams(self, Params, Sample : 'Sampleclass', data : 'OpticalItem') :
        # 이 함수는 Sample 내의 Layer들의 모든 파라미터의 모음을 받아서 Simulation 결과를 반환한다.
        # 먼저, Params 내의 파라미터들이 어떤 Layer의 파라미터인지 나눠준다.
        ParamGroups = [] # 각 레이어의 파라미터들을 리스트 형태로 저장할 변수
        OscTypesGroups = [] # 각 레이어의 OscTypes를 저장하기 위한 변수
        isCoherent = [] # 각 레이어가 Coherent한지 저장하기 위한 변수

        i = 0 # Params를 슬라이싱 하기 위한 변수
        for Layer in Sample.Layers :
            # 각 Layer의 파라미터 수 (두께, Einf, Params) 를 세준다.
            num_params = 2 + sum(len(row_Params) for row_Params in Layer.getParams())
            # 2는 두께, Einf를 포함시킨것.
            OscTypesGroups.append(Layer.getOscTypes())
            isCoherent.append(Layer.isCoherent)
            ParamGroups.append(Params[i:i+num_params])
            i += num_params
        
        Layers = []
        for i in range(len(ParamGroups)) : # 각 ParamGroup으로 Layer를 만들어 Layers리스트를 만들자.
            if Sample.Layers[i].isFixedLayer : # e1, e2 고정된 Layer의 경우 parameter에 관계없이 n, k를 따로 불러온다
                n = self.getLayerSimulation(data.x, Sample.Layers[i], dtype='n')
                k = self.getLayerSimulation(data.x, Sample.Layers[i], dtype='k')
            else :
                n = self.getLayerSimulation_withParams(ParamGroups[i], OscTypesGroups[i], data.x, data.y, dtype='n')
                k = self.getLayerSimulation_withParams(ParamGroups[i], OscTypesGroups[i], data.x, data.y, dtype='k')
            Layer_made = make_layer(n, k, thickness=ParamGroups[i][0], coherence=isCoherent[i])
            Layers.append(Layer_made)
        VacuumLayer = make_layer(n=np.full_like(data.x, 1.), k=np.zeros_like(data.x), thickness=0., coherence=True)
        Layers.insert(0, VacuumLayer)
        Layers.append(VacuumLayer) # 진공 레이어 앞뒤로 삽입
        config = make_config(wavenumber=data.x, incidence=0., polarization='s')
        # 일단은 0도, s편광 기준으로 계산하도록 하자. 입사각과 편광 넣는건 나중에
        output = SMMO(Layers, config)()
        
        if data.dtype == 'T' : return output['T']
        elif data.dtype == 'R' : return output['R']
        else : raise ValueError("Received wrong dtype for Sample : {}".format(data.dtype))

    def getSampleMSE_withAdjustableParams(self, adjustable_Params, Sample : 'Sampleclass', datas : List['OpticalItem'], weight) :
        params = []
        MSE = 0.

        isAdjustables = Sample.getAll_isAdjustable_flattened()
        original_params = Sample.getAllParams_flattened()
        j = 0
        for i in range(len(isAdjustables)) :
            if isAdjustables[i] :
                params.append(adjustable_Params[j])
                j += 1
            else :
                params.append(original_params[i])
        
        for data in datas :
            y = data.y
            simulated = self.getSampleSimulation_withParams(params, Sample, data)
            MSE += np.sum((simulated-y)**2)*weight

        return MSE
    

    def getSampleMSE(self, datas: List['OpticalItem'], Sample:'Sampleclass', weight) :
        MSE = 0.
        for data in datas :
            simulated = self.getSampleSimulation(data.x, Sample, data.dtype)
            MSE += np.sum((simulated-data.y)**2)*weight
        return MSE
    
    def getfitGroupsMSE_with_adjustable_params(self, adjustable_Params, fitGroups, Models_to_Adjust, weight) :
        # 받은 adjustable_params를 가지고 MSE를 계산해 반환하는 함수.
        # 각 Model의 복사본을 만들어서 parameter를 바꿔넣은 뒤 계산하는 전략.
        # Sample내에 이미 포함된 Layer가 fit Groups 에 있을 경우가 고민이긴 한데..
        # Models_to_Adjust에서 한번 걸러주니 이용해보자

        from .Sample import Sampleclass
        from .Layer import Layerclass

        copied_Models = []
        duplicated_Layers = []
        # Model을 복사한 것에 받은 adjustable_Params로 기존 params 갈아끼우기
        # 그 뒤 copied_Models에 추가
        i = 0
        for Model_ in Models_to_Adjust :
            Model = copy.deepcopy(Model_) # 기존 Model 복사하여 새로운 모델로
            if isinstance(Model, Sampleclass) or isinstance(Model, Layerclass) :
                num_Adjustable_Params_Model = len(Model.getAllAdjustableParams_flattened())
                if (i + num_Adjustable_Params_Model) < len(adjustable_Params) :
                    new_Adjustable_Params_Model = adjustable_Params[i:i+num_Adjustable_Params_Model]
                else : # index가 최대범위를 넘어서는 걸 방지하기 위한 if문. i+num_Adjustable_Params_Model이 최대 index (len-1) 일때만 위. 아니면 else
                    new_Adjustable_Params_Model = adjustable_Params[i:]
                Model.replace_Adjustable_Parameters_NOT_Change_UI(new_Adjustable_Params_Model)
                copied_Models.append(Model)
                if isinstance(Model, Sampleclass) : duplicated_Layers.extend(Model.getLayers())
                i += num_Adjustable_Params_Model

        copied_fitGroups = [] # 복사된 Model들로 구성한 fitGroups를 새로 만들것
        for fitGroup in fitGroups :
            model_, datas_ = fitGroup
            # fitGroups 안에 model_이 들어있지만 copied_Models 안에 없다면 Models_to_Adjust안에 없는 중복되는 Layer이므로
            # duplicated_Layers에서 찾아서 복사.
            
            if model_.name not in [copied_model.name for copied_model in copied_Models] :
                for Layer in duplicated_Layers :
                    if model_.name == Layer.name : model_ = Layer

            # copied_Models 안에 있다면 그 안에서 할당.
            for model in copied_Models :
                if model_.name == model.name : model_ = model
            
            copied_fitGroups.append( (model_, datas_) )
        
        MSE = self.getTotalMSE_fitGroups(copied_fitGroups, weight)
        return MSE
                

    def Adjust_Params_of_fitGroups(self, adjustable_Params, Models_to_Adjust) :
        
        MSE = 0.
        from .Sample import Sampleclass
        from .Layer import Layerclass

        # 받은 adjustable_Params로 기존 params 갈아끼우기
        i = 0
        for Model in Models_to_Adjust :
            if isinstance(Model, Sampleclass) or isinstance(Model, Layerclass) :
                num_Adjustable_Params_Model = len(Model.getAllAdjustableParams_flattened())
                if (i + num_Adjustable_Params_Model) < len(adjustable_Params) :
                    new_Adjustable_Params_Model = adjustable_Params[i:i+num_Adjustable_Params_Model]
                else : # index가 최대범위를 넘어서는 걸 방지하기 위한 if문. i+num_Adjustable_Params_Model이 최대 index (len-1) 일때만 위. 아니면 else
                    new_Adjustable_Params_Model = adjustable_Params[i:]
                Model.replace_Adjustable_Parameters(new_Adjustable_Params_Model)
                i += num_Adjustable_Params_Model
    
    def getTotalMSE_fitGroups(self, fitGroups, weight) :
        MSE = 0.
        from .Sample import Sampleclass
        from .Layer import Layerclass

        #각 fitGroup에 대해 MSE계산해서 더해준다
        for fitGroup in fitGroups :
            model, datas = fitGroup
            if isinstance(model, Sampleclass) :
                MSE += self.getSampleMSE(datas, model, weight)
            elif isinstance(model, Layerclass) :
                MSE += self.getLayerMSE(datas, model, weight)
        return MSE
        
        
    def getOscParameterNumber(self, OscType) : # OscType별 parameter개수를 반환하는 함수
        if OscType == 'Tauc-Lorentz' : return 4
        else : return 3

    def interpolate_or_extrapolate(self, x : np.ndarray, y, new_x, fill_value = None): 
        # e1, e2를 Layer에 불러올 시 그래프가 요청하는 x범위가 e1,e2의 데이터와 안맞으므로 해당 x범위에 맞게 interpolate해주는 함수
        # Linear방식으로 보간하고, x축 범위가 다를 경우 가장 가까운 y값을 할당한다.
        # fill_value가 없을 경우는 가장 가까운 y값을 할당, 있을 경우는 해당 값으로 할당.
        f = interp1d(x, y, kind='linear', fill_value='extrapolate')
        new_y = np.zeros_like(new_x)
        for i, nx in enumerate(new_x):
            if nx < x.min():
                if fill_value != None : new_y[i] = fill_value
                else : new_y[i] = y[0]
            elif nx > x.max():
                if fill_value != None : new_y[i] = fill_value
                else : new_y[i] = y[-1]
            else:
                new_y[i] = f(nx)
        return new_y