from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal
import logging

logger = logging.getLogger(__name__)


class DraggableItemFrame(QFrame):
    list_signal = Signal(list)
    def __init__(self,x=5,y=5, w=200, h=150, lista=None):
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.lista = lista
        self.dragging = False
        self.initUI()

    def initUI(self):
        checkstate = False
        if not self.lista:
            self.lista = [("EGB_DzialkaEwidencyjna", 1, True), ("EGB_KonturUzytkuGruntowego", 2)]
        
        self.listWidget = QListWidget()
        for i, data, checkstate in self.lista:
            item = QListWidgetItem(i)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if checkstate:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, data)
            self.listWidget.addItem(item)

        self.listWidget.itemDoubleClicked.connect(self.toggleCheckState)
        self.listWidget.itemDoubleClicked.connect(self.getCheckedItems)
        self.listWidget.itemClicked.connect(self.getCheckedItems)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 15, 0, 0)
        layout.addWidget(self.listWidget)
        self.setLayout(layout)
        self.setStyleSheet("background-color: lightgrey; border: 0px;")
        self.setGeometry(self.x, self.y, self.w, self.h)

    def toggleCheckState(self, item):
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)

    def getCheckedItems(self):
        checked_items = []
        un_checked_items = []
        for index in range(self.listWidget.count()):
            list_item = self.listWidget.item(index)
            item_data = list_item.data(Qt.UserRole)  # Pobieramy obiekt z przypisaną sceną
            
            if list_item.checkState() == Qt.Checked:
                checked_items.append(item_data)
            else:
                un_checked_items.append(item_data)
        
        self.send_list(checked_items, un_checked_items)
        return checked_items, un_checked_items
    
    def send_list(self, checked_items, un_checked_items):
        self.list_signal.emit((checked_items, un_checked_items))

    def update_list_widget(self, lista):
        self.listWidget.clear()  # Clear the existing items
        for i, data, checkstate in lista:
            item = QListWidgetItem(i)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if checkstate else Qt.Unchecked)
            item.setData(Qt.UserRole, data)
            self.listWidget.addItem(item)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.dragStartPosition = (event.globalPosition().toPoint() - self.frameGeometry().topLeft())
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.dragStartPosition)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()


if __name__ == '__main__':
    pass