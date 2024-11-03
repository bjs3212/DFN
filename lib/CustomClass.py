from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QLineEdit, QWidget
from PyQt6.QtCore import pyqtSignal

class OpticalItem() : # class for optical measurement data file

    def __init__(self, name=None, dtype=None, curveType=None, x=None, y=None, xtype=None) :
        self.name = name
        self.dtype = dtype
        self.curveType = curveType
        self.x = x
        self.y = y
        self.xtype = xtype

    def __setattr__(self, name, value):
        self.__dict__[name] = value

class CustomListWidgetItem(QtWidgets.QListWidgetItem) : # ListWidgetItem에 몇가지 항목을 추가하여 custom
    name : str
    dtype : str
    curveType : str
    fitDataName : str
    fitModelName : str
    isData : bool
    isSample : bool
    isLayer : bool
    isCHISQ : bool
    isMulti : bool
    isFitItem : bool

    def setNameofItem(self) :
        if self.isFitItem :
            name = self.name
            self.setText(name)
        
        else :
            if self.isData : name = 'Data'
            elif self.isSample : name = 'Sample'
            elif self.isLayer : name = 'Layer'
            elif self.isCHISQ : name = 'CHISQ'
            elif self.isMulti : name = 'Multi'
            else : raise ValueError("This item has no type!")
            self.curveType = name
            if self.dtype == 'any' : name = name + ' : ' + self.name # dtype 이 필요없는 List itme 일때
            else : name = name + ' ['+self.dtype+'] ' + self.name
            self.setText(name)

class FitListWidgetItem(CustomListWidgetItem) :

    def __init__(self, name, dtype, fitDataName, fitModelName, parent = None) :
        super().__init__(parent)
        self.name = name
        self.dtype = dtype
        self.fitDataName = fitDataName
        self.fitModelName = fitModelName
        self.isData = False
        self.isSample = False
        self.isLayer = False
        self.isCHISQ = False
        self.isMulti = False
        self.isFitItem = True
        self.setNameofItem()

class DataListWidgetItem(CustomListWidgetItem) :

    def __init__(self, data : OpticalItem, parent = None) :
        super().__init__(parent)
        self.name = data.name
        self.dtype = data.dtype
        self.isData = True
        self.isSample = False
        self.isLayer = False
        self.isCHISQ = False
        self.isMulti = False
        self.isFitItem = False
        self.setNameofItem()

class LayerListWidgetItem(CustomListWidgetItem) :
    def __init__(self, data : OpticalItem, parent = None) :
        super().__init__(parent)
        self.name = data.name
        self.dtype = data.dtype
        self.isData = False
        self.isSample = False
        self.isLayer = True
        self.isCHISQ = False
        self.isMulti = False
        self.isFitItem = False
        self.setNameofItem()

class SampleListWidgetItem(CustomListWidgetItem):
    def __init__(self, data : OpticalItem, parent = None) :
        super().__init__(parent)
        self.name = data.name
        self.dtype = data.dtype
        self.isData = False
        self.isSample = True
        self.isLayer = False
        self.isCHISQ = False
        self.isMulti = False
        self.isFitItem = False
        self.setNameofItem()

class CHISQListWidgetItem(CustomListWidgetItem):
    def __init__(self, data : OpticalItem, model : OpticalItem, parent = None) :
        super().__init__(parent)
        self.name = data.name + ' - ' + model.name
        self.dtype = data.dtype
        self.isData = False
        self.isSample = False
        self.isLayer = False
        self.isCHISQ = True
        self.isMulti = False
        self.isFitItem = False
        self.setNameofItem()

class MultiListWidgetItem(CustomListWidgetItem):
    def __init__(self, data : OpticalItem, parent = None) :
        super().__init__(parent)
        self.name = data.name
        self.dtype = data.dtype
        self.isData = False
        self.isSample = False
        self.isLayer = False
        self.isCHISQ = False
        self.isMulti = True
        self.isFitItem = False
        self.setNameofItem()

class EditableLabel(QWidget):
    editingFinished = pyqtSignal(str) # label의 text를 담아 emit할 signal 정의

    def __init__(self, text='LayerName', parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.label = QLabel(text, self)
        self.line_edit = QLineEdit(self)
        self.line_edit.setVisible(False)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.line_edit)
        
        self.label.mouseDoubleClickEvent = self.edit_label
        self.line_edit.editingFinished.connect(self.finish_edit)
        
        self.setLayout(self.layout)
    
    def edit_label(self, event):
        self.line_edit.setText(self.label.text())
        self.label.setVisible(False)
        self.line_edit.setVisible(True)
        self.line_edit.setFocus()
        self.line_edit.selectAll()
    
    def finish_edit(self):
        self.label.setText(self.line_edit.text())
        self.line_edit.setVisible(False)
        self.label.setVisible(True)
        self.label.text()
        self.editingFinished.emit(self.label.text()) # label의 text를 담아 emit

    def text(self) :
        return self.label.text()
    
    def setText(self, name) :
        self.label.setText(name)

