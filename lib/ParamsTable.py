from PyQt6.QtCore import Qt, QAbstractTableModel, pyqtSignal, QModelIndex
from PyQt6.QtWidgets import QApplication, QTableView, QStyledItemDelegate, QLineEdit
from PyQt6.QtGui import QColor, QBrush
import numpy as np
import re

color_Adjustable = QColor(0,0,255)
color_NotAdjustable = QColor(255, 0, 0)
color_Normal = QColor(0,0,0)

class ParamsTableModel(QAbstractTableModel):
    tableChanged = pyqtSignal() # 정렬이나 행 추가, 삭제 등이 일어났을 때 발생시킬 Signal 정의

    def __init__(self, parent, data, horizontal_header, vertical_header):
        super(ParamsTableModel, self).__init__(parent)
        self._data = data
        self._isAdjustable = [[True for data in data_row[1:]] for data_row in self._data] # data_row의 첫 요소는 OscType이므로 제외
        self._color_Adjustable = [[color_Adjustable if isAdjustable else color_NotAdjustable for isAdjustable in isAdjustable_row]
                        for isAdjustable_row in self._isAdjustable]
        self._color = [[color_Normal] + color_Adjustable_row for color_Adjustable_row in self._color_Adjustable]
        # isAdjustable이 True이면 color_Adjustable을 할당, 아니면 color_inAdjustable을 할당
        self._horizontal_header = horizontal_header
        self._vertical_header = vertical_header
        self.sort_order = Qt.SortOrder.AscendingOrder
        
    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            value = self._data[index.row()][index.column()]
            if isinstance(value, np.float64):
                return float(value)
            return value
        
        elif role == Qt.ItemDataRole.ForegroundRole:
            color = self._color[index.row()][index.column()]
            return QBrush(color)
            
    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            self._data[index.row()][index.column()] = value
            self.check_OscType_and_adjust_columns()
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
            return True
        return False
    
    def change_isAdjustable(self, index : QModelIndex) :
        if index.isValid() :
            if index.column() > 0 : # 0번째 column은  OscType이므로 무시
                self._isAdjustable[index.row()][index.column()-1] = not self._isAdjustable[index.row()][index.column()-1]
                # True이면 False, False이면 True로 바꾼다.
                self._color_Adjustable = [[color_Adjustable if isAdjustable else color_NotAdjustable for isAdjustable in isAdjustable_row]
                                                                        for isAdjustable_row in self._isAdjustable]
                self._color = [[color_Normal] + color_Adjustable_row for color_Adjustable_row in self._color_Adjustable]
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
    
    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()

        combined = list(zip(self._data, self._isAdjustable, self._color_Adjustable, self._color))
        # 정렬하기 위해 함께 정렬될 리스트들 (데이터, 데이터가 조정가능한지, 데이터의 색깔 리스트 등) 을 묶는다
        combined.sort(key = lambda x:x[0][column], reverse= (order == Qt.SortOrder.DescendingOrder))
        # 0번째가 data이므로 data의 column에 따라 정렬한다.
        self._data, self._isAdjustable, self._color_Adjustable, self._color = map(list, zip(*combined))
        self.layoutChanged.emit()
        self.tableChanged.emit()
    
    def getData(self) :
        return self._data
    
    def getisAdjustable(self) :
        return self._isAdjustable

    def rowCount(self, index=None):
        return len(self._data)

    def columnCount(self, index=None):
        return len(self._data[0])
    
    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._horizontal_header[section]
            elif orientation == Qt.Orientation.Vertical:
                return self._vertical_header[section]
    
    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
    

    def addRow(self, row_data, clicked_index):
        if self._data : # data가 비어있지 않다면
            if len(row_data) < len(self._data[0]) : # data의 column수가 추가할 row_data보다 많은 경우 row_data 수를 늘려서 column수와 맞춰준다.
                while len(row_data) < len(self._data[0]) : row_data.append(10.) 
        if clicked_index == None :
            # Append to the end if no valid row is clicked
            self.beginInsertRows(self.index(-1,-1), self.rowCount(), self.rowCount())
            self._data.append(row_data)
            self._isAdjustable.append([True for data in row_data[1:]])
            self._color_Adjustable.append([color_Adjustable for data in row_data[1:]])
            self._color.append([color_Normal] + [color_Adjustable for data in row_data[1:]])
        else:
            clicked_index_row = clicked_index.row()
            # Insert below the clicked row
            insert_position = clicked_index_row+1
            self.beginInsertRows(self.index(-1,-1), insert_position, insert_position)
            self._data.insert(insert_position, row_data)
            self._isAdjustable.insert(insert_position, [True for data in row_data[1:]]) # row_data의 첫 요소는 OscType이므로 제외
            self._color_Adjustable.insert(insert_position, [color_Adjustable for data in row_data[1:]])
            self._color.insert(insert_position, [color_Normal] + [color_Adjustable for data in row_data[1:]])
        
        self.endInsertRows()
        # Update vertical header
        
        self._vertical_header.append(str(len(self._data)))
        self.tableChanged.emit()

    def removeRow(self, clicked_index):
        if clicked_index is None :
            # Do nothing if no valid row is clicked
            return

        clicked_index_row = clicked_index.row()
        self.beginRemoveRows(self.index(-1, -1), clicked_index_row, clicked_index_row)
        del self._data[clicked_index_row]
        del self._isAdjustable[clicked_index_row]
        del self._color_Adjustable[clicked_index_row]
        del self._color[clicked_index_row]
        self.endRemoveRows()
        # Update vertical header
        self._vertical_header = [str(i + 1) for i in range(len(self._data))]
        self.tableChanged.emit()

    def check_OscType_and_adjust_columns(self):
        target_string = "Tauc-Lorentz"
        if isinstance(self._data[0][0], str) : add_column = any(target_string in row[0] for row in self._data)
        else : add_column = False

        if add_column and len(self._data[0]) == 4:
            self.beginInsertColumns(QModelIndex(), len(self._data[0]), len(self._data[0]))
            for i in range(len(self._data)):
                self._data[i].append(10.)
                self._isAdjustable[i].append(True)
                self._color[i].append(color_Adjustable)
                self._color_Adjustable[i].append(color_Adjustable)
                self._horizontal_header.append('param')
            self.endInsertColumns()
            print("Column added.")
        elif not add_column and len(self._data[0]) == 5:
            self.beginRemoveColumns(QModelIndex(), len(self._data[0]) - 1, len(self._data[0]) - 1)
            for i in range(len(self._data)):
                self._data[i].pop()
                self._isAdjustable[i].pop()
                self._color[i].pop()
                self._color_Adjustable[i].pop()
                self._horizontal_header.pop()
            self.endRemoveColumns()
            print("Column removed.")


