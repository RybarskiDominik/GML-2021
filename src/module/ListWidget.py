import sys
from PySide6.QtWidgets import QApplication, QListWidget
from PySide6.QtCore import Qt, QSize, Signal
from PySide6 import QtCore, QtWidgets
import pandas as pd
import logging

import re
from model.DataFrameProcessing import myDataFrame

class ListWidget(QtWidgets.QMainWindow):
    refresh_data = Signal()
    def __init__(self,
                manual_mode = None,  # None=df_memory
                lelf_or_right = None,  # "both", "lelf" or "right"
                points_name = "NR",
                gml_mode = False,
                gml_output = True,
                left_and_right_list_name=["Lista punktów:", "Wybrane punkty:"],  # ListWidget
                ):
        super().__init__()
        self.setWindowTitle("Porównanie współrzędnych.")
        
        self.gml_mode = gml_mode
        self.gml_output = gml_output

        self.manual_mode = manual_mode
        self.lelf_or_right = lelf_or_right
        self.left_and_right_list_name = left_and_right_list_name
        self.points_name = points_name

        self.list_NR1 = pd.DataFrame()
        self.list_NR2 = pd.DataFrame()

        self.setFixedSize(400, 350)

        self.init_UI()

        self.start()

    def init_UI(self):
        self.main_widget = QtWidgets.QWidget()
        self.layout = QtWidgets.QHBoxLayout()
        self.verticallayout = QtWidgets.QVBoxLayout()
        self.gridlayout = QtWidgets.QGridLayout()

        self.listWidgetLeft = QtWidgets.QListWidget()  # QListWidget()
        self.listWidgetLeft.setGeometry(0, 2, 100, 400)
        self.listWidgetLeft.setSortingEnabled(True)
        self.listWidgetLeft.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.listWidgetLeft.setSelectionMode(QListWidget.ExtendedSelection)
        self.listWidgetLeft.doubleClicked.connect(self.on_double_clicked_to_right)
        #self.listWidgetLeft.show()
        #self.listWidgetLeft.setDragEnabled(True)

        self.listWidgetRight = QtWidgets.QListWidget()  # QListWidget()
        self.listWidgetRight.setGeometry(100, 22, 100, 400)
        self.listWidgetRight.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        #self.listWidgetRight.setDragDropOverwriteMode(False)
        self.listWidgetRight.setSelectionMode(QListWidget.ExtendedSelection)
        self.listWidgetRight.doubleClicked.connect(self.on_double_clicked_to_left)
        #self.listWidgetRight.setDragEnabled(True)

        self.list_Item_left = QtWidgets.QLineEdit()
        self.list_Item_left.setText(self.left_and_right_list_name[0])
        self.list_Item_left.setReadOnly(True)

        self.sortleft = QtWidgets.QPushButton()
        self.sortleft.setText("Sort")
        self.sortleft.setMaximumSize(QSize(32, 32))
        self.sortleft.clicked.connect(self.sort_left_list)

        self.list_Item_right = QtWidgets.QLineEdit()
        self.list_Item_right.setText(self.left_and_right_list_name[1])
        self.list_Item_right.setReadOnly(True)

        self.sortright = QtWidgets.QPushButton()
        self.sortright.setText("Sort")
        self.sortright.setMaximumSize(QSize(30, 30))
        self.sortright.clicked.connect(self.sort_right_list)
        
        self.buttonok = QtWidgets.QPushButton()
        self.buttonok.setText("OK")
        self.buttonok.clicked.connect(self.send_item_list)

        self.buttoncancel = QtWidgets.QPushButton()
        self.buttoncancel.setText("Anuluj")
        self.buttoncancel.clicked.connect(self.close_win)

        self.clear = QtWidgets.QPushButton()
        self.clear.setText("Wyczyść")
        self.clear.setGeometry(0, 20, 95, 28)
        self.clear.clicked.connect(self.clear_list)

        self.add_L = QtWidgets.QPushButton()
        self.add_L.setText("<")
        self.add_L.setMaximumSize(QSize(30, 30))
        self.add_L.clicked.connect(self.add_selected_to_left)

        self.add_R = QtWidgets.QPushButton()
        self.add_R.setText(">")
        self.add_R.setMaximumSize(QSize(30, 30))
        self.add_R.clicked.connect(self.add_selected_to_right)


        self.all_R = QtWidgets.QPushButton()
        self.all_R.setText(">>")
        self.all_R.setMaximumSize(QSize(30, 30))
        self.all_R.clicked.connect(self.all_to_right)

        self.all_L = QtWidgets.QPushButton()
        self.all_L.setText("<<")
        self.all_L.setMaximumSize(QSize(30, 30))
        self.all_L.clicked.connect(self.all_to_left)

        self.custom_sort = QtWidgets.QLineEdit()
        self.custom_sort.setMaxLength(1)
        self.custom_sort.setAlignment(QtCore.Qt.AlignCenter)
        self.custom_sort.setPlaceholderText("*")
        self.custom_sort.setMaximumSize(QSize(26, 26))
        self.custom_sort.textChanged.connect(self.custom_sort_list)
        self.custom_sort.setToolTip("Sortowanie")


        self.layoutsort1 = QtWidgets.QHBoxLayout()
        self.layoutsort1.addWidget(self.list_Item_left)
        self.layoutsort1.addWidget(self.sortleft, alignment=Qt.AlignTop)
        self.gridlayout.addLayout(self.layoutsort1, 0, 0, 1, 1,)
        self.gridlayout.addWidget(self.listWidgetLeft, 1, 0, 1, 1)
        self.gridlayout.setSpacing(0)

        '''
        self.layout.addWidget(self.del_Item, alignment=Qt.AlignTop)
        self.layout.addWidget(self.clear, alignment=Qt.AlignTop)
        self.layout.addWidget(self.add_L, alignment=Qt.AlignTop)
        self.layout.addWidget(self.all_L, alignment=Qt.AlignTop)
        self.layout.addWidget(self.add_R, alignment=Qt.AlignTop)
        self.layout.addWidget(self.all_R, alignment=Qt.AlignTop)
        '''

        self.verticallayout.addWidget(self.add_R, alignment=Qt.AlignTop)
        self.verticallayout.addWidget(self.all_R, alignment=Qt.AlignTop)
        self.verticallayout.addWidget(self.add_L, alignment=Qt.AlignTop)
        self.verticallayout.addWidget(self.all_L, alignment=Qt.AlignTop)
        self.verticallayout.addWidget(self.custom_sort, alignment=Qt.AlignCenter)
        self.verticallayout.setSpacing(5)
        self.verticallayout.addStretch(1)

        self.layoutsort2 = QtWidgets.QHBoxLayout()
        self.layoutsort2.addWidget(self.list_Item_right)
        self.layoutsort2.addWidget(self.sortright, alignment=Qt.AlignTop)
        self.gridlayout.addLayout(self.layoutsort2, 0, 3, 1, 1,)

        self.gridlayout.addWidget(self.listWidgetRight, 1, 3, 1, 1)
        self.gridlayout.addLayout(self.verticallayout, 1, 2, 1, 1)
        
        self.layoutsort3 = QtWidgets.QHBoxLayout()
        self.layoutsort3.addWidget(self.buttonok)
        self.layoutsort3.addWidget(self.buttoncancel)
        self.gridlayout.addLayout(self.layoutsort3, 3, 3, 1, 1,)

        self.main_widget.setLayout(self.gridlayout)

        self.setCentralWidget(self.main_widget)

    def start(self):
        if myDataFrame.df_memory.empty and myDataFrame.df_1.isna().all().all() and myDataFrame.df_2.empty and myDataFrame.df_gml.empty:
            return

        if self.manual_mode == False:
            try:
                for index, row in myDataFrame.df_memory.iterrows():
                        self.listWidgetLeft.addItem(row[self.points_name])
            except Exception as e:
                logging.exception(e)
                print(e)
        elif self.manual_mode == True:
            try:
                for index, row in myDataFrame.df_1.iterrows():
                    self.listWidgetLeft.addItem(row[self.points_name])           
            except Exception as e:
                logging.exception(e)
                print(e)
            try:
                for index, row in myDataFrame.df_2.iterrows():
                    self.listWidgetRight.addItem(row[self.points_name])
            except Exception as e:
                logging.exception(e)
                print(e)
        elif self.manual_mode == None and self.gml_mode == True:
            try:
                for index, row in myDataFrame.df_gml_list.iterrows():
                    self.listWidgetLeft.addItem(row["Działka"])
            except Exception as e:
                logging.exception(e)

    def send_item_list(self):
        if self.manual_mode == True:
            try:
                items = []
                for i in range(self.listWidgetLeft.count()):
                    item = self.listWidgetLeft.item(i)
                    items.append(item.text())
                myDataFrame.df_1_sort_list = items
            except Exception as e:
                logging.exception(e)
                print(e)
            try:
                items = []
                for i  in range(self.listWidgetRight.count()):
                    item = self.listWidgetRight.item(i)
                    items.append(item.text())
                myDataFrame.df_2_sort_list = items
            except Exception as e:
                logging.exception(e)
                print(e)
            myDataFrame.synchronize_manual()

        if self.manual_mode == False:
            items = []
            if self.lelf_or_right == "left":
                for i in range(self.listWidgetRight.count()):
                    item = self.listWidgetRight.item(i)
                    items.append(item.text())
                myDataFrame.df_1_sort_list = items
                myDataFrame.synchronize_df_1()
            elif self.lelf_or_right == "right":
                for i  in range(self.listWidgetRight.count()):
                    item = self.listWidgetRight.item(i)
                    items.append(item.text())
                myDataFrame.df_2_sort_list = items
                myDataFrame.synchronize_df_2()

        
        if self.gml_mode == True:
            items = []
            for i  in range(self.listWidgetRight.count()):
                item = self.listWidgetRight.item(i)
                items.append(item.text())

            df = myDataFrame.df_gml
            matching_rows = df[df['Działka'].isin(items)]
            df = matching_rows.reset_index(drop=True)
            df = df.drop(columns='Działka')

            df["X"] = df["X"].replace(',', '.', regex=True)
            df["X"] = pd.to_numeric(df["X"], errors='coerce')
            df["Y"] = df["Y"].replace(',', '.', regex=True)
            df["Y"] = pd.to_numeric(df["Y"], errors='coerce')
            df,_ = myDataFrame.is_duplicated(df=df)
            if self.gml_output == 1:
                myDataFrame.df_1 = df
            if self.gml_output == 2:
                myDataFrame.df_2 = df
            if self.gml_output == 3:
                myDataFrame.df_memory = df

        self.refresh()
        self.close()

    def add_selected_to_left(self):
        selected_items = self.listWidgetRight.selectedItems()
        for item in selected_items:
            self.listWidgetLeft.addItem(item.text())
            self.listWidgetRight.takeItem(self.listWidgetRight.row(item))

    def add_selected_to_right(self):
        selected_items = self.listWidgetLeft.selectedItems()
        for item in selected_items:
            self.listWidgetRight.addItem(item.text())
            self.listWidgetLeft.takeItem(self.listWidgetLeft.row(item))
    
    def all_to_right(self):
        for i in range(self.listWidgetLeft.count()):
            self.listWidgetRight.addItem(self.listWidgetLeft.takeItem(0))

    def all_to_left(self):
        for i in range(self.listWidgetRight.count()):
            self.listWidgetLeft.addItem(self.listWidgetRight.takeItem(0))

    def delete_item(self):
        listItems = self.listWidgetRight.selectedItems()
        if not listItems:
            self.listWidgetRight.setCurrentItem(self.listWidgetRight.item(0))
            if self.listWidgetRight.count() > 0:
                self.delete_item()
        for item in listItems:
            self.listWidgetRight.takeItem(self.listWidgetRight.row(item))

    def clear_list(self):
        self.listWidgetRight.setCurrentItem(self.listWidgetRight.item(0))
        for i in range(self.listWidgetRight.count()):
            self.listWidgetRight.clear()

    def on_double_clicked_to_right(self):
        row = self.listWidgetLeft.currentRow()
        rowItem = self.listWidgetLeft.takeItem(row)
        self.listWidgetRight.addItem(rowItem)

    def on_double_clicked_to_left(self):
        row = self.listWidgetRight.currentRow()
        rowItem = self.listWidgetRight.takeItem(row)
        self.listWidgetLeft.addItem(rowItem)

    def sort_left_list(self):
        self.listWidgetLeft.sortItems()
        print('L')

    def sort_right_list(self):
        self.listWidgetRight.sortItems()
        print('R')

    def custom_sort_list(self):
        sort_value = self.custom_sort.text()
        item_count = self.listWidgetLeft.count()
        if sort_value != '':
            pattern = re.compile(re.escape(sort_value), re.IGNORECASE)  # Create a regular expression pattern with wildcard and ignore case
            for i in range(item_count):
                item = self.listWidgetLeft.item(i)
                if not re.search(pattern, item.text()):  # Check if sort_value is not found in item.text()
                    item.setHidden(True)
        else:
            item_count = self.listWidgetLeft.count()
            for i in range(item_count):
                item = self.listWidgetLeft.item(i)
                item.setHidden(False)

    def close_win(self):
        self.close()

    def refresh(self):
        self.refresh_data.emit()

if __name__ == "__main__":
    myDataFrame.default()
    app = QtWidgets.QApplication(sys.argv)
    window = ListWidget()
    window.show()
    sys.exit(app.exec())
