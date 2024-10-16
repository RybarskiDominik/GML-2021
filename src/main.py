from PySide6.QtWidgets import (QApplication, QGraphicsLineItem, QMainWindow, QGraphicsItem, QFileDialog, QCheckBox,
    QTableWidget,QGraphicsEllipseItem, QTableWidgetItem, QLineEdit, QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsPolygonItem,
    QGraphicsTextItem, QProgressBar, QSplashScreen, QPushButton, QGraphicsPixmapItem, QMenu)
from PySide6.QtGui import QFont, QPolygonF, QPolygonF, QPainter, QFont, QColor, QTransform, QBrush, QPen, QIcon, QPainterPath, QPixmap, QPalette, QCursor, QKeySequence, QShortcut
from PySide6.QtCore import Signal, QSettings, Qt, QRectF, QThread
from PySide6 import QtCore, QtWidgets, QtGui
from dataclasses import dataclass
from os.path import exists
from pathlib import Path
import pandas as pd
import webbrowser
import logging
import random
import shutil
import time
import sys
import os

from obf import parser  # gml_reader return pd.DataFrame -> ['Działka', 'KW', 'Pole. pow.', 'Własność', 'udziały', 'Właściciele', 'Nazwisko', 'Drugie Imię', 'Imie ojca', 'Imie matki', 'Pesel', 'Adres', 'Adres Korespodencyjny', 'IDM', 'Status', 'JGR', 'Grupa Rejestrowa']
from obf.lista_dzialek import lista_dzialek_update  # return pd.DataFrame -> ['Działka']

from obf.dzialki import gml_działki  # return pd.DataFrame -> ['Działka', 'KW', 'Pole. pow.', 'Dokładność do:', 'Pole']
from obf.uzytki import gml_użytek  # return pd.DataFrame -> ['Działka', 'KW', 'Pole. pow.', 'Użytek', 'Pow. Użytku']
from obf.budynki import kartoteki  # return pd.DataFrame -> ['Działka', 'KW', 'Budynek', 'KŚT', 'Pole. pow.', 'Nad', 'Pod', 'Adres']

from obf.punkty_poligon import punkty_w_dzialkach  # return pd.DataFrame -> ['Działka', 'ID']
from obf.punkty import punkt_graniczny  # return pd.DataFrame -> ['ID', 'NR', 'X', 'Y', 'SPD', 'ISD','STB']

from function.copy import copy_file # Copy (*.gml) file to GML folder.

from gui.toggle import ToggleButton

from gui.settings import SettingsWindow
from module.Map import WindowMap, EmitMapW
from module.GraphicView import GraphicsView, EmitMap, MapHandler, działki_wizualizacja, działki_punkty_stabilizacja, text_wizualizacja
from module.coordinate_comparison import Win_coordinate_comparison

from model.path import PathManager
path_manager = PathManager()

if not path_manager.gml_folder_path.exists():
    try:
        path_manager.gml_folder_path.mkdir()  # Utwórz folder GML
        print(f"Utworzono folder: {path_manager.gml_folder_path}")
    except Exception as e:
        logging.exception(e)

log_file_path = path_manager.get_log_file_path()
gml_file_path = path_manager.get_gml_file_path()
xlsx_target_path = path_manager.get_xlsx_target_path()

logging.basicConfig(level=logging.INFO, filename=log_file_path, filemode="w", format="%(asctime)s - %(lineno)d - %(levelname)s - %(message)s") #INFO NOTSET
settings = QSettings('GML', 'GML Reader')


versja = "1.7.2"


@dataclass
class GlobalInterpreter:
    EPSG: str = None
    # Path to GML
    input_path: str = None
    path: str = gml_file_path # Patch do pliku *.GML

    # Dane w pliku GML
    uzytki_gml = pd.DataFrame()
    działki_gml = pd.DataFrame()
    prased_gml = pd.DataFrame()
    budynki_gml = pd.DataFrame()

    # Klasyfikacja małżeństw kolorami
    color_dict = {}

    # Check if GML is impoted. >>> False - GML nie wczytany czyli Offline bez mapy ||| True - GML wczytany ||| None - Tryb Mapa + Offline
    status: bool = False  

    # Status offline GML. >>> None - Offline || True - GML wczytany || False - GML nie wczytany
    status_osoby: bool = None
    status_budynki: bool = None
    status_działki: bool = None
    status_użytki: bool = None

    lastwindow: int = None # Ostatnie otwarte okno | GML DZIALKI UZYTKI

    clean: bool = False
    table: bool = False

    @classmethod
    def reset(cls):
        GlobalInterpreter.status_osoby: bool = None
        GlobalInterpreter.status_budynki: bool = None
        GlobalInterpreter.status_działki: bool = None
        GlobalInterpreter.status_użytki: bool = None


class WorkerMain(QThread):
    def __init__(self):
        super().__init__()
        self.pause = False
        self.kill = False

    def run(self):
        GlobalInterpreter.prased_gml, GlobalInterpreter.działki_gml = parser.gml_reader(gml_file_path)

    def kill_main(self):
        self.kill = True

    def pause_main(self):
        if self.pause:
            self.pause = False
        else:
            self.pause = True