class ParamsTableView(QTableView):
    def __init__(self, parent):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.installEventFilter(self)
        self.setItemDelegate(ScientificNotationDelegate(self))

    def eventFilter(self, source, event):
        if event.type() == event.Type.Wheel and source is self:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == (Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.ControlModifier):
                pos = self.viewport().mapFromGlobal(event.globalPosition().toPoint())
                index = self.indexAt(pos)
                if index.isValid() & (type(index.data()) != str):
                    current_value = float(index.data())
                    delta = event.angleDelta().y() // 120
                    new_value = current_value + float(delta)*10
                    self.model().setData(index, new_value, Qt.ItemDataRole.EditRole)
                    return True
            elif modifiers == Qt.KeyboardModifier.ShiftModifier:
                pos = self.viewport().mapFromGlobal(event.globalPosition().toPoint())
                index = self.indexAt(pos)
                if index.isValid() & (type(index.data()) != str):
                    current_value = int(index.data())
                    delta = event.angleDelta().y() // 120
                    new_value = current_value + float(delta)*100
                    self.model().setData(index, new_value, Qt.ItemDataRole.EditRole)
                    return True
        return super().eventFilter(source, event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            index = self.indexAt(event.position().toPoint())
            if index.isValid():
                self.model().change_isAdjustable(index)
        super().mousePressEvent(event)
    
class FixedParamsTableModel(ParamsTableModel) : 
    # Oscillator parameter들만 1번쨰 컬럼에 OscType이 들어가있어서.. 다른 table의 경우 Color 설정 등에 문제가 있음. 따로 설정해주자
    def __init__(self, parent, data, horizontal_header, vertical_header):
        super().__init__(parent, data, horizontal_header, vertical_header)
        self._isAdjustable = [[True for data in data_row[:]] for data_row in self._data] # data_row의 첫 요소는 OscType이므로 제외
        self._color_Adjustable = [[color_Adjustable if isAdjustable else color_NotAdjustable for isAdjustable in isAdjustable_row]
                        for isAdjustable_row in self._isAdjustable]
        self._color = [color_Adjustable_row for color_Adjustable_row in self._color_Adjustable]

    def change_isAdjustable(self, index : QModelIndex) :
        if index.isValid() :
            self._isAdjustable[index.row()][index.column()] = not self._isAdjustable[index.row()][index.column()]
            # True이면 False, False이면 True로 바꾼다.
            self._color_Adjustable = [[color_Adjustable if isAdjustable else color_NotAdjustable for isAdjustable in isAdjustable_row]
                                                                    for isAdjustable_row in self._isAdjustable]
            self._color = [color_Adjustable_row for color_Adjustable_row in self._color_Adjustable]
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])

    def check_OscType_and_adjust_columns(self): 
        # element수가 고정된 Table의 경우 이 함수를 실행할 필요가 없어서 오버라이딩해서 없애준다
        return
    

class ScientificNotationDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        text = editor.text()
        original_value = index.model().data(index, Qt.ItemDataRole.EditRole)
        
        if self.is_valid_number(text):
            model.setData(index, float(text), Qt.ItemDataRole.EditRole)
        else:
            # 원래 값이 문자열인 경우는 편집한 값을 그대로 넣어줍니다.
            if isinstance(original_value, str):
                model.setData(index, text, Qt.ItemDataRole.EditRole)
            else:
                editor.setText(str(original_value))

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def is_valid_number(self, text):
        # Check if the text is a valid scientific notation number
        regex = re.compile(r'^-?\d+(\.\d+)?(e-?\d+)?$', re.IGNORECASE)
        return bool(regex.match(text))

'''class ScientificNotationDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        text = editor.text()
        if self.is_valid_number(text):
            model.setData(index, float(text), Qt.ItemDataRole.EditRole)
        else:
            editor.setText(str(index.model().data(index, Qt.ItemDataRole.EditRole)))

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def is_valid_number(self, text):
        # Check if the text is a valid scientific notation number
        regex = re.compile(r'^-?\d+(\.\d+)?(e-?\d+)?$', re.IGNORECASE)
        return bool(regex.match(text))'''
