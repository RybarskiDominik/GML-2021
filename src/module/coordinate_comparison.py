"""
Porównanie współrzędnych
"""
from PySide6.QtWidgets import (QMainWindow, QApplication, QTableView, QPushButton, 
                               QFileDialog, QTabWidget, QMessageBox, QMenuBar, 
                               QGroupBox, QVBoxLayout, QHBoxLayout, QCheckBox, QGridLayout,
                               QLineEdit, QMenu, QWidget, QToolButton, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Slot, Signal, QRect
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction, QIcon, QShortcut, QKeySequence, QCursor, QColor, QFont
import pandas as pd
import logging
import sys
import os

from model.DataFrameProcessing import myDataFrame
from module.ListWidget import ListWidget
from obf.punkty import punkt_graniczny
from obf.punkty_poligon import punkty_w_dzialkach

logger = logging.getLogger(__name__)

if getattr(sys, 'frozen', False):
    path_stylesheets = os.path.dirname(sys.executable) + '\\gui\\Stylesheets\\images_dark-light\\'
    target_path_for_GML = os.path.dirname(sys.executable) + "\\GML\\Parsed_GML.gml"
else:
    folder = os.path.basename(sys.path[0])
    if folder == "src":
        path_stylesheets = sys.path[0] + '\\gui\\Stylesheets\\images_dark-light\\'
        target_path_for_GML = sys.path[0] + "\\GML\\Parsed_GML.gml"
    else:
        path_stylesheets = sys.path[0] + '\\src\\Stylesheets\\images_dark-light\\'
        target_path_for_GML = sys.path[0] + "\\src\\GML\\Parsed_GML.gml"


class DataFrameTableModel(QStandardItemModel):
    def __init__(self, df=None, filename=''):
        super().__init__()
        self._df = df if df is not None else pd.DataFrame()
        self._filename = filename
        self._changes = [self._df.copy()]
        self._currChange = 0
        self.update_view()

        #self.itemChanged.connect(self.onItemChanged)

    def setDataFrame(self, df):
        self._df = df
        self._changes = [df.copy()]
        self._currChange = 0
        self.update_view()

    def update_view(self):
        self.clear()

        self.setHorizontalHeaderLabels(self._df.columns.tolist())

        self.setColumnCount(len(self._df.columns))
        self.setRowCount(len(self._df))
        for row in range(len(self._df)):
            for col in range(len(self._df.columns)):
                value = self._df.iat[row, col]

                if isinstance(value, float):
                    item = f"{value:.2f}"
                else:
                    item = str(value)
                self.setItem(row, col, QStandardItem(item))
    
    '''
    def addChange(self):
        """Track change in DataFrame."""
        self._currChange += 1
        #self._changes = self._changes[:self._currChange]
        #self._changes.append(self._df.copy())
        #print(self._currChange)
        #print(self._changes)
        #self.trackDataChange.emit()

    def onItemChanged(self, item):
        print("chenge")

        """Handle item change and update the DataFrame."""

        row = item.row()
        col = item.column()
        value = item.text()

        self._df.iat[row, col] = value

        self.addChange()
    '''


class ImportWin(QMainWindow):
    def __init__(self, win, tabela=None, dark_mode_enabled=None, path=False):
        super().__init__()
        self.win = win
        self.setWindowIcon(QIcon(r'gui\Stylesheets\WSP.ico'))
        self.setWindowTitle("Import punktów")
        self.setFixedSize(300, 250)
        self.dark_mode_enabled = dark_mode_enabled
        self.path = path
        self.tabela = tabela
        
        if tabela == 1:
            self.setWindowTitle("Import punktów do tabeli NR 1")
        elif tabela == 2:
            self.setWindowTitle("Import punktów do tabeli NR 2")

        if self.dark_mode_enabled:
            self.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                }
            QGroupBox {
                color: #ffffff;
                }
            """)

        self.init_UI()

    def init_UI(self):
        group_main = QGroupBox("Dane", self)
        group_main.setGeometry(5, 0, 290, 90)

        group_spec = QGroupBox("Specyfikacja", self)
        group_spec.setGeometry(5, 90, 140, 40)

        group_gml = QGroupBox("GML", self)
        group_gml.setGeometry(150, 90, 145, 40)

        group_tab = QGroupBox("Którą zbiór wypełnić?", self)
        group_tab.setGeometry(5, 132, 155, 90)

        group_sep = QGroupBox("Separator dziesiętny?", self)
        group_sep.setGeometry(170, 132, 125, 90)
        group_sep.setDisabled(True)


        self.button_import = QtWidgets.QPushButton('Import', self)
        self.button_import.setGeometry(5, 222, 72, 28)
        self.button_import.clicked.connect(self.send_instruction)

        self.button_lista = QtWidgets.QPushButton('lista', self)
        self.button_lista.setGeometry(77, 222, 73, 28)
        self.button_lista.setDisabled(True)

        self.button_gml = QtWidgets.QPushButton('GML', self)
        self.button_gml.setGeometry(150, 222, 73, 28)
        self.button_gml.clicked.connect(self.gml_instruction)
        #self.button_gml.setDisabled(True)

        self.button_anuluj = QtWidgets.QPushButton('Anuluj', self)
        self.button_anuluj.setGeometry(223, 222, 72, 28)
        self.button_anuluj.clicked.connect(self.anuluj)


        self.order_1 = QCheckBox("NR X Y (H)", self)  # [0,1,2,3,4,5,6]
        self.order_1.setChecked(True)
        self.order_1.stateChanged.connect(lambda: self.state(self.order_1))
        self.order_2 = QCheckBox("NR X Y SPD ISD STB", self)
        self.order_2.stateChanged.connect(lambda: self.state(self.order_2))
        self.order_3 = QCheckBox("NR X Y H SPD ISD STB", self)
        self.order_3.stateChanged.connect(lambda: self.state(self.order_3))
        
        self.order_4 = QCheckBox("Y<-- -->X", self)
        
        layout = QGridLayout()
        layout.addWidget(self.order_1, 0, 0)
        layout.addWidget(self.order_2, 1, 0)
        layout.addWidget(self.order_3, 2, 0)
        layout.addWidget(self.order_4, 1, 1)
        group_main.setLayout(layout)


        self.gml_origin = QCheckBox("GML z pamięci.", self)
        self.gml_origin.setChecked(True)
        
        layout = QVBoxLayout()
        layout.addWidget(self.gml_origin)
        layout.setContentsMargins(5, 0, 0, 5)
        group_gml.setLayout(layout)

        self.tabela_1 = QCheckBox('Lewy zbiór punktów', self)  # Tabela Nr1
        if self.tabela == None or self.tabela == 1:
            self.tabela_1.setChecked(True)
        else:
            self.tabela_2.setChecked(True)
        self.tabela_1.stateChanged.connect(lambda: self.state(self.tabela_1))
        self.tabela_2 = QCheckBox('Prawy zbiór punktów', self)   # Tabela Nr2
        self.tabela_2.stateChanged.connect(lambda: self.state(self.tabela_2))
        self.memory = QCheckBox('Pamięć', self)
        #self.memory.setDisabled(True)
        self.memory.stateChanged.connect(lambda: self.state(self.memory))

        layout = QVBoxLayout()
        #layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.tabela_1)
        layout.addWidget(self.tabela_2)
        layout.addWidget(self.memory)
        group_tab.setLayout(layout)


        self.sep_kropka = QCheckBox('Kropka', self)
        self.sep_kropka.setChecked(True)
        self.sep_kropka.stateChanged.connect(lambda: self.state(self.sep_kropka))
        self.sep_przecinek = QCheckBox('Przecinek', self)
        self.sep_przecinek.stateChanged.connect(lambda: self.state(self.sep_przecinek))

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.sep_kropka)
        layout.addWidget(self.sep_przecinek)
        group_sep.setLayout(layout)

    def state(self, check_box):
        if check_box.isChecked() and check_box in [self.order_1, self.order_2, self.order_3]:
            if check_box != self.order_1:
                self.order_1.setChecked(False)
            if check_box != self.order_2:
                self.order_2.setChecked(False)
            if check_box != self.order_3:
                self.order_3.setChecked(False)

        if check_box.isChecked() and check_box in [self.tabela_1, self.tabela_2, self.memory]:
            if check_box != self.tabela_1:
                self.tabela_1.setChecked(False)
            if check_box != self.tabela_2:
                self.tabela_2.setChecked(False)
            if check_box != self.memory:
                self.memory.setChecked(False)

        if check_box.isChecked() and check_box in [self.sep_kropka, self.sep_przecinek]:
            if check_box != self.sep_kropka:
                self.sep_kropka.setChecked(False)
            if check_box != self.sep_przecinek:
                self.sep_przecinek.setChecked(False)

    def gml_instruction(self):
        if self.tabela_1.isChecked():
            tabela = 1
        elif self.tabela_2.isChecked():
            tabela = 2
        elif self.memory.isChecked():
            tabela = 3
        else:
            tabela = 1

        if self.sep_kropka.isChecked():
            separator = "."
        elif self.sep_przecinek.isChecked():
            separator = "," 
        else:
            separator = "."

        if self.gml_origin.isChecked():
            self.path = target_path_for_GML
        else:
            self.path = None

        Win_coordinate_comparison.import_gml_points(self.win, tabela, self.path, True)
        
        self.close()

    def send_instruction(self):
        if self.order_1.isChecked() or self.order_3.isChecked():
            order = [0,1,2,3,4,5,6]
        elif self.order_2.isChecked():
            order = [0,1,2,4,5,6,3]
        else:
            order = [0,1,2,3,4,5,6]

        if self.order_4.isChecked():
            order[1] = 2
            order[2] = 1

        if self.tabela_1.isChecked():
            tabela = 1
        elif self.tabela_2.isChecked():
            tabela = 2
        elif self.memory.isChecked():
            tabela = 3
        else:
            tabela = 1

        if self.sep_kropka.isChecked():
            separator = "."
        elif self.sep_przecinek.isChecked():
            separator = "," 
        else:
            separator = "."

        Win_coordinate_comparison.import_points(self.win, order, tabela, self.path)

        self.close()

    def anuluj(self):
        self.close()


class DropWin(QMainWindow):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle("..NR..")
        self.setWindowIcon(QIcon(r'gui\Stylesheets\WSP.ico'))
        #self.setMinimumSize(100, 150)
        self.setFixedSize(200, 200)

        self.prefix_box = QCheckBox("Przedrostek?")
        self.prefix_box.setChecked(True)
        self.suffix_box = QCheckBox("Przyrostek?")

        self.prefix_text = QLineEdit()
        self.prefix_text.setPlaceholderText("Wpisz tekst przedrosteka...")
        
        self.suffix_text = QLineEdit()
        self.suffix_text.setPlaceholderText("Wpisz tekst przyrosteka...")

        self.set_1 = QCheckBox("Zbiór Lewy?")
        self.set_1.setChecked(True)
        self.set_1.stateChanged.connect(lambda: self.state(self.set_1))
        self.set_2 = QCheckBox("Zbiór prawy?")
        self.set_2.stateChanged.connect(lambda: self.state(self.set_2))
        self.set_3 = QCheckBox("Zbiór w Pamięci?")
        self.set_3.stateChanged.connect(lambda: self.state(self.set_3))

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.split_NR)

        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.anuluj)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget(self)
        main_layout = QVBoxLayout(central_widget)
        checkbox_layout_1 = QHBoxLayout()
        checkbox_layout_1.addWidget(self.prefix_box)
        checkbox_layout_1.addWidget(self.suffix_box)

        set_layout = QHBoxLayout()
        set_layout.addWidget(self.set_1)
        set_layout.addWidget(self.set_2)
        
        set_layout_3 = QVBoxLayout()
        set_layout_3.addWidget(self.set_3)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)


        main_layout.addLayout(checkbox_layout_1)    # Checkboxy przedrostek/przyrostek (u góry)
        main_layout.addWidget(self.prefix_text)   # Pole tekstowe 1
        main_layout.addWidget(self.suffix_text)   # Pole tekstowe 2
        main_layout.addLayout(set_layout)           # Checkboxy zbiorów (w poziomie)
        main_layout.addLayout(set_layout_3)         # Checkboxy pamięci (w poziomie)
        main_layout.addLayout(button_layout)        # Przyciski OK/Anuluj (na dole)

        self.setCentralWidget(central_widget)

    def state(self, check_box):
        if check_box.isChecked() and check_box in [self.set_1, self.set_2, self.set_3]:
            if check_box != self.set_1:
                self.set_1.setChecked(False)
            if check_box != self.set_2:
                self.set_2.setChecked(False)
            if check_box != self.set_3:
                self.set_3.setChecked(False)

    def split_NR(self):
        prefix_state= False
        suffix_state= False
        prefix = None
        suffix = None

        if self.set_1.isChecked():
            df_name = "df_1"
        if self.set_2.isChecked():
            df_name = "df_2"
        if self.set_3.isChecked():
            df_name = "df_memory"

        if self.prefix_box.isChecked():
            if self.prefix_text.text():
                prefix = self.prefix_text.text()
                prefix_state = True
            
        if self.suffix_box.isChecked():
            if self.suffix_text.text():
                suffix = self.suffix_text.text()
                suffix_state = True
        
        if not self.prefix_box.isChecked() and not self.suffix_box.isChecked():
            return
        
        try:
            myDataFrame.drop_prefix_or_suffix(df_name, "NR", prefix_mode=prefix_state, prefix_text=prefix, suffix_mode=suffix_state, suffix_text=suffix)
        except Exception as e:
            logging.exception(e)
            print(e)
        
        Win_coordinate_comparison.display_data(self.win)

        self.close()

    def anuluj(self):
        self.close()


class Win_coordinate_comparison(QMainWindow):
    refresh_data = Signal()
    def __init__(self, dark_mode_enabled=None):
        super().__init__()
        self.setWindowIcon(QIcon(path_stylesheets + 'WSP.ico'))
        self.setWindowIcon(QIcon(r'gui\Stylesheets\WSP.ico'))
        self.setWindowTitle("Porównanie współrzednych")
        self.setMinimumSize(706, 430)
        self.setAcceptDrops(True)
        self.win = self

        self.dark_mode_enabled = dark_mode_enabled

        shortcut = QShortcut(QKeySequence(Qt.CTRL | Qt.Key_C), self)
        shortcut.activated.connect(self.copy_to_clipboard)

        if self.dark_mode_enabled:
            self.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                }
            QGroupBox {
                color: #ffffff;
                }
            """)

        self.init_UI()
        self.init_resize_UI()
        self.GMLDefaultTable()

    def init_UI(self):

        self.button_import = QPushButton("Import", self)
        self.button_import.setFixedHeight(26)  # Set fixed height
        self.button_import.setFixedWidth(65)   # Set fixed width
        if self.dark_mode_enabled:
            self.button_import.setIcon(QIcon(path_stylesheets + "Strzałka-export-light"))
        else:
            self.button_import.setIcon(QIcon(path_stylesheets + 'Strzałka-import-dark.svg'))
        self.button_import.clicked.connect(self.import_window)

        self.button_export = QPushButton("Export", self)
        self.button_export.setFixedHeight(26)  # Set fixed height
        self.button_export.setFixedWidth(65)   # Set fixed width
        if self.dark_mode_enabled:
            self.button_export.setIcon(QIcon(path_stylesheets + 'Strzałka-export-light.svg'))
        else:
            self.button_export.setIcon(QIcon(path_stylesheets + 'Strzałka-export-dark.svg'))
        self.button_export.clicked.connect(self.export)
        self.button_export.setToolTip('<p>Export do <b>EXCEL</b>.</p>')

        self.button_remove = QPushButton("..NR..", self)
        self.button_remove.setFixedHeight(26)  # Set fixed height
        self.button_remove.setFixedWidth(38)   # Set fixed width
        self.button_remove.clicked.connect(self.remove_text_from_NR)
        self.button_remove.setToolTip('<p>Usuwanie przedrostka lub przyrostka numeru punktu.</p>'
                                      '<p>Funkcja ta praktyczne zastosowanie przy imporcie punktów z pliku GML</p>')

        self.button_manual_sortin = QPushButton(self)
        self.button_manual_sortin.setFixedHeight(26)  # Set fixed height
        self.button_manual_sortin.setFixedWidth(40)   # Set fixed width
        if self.dark_mode_enabled:
            self.button_manual_sortin.setIcon(QIcon(path_stylesheets + 'Exchange-light.svg'))
        else:
            self.button_manual_sortin.setIcon(QIcon(path_stylesheets + 'Exchange-dark.svg'))
        self.button_manual_sortin.setIconSize(QtCore.QSize(24, 24))
        self.button_manual_sortin.clicked.connect(self.manual_sorting)
        self.button_manual_sortin.setToolTip('<p>Ręczne porządkowanie zbiorów.</p>')


        self.left_set = QToolButton(self)
        self.left_set.setFixedHeight(26)  # Set fixed height
        self.left_set.setFixedWidth(26)   # Set fixed width
        if self.dark_mode_enabled:
            self.left_set.setIcon(QIcon(path_stylesheets + 'Left-light.svg'))
        else:
            self.left_set.setIcon(QIcon(path_stylesheets + 'Left-dark.svg'))
        self.left_set.setIconSize(QtCore.QSize(24, 24))
        self.left_set.clicked.connect(self.left_data_set)
        self.left_set.setToolTip('<p>Wprowadź ręcznie dane dla lewego zbioru.</p>')

        self.right_set = QToolButton(self)
        self.right_set.setFixedHeight(26)  # Set fixed height
        self.right_set.setFixedWidth(26)   # Set fixed width
        if self.dark_mode_enabled:
            self.right_set.setIcon(QIcon(path_stylesheets + 'Right-light.svg'))
        else:
            self.right_set.setIcon(QIcon(path_stylesheets + 'Right-dark.svg'))
        self.right_set.setIconSize(QtCore.QSize(24, 24))
        self.right_set.clicked.connect(self.right_data_set)
        self.right_set.setToolTip('<p>Wprowadź ręcznie dane dla prawego zbioru.</p>')

        self.button_reset = QToolButton(self)
        self.button_reset.setFixedHeight(24)  # Set fixed height
        self.button_reset.setFixedWidth(24)   # Set fixed width
        self.button_reset.setIcon(QIcon(path_stylesheets + 'Kosz.svg'))
        self.button_reset.setIconSize(QtCore.QSize(24, 24))
        self.button_reset.clicked.connect(self.reset)
        self.button_reset.setToolTip("Czyszczona jest cała pamięć programu.")

        self.CheckBox_wysokość = QCheckBox('H', self)
        self.CheckBox_wysokość.setFixedHeight(24)  # Set fixed height
        self.CheckBox_wysokość.setFixedWidth(30)
        self.CheckBox_wysokość.stateChanged.connect(self.wysokość)

        self.CheckBox_kody = QCheckBox('SPD ISD STB', self)
        self.CheckBox_kody.setFixedHeight(24)  # Set fixed height
        self.CheckBox_kody.setFixedWidth(85)
        self.CheckBox_kody.stateChanged.connect(self.kody)

        self.button_separation = QPushButton("Rozdziel", self)
        self.button_separation.setFixedHeight(26)  # Set fixed height
        self.button_separation.setFixedWidth(50)   # Set fixed width
        self.button_separation.clicked.connect(self.separation)
        self.button_separation.setToolTip('<p>Program stara się sam rozdzielić dane z lewej tabeli.</p>'
                            '<p style="margin: 0;">W <b>lewej</b> tabeli pozostają numery bez liter.</p>'
                            '<p style="margin: 0;">W <b>prawej</b> tabeli pozostają numery z literami.</p>')

        self.button_assign = QPushButton("Przyporządkuj", self)
        self.button_assign.setFixedHeight(26)  # Set fixed height
        self.button_assign.setFixedWidth(80)   # Set fixed width
        self.button_assign.clicked.connect(self.assign)
        self.button_assign.setToolTip('<p>Program stara się sam przyporządkować dane z lewej oraz prawej tabeli.</p>')

        self.line_przyrostek = QLineEdit(self)
        self.line_przyrostek.setFixedHeight(20)  # Set fixed height
        self.line_przyrostek.setFixedWidth(18)   # Set fixed width
        self.line_przyrostek.setPlaceholderText("K")
        self.line_przyrostek.setMaxLength(1)
        self.line_przyrostek.setAlignment(Qt.AlignCenter)
        self.line_przyrostek.setToolTip("Przyrostek nowo tworzonego zbioru punktów.")

        self.button_create = QPushButton("Twórz", self)
        self.button_create.setFixedHeight(26)  # Set fixed height
        self.button_create.setFixedWidth(55)   # Set fixed width
        self.button_create.clicked.connect(self.creat)
        self.button_create.setToolTip("Tworzy punkty w prawej tabeli.")

        self.button_count = QPushButton("Oblicz", self)
        self.button_count.setFixedHeight(26)  # Set fixed height
        self.button_count.setFixedWidth(55)   # Set fixed width
        self.button_count.clicked.connect(self.calculate)
    
    def init_resize_UI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 2, 0, 0)  # Remove margins
        main_layout.setSpacing(2)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)

        # Now add all widgets to the button layout at once
        button_layout.addWidget(self.button_import)
        button_layout.addWidget(self.button_export)
        button_layout.addSpacerItem(QSpacerItem(3, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        button_layout.addWidget(self.button_remove)
        button_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        button_layout.addWidget(self.button_manual_sortin)
        button_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        button_layout.addWidget(self.left_set)
        button_layout.addWidget(self.right_set)
        button_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        button_layout.addWidget(self.button_reset)
        button_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        button_layout.addWidget(self.CheckBox_wysokość)
        button_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        button_layout.addWidget(self.CheckBox_kody)
        button_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        button_layout.addStretch(1) 
        button_layout.addWidget(self.button_separation)
        button_layout.addWidget(self.button_assign)
        button_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        button_layout.addWidget(self.line_przyrostek)
        button_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        button_layout.addWidget(self.button_create)
        button_layout.addWidget(self.button_count)
        #button_layout.addStretch(1) 

        main_layout.addLayout(button_layout)

        self.table_widget = QTableView(self)
        main_layout.addWidget(self.table_widget)
        self.table_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.context_menu)

    def remove_text_from_NR(self):
        self.drop_win= DropWin(self.win)
        self.drop_win.show()

    def import_window(self):
        self.import_win = ImportWin(self.win, None, self.dark_mode_enabled)
        self.import_win.show()

    def import_gml_points(self, tabela, path=None, gml=None):
        filters = "GML files (*.gml)"
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Select a file", os.path.expanduser("~/Desktop"), filters)
        else:
            path = target_path_for_GML

        order = [0,1,2,4,5,6,3]

        try:
            df_działki = punkty_w_dzialkach(path)  # >>> Dzialka + ID Path
            df_punkty = punkt_graniczny(path)  # Path
            df_punkty_działki = df_działki.merge(df_punkty, how = 'outer', on=['ID'])
            df_punkty_działki.drop('ID', axis=1, inplace=True)
            myDataFrame.df_gml = df_punkty_działki
            myDataFrame.df_gml_list = df_działki[['Działka']]
            myDataFrame.is_duplicated('df_gml_list', 'Działka')
        except Exception as e:
            logging.exception(e)
            print(e)
            return

        self.lista = ListWidget(None, gml_mode = True, gml_output = tabela)
        self.lista.refresh_data.connect(self.display_data)
        self.lista.show()

    def import_points(self, order, tabela, path=None, gml=None, separator=None):
        filters = "TXT Files (*.txt);;CSV Files (*.csv);;Excel Files (*.xlsx)"

        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Select a file", os.path.expanduser("~/Desktop"), filters)

        if not path:
            return
        
        self.read_points(tabela, order, path)

    def read_points(self, tabela, order, path=None):
        if tabela is None or tabela == 1:
            status = myDataFrame.read(path, "df_1")
            if status is False:
                return
            myDataFrame.castling("df_1", order)
            myDataFrame.clean("df_1")
            myDataFrame.set_float_and_name("df_1")  # Nadawane są ostateczne nazwy kolumn - ['NR', 'X', 'Y', 'H', 'SPD', 'ISD', 'STB']
            myDataFrame.is_duplicated('df_1')
            myDataFrame.sort("df_1", "NR")
        elif tabela == 2:
            status = myDataFrame.read(path, "df_2")
            if status is False:
                return
            myDataFrame.castling("df_2", order)
            myDataFrame.clean("df_2")
            myDataFrame.set_float_and_name("df_2")  # Nadawane są ostateczne nazwy kolumn - ['NR', 'X', 'Y', 'H', 'SPD', 'ISD', 'STB']
            myDataFrame.is_duplicated('df_2')
            myDataFrame.sort("df_2", "NR")
        elif tabela == 3:
            status = myDataFrame.read(path, "df_memory")
            if status is False:
                return
            myDataFrame.castling("df_memory", order)
            myDataFrame.clean("df_memory")
            myDataFrame.set_float_and_name("df_memory")  # Nadawane są ostateczne nazwy kolumn - ['NR', 'X', 'Y', 'H', 'SPD', 'ISD', 'STB']
            myDataFrame.is_duplicated('df_memory')
            myDataFrame.sort("df_memory", "NR")

        self.display_data()

    def export(self):
        s_name = QFileDialog.getSaveFileName(self, 'select a file', os.path.expanduser("~/Desktop"),'Excel File(*.xlsx);;TXT File (*.txt);;TXT File With Tab Separator (*.txt);;CSV File (*.csv)')
        
        if s_name == ('', ''):
            return

        df = myDataFrame.df_all

        if s_name[1] == "Excel File(*.xlsx)":
            df.to_excel(s_name[0], index=False)
        
        if s_name[1] == "TXT File (*.txt)":
            df.to_csv(s_name[0], index=False, sep=' ')

        elif s_name[1] == "TXT File With Tab Separator (*.txt)":
            df.to_csv(s_name[0], index=False, sep='\t')

        elif s_name[1] == "CSV File (*.csv)":
            df.to_csv(s_name[0], index=False)
        else:
            df.to_excel(s_name[0], index=False)

        print("Export")


    def manual_sorting(self):
        if myDataFrame.df_1.isna().all().all() and myDataFrame.df_2.empty:
            return
        name = ["Lista punktów tabela nr 1:", "Lista punktów tabela nr 2:"]
        self.lista = ListWidget(True, left_and_right_list_name=name)
        self.lista.refresh_data.connect(self.display_data)
        self.lista.show()

    def left_data_set(self):
        if myDataFrame.df_memory.empty:
            return
        
        self.lista = ListWidget(False, "left")
        self.lista.refresh_data.connect(self.display_data)
        self.lista.show()

    def right_data_set(self):
        if myDataFrame.df_memory.empty:
            return
        
        self.lista = ListWidget(False, "right")
        self.lista.refresh_data.connect(self.display_data)
        self.lista.show()

    def reset(self):
        myDataFrame.default()
        self.display_data()

    def separation(self):
        output = myDataFrame.separation()
        if output == False:
            return
        self.display_data()

    def assign(self):
        output = myDataFrame.assign()
        if output == False:
            return
        self.display_data()

    def creat(self):
        przyrostek = self.line_przyrostek.text() or "K"
        myDataFrame.create_new_data(przyrostek)
        self.display_data()

    def calculate(self):
        myDataFrame.subtract()
        self.display_data()

    def wysokość(self):
        if self.CheckBox_wysokość.isChecked():
            self.display_data()
        else:
            self.display_data()

    def kody(self):
        if self.CheckBox_kody.isChecked():
            self.display_data()
        else:
            self.display_data()

    def display_data(self):
        myDataFrame.display_data()
        col = 17
        if not self.CheckBox_wysokość.isChecked():
            myDataFrame.drop_columns_in_df("df_all", "H", "DH")
            col -= 3

        if not self.CheckBox_kody.isChecked():
            myDataFrame.drop_columns_in_df("df_all", "SPD", "ISD", "STB")
            col -= 6

        df = myDataFrame.df_all
        df = df.fillna("")
        model = DataFrameTableModel(df)
        self.table_widget.setModel(model)

        try:
            df = myDataFrame.df_3
            if not df.empty:
                if 'DL' in df.columns:
                    df['DL'] = pd.to_numeric(df['DL'], errors='coerce')
                
                # Iterate through the data to check the column values in 'DL'
                for row_index in range(df.shape[0]):  # Iterate over rows
                    col_index = df.columns.get_loc('DL')  # Get index of 'DL' column
                    col_value = df.iloc[row_index, col_index]  # Get value in 'DL' column
                    
                    if pd.notna(col_value) and col_value > 0.14:
                        # Set background color for the item in the model
                        index = model.index(row_index, col)
                        model.setData(index, QColor(Qt.red), Qt.BackgroundRole)
        
        except Exception as e:
            logging.exception(e)
            print(e)
            pass
        self.table_widget.resizeColumnsToContents()


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                
                if url.toLocalFile().endswith(".txt") or url.toLocalFile().endswith(".csv") or url.toLocalFile().endswith(".xlsx"):
                    event.acceptProposedAction()
                    return       

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()

            self.import_win = ImportWin(self.win, None, self.dark_mode_enabled, file_path)
            self.import_win.show()

    def copy_to_clipboard(self):
        selection_model = self.table_widget.selectionModel()

        selected_indexes = selection_model.selectedIndexes()

        if not selected_indexes:
            print("No items selected.")
            return

        selected_indexes.sort(key=lambda x: (x.row(), x.column()))
        
        copied_data = ''
        previous_row = selected_indexes[0].row()
        for index in selected_indexes:
            if index.row() != previous_row:
                copied_data += '\n'
                previous_row = index.row()

            copied_data += self.table_widget.model().data(index)
            if index.column() < self.table_widget.model().columnCount() - 1:
                copied_data += '\t'  # Tab delimiter between columns

        clipboard = QApplication.clipboard()
        clipboard.setText(copied_data)

        print("copy")

    def context_menu(self, pos):
        context_menu = QMenu(self)
        copy_action = context_menu.addAction("Kopiuj")
        copy_action.triggered.connect(self.copy_to_clipboard)
        context_menu.exec(QCursor.pos())

    def GMLDefaultTable(self):
        myDataFrame.default()
        self.display_data()

    def closeEvent(self, event):
        try:
            self.import_win.close()
        except AttributeError:
            return


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window_wsp = Win_coordinate_comparison()
    window_wsp.show()
    sys.exit(app.exec())