class MyWindow(QMainWindow):
    item_signal = Signal(str)
    def __init__(self, argv_path=None):
        super(MyWindow,self).__init__()
        self.worker = None

        self.map_signal = EmitMap()
        self.map_signal.item_signal.connect(self.receive_item)

        self.settings = settings

        self.setWindowIcon(QIcon(r'gui\Stylesheets\GML.ico'))
        
        #self.setMinimumSize(1327, 430)
        self.setMinimumSize(1334, 430)
        
        if self.settings.value('FullScene', True, type=bool) == True:
            self.setWindowState(Qt.WindowMaximized)
        else:
            self.setGeometry(200, 200, 1500, 430)

        shortcut = QShortcut(QKeySequence(Qt.CTRL | Qt.Key_C), self)
        shortcut.activated.connect(self.copy_to_clipboard)

        self.init_UI()
        self.init_widget()

        if argv_path and isinstance(argv_path, str) and argv_path.endswith(".gml"):
            var = copy_file(argv_path, gml_file_path)
            if not var:
                return
            self.update_GML()

        if self.settings.value('UproszczonaMapa', True, type=bool) == True:
            try:
                self.graphic_map_view()
                #if self.settings.value('UproszczonaMapa', True, type=bool) == False:
                    #self.gview.hide()
            except Exception as e:
                logging.exception(e)

    def init_UI(self):
        obiekt = self.settings.value('Tytuł', None)
        if obiekt:
            self.setWindowTitle(obiekt)
        else:
            self.setWindowTitle("GML Reader")
        self.setAcceptDrops(True)
        fname = []
        font = QFont()
        font.setPointSize(8)  # Ustaw rozmiar czcionki na 8

        self.b1 = QtWidgets.QPushButton(self)
        self.b1.setText("Import GML")
        self.b1.setGeometry(0, 2, 70, 28)
        self.b1.clicked.connect(self.import_GML)
        self.b1.setToolTip("Wczytaj GML")

        self.button_export = QtWidgets.QToolButton(self)
        if dark_mode_enabled:
            self.button_export.setIcon(QtGui.QIcon(path_manager.get_stylesheets_path("Strzałka-export-light")))
        else:
            self.button_export.setIcon(QtGui.QIcon(path_manager.get_stylesheets_path("Strzałka-export-dark")))
        self.button_export.setIconSize(QtCore.QSize(30, 30))
        self.button_export.setGeometry(70, 2, 28, 28)
        self.button_export.clicked.connect(self.export_data)
        self.button_export.setToolTip("Export zawartości tabeli do Excela.")
        
        self.toggle_button = ToggleButton(parent=self)
        self.toggle_button.setGeometry(98, 1, 5, 2)
        self.toggle_button.clicked.connect(self.update_GML)
        self.toggle_button.setToolTip('<p>Funkcja <b>"drag and drop"</b> dla plików GML</p>'
                                      '<p style="margin: 0;"><b>Kolory oznaczają:</b></p>'
                                      '<p style="margin: 0;">-<b style="color: gray;">szary</b> tryb offline z możliwością wczytania mapy.</p>'
                                      '<p style="margin: 0;">-<b style="color: purple;">fioletowy</b> tryb offline. (Ostatni wczytany plik GML.)</p>'
                                      '<p style="margin: 0;">-<b style="color: green;">zielony</b> poprawne wczytanie pliku GML.</p>'
                                      '<p style="margin: 0;">-<b style="color: red;">czerwony</b> błąd podczas wczytywania pliku GML.</p>')

        self.myTextBox = QLineEdit(self)
        self.myTextBox.setText("")
        self.myTextBox.setReadOnly(True)
        self.myTextBox.setGeometry(148, 3, 146, 26)
        self.myTextBox.setCursorPosition(0)
        
        self.b2 = QtWidgets.QPushButton(self)
        self.b2.setText("Wyczyść!!!")
        self.b2.setGeometry(295, 2, 95, 28)
        self.b2.clicked.connect(self.clean_all)
        self.b2.setToolTip('<p>Czyści dane z tabeli.</p>'
                           '<p><b style="color: red;">*</b>Nie usuwa danych z pamięci!</p>')

        self.b_points = QtWidgets.QPushButton(self)
        self.b_points.setText("Punkty")
        self.b_points.setGeometry(682, 2, 47, 28)
        self.b_points.clicked.connect(self.punkty_w_dzialkach)
        self.b_points.setToolTip('<p>Funkcja eksportuje punkty ich wsółrzędne oraz atrybuty.</p>'
                           '<p>NR X Y SPD ISD STB</p>'
                           '<p>Eksportowane są tylko punkty w wybranej działce na liście.</p>')

        self.b_upr = QtWidgets.QPushButton(self)
        self.b_upr.setText("Upr.")
        self.b_upr.setGeometry(729, 2, 28, 28)
        self.b_upr.clicked.connect(self.punkty_w_dzialkach_uproszczone)
        self.b_upr.setToolTip('<p>Funkcja eksportuje punkty i wsółrzędne.</p>'
                           '<p>NR X Y</p>'
                           '<p>Eksportowane są tylko punkty w wybranej działce na liście.</p>')

        self.b_all = QtWidgets.QPushButton(self)
        self.b_all.setText("All")
        self.b_all.setGeometry(757, 2, 28, 28)
        self.b_all.clicked.connect(self.punkty_GML)
        self.b_all.setToolTip('<p>Funkcja eksportuje wszystkie punkty, ich wsółrzędne oraz atrybuty.</p>')

        self.por_wsp = QtWidgets.QPushButton(self)
        self.por_wsp.setText("Por.")
        if dark_mode_enabled:
            self.por_wsp.setIcon(QtGui.QIcon(path_manager.get_stylesheets_path("Exchange-light")))
        else:
            self.por_wsp.setIcon(QtGui.QIcon(path_manager.get_stylesheets_path("Exchange-dark")))
        self.por_wsp.setGeometry(790, 2, 62, 28)
        self.por_wsp.setIconSize(QtCore.QSize(24, 24))
        self.por_wsp.clicked.connect(self.por_wsp_win)
        self.por_wsp.setToolTip('Moduł umożliwiający porównanie współrzędnych.')

        self.button_settings = QtWidgets.QPushButton(self)
        if dark_mode_enabled:
            self.button_settings.setIcon(QtGui.QIcon(path_manager.get_stylesheets_path("Zębatka-light")))
        else:
            self.button_settings.setIcon(QtGui.QIcon(path_manager.get_stylesheets_path("Zębatka-dark")))
        self.button_settings.setGeometry(859, 2, 28, 28)
        self.button_settings.setIconSize(QtCore.QSize(20, 20))
        self.button_settings.clicked.connect(self.settings_menu)
        
        self.b7v2 = QtWidgets.QPushButton(self)
        self.b7v2.setText("Donate")
        self.b7v2.setGeometry(893, 3, 80, 26)
        self.b7v2.setIcon(QtGui.QIcon(path_manager.get_stylesheets_path("PayPal.svg")))
        self.b7v2.clicked.connect(self.open_edge)

        self.git = QtWidgets.QPushButton(self)
        self.git.setText("Github")
        self.git.setGeometry(973, 3, 80, 26)

        if dark_mode_enabled:
            self.git.setIcon(QtGui.QIcon(path_manager.get_stylesheets_path("Github-light")))
        else:
            self.git.setIcon(QtGui.QIcon(path_manager.get_stylesheets_path("Github-dark")))
        self.git.clicked.connect(self.open_git)

        self.b_l_m = QtWidgets.QToolButton(self)
        self.b_l_m.setText(" Mapa")
        b_l_m_font = QFont()
        #b_l_m_font.setBold(True)
        b_l_m_font.setPointSize(10)  
        self.b_l_m.setFont(b_l_m_font)
        if dark_mode_enabled:
            self.b_l_m.setIcon(QtGui.QIcon(path_manager.get_stylesheets_path("Mapa-light")))
        else:
            self.b_l_m.setIcon(QtGui.QIcon(path_manager.get_stylesheets_path("Mapa-dark")))
        self.b_l_m.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.b_l_m.setIconSize(QtCore.QSize(30, 30))
        self.b_l_m.setGeometry(1400, 0, 95, 30)
        self.b_l_m.clicked.connect(lambda: self.run_my_window_map())

        self.comboBox = QtWidgets.QComboBox(self)
        my_listComboBox = ["Wybierz Działkę."]
        self.comboBox.addItems(my_listComboBox)
        self.comboBox.setMaxVisibleItems(30)
        self.comboBox.setFont(font)
        self.comboBox.setView(QtWidgets.QListView())
        self.comboBox.setGeometry(1000, 2, 200, 26)
        self.comboBox.activated.connect(self.last_window)        
        self.comboBox.setObjectName("comboBox")
        self.comboBox.setToolTip('<p>Listę działek należy wczytać przyciskiem <b>"Wczytaj Listę."</b></p>'
                                 '<p>Listę resetuje się przyciskiem <b>"Reset"</b></p>')

        self.b9 = QtWidgets.QPushButton(self)
        self.b9.setText("Wczytaj Listę.")
        self.b9.setGeometry(1200, 0, 95, 30)
        self.b9.clicked.connect(self.comboBox_Update)
        self.b9.setToolTip('<p>Wczytanie listy działek.</p>')

        self.b10 = QtWidgets.QPushButton(self)
        self.b10.setText("Reset")
        self.b10.setGeometry(1300, 0, 95, 30)
        self.b10.clicked.connect(self.comboBox_Reset)
        self.b10.setToolTip('<p>Reset listy działek.</p>')

        '''
        self.b11 = QtWidgets.QPushButton(self)
        self.b11.setText("Import Excel!")
        self.b11.move(1600, 0)
        self.b11.clicked.connect(self.import_Excel)
        '''

        self.table_widget = QTableWidget(self)
        #self.table_widget.setFixedSize(1500, 400)
        self.table_widget.move(0, 31)
        self.table_widget.setColumnCount(16)
        self.table_widget.setRowCount(5)
        self.table_widget.setAcceptDrops(True)
        self.table_widget.setObjectName("True")
        self.table_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.context_menu)
        self.setTableHeaders()
        self.GMLTable()

    def init_widget(self):
        self.button_osoby = QtWidgets.QPushButton(self)
        self.set_botton_border(self.button_osoby)
        self.button_osoby.setText("Osoby")
        self.button_osoby.setGeometry(412, 2, 62, 26)
        self.button_osoby.clicked.connect(self.visualize_osoby)
        self.button_osoby.clicked.connect(lambda: self.reset_and_set(self.button_osoby))
        self.button_osoby.setToolTip('<p>Funkcja wczytuje wszystkie dane osobowe zawarte w pliku GML</p>'
                           '<p>Filtrowanie danych następuje poprzez wczytanie oraz wybór konkretnej dzialki</p>')

        self.button_budynki = QtWidgets.QPushButton(self)
        self.button_budynki.setText("Budynki")
        self.button_budynki.setGeometry(474, 2, 62, 26)
        self.button_budynki.clicked.connect(self.visualize_budynki)
        self.button_budynki.clicked.connect(lambda: self.reset_and_set(self.button_budynki))
        self.button_budynki.setToolTip('<p>Funkcja wczytuje kartoteki budynków na działce.</p>')

        self.button_dzialki = QtWidgets.QPushButton(self)
        self.button_dzialki.setText("Działki")
        self.button_dzialki.setGeometry(536, 2, 62, 26)
        self.button_dzialki.clicked.connect(self.visualize_dzialki)
        self.button_dzialki.clicked.connect(lambda: self.reset_and_set(self.button_dzialki))
        self.button_dzialki.setToolTip('<p>Funkcja wczytuje numer, księgę wieczystą, powierzchnię oraz oblicza powierzchnię działki uwzględniając poprawkę.</p>')

        self.button_uzytki = QtWidgets.QPushButton(self)
        self.button_uzytki.setText("Użytki")
        self.button_uzytki.setGeometry(598, 2, 62, 26) #675
        self.button_uzytki.clicked.connect(self.visualize_uzytki)
        self.button_uzytki.clicked.connect(lambda: self.reset_and_set(self.button_uzytki))
        self.button_uzytki.setToolTip('<p>Funkcja wczytuje użytki w działce</p>')

        self.set_button_styles(self.button_budynki, self.button_dzialki, self.button_uzytki)

    def set_button_styles(self, *buttons):
        for button in buttons:
            button.setStyleSheet("""
                QPushButton {
                    border: none;
                    border-bottom: none;
                }
            """)

    def set_botton_border(self, button):
        button.setStyleSheet("""
            QPushButton {
                border: none;
                border-bottom: 2px solid red;
            }
        """)

    def reset_and_set(self, selected_button):
        self.set_button_styles(self.button_osoby, self.button_budynki, self.button_dzialki, self.button_uzytki)
        self.set_botton_border(selected_button)

    def visualize_osoby(self):
        GlobalInterpreter.lastwindow = "GML"
        self.clean()
        self.table_widget.clear()
        self.setTableHeaders()
        
        if GlobalInterpreter.prased_gml.empty:
            self.myTextBox.setText('First Import GML!!!')
            self.myTextBox.setCursorPosition(0)

            self.table_widget.setRowCount(5)
            self.GMLTable()
            self.table_widget.setObjectName("True")
            self.adjustTableColumnWidth()
            return
        else:
            self.table_widget.setObjectName(None)
            prased_gml_V = GlobalInterpreter.prased_gml.copy()
            if not self.comboBox.currentText() == "Wybierz Działkę.":
                prased_gml_V = prased_gml_V[prased_gml_V['Działka'].isin([self.comboBox.currentText()])]

            prased_gml_V['Działka'] = prased_gml_V['Działka'].astype(str)
            #prased_gml_V.reset_index(drop=True, inplace=True)
            try:
                prased_gml_V.fillna('',inplace=True)
            except:
                prased_gml_V
            for r in range(len(prased_gml_V['Działka'])):
                self.table_widget.insertRow(r)
                for k in range(17):
                    self.table_widget.setItem(r, k, QTableWidgetItem(str(prased_gml_V.iloc[r, k])))
            self.table_widget.resizeColumnsToContents() #setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        
        self.color_duplicates_pastel(self.table_widget, column_index=13)

    def visualize_budynki(self):
        GlobalInterpreter.lastwindow = "BUDYNKI"
        self.clean()
        self.table_widget.clear()
        self.setBudynkiHeaders()

        if GlobalInterpreter.status_budynki == None or GlobalInterpreter.status_budynki == True:
            try:
                df_budynki = pd.DataFrame(kartoteki(gml_file_path))  # path_dz
                GlobalInterpreter.budynki_gml = df_budynki
                GlobalInterpreter.status_budynki = False
            except:
                self.message("Error działki!", "#ab2c0c")
                return
        else:
            df_budynki = GlobalInterpreter.budynki_gml.copy()

        if GlobalInterpreter.status is False:
            self.message("Offline.", "#975D9F")
        if GlobalInterpreter.status is None:
            self.message("Offline.")

        df_budynki = df_budynki.copy()
        if not self.comboBox.currentText() == "Wybierz Działkę.":
            df_budynki = df_budynki[df_budynki['Działka'].isin([self.comboBox.currentText()])]
        
        duplicates = df_budynki.duplicated(subset=['Działka', 'KW'], keep='first')
        df_budynki.loc[duplicates, ['Działka', 'KW']] = ''

        try:
            df_budynki.fillna('',inplace=True)
        except:
            pass

        for r in range(len(df_budynki['Działka'])):
            self.table_widget.insertRow(r)
            for k in range(8):
                self.table_widget.setItem(r, k, QTableWidgetItem(str(df_budynki.iloc[r, k])))
        self.table_widget.resizeColumnsToContents()

    def visualize_dzialki(self):
        GlobalInterpreter.lastwindow = "DZIALKI"
        self.clean()
        self.table_widget.clear()
        self.setDzialkiHeaders()

        if GlobalInterpreter.status_działki == None or GlobalInterpreter.status_działki == True:
            try:
                df_działki = pd.DataFrame(gml_działki(gml_file_path))  # path_dz
                GlobalInterpreter.działki_gml = df_działki
                GlobalInterpreter.status_działki = False
                #self.message("Offline.", "#686868")
            except:
                self.message("Error działki!", "#ab2c0c")
                return
        else:
            df_działki = GlobalInterpreter.działki_gml.copy()
        
        if GlobalInterpreter.status is False:
            self.message("Offline.", "#975D9F")
        if GlobalInterpreter.status is None:
             self.message("Offline.")

        df_działki = df_działki.copy()
        if not self.comboBox.currentText() == "Wybierz Działkę.":
            df_działki = df_działki[df_działki['Działka'].isin([self.comboBox.currentText()])]
        
        try:
            df_działki.fillna('',inplace=True)
        except:
            df_działki

        for r in range(len(df_działki['Działka'])):
            self.table_widget.insertRow(r)
            for k in range(5):
                self.table_widget.setItem(r, k, QTableWidgetItem(str(df_działki.iloc[r, k]))) #(działki_gml.loc[r][k])
        #self.table_widget.setColumnCount(3)
        self.table_widget.resizeColumnsToContents()

    def visualize_uzytki(self):
        GlobalInterpreter.lastwindow = "UZYTKI"
        self.clean()
        self.table_widget.clear()
        self.setUzytkiHeaders()

        if GlobalInterpreter.status_użytki == None or GlobalInterpreter.status_użytki == True:
            try:
                df_uzytki = pd.DataFrame(gml_użytek(gml_file_path))  # path_U
                GlobalInterpreter.uzytki_gml = df_uzytki
                GlobalInterpreter.status_użytki = False
            except Exception as e:
                logging.exception(e)
                self.message("Error Użytki!", "#ab2c0c")
                return
        else:
            df_uzytki = GlobalInterpreter.uzytki_gml.copy()

        if GlobalInterpreter.status is False:
            self.message("Offline.", "#975D9F")
        if GlobalInterpreter.status is None:
            self.message("Offline.")

        df_uzytki = df_uzytki.copy()
        if self.comboBox.currentText() != "Wybierz Działkę.":
            df_uzytki = df_uzytki[df_uzytki['Działka'].isin([self.comboBox.currentText()])]

        duplicates = df_uzytki.duplicated(subset=['Działka', 'KW', 'Pole. pow.'], keep='first')
        df_uzytki.loc[duplicates, ['Działka', 'KW', 'Pole. pow.']] = ''

        try:
            df_uzytki.fillna('',inplace=True)
        except Exception as e:
            print(f"Error occurred during fillna operation: {e}")

        for r in range(len(df_uzytki.index)):   #len(uzytki_dzialek['Działka'])): #len(uzytki_dzialek.index):
            self.table_widget.insertRow(r)
            for k in range(5):
                self.table_widget.setItem(r, k, QTableWidgetItem(str(df_uzytki.iloc[r, k])))

        self.table_widget.resizeColumnsToContents()

    def import_GML(self):
        fname = QFileDialog.getOpenFileName(self, 'open file', os.path.expanduser("~/Desktop"), 'GML File(*.gml)')
        
        GlobalInterpreter.Input_Path = fname[0]

        try:
            obiekt = (f"GML Readere   Obiekt: {os.path.splitext(os.path.basename(GlobalInterpreter.Input_Path))[0]}")
            self.setWindowTitle(obiekt)
            self.settings.setValue("Tytuł", obiekt)
        except Exception as e:
            logging.exception(e)

        if fname == ('', ''):
            return
        else:
            try:
                copy_file(fname[0], gml_file_path)
            except Exception as e:
                logging.exception(e)
                self.result_output("Parse GML Error!", "#ab2c0c")
                return
            try:
                S = time.perf_counter()
                GlobalInterpreter.prased_gml, GlobalInterpreter.działki_gml = parser.gml_reader(fname[0])
                E = time.perf_counter()
                print(f"{E-S:.4}")
            except Exception as e:
                logging.exception(e)
                self.result_output("GML Reader Error!", "#ab2c0c")
                return
            
            if GlobalInterpreter.status is None and self.settings.value('UproszczonaMapa', True, type=bool) == True:
                self.refresh_map_view()
            
            GlobalInterpreter.reset()
            GlobalInterpreter.status = True
            
            self.result_output("GML wczytany.", "#77C66E")
        
        self.last_window()
        
        return fname[0]
    
    def update_GML(self):
        try:
            S = time.perf_counter()
            GlobalInterpreter.prased_gml, GlobalInterpreter.działki_gml = parser.gml_reader(gml_file_path)
            E = time.perf_counter()
            print(f"{E-S:.4}")
        except Exception as e:
            logging.exception(e)
            print(e)
            self.result_output("GML Reader Error!", "#ab2c0c")
            return
        

        if GlobalInterpreter.status is None and self.settings.value('UproszczonaMapa', True, type=bool) == True:
                self.refresh_map_view()
        
        GlobalInterpreter.reset()
        GlobalInterpreter.status = True
        
        self.result_output("GML wczytany!!!", "#77C66E")
        ToggleButton.updateIndicatorColor(self.toggle_button, QColor("#77C66E")) #FFD700    
        
        GlobalInterpreter.input_path = gml_file_path

        self.last_window()

    def run_qtreat(self):
        try:
            S = time.perf_counter()
            if self.worker is not None and self.worker.isRunning():
                self.result_output("Please wait", "#FFD700")
                return
            self.worker = WorkerMain()
            self.worker.finished.connect(self.on_worker_finished)
            self.worker.start()
            E = time.perf_counter()
            print(f"{E-S:.4}")
        except Exception as e:
            logging.exception(e)
            print(e)
            self.result_output("GML Reader Error!", "#ab2c0c")
            return

    def on_worker_finished(self):
        self.worker = None

    def export_data(self):
        #s_name = QFileDialog.getSaveFileName(self, 'select a file', os.path.expanduser("~/Desktop"), 'Excel File(*.xlsx)')
        s_name = QFileDialog.getSaveFileName(self, 'select a file', os.path.expanduser("~/Desktop"),'Excel File(*.xlsx);;TXT File (*.txt);;TXT File With Tab Separator (*.txt);;CSV File (*.csv)')

        if s_name == ('', ''):
            return
        else:
            columnHeaders = []

            # create column header list
            for j in range(self.table_widget.model().columnCount()):
                columnHeaders.append(self.table_widget.horizontalHeaderItem(j).text())

            df = pd.DataFrame(columns=columnHeaders)

            # create dataframe object recordset
            for row in range(self.table_widget.rowCount()):
                for col in range(self.table_widget.columnCount()):
                    df.at[row, columnHeaders[col]] = self.table_widget.item(row, col).text()

            if s_name[1] == "Excel File(*.xlsx)":
                df.to_excel(s_name[0], index=True)
            
            if s_name[1] == "TXT File (*.txt)":
                df.to_csv(s_name[0], index=False, sep=' ')

            elif s_name[1] == "TXT File With Tab Separator (*.txt)":
                df.to_csv(s_name[0], index=False, sep='\t')

            elif s_name[1] == "CSV File (*.csv)":
                df.to_csv(s_name[0], index=False)
            else:
                df.to_excel(s_name[0], index=True)

            print("Export")


    def last_window(self):
        if GlobalInterpreter.lastwindow == "GML":
            self.visualize_osoby()
        elif GlobalInterpreter.lastwindow == "BUDYNKI":
            self.visualize_budynki()
        elif GlobalInterpreter.lastwindow == "DZIALKI":
            self.visualize_dzialki()
        elif GlobalInterpreter.lastwindow == "UZYTKI":
            self.visualize_uzytki()
        else:
            self.visualize_osoby()
        self.myTextBox.setText(self.comboBox.currentText())

    def settings_menu(self):
        self.sett = SettingsWindow(dark_mode_enabled, versja)
        self.sett.show()

    def por_wsp_win(self):
        self.win_wsp = Win_coordinate_comparison(dark_mode_enabled)
        self.win_wsp.show()


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustTableColumnWidth()
        self.adjustButtons()

        if self.settings.value('UproszczonaMapa', True, type=bool) == True:
            self.adjustGview()

    def adjustTableColumnWidth(self):
        table_width = self.width()

        self.table_widget.setFixedSize(table_width, 400)

        column_count = self.table_widget.columnCount()
        column_width = table_width // column_count
        
        table_name = self.table_widget.objectName()

        if table_name == "True":
            for column in range(column_count):
                self.table_widget.setColumnWidth(column, column_width)
        #self.table_widget.resizeColumnsToContents()        

    def adjustButtons(self):
        button_width = 80
        spacing = 0  # Adjust the spacing between buttons if needed
        right_edge = self.width()

        self.b_l_m.setGeometry((right_edge - button_width - spacing + 5), 2, button_width - 5, 28)  # Mapa
        self.b10.setGeometry(right_edge - 2 * (button_width + spacing), 2, button_width - 15, 28)  # Reset
        self.b9.setGeometry(right_edge - 3 * (button_width + spacing), 2, button_width, 28)  # Lista działek.
        self.comboBox.setGeometry(right_edge - 440, 3, 200, 26)

    def adjustGview(self):
        move = 100
        self.gview.setGeometry(self.width()/2 - move, 432, self.width()/2 + move, self.height() - 432)


    def import_Excel(self):
        file_exists = exists(sys.path[0] + "\\GML\\GML.xlsx")
        if file_exists == False:
            self.myTextBox.setText('First Import GML!!!')
            self.myTextBox.setCursorPosition(0)
            return
        else:
            df = pd.read_excel(sys.path[0] + "\\GML\\GML.xlsx")
            if df.size == 0:
                return

            #df.fillna('', inplace=True)

            self.table_widget.setRowCount(df.shape[0])
            self.table_widget.setColumnCount(df.shape[1])
            self.table_widget.setHorizontalHeaderLabels(df.columns)
            
            # returns pandas array object
            for row in df.iterrows():
                values = row[1]
                for col_index, value in enumerate(values):
                    if isinstance(value, (float, int)):
                        value = '{0:0.0f}'.format(value)
                    tableItem = QTableWidgetItem(str(value))
                    self.table_widget.setItem(row[0], col_index, tableItem)

            self.myTextBox.setText('Excel imported!!!')
            self.myTextBox.setCursorPosition(0)
            self.myTextBox.setText('Excel imported!!!')
            self.myTextBox.setCursorPosition(0)

    def GMLTable(self):  # Wprowadź dane do tabeli
        for row in range(5):
            for column in range(16):
                item = QTableWidgetItem("Wczytaj GML")
                self.table_widget.setItem(row, column, item)

    def run_my_window_map(self):
        if GlobalInterpreter.input_path == None:
            self.myTextBox.setText('First Import GML!!!')
            self.myTextBox.setCursorPosition(0)
            self.myTextBox.setStyleSheet("")
        else:
            try:
                self.window = WindowMap(GlobalInterpreter.input_path, GlobalInterpreter.prased_gml, xlsx_target_path)
                #self.map_sig = EmitMapW()
                #self.map_sig.item_signal.connect(self.receive_item)
                self.window.item_signal.connect(self.receive_item)
                self.window.show()
            except Exception as e:
                logging.exception(e)
                self.myTextBox.setText('Error on open Map!!!')
                self.myTextBox.setCursorPosition(0)
                self.myTextBox.setStyleSheet("background-color: #EEAA99")
                print(e)

    def comboBox_Reset(self):
        self.comboBox.clear()
        self.comboBox.addItem("Wybierz Działkę.")

    def comboBox_Update(self):
        if GlobalInterpreter.działki_gml.empty:
            lista_dzialek = lista_dzialek_update(gml_file_path)  # Path
            działki_gml_list = lista_dzialek['Działka']
            self.message("Offline!", "#975D9F")
        else:
            działki_gml_list = GlobalInterpreter.działki_gml['Działka'].copy()

        self.comboBox_Reset()
        działki_gml_list.reset_index(drop=True, inplace=True)
        działki_gml_list.fillna('',inplace=True)
        lists = działki_gml_list.values.tolist()
        self.comboBox.addItems(lists)

    def punkty_GML(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly  # Optionally, set options as needed
        fname_p = QFileDialog.getSaveFileName(None, "Save File", os.path.expanduser("~/Desktop"), "Text Files (*.txt);;All Files (*)", options=options)        
        if fname_p[0] == '':
            self.message("Nie wybrano ścieżki.", '')
            return
        try:
            PunktyGr = punkt_graniczny(gml_file_path)  # Path
            PunktyGr.drop('ID', axis=1, inplace=True)
            PunktyGr['X'] = pd.to_numeric(PunktyGr['X'], errors='coerce')
            PunktyGr['Y'] = pd.to_numeric(PunktyGr['Y'], errors='coerce')

            if self.settings.value('FullID', False, type=bool) == True:
                pass
            else:
                PunktyGr['NR'] = PunktyGr['NR'].str.rsplit('.', n=1).str.get(-1)
            PunktyGr['NR'].fillna('Brak Punktu.', inplace=True)

        except:
            self.message("Error Punkty!", "#ab2c0c")
            return
        PunktyGr.to_csv(fname_p[0], sep=' ', index=False)

    def punkty_w_dzialkach(self):
        if self.comboBox.currentText() == "Wybierz Działkę.":
            self.message("Wybierz działkę!", 'Red')
            return

        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly  # Optionally, set options as needed
        fname_p = QFileDialog.getSaveFileName(None, "Save File", os.path.expanduser("~/Desktop"), "Text Files (*.txt);;All Files (*)", options=options)        
        if fname_p[0] == '':
            self.message("Nie wybrano ścieżki.", '')
            return
        try:
            df_działki = punkty_w_dzialkach(gml_file_path)  # >>> Dzialka + ID Path
            df_punkty = punkt_graniczny(gml_file_path)  # Path
            df_punkty_działki = df_działki.merge(df_punkty, how = 'outer', on=['ID'])
            df_punkty_działki.drop('ID', axis=1, inplace=True)
        except Exception as e:
            logging.exception(e)
            self.message("Error Punkty!", "#ab2c0c")
            return
        
        if not self.comboBox.currentText() == "Wybierz Działkę.":
            df_punkty_działki = df_punkty_działki[df_punkty_działki['Działka'].isin([self.comboBox.currentText()])]
            df_punkty_działki.drop('Działka', axis=1, inplace=True)
        else:
            self.message("Wybierz działkę!", '')
            return
        
        df_punkty_działki['X'] = pd.to_numeric(df_punkty_działki['X'], errors='coerce')
        df_punkty_działki['Y'] = pd.to_numeric(df_punkty_działki['Y'], errors='coerce')
        df_punkty_działki['X'] = df_punkty_działki['X'].map('{:.2f}'.format)
        df_punkty_działki['Y'] = df_punkty_działki['Y'].map('{:.2f}'.format)
        
        #df_punkty_działki['NR'] = df_punkty_działki['NR'].str.rsplit('.', 1).str[1]
        if self.settings.value('FullID', False, type=bool) == True:
            pass
        else:
            df_punkty_działki['NR'] = df_punkty_działki['NR'].str.rsplit('.', n=1).str.get(-1)
        df_punkty_działki['NR'].fillna('Brak Punktu.', inplace=True)
        #df_punkty_działki['ISD'] = df_punkty_działki['ISD'].replace('', '-')
        df_punkty_działki.to_csv(fname_p[0], sep=' ', index=False)
        return df_punkty_działki

    def punkty_w_dzialkach_uproszczone(self):
        if self.comboBox.currentText() == "Wybierz Działkę.":
            self.message("Wybierz działkę!", 'Red')
            return

        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly  # Optionally, set options as needed
        fname_p = QFileDialog.getSaveFileName(None, "Save File", os.path.expanduser("~/Desktop"), "Text Files (*.txt);;All Files (*)", options=options)        
        if fname_p[0] == '':
            self.message("Nie wybrano ścieżki.", '')
            return
        try:
            df_działki = punkty_w_dzialkach(gml_file_path)  # >>> Dzialka + ID Path
            df_punkty = punkt_graniczny(gml_file_path) # Path
            df_punkty_działki = df_działki.merge(df_punkty, how = 'outer', on=['ID'])
        except Exception as e:
            logging.exception(e)
            self.message("Error Punkty!", "#ab2c0c")
            return
        if not self.comboBox.currentText() == "Wybierz Działkę.":
            df_punkty_działki = df_punkty_działki[df_punkty_działki['Działka'].isin([self.comboBox.currentText()])]
        else:
            self.message("Wybierz działkę!", '')
            return
        df_punkty_działki['X'] = pd.to_numeric(df_punkty_działki['X'], errors='coerce')
        df_punkty_działki['Y'] = pd.to_numeric(df_punkty_działki['Y'], errors='coerce')

        df_punkty_działki['X'] = df_punkty_działki['X'].map('{:.2f}'.format)
        df_punkty_działki['Y'] = df_punkty_działki['Y'].map('{:.2f}'.format)
        if self.settings.value('FullID', False, type=bool) == True:
            pass
        else:
            df_punkty_działki['NR'] = df_punkty_działki['NR'].str.rsplit('.', n=1).str.get(-1)
        df_punkty_działki['NR'].fillna('Brak Punktu/WSP.', inplace=True)
        df_punkty_działki = df_punkty_działki[['NR', 'X', 'Y']]
        df_punkty_działki.to_csv(fname_p[0], sep=' ', index=False)

    def clean(self):
        for i in range(self.table_widget.rowCount()):
            self.table_widget.removeRow(0)
        self.myTextBox.setStyleSheet("")

    def clean_all(self):
        table_name = self.table_widget.objectName()
        #print(table_name)
        if table_name == "True" or table_name == "":
            self.table_widget.setObjectName("True")
            self.adjustTableColumnWidth()

        self.comboBox.setItemText(0, "Wybierz Działkę.")
        MainWindow.myTextBox.setText("")
        for i in range(self.table_widget.rowCount()):
            self.table_widget.removeRow(0)
            self.myTextBox.setStyleSheet("")
   
    def open_edge(self):
        url = "https://www.paypal.com/donate/?hosted_button_id=DVJJ5QVHCN2X6"
        try:  # Spróbuj otworzyć w domyślnej przeglądarce
            webbrowser.open(url)
        except webbrowser.Error:  # Jeśli wystąpi błąd, np. brak dostępnej przeglądarki, otwórz w Edge
            edge_path = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"  # Ścieżka do exe Edge'a na Windows, dostosuj ją do swojego środowiska
            webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path), 1)
            webbrowser.get('edge').open(url)

    def open_git(self):
        url = "https://github.com/RybarskiDominik/GML-2021"
        try:  # Spróbuj otworzyć w domyślnej przeglądarce
            webbrowser.open(url)
        except webbrowser.Error:  # Jeśli wystąpi błąd, np. brak dostępnej przeglądarki, otwórz w Edge
            edge_path = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"  # Ścieżka do exe Edge'a na Windows, dostosuj ją do swojego środowiska
            webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path), 1)
            webbrowser.get('edge').open(url)

    def closeEvent(self, event):
        try:
            self.window.close()
        except AttributeError:
            return

    def color_duplicates_pastel(self, tableWidget, column_index):
        
        data = []

        for row in range(tableWidget.rowCount()):
            item = tableWidget.item(row, column_index)
            data.append(item.text() if item is not None else "")  # Sprawdź, czy komórka jest pusta

        unique_values = set()  # color_map = {}
        for value in data:
            if value != "":
                if value in unique_values:
                    if value in GlobalInterpreter.color_dict:
                        unique_color = GlobalInterpreter.color_dict[value]
                    else:
                        unique_color = self.generate_pastel_color()
                        GlobalInterpreter.color_dict[value] = unique_color

                    for row in range(tableWidget.rowCount()):
                        item = tableWidget.item(row, column_index)
                        if item is not None and item.text() == value:
                            item.setBackground(unique_color)
                else:
                    unique_values.add(value)

    def generate_pastel_color(self):
        while True:
            r = random.randint(150, 255)
            g = random.randint(150, 255)
            b = random.randint(150, 255)
            if r + g + b > 650:  # Check if the color is not too close to white
                continue
            return QColor(r, g, b)

    def setTableHeaders(self):
        self.table_widget.setColumnCount(16)
        # Ustaw nagłówki kolumn
        column_headers = ['Działka', 'KW', 'Pole pow.', 'Własność', 'udziały',
                          	'Właściciele', 'Nazwisko', 'Drugie Imię', 'Imie ojca',
                            'Imie matki', 'Pesel', 'Adres', 'Adres Korespodencyjny',
                            'IDM', 'Status', 'JGR', 'Grupa Rejestrowa', 'Działka', 'KW']
        self.table_widget.setHorizontalHeaderLabels(column_headers)

    def setBudynkiHeaders(self):
        self.table_widget.setObjectName("False")

        self.table_widget.setColumnCount(8)
        # Ustaw nagłówki kolumn
        
        column_headers = ["Działka", "KW", "Budynek", "KŚT", "Pole. pow.", "Nad", "Pod", "Adres"]
        self.table_widget.setHorizontalHeaderLabels(column_headers)

    def setDzialkiHeaders(self):
        self.table_widget.setObjectName("False")

        self.table_widget.setColumnCount(5)
        # Ustaw nagłówki kolumn
        
        column_headers = ['Działka', 'KW', 'Pow.', 'Dokł. do', "Obl. pow. z poprawką"]
        self.table_widget.setHorizontalHeaderLabels(column_headers)

    def setUzytkiHeaders(self):
        self.table_widget.setObjectName("False")
        
        self.table_widget.setColumnCount(5)
        
        # Ustaw nagłówki kolumn
        column_headers = ['Działka', 'KW', 'Pow.', 'Rodzaj', 'Pow. Użytku']
        self.table_widget.setHorizontalHeaderLabels(column_headers)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()  # Pobierz listę URL-ów przeciąganych plików
            for url in urls:
                
                if url.toLocalFile().endswith(".gml"):  # Sprawdź, czy rozszerzenie pliku to ".gml"
                    event.acceptProposedAction()
                    return       

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            print(f'Dropped GML file: {file_path}')
            GlobalInterpreter.input_path = file_path
            copy_file(file_path, gml_file_path)

            try:
                obiekt = (f"GML Readere   Obiekt: {os.path.splitext(os.path.basename(GlobalInterpreter.input_path))[0]}")
                self.setWindowTitle(obiekt)
                self.settings.setValue("Tytuł", obiekt)
            except Exception as e:
                logging.exception(e)
                pass

            self.result_output("Offline.", "#686868")
            
            GlobalInterpreter.reset()
            GlobalInterpreter.status = None

    def message(self, Text = None, color = "#686868"): #message
        try:
            self.myTextBox.setText(Text)
            self.myTextBox.setCursorPosition(0)
            self.myTextBox.setStyleSheet(f'background-color: {color}')
        except Exception as e:
            logging.exception(e)

    def result_output(self, Text = None, color = "#686868"):  # green -> "#77C66E" | red -> "#ab2c0c" | purple -> "#975D9F" | black -> "#686868"
        try:
            if self.toggle_button.isChecked():
                self.toggle_button.setChecked(False)
            else:
                self.toggle_button.setChecked(True)
            ToggleButton.updateIndicatorColor(self.toggle_button, QColor(color)) #FFD700
        except Exception as e:
            logging.exception(e)

        try:
            self.myTextBox.setText(Text)
            self.myTextBox.setCursorPosition(0)
            self.myTextBox.setStyleSheet(f'background-color: {color}')
        except Exception as e:
            logging.exception(e)

    def receive_item(self, id=None):
        MainWindow.comboBox_Reset()
        MainWindow.comboBox.setItemText(0, id)
        MainWindow.myTextBox.setText(id)

        MainWindow.last_window()

        print(f"Receive {id}.")


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


    def load_visualizations(self):
        """Function to load visualizations into the scene."""
        try:
            działki_wizualizacja(self.scene, GlobalInterpreter.path)
        except Exception as e:
            logging.exception("Error during działki_wizualizacja: %s", e)
            print(e)

        try:
            text_wizualizacja(self.scene, GlobalInterpreter.path)
        except Exception as e:
            logging.exception("Error during text_wizualizacja: %s", e)
            print(e)

        try:
            działki_punkty_stabilizacja(self.scene, GlobalInterpreter.path)
        except Exception as e:
            logging.exception("Error during działki_punkty_stabilizacja: %s", e)
            print(e)
        self.remove_gfs_file()

    def graphic_map_view(self):
        self.scene = QGraphicsScene()

        # Load visualizations
        if self.settings.value('UproszczonaMapa', True, type=bool) == True:
            self.load_visualizations()

        self.gview = GraphicsView(self)
        self.gview.setStyleSheet("""
                                 QGraphicsView {
                                 border: none;
                                 background-color: #e0e0e0;
                                 }""")
        self.gview.setScene(self.scene)
        self.gview.setGeometry(800, 432, 1120, 590)
        
        # Expand the scene rect
        expanded_scene_rect = self.scene.sceneRect().adjusted(-1000, -1000, 1000, 1000)
        self.scene.setSceneRect(expanded_scene_rect)
        self.gview.setSceneRect(expanded_scene_rect)

    def clean_map_view(self):
        self.scene.clear()

    def refresh_map_view(self):
        """Refresh the visualizations and update the viewport."""
        
        self.scene.clear()
        self.load_visualizations()

        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        expanded_scene_rect = self.scene.sceneRect().adjusted(-1000, -1000, 1000, 1000)
        
        self.gview.setSceneRect(expanded_scene_rect)
        
        self.gview.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def remove_gfs_file(self):
        try:
            root, ext = os.path.splitext(GlobalInterpreter.path)
            os.remove(root + ".gfs")
            #print(root + ".gfs")
        except Exception as e:
            logging.exception(e)
            print("GFS file not removed.")
    
    def find_parcel_in_geoportal(self):
        MapHandler.find_polygon_in_web(self)


if __name__ == '__main__':
    app = QApplication( sys.argv )

    argv_path = None
    if len(sys.argv) > 1:
        argv_path = sys.argv[1]

    dark_mode_enabled = settings.value('DarkMode', False, type=bool)

    try:
        if dark_mode_enabled:
            app.setStyleSheet(Path(path_manager.get_stylesheets_folder_path('Darkmode.qss')).read_text())
        else:
            app.setStyleSheet("""
            QGraphicsView {
                border: none;
                background: transparent;
            }
            """)
    except Exception as e:
            logging.exception(e)
            print(e)

    MainWindow = MyWindow(argv_path)
    MainWindow.show()
    sys.exit(app.exec())