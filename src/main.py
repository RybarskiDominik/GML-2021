from PySide6.QtWidgets import (QApplication, QGraphicsLineItem, QMainWindow,
                               QGraphicsItem, QFileDialog, QCheckBox, QTableWidget,
                               QGraphicsEllipseItem, QTableWidgetItem, QLineEdit,
                               QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
                               QGraphicsPolygonItem, QGraphicsTextItem, QSpacerItem,
                               QProgressBar, QSplashScreen, QSizePolicy, QPushButton,
                               QGraphicsPixmapItem, QMenu, QSplitter, QStatusBar,
                               QMainWindow, QWidget, QTextEdit, QPushButton, QGridLayout,
                               QSplitter, QFrame, QVBoxLayout, QHBoxLayout, QLabel)
    
from PySide6.QtGui import (QFont, QPolygonF, QPolygonF, QPainter, QFont, QColor, QTransform,
                           QBrush, QPen, QIcon, QPainterPath, QPixmap, QPalette, QCursor,
                           QKeySequence, QShortcut)
from PySide6.QtCore import Signal, QSettings, Qt, QRectF, QThread, QByteArray, Qt, QTimer, Slot
from PySide6 import QtCore, QtWidgets, QtGui
from dataclasses import dataclass
from os.path import exists
from pathlib import Path
import pandas as pd
import unicodedata
import webbrowser
import logging
import random
import shutil
import time
import sys
import os

from processing.punkty_poligon import punkty_w_dzialkach  # return pd.DataFrame -> ['Działka', 'ID']
from processing.punkty import punkt_graniczny  # return pd.DataFrame -> ['ID', 'NR', 'X', 'Y', 'SPD', 'ISD','STB']

from module.log_window import LogWindow

from function.file_operations import copy_file # Copy (*.gml) file to APP folder.

from gui.toggle import ToggleButton

from gui.settings import SettingsWindow
from deprecated_function.Map import WindowMap, EmitMapW
from module.coordinate_comparison import Win_coordinate_comparison

from map_view.MapGraphicView import QDMGraphicsView, EmitMap, MapHandler, data
from map_view.GraphicView_list import DraggableItemFrame
from GML_processing.GML_processing_by_ET_Main_obf import GMLParser

from module.DOCX import DOCX
from module.GML_Handler import GML_Handler
from module.KW.KW_Handler import KW_Handler
from module.Raster_handler import Raster_handler

from FileManager.FileManager import file_manager
from E_operat.e_operat import e_operat

#file_manager = FileManager()
#file_manager.reset_docx_path()  # Reset docx path to default.
#file_manager.reset_workspace_path()  # Reset workspace to default path.
#file_manager.print_info()
#file_manager.check_workspace_structure()

gml_file_path = file_manager.gml_file_path
data_base_file_path = file_manager.data_base_file_path
xlsx_target_path = file_manager.xlsx_target_path


logging.basicConfig(level=logging.NOTSET, filename=file_manager.log_file_path, filemode="w", format="%(asctime)s - %(lineno)d - %(levelname)s - %(message)s") #INFO NOTSETManager
settings = QSettings('GML', 'GML Reader')


VERSION = "2.1.1"


class MyWindow(QMainWindow):
    item_signal = Signal(str)
    kw_signal = Signal(str)
    parcelHighlightRequested = Signal(str)
    def __init__(self, argv_path=None):
        super().__init__()
        self.settings = settings
        self.gml = GMLParser()

        self.log_window = LogWindow(self)
        file_manager.logger_info()

        self._setup_window()
        self._init_state()
        self._setup_shortcuts()
        
        # Initialize UI
        self.init_ui()
        self.init_frames()
        self.init_function_btn()

        self.init_widget()
        self.init_MainButton()
        self._setup_icons()

        self.init_status_bar()

        self._restore_previous_session(argv_path)
        self.signal_and_slot_connections()

        logging.debug(file_manager.base_path)
        logging.debug("Initialize MAIN APP completed.")

    def _init_state(self):
        self.input_gml_path: str = None
        self.color_dict = {}
        self.path_to_gml: str = gml_file_path
        self.prased_gml = pd.DataFrame()
        self.lastwindow: int = None # Ostatnie otwarte okno | GML DZIALKI UZYTKI PUNKTY

    def _setup_window(self):
        self.setWindowIcon(QIcon(r'gui\Stylesheets\GML.ico'))
        self.setMinimumSize(1334, 430)
        self.setAcceptDrops(True)
        if self.settings.value('FullScreen', True, type=bool):
            self.setWindowState(Qt.WindowMaximized)

    def _setup_shortcuts(self):
        shortcut = QShortcut(QKeySequence(Qt.CTRL | Qt.Key_C), self)
        shortcut.activated.connect(self.copy_to_clipboard)

    def _restore_previous_session(self, argv_path):
        if data_base_file_path.exists() and self.settings.value('LastGML', True, type=bool):
            self.import_dataframe_on_start()
            self.last_window()
        else:
            self.GMLTable()

        try:
            self.init_graphic_map_view()
            self.init_map_button()
            self.setMinimumSize(1334, 632)
        except Exception as e:
            logging.exception(e)
            print(e)

        if argv_path and isinstance(argv_path, str) and argv_path.endswith(".gml"):
            if copy_file(argv_path, gml_file_path):
                self.import_GML()

        self.restore_splitter_state()

    # Signal and slot.
    def signal_and_slot_connections(self):
        self.map_signal = EmitMap()
        self.map_signal.item_signal.connect(self.receive_item)

        self.r_handler.update_statusbar.connect(self.update_statusBar)
        self.r_handler.update_statusbar_timeout.connect(self.clear_status)

        # Połączenie sygnałów i slotów
        self.gml_handler.turn_on_polygon_selection_signal.connect(self.map_handler.turn_on_polygon_selection_slot)
        self.gml_handler.find_polygons_signal.connect(self.map_handler.find_polygons_slot)
        self.gml_handler.find_overlap_polygons_signal.connect(self.map_handler.find_overlap_polygons_slot)
        
        # Obsługa wyników gml
        self.map_handler.gml_handler = self.gml_handler  # Przekazanie instancji GML_Handler do MapHandler
        self.gml_handler.polygons_found.connect(self.gml_handler.handle_polygons_found)
        self.gml_handler.overlap_polygons_found.connect(self.gml_handler.handle_overlap_polygons_found)

        self.docx_gui.table_model.send_dict.connect(self.gml_handler.receve_table_content)

        self.r_handler.raster_signal.connect(self.map_handler.add_tiff)

        self.r_handler.search_in_map.connect(self.activate_position_selection)
        # Połączenie sygnału wyboru punktu z funkcją obsługi w Raster_handler
        self.map_handler.gview.position_clicked.connect(self.r_handler.get_raster_from_WMS)
        self.parcelHighlightRequested.connect(self.map_handler.gview.highlight_parcel_by_id)

    def activate_position_selection(self):
        self.map_handler.gview.selecting_position = True

    # Init function frame.
    def init_ui(self):
        # Central Widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Main Layout
        self.main_layout = QGridLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setVerticalSpacing(0)

        # Button Widget and Layout
        self.button_widget = QWidget(self)
        self.button_layout = QHBoxLayout(self.button_widget)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(0)
        self.main_layout.addWidget(self.button_widget, 0, 0, 1, 1)

        # Table Widget and Layout
        self.table_widget = QWidget(self)
        self.table_layout = QVBoxLayout(self.table_widget)
        self.table_layout.setContentsMargins(0, 0, 0, 0)

        # Map Widget and Layout
        self.map_widget = QWidget(self)
        self.map_layout = QGridLayout(self.map_widget)
        self.map_layout.setContentsMargins(0, 0, 0, 0)
        self.map_layout.setSpacing(0)

        # Function Widget and Layout
        self.function_widget = QWidget(self)
        self.function_layout = QVBoxLayout(self.function_widget)
        self.function_layout.setContentsMargins(0, 0, 0, 0)
        self.function_layout.setSpacing(0)

        # Vertical Splitter
        self.vertical_splitter = QSplitter(Qt.Vertical)
        self.vertical_splitter.splitterMoved.connect(self.onSplitterMoved)
        self.vertical_splitter.setHandleWidth(5)
        self.vertical_splitter.setStyleSheet("""
                                    QSplitter::handle {
                                        background-color: #9b59b6;
                                    }
                                    """)
        self.vertical_splitter.addWidget(self.table_widget)

        # Horizontal Splitter
        self.horizontal_splitter = QSplitter(Qt.Horizontal)
        self.horizontal_splitter.splitterMoved.connect(self.onSplitterMoved)
        self.horizontal_splitter.setHandleWidth(5)
        self.horizontal_splitter.addWidget(self.function_widget)
        self.horizontal_splitter.addWidget(self.map_widget)

        # Add Horizontal Splitter to Vertical Splitter
        self.vertical_splitter.addWidget(self.horizontal_splitter)

        # Add Splitter to Main Layout
        self.main_layout.addWidget(self.vertical_splitter, 1, 0, 1, 1)

        self.button_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.main_layout.setRowStretch(0, 0)
        self.main_layout.setRowStretch(1, 1)

    def init_frames(self):
        # Button Frame
        self.button_frame = QFrame(self)
        self.button_frame.setFixedHeight(30)
        self.button_frame_layout = QHBoxLayout(self.button_frame)
        self.button_frame_layout.setContentsMargins(0, 0, 0, 0)
        self.button_frame_layout.setSpacing(0)

        # Table Frame
        self.table_frame = QFrame(self)
        self.table_frame_layout = QVBoxLayout(self.table_frame)
        self.table_frame_layout.setContentsMargins(0, 0, 0, 0)

        # Button function Frame
        self.button_function_frame = QFrame(self)
        self.button_function_frame.setFixedHeight(28)
        self.button_function_frame.setStyleSheet("QFrame { border: none; border-bottom: 1px solid yellow; }")
        self.function_button_layout = QHBoxLayout(self.button_function_frame)
        self.function_button_layout.setContentsMargins(2, 0, 2, 0)
        self.function_button_layout.setSpacing(0)

        # Function Frame
        self.function_frame = QFrame(self)
        self.function_win_layout = QVBoxLayout(self.function_frame)
        self.function_win_layout.setContentsMargins(0, 0, 0, 0)
        #self.function_win_layout.setSpacing(0)
        
        # Embed DOCX GUI    
        self.docx_gui = DOCX()
        self.docx_gui.setVisible(False)
        self.function_win_layout.addWidget(self.docx_gui)

        self.coord_gui = Win_coordinate_comparison()
        self.coord_gui.setVisible(False)
        self.function_win_layout.addWidget(self.coord_gui)

        self.gml_handler = GML_Handler(self.gml.df_GML_personal_data, self.docx_gui.dict)
        self.gml_handler.setVisible(False)
        self.function_win_layout.addWidget(self.gml_handler)

        self.kw_handler = KW_Handler()
        self.kw_signal.connect(self.kw_handler.search_kw)
        #self.kw_handler.setVisible(False)
        self.function_win_layout.addWidget(self.kw_handler)

        self.r_handler = Raster_handler()
        self.r_handler.setVisible(False)
        self.function_win_layout.addWidget(self.r_handler)

        # Map Frame
        #self.map_frame = QFrame(self)
        #self.map_layout.addWidget(self.map_frame)

        # Add Frames to Layouts
        self.button_layout.addWidget(self.button_frame)
        self.table_layout.addWidget(self.table_frame)
        self.function_layout.addWidget(self.button_function_frame)
        self.function_layout.addWidget(self.function_frame)

    def init_function_btn(self):
        self.btn_asystent = QtWidgets.QPushButton("Asystent operatu", self)
        self.btn_asystent.setFixedWidth(100)
        self.btn_asystent.setFixedHeight(26)
        self.btn_asystent.clicked.connect(lambda :self.hide_function_widget(self.btn_asystent, self.docx_gui))  # Podłącz metodę toggle_docx_gui
        self.btn_asystent.setToolTip('<p>Asystent operatu, podmienia tagi w pliku *.DOCX </p>'
                                      'Następnie eksportuje poprawione dokumenty do wybranej lokalizacji.</p>')
        
        self.btn_por_wsp = QtWidgets.QPushButton("coord_gui", self)
        self.btn_por_wsp.setText("Por.")
        if dark_mode_enabled:
            self.btn_por_wsp.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("Exchange-light")))
        else:
            self.btn_por_wsp.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("Exchange-dark")))
        self.btn_por_wsp.setToolTip('Moduł umożliwiający porównanie współrzędnych.')
        self.btn_por_wsp.setIconSize(QtCore.QSize(24, 24))
        self.btn_por_wsp.setFixedWidth(70)
        self.btn_por_wsp.setFixedHeight(26)
        self.btn_por_wsp.clicked.connect(lambda :self.hide_function_widget(self.btn_por_wsp, self.coord_gui))  # Podłącz metodę toggle_docx_gui

        self.btn_r = QtWidgets.QPushButton("Rastry", self)  # Handler
        self.btn_r.setFixedWidth(90)
        self.btn_r.setFixedHeight(26)
        self.btn_r.clicked.connect(lambda :self.hide_function_widget(self.btn_r, self.r_handler))

        self.btn_kw = QtWidgets.QPushButton("KW Menedżer", self)  # Handler
        self.btn_kw.setFixedWidth(90)
        self.btn_kw.setFixedHeight(26)
        self.btn_kw.clicked.connect(lambda :self.hide_function_widget(self.btn_kw, self.kw_handler))

        self.btn_gml = QtWidgets.QPushButton("GML Menedżer", self)  # Handler
        self.set_botton_border(self.btn_gml)
        self.btn_gml.setFixedWidth(90)
        self.btn_gml.setFixedHeight(26)
        self.btn_gml.clicked.connect(lambda :self.hide_function_widget(self.btn_gml, self.gml_handler))

        self.set_button_styles(self.btn_asystent, self.btn_por_wsp, self.btn_gml, self.btn_kw, self.btn_r)
        self.set_botton_border(self.btn_kw)

        self.function_button_layout.addWidget(self.btn_asystent)
        self.function_button_layout.addWidget(self.btn_por_wsp)
        self.function_button_layout.addStretch(1)
        self.function_button_layout.addWidget(self.btn_r)
        self.function_button_layout.addWidget(self.btn_kw)
        self.function_button_layout.addSpacerItem(QSpacerItem(25, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.function_button_layout.addWidget(self.btn_gml)

    def toggle_frame(self, frame):
        frame.setVisible(not frame.isVisible())

    # Status bar.
    def init_status_bar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.default_color = "black"
        if dark_mode_enabled:
            self.default_color = "white"

        # Tworzenie centralnego widgetu w statusbarze
        status_widget = QWidget()
        status_widget.setMaximumHeight(20)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Usunięcie marginesów
        layout.setSpacing(0)

        self.btn_log = QtWidgets.QPushButton("", self)
        self.btn_log.setFixedWidth(20)
        self.btn_log.setFixedHeight(20)
        if dark_mode_enabled:
            self.btn_log.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("Data-light")))
        else:
            self.btn_log.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("Data-dark")))
        self.btn_log.setIconSize(QtCore.QSize(20, 20))
        self.btn_log.clicked.connect(self.log_window.show)
        self.btn_log.setToolTip("Logi aplikacji")

        # Tworzenie etykiety na wiadomość
        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"color: {self.default_color}; font-size: 14px;")

        layout.addWidget(self.btn_log)
        layout.addStretch()  # Rozciąganie przed etykietą
        layout.addWidget(self.status_label)
        layout.addStretch()  # Rozciąganie za etykietą

        status_widget.setLayout(layout)
        self.statusbar.addWidget(status_widget, 1)  # Dodanie widgetu do statusbara


        update_available = False
        if SettingsWindow.simple_check_update(VERSION):
            update_available = True
            print("Dostępna jest aktualizacja")

        if update_available:
            self.update_statusBar("🚀 Dostępna jest nowa aktualizacja.", 10000, "red")

    @Slot(str)
    def update_statusBar(self, message: str, duration: int = 10000, color: str = None):
        if color is None:
            color = self.default_color
        
        self.status_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        self.status_label.setText(message)
        
        if duration:
            QTimer.singleShot(duration, self.clear_status)

    def clear_status(self):
        self.status_label.setStyleSheet(f"color: {self.default_color}; font-size: 14px;")
        self.status_label.setText("")

    # Win events.
    def resizeEvent(self, event):
        super().resizeEvent(event)
        available_width = self.width()
        #print(available_width)
        """
        if available_width < 1485:  # Jeśli dostępna szerokość jest zbyt mała, ukrywamy przyciski
            self.btn_donate.setVisible(False)
            self.btn_git.setVisible(False)
        else:
            self.btn_donate.setVisible(True)
            self.btn_git.setVisible(True)
        """

        #if self.settings.value('UproszczonaMapa', True, type=bool) == True:
        try:
            self.adjustGview()
        except Exception as e:
            logging.exception(e)
            print(e)

    def onSplitterMoved(self, pos, index):
        #print(self, pos, index)
        #if self.settings.value('UproszczonaMapa', True, type=bool) == True:
        try:
            self.adjustGview()
        except Exception as e:
            logging.exception(e)
            print(e)

    def adjustGview(self):
        #self.gview.setGeometry(self.map_frame.geometry())
        #print(self.map_widget.width(), self.map_widget.height())
        self.browse_in_geoportal.setGeometry(self.map_widget.width() - 162, 20, 140, 28)
        self.browse_in_street_view.setGeometry(self.map_widget.width() - 162, 50, 140, 28)

    def closeEvent(self, event):    # Zdarzenie zamknięcia okna
        self.save_splitter_state()  # Zapisz stan splitera przed zamknięciem aplikacji
        super().closeEvent(event)

    # Splitter.
    def save_splitter_state(self):  # Zapisz stan splitera w ustawieniach
        self.settings.setValue("verticalSplitterState", self.vertical_splitter.saveState())
        self.settings.setValue("horizontalSplitterState", self.horizontal_splitter.saveState())

    def restore_splitter_state(self):  # Przywróć stan splitera z ustawień
        vertical_state = self.settings.value("verticalSplitterState")
        horizontal_state = self.settings.value("horizontalSplitterState")
        if vertical_state is None and horizontal_state is None:
            self.vertical_splitter.setSizes([self.height() // 3, self.width() // 2])

        if vertical_state:
            self.vertical_splitter.restoreState(vertical_state)
        if horizontal_state:
            self.horizontal_splitter.restoreState(horizontal_state)

    # Init main button frame.
    def init_MainButton(self):
        obiekt = self.settings.value('Tytuł', None)
        if obiekt:
            self.setWindowTitle(obiekt)
        else:
            self.setWindowTitle("GML Reader")

        font = QFont()
        font.setPointSize(8)

        self.btn_import = QtWidgets.QPushButton(self)
        self.btn_import.setText("Import GML")
        self.btn_import.setFixedWidth(70)
        self.btn_import.setFixedHeight(28)
        self.btn_import.clicked.connect(self.import_from_path)
        self.btn_import.setToolTip("Wczytaj GML")

        self.btn_export = QtWidgets.QToolButton(self)
        if dark_mode_enabled:
            self.btn_export.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("Strzałka-export-light")))
        else:
            self.btn_export.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("Strzałka-export-dark")))
        self.btn_export.setIconSize(QtCore.QSize(30, 30))
        self.btn_export.setFixedWidth(28)
        self.btn_export.setFixedHeight(28)
        self.btn_export.clicked.connect(self.export_data)
        self.btn_export.setToolTip("Export zawartości tabeli do Excela.")

        self.btn_e_operat = QtWidgets.QPushButton(self)
        self.btn_e_operat.setText("E-Operat")
        self.btn_e_operat.setFixedWidth(65)
        self.btn_e_operat.setFixedHeight(28)
        self.btn_e_operat.clicked.connect(self.run_e_operat)
        self.btn_e_operat.setToolTip("Beta maduł operat i baza")


        self.toggle_button = ToggleButton(parent=self)
        self.toggle_button.setFixedWidth(50)
        self.toggle_button.setFixedHeight(30)
        self.toggle_button.clicked.connect(self.import_GML)
        self.toggle_button.setToolTip('<p>Funkcja importująca dla plików GML wrzuconych do programu poprzez <b>"drag and drop"</b></p>'
                                      '<p style="margin: 0;"><b>Kolory oznaczają:</b></p>'
                                      '<p style="margin: 0;">-<b style="color: purple;">fioletowy</b> Program pracuje na ostatnim wczytanym pliku GML.</p>'
                                      '<p style="margin: 0;">-<b style="color: green;">zielony</b> Poprawne wczytanie pliku GML.</p>'
                                      '<p style="margin: 0;">-<b style="color: red;">czerwony</b> Błąd podczas wczytywania pliku GML.</p>')
        
        """
        self.btn_clean = QtWidgets.QPushButton(self)
        self.btn_clean.setText("Wyczyść!!!")
        self.btn_clean.setFixedWidth(65)
        self.btn_clean.setFixedHeight(28)
        self.btn_clean.clicked.connect(self.clean_all)
        self.btn_clean.setToolTip('<p>Czyści dane z tabeli.</p>'
                           '<p><b style="color: red;">*</b>Nie usuwa danych z pamięci!</p>')
        """

        self.btn_points = QtWidgets.QPushButton(self)
        self.btn_points.setText("Punkty")
        self.btn_points.setFixedWidth(47)
        self.btn_points.setFixedHeight(28)
        self.btn_points.clicked.connect(self.punkty_w_dzialkach)
        self.btn_points.setToolTip('<p>Funkcja eksportuje punkty ich wsółrzędne oraz atrybuty.</p>'
                           '<p>NR X Y SPD ISD STB</p>'
                           '<p>Eksportowane są tylko punkty w wybranej działce na liście.</p>')

        self.btn_upr_points = QtWidgets.QPushButton(self)
        self.btn_upr_points.setText("Upr.")
        self.btn_upr_points.setFixedWidth(28)
        self.btn_upr_points.setFixedHeight(28)
        self.btn_upr_points.clicked.connect(self.punkty_w_dzialkach_uproszczone)
        self.btn_upr_points.setToolTip('<p>Funkcja eksportuje punkty i wsółrzędne.</p>'
                           '<p>NR X Y</p>'
                           '<p>Eksportowane są tylko punkty w wybranej działce na liście.</p>')

        self.btn_all_points = QtWidgets.QPushButton(self)
        self.btn_all_points.setText("All")
        self.btn_all_points.setFixedWidth(28)
        self.btn_all_points.setFixedHeight(28)
        self.btn_all_points.clicked.connect(self.punkty_GML)
        self.btn_all_points.setToolTip('<p>Funkcja eksportuje wszystkie punkty, ich wsółrzędne oraz atrybuty.</p>')

        self.btn_settings = QtWidgets.QPushButton(self)
        if dark_mode_enabled:
            self.btn_settings.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("Zębatka-light")))
        else:
            self.btn_settings.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("Zębatka-dark")))
        self.btn_settings.setFixedWidth(28)
        self.btn_settings.setFixedHeight(28)
        self.btn_settings.setIconSize(QtCore.QSize(20, 20))
        self.btn_settings.clicked.connect(self.settings_menu)
        self.btn_settings.setToolTip('Ustawienia')
        
        self.btn_donate = QtWidgets.QPushButton(self)
        self.btn_donate.setText("Donate")
        self.btn_donate.setMinimumWidth(0)
        #self.btn_donate.setMaximumWidth(80)
        self.btn_donate.setFixedWidth(80)
        self.btn_donate.setFixedHeight(26)
        self.btn_donate.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("PayPal.svg")))
        self.btn_donate.clicked.connect(self.open_edge)

        self.btn_git = QtWidgets.QPushButton(self)
        self.btn_git.setText("Github")
        #self.btn_git.setMaximumWidth(80)
        self.btn_git.setFixedWidth(80)
        self.btn_git.setFixedHeight(26)
        if dark_mode_enabled:
            self.btn_git.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("Github-light")))
        else:
            self.btn_git.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("Github-dark")))
        self.btn_git.clicked.connect(self.open_git)

        self.btn_map = QtWidgets.QToolButton(self)
        self.btn_map.setText(" Mapa")
        b_l_m_font = QFont()
        #b_l_m_font.setBold(True)
        b_l_m_font.setPointSize(10)  
        self.btn_map.setFont(b_l_m_font)
        if dark_mode_enabled:
            self.btn_map.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("Mapa-light")))
        else:
            self.btn_map.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("Mapa-dark")))
        self.btn_map.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.btn_map.setIconSize(QtCore.QSize(30, 30))
        self.btn_map.setFixedWidth(80)
        self.btn_map.setFixedHeight(30)
        self.btn_map.clicked.connect(lambda: self.run_my_window_map())

        self.btn_highlightn = QPushButton(self)
        self.btn_highlightn.setFixedWidth(28)
        self.btn_highlightn.setFixedHeight(28)
        self.btn_highlightn.clicked.connect(self.on_button_clicked)
        self.btn_highlightn.setToolTip("Podświetl działkę")

        self.comboBox = QtWidgets.QComboBox(self)
        my_listComboBox = ["Wybierz Działkę."]
        self.comboBox.addItems(my_listComboBox)
        self.comboBox.setMaxVisibleItems(30)
        self.comboBox.setFont(font)
        self.comboBox.setView(QtWidgets.QListView())
        self.comboBox.setFixedWidth(190)
        self.comboBox.setFixedHeight(26)
        self.comboBox.activated.connect(self.last_window)        
        self.comboBox.setObjectName("comboBox")
        self.comboBox.setToolTip('<p>Lista działek.')

        self.btn_refresh_comboBox = QtWidgets.QPushButton(self)
        #self.btn_refresh_comboBox.setText("Wczytaj Listę.")
        self.btn_refresh_comboBox.setFixedWidth(28)
        self.btn_refresh_comboBox.setFixedHeight(28)
        self.btn_refresh_comboBox.clicked.connect(self.comboBox_Update)
        self.btn_refresh_comboBox.setToolTip('<p>Odśwież listę działek.</p>')

        self.line_comboBox_search = QtWidgets.QLineEdit(self)
        self.line_comboBox_search.setPlaceholderText("Wyszukaj")
        self.line_comboBox_search.setFixedWidth(75)
        self.line_comboBox_search.setFixedHeight(26)
        self.line_comboBox_search.setAlignment(Qt.AlignCenter)
        self.line_comboBox_search.textChanged.connect(self.find_best_match)

        self.table_widget = QTableWidget(self)
        self.table_widget.setColumnCount(16)
        self.table_widget.setRowCount(5)
        #self.table_widget.setAcceptDrops(True)
        self.table_widget.setObjectName("True")
        self.table_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.context_menu)
        self.setTableHeaders()


        self.button_frame_layout.addWidget(self.btn_import)
        self.button_frame_layout.addWidget(self.btn_export)
        self.button_frame_layout.addWidget(self.toggle_button)
        self.button_frame_layout.addSpacerItem(QSpacerItem(25, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addWidget(self.btn_e_operat)
        self.button_frame_layout.addSpacerItem(QSpacerItem(25, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addWidget(self.btn_refresh_comboBox)
        self.button_frame_layout.addWidget(self.comboBox)
        self.button_frame_layout.addSpacerItem(QSpacerItem(2, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addWidget(self.btn_highlightn)
        self.button_frame_layout.addSpacerItem(QSpacerItem(2, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addWidget(self.line_comboBox_search)
        #self.button_frame_layout.addSpacerItem(QSpacerItem(25, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addStretch(3)
        self.button_frame_layout.addSpacerItem(QSpacerItem(15, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addWidget(self.btn_osoby)
        self.button_frame_layout.addWidget(self.btn_budynki)
        self.button_frame_layout.addWidget(self.btn_dzialki)
        self.button_frame_layout.addWidget(self.btn_uzytki)
        self.button_frame_layout.addWidget(self.btn_punkty)
        self.button_frame_layout.addWidget(self.btn_dokuments)
        self.button_frame_layout.addSpacerItem(QSpacerItem(15, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addStretch(3)
        self.button_frame_layout.addWidget(self.btn_points)
        self.button_frame_layout.addWidget(self.btn_upr_points)
        self.button_frame_layout.addWidget(self.btn_all_points)
        #self.button_frame_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        #self.button_frame_layout.addWidget(self.btn_por_wsp)
        self.button_frame_layout.addStretch(2)
        self.button_frame_layout.addWidget(self.btn_donate)
        self.button_frame_layout.addWidget(self.btn_git)
        self.button_frame_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addWidget(self.btn_settings)
        self.button_frame_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addStretch(2)
        self.button_frame_layout.addWidget(self.btn_map)

        self.table_frame_layout.addWidget(self.table_widget)

    def init_widget(self):
        self.btn_osoby = QtWidgets.QPushButton(self)
        self.set_botton_border(self.btn_osoby)
        self.btn_osoby.setText("Osoby")
        self.btn_osoby.setGeometry(412, 2, 62, 26)
        self.btn_osoby.setFixedWidth(62)
        self.btn_osoby.setFixedHeight(26)
        self.btn_osoby.clicked.connect(self.visualize_osoby)
        self.btn_osoby.clicked.connect(lambda: self.reset_and_set(self.btn_osoby))
        self.btn_osoby.setToolTip('<p>Funkcja wczytuje wszystkie dane osobowe zawarte w pliku GML</p>'
                           '<p>Filtrowanie danych następuje poprzez wczytanie oraz wybór konkretnej dzialki</p>')

        self.btn_budynki = QtWidgets.QPushButton(self)
        self.btn_budynki.setText("Budynki")
        self.btn_budynki.setGeometry(474, 2, 62, 26)
        self.btn_budynki.setFixedWidth(62)
        self.btn_budynki.setFixedHeight(26)
        self.btn_budynki.clicked.connect(self.visualize_budynki)
        self.btn_budynki.clicked.connect(lambda: self.reset_and_set(self.btn_budynki))
        self.btn_budynki.setToolTip('<p>Funkcja wczytuje kartoteki budynków na działce.</p>')

        self.btn_dzialki = QtWidgets.QPushButton(self)
        self.btn_dzialki.setText("Działki")
        self.btn_dzialki.setGeometry(536, 2, 62, 26)
        self.btn_dzialki.setFixedWidth(62)
        self.btn_dzialki.setFixedHeight(26)
        self.btn_dzialki.clicked.connect(self.visualize_dzialki)
        self.btn_dzialki.clicked.connect(lambda: self.reset_and_set(self.btn_dzialki))
        self.btn_dzialki.setToolTip('<p>Funkcja wczytuje numer, księgę wieczystą, powierzchnię oraz oblicza powierzchnię działki uwzględniając poprawkę.</p>')

        self.btn_uzytki = QtWidgets.QPushButton(self)
        self.btn_uzytki.setText("Użytki")
        self.btn_uzytki.setGeometry(598, 2, 62, 26)
        self.btn_uzytki.setFixedWidth(62)
        self.btn_uzytki.setFixedHeight(26)
        self.btn_uzytki.clicked.connect(self.visualize_uzytki)
        self.btn_uzytki.clicked.connect(lambda: self.reset_and_set(self.btn_uzytki))
        self.btn_uzytki.setToolTip('<p>Funkcja wczytuje użytki w działce</p>')

        self.btn_punkty = QtWidgets.QPushButton(self)
        self.btn_punkty.setText("Punkty")
        self.btn_punkty.setGeometry(598, 2, 62, 26)
        self.btn_punkty.setFixedWidth(62)
        self.btn_punkty.setFixedHeight(26)
        self.btn_punkty.clicked.connect(self.visualize_punkty)
        self.btn_punkty.clicked.connect(lambda: self.reset_and_set(self.btn_punkty))
        self.btn_punkty.setToolTip('<p>Funkcja wczytuje punkty w działce</p>')

        self.btn_dokuments = QtWidgets.QPushButton(self)
        self.btn_dokuments.setText("Dokumenty")
        self.btn_dokuments.setGeometry(598, 2, 62, 26)
        self.btn_dokuments.setFixedWidth(62)
        self.btn_dokuments.setFixedHeight(26)
        self.btn_dokuments.clicked.connect(self.visualize_dekumenty)
        self.btn_dokuments.clicked.connect(lambda: self.reset_and_set(self.btn_dokuments))
        self.btn_dokuments.setToolTip('<p>Funkcja wczytuje dokumenty dla działki</p>')

        self.set_button_styles(self.btn_budynki, self.btn_dzialki, self.btn_uzytki, self.btn_punkty, self.btn_dokuments)

    def init_map_button(self):
        self.browse_in_geoportal = QPushButton(self.map_widget)
        self.browse_in_geoportal.setIcon(QtGui.QIcon(file_manager.get_stylesheets_folder_path("Geoportal.svg")))
        style = ("""QPushButton {
                background-color: #ababab;
                border: 1px solid #4d4d4d;
                color: #ffffff;
                border-radius: 5px;
                border: none;
                padding: 0px;
                margin: 2px; 
                }
                QPushButton:hover {
                    background-color: #2e2e2e;
                    border: 1px solid #5a5a5a;
                }""")
        self.browse_in_geoportal.setStyleSheet(style)
        self.browse_in_geoportal.setText("Szukaj w Geoportalu")
        self.browse_in_geoportal.clicked.connect(MapHandler.find_parcel_in_geoportal)
        self.browse_in_geoportal.setToolTip("Po naciśnięciu tego przycisku wybierz działkę, która ma zostać otwarta w Geoportalu Krajowy.")
        
        self.browse_in_street_view = QPushButton(self.map_widget)
        self.browse_in_street_view.setIcon(QtGui.QIcon(file_manager.get_stylesheets_folder_path("StreetView.svg")))
        style = ("""QPushButton {
                background-color: #ababab;
                border: 1px solid #4d4d4d;
                color: #ffffff;
                border-radius: 5px;
                border: none;
                padding: 0px;
                margin: 2px; 
                }
                QPushButton:hover {
                    background-color: #2e2e2e;
                    border: 1px solid #5a5a5a;
                }""")
        self.browse_in_street_view.setStyleSheet(style)
        self.browse_in_street_view.setText("Szukaj w StreetView")
        self.browse_in_street_view.clicked.connect(self.map_handler.find_parcel_in_street_view)
        self.browse_in_street_view.setToolTip("Po naciśnięciu tego przycisku wybierz działkę drogową, która ma zostać otwarta w StreetView.")

    def _setup_icons(self):
        """Konfiguruje wszystkie ikony na podstawie motywu."""
        icon_size = QtCore.QSize(22, 22)
        
        # Mapa ikon z ich rozmiarami
        icons_config = [
            (self.btn_highlightn, "Zoom", icon_size),
            (self.btn_refresh_comboBox, "Refresh", icon_size),
        ]
        
        # Ustaw ikony dla wszystkich przycisków
        for button, icon_name, size in icons_config:
            icon_path = file_manager.get_icon_path(icon_name, dark_mode_enabled)
            button.setIcon(QtGui.QIcon(icon_path))
            button.setIconSize(size)

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
        self.set_button_styles(self.btn_osoby, self.btn_budynki, self.btn_dzialki, self.btn_uzytki, self.btn_punkty, self.btn_dokuments)
        self.set_botton_border(selected_button)

    def hide_all_in_function_win_layout(self):
        """Ukrywa wszystkie widżety w układzie function_win_layout."""
        for i in range(self.function_win_layout.count()):
            widget = self.function_win_layout.itemAt(i).widget()
            if widget is not None:
                widget.setVisible(False)

    def hide_function_widget(self, selected_button, widget):
        self.set_button_styles(self.btn_asystent, self.btn_por_wsp, self.btn_gml, self.btn_kw, self.btn_r)

        if widget.isVisible():
            self.hide_all_in_function_win_layout()
            widget.setVisible(False)
        else:
            self.hide_all_in_function_win_layout()
            widget.setVisible(True)
            self.set_botton_border(selected_button)

    def on_button_clicked(self):
        selected = self.comboBox.currentText()
        if selected == "Wybierz Działkę.":
            self.update_statusBar("Proszę wybrać działkę z listy.")
            return
        parcel_id = selected
        self.parcelHighlightRequested.emit(parcel_id)

    def normalize_text(self, text):
        # Normalize Unicode text and convert to lowercase
        normalized_text = unicodedata.normalize('NFKD', text)
        return normalized_text.encode('ASCII', 'ignore').decode('ASCII').lower()

    def find_best_match(self, text):
        normalized_input = self.normalize_text(text)

        # Pomijamy pierwszy element "Wybierz Działkę."
        for index in range(1, self.comboBox.count()):
            item_text = self.comboBox.itemText(index)
            normalized_item = self.normalize_text(item_text)

            if normalized_input in normalized_item:
                self.comboBox.setCurrentIndex(index)
                self.last_window()
                return

        # Jeśli nic nie znaleziono, ustawiamy pierwszy element
        self.comboBox.setCurrentIndex(0)


    def visualize_osoby(self):
        column_index = 20
        
        self.lastwindow = "GML"
        df = self.gml.df_GML_personal_data.copy()
        
        if df.empty:
            self.update_statusBar("Brak danych do wyświetlenia (Osoby).")
            return

        try:
            if self.settings.value('ShortOwnerAddr', True, type=bool) == True:
                df["Adres"] = (df["ulica"] + " " + df["numerPorzadkowy"] + df["numerLokalu"].apply(lambda x: f" Lokal nr {x}" if pd.notna(x) and str(x).strip() != "" else ""))
                df["Miejscowość"] = df["kodPocztowy"] + " " + df["miejscowosc"] + " " + df["kraj"]

                df["Adres_Kores."] = (df["ulica_Kores."] + " " + df["numerPorzadkowy_Kores."] + df["numerLokalu_Kores."].apply(lambda x: f" Lokal nr {x}" if pd.notna(x) and str(x).strip() != "" else ""))
                df["Miejscowość_Kores."] = df["kodPocztowy_Kores."] + " " + df["miejscowosc_Kores."] + " " + df["kraj_Kores."]

                df["nazwaPelna"] = df["nazwaPelna"].where(df["nazwaPelna"].str.strip() != "", 
                                                df["pierwszeImie"].fillna("") + " " + df["drugieImie"].fillna("") + " " + df["pierwszyCzlonNazwiska"].fillna("") + " " + df["drugiCzlonNazwiska"].fillna(""))
                
                df = df[["idDzialki", "numerKW", "poleEwidencyjne", "dokladnoscReprezentacjiPola", "rodzajPrawa", "udzialWlasnosci", "rodzajWladania", "udzialWladania", "nazwaPelna", "nazwaSkrocona", "imieOjca", "imieMatki", "plec", "pesel", "regon", "informacjaOSmierci", "IDM", "status", "Adres", "Miejscowość", "Adres_Kores.", "Miejscowość_Kores.", "grupaRejestrowa", "idJednostkiRejestrowej"]]
                column_index = 16
        except Exception as e:
            logging.exception(e)
            print(e)

        self.visualize_data_in_Table(df)
        self.color_duplicates_pastel(self.table_widget, column_index=column_index)

    def visualize_budynki(self):
        self.lastwindow = "BUDYNKI"
        df = self.gml.df_GML_budynki.copy()

        if df.empty:
            self.update_statusBar("Brak danych do wyświetlenia (Budynki).")
            return
        
        self.visualize_data_in_Table(df)

    def visualize_dzialki(self):
        self.lastwindow = "DZIALKI"
        df = self.gml.df_GML_dzialki.copy()
        
        if df.empty:
            self.update_statusBar("Brak danych do wyświetlenia (Działki).")
            return

        try:
            df = df.drop(columns=['klasouzytek'])
        except Exception as e:
            logging.exception(e)
            print(e)

        self.visualize_data_in_Table(df)

    def visualize_uzytki(self):
        self.lastwindow = "UZYTKI"
        df = self.gml.df_GML_dzialki.copy()

        if df.empty:
            self.update_statusBar("Brak danych do wyświetlenia (Użytki).")
            return

        df = df.drop(columns=["grupaRejestrowa", "idJednostkiRejestrowej"])
        df = df.explode("klasouzytek")
        df = self.columns_explode(df, explode_on="klasouzytek", new_column=["OFU", "OZU", "OZK", "Pow."])
        self.visualize_data_in_Table(df)

    def visualize_punkty(self):
        self.lastwindow = "PUNKTY"
        df = self.gml.df_GML_points_in_dzialki.copy()

        if df.empty:
            self.update_statusBar("Brak danych do wyświetlenia (Punkty).")
            return

        df = self.columns_explode(df, explode_on="geometria_punkt", new_column=["X", "Y"])
        self.visualize_data_in_Table(df)

    def visualize_dekumenty(self):
        self.lastwindow = "DOKUMENTY"
        df = self.gml.df_GML_documents.copy()

        if df.empty:
            self.update_statusBar("Brak danych do wyświetlenia (Dokumenty).")
            return

        self.visualize_data_in_Table(df)


    def columns_explode(self, df, explode_on=None, new_column=None):
        try:
            lista_df = df[explode_on].apply(pd.Series)
            if new_column:
                lista_df.columns = new_column

            for col in lista_df.columns:
                if col not in df.columns:
                    df[col] = lista_df[col]

            df = df.drop(columns=[explode_on])
        except Exception as e:
            logging.exception(e)
            print(e)
        return df

    def column_mapping(self,df):
        column_dictionary = {
        "idDzialki": "Działka",
        "numerKW": "KW",
        "poleEwidencyjne": "Pole pow.",
        "dokladnoscReprezentacjiPola": "Do:",
        "rodzajPrawa": "Rodzaj Prawa",
        "udzialWlasnosci": "Udział",
        "rodzajWladania": "Rodzaj Wład.",
        "udzialWladania": "Udział",
        'nazwaPelna': "Nazwa Pełna",
        'nazwaSkrocona': "Skrót",
        "pierwszeImie": "Imie",
        "drugieImie": "Drugie Imie",
        "pierwszyCzlonNazwiska": "Nazwisko",
        "drugiCzlonNazwiska": "Człon Nazw.",
        "imieOjca": "Im. Ojca",
        "imieMatki": "Im. Matki",
        "pesel": "Pesel",
        "plec": "Płeć",
        "status": "Status",
        "informacjaOSmierci": "Info. o śmierci",
        "regon": "Regon",
        "kraj": "Kraj",
        "miejscowosc": "Miejs.",
        "kodPocztowy": "kod poczt.",
        "ulica": "Ulica",
        "numerPorzadkowy": "Nr por.",
        "numerLokalu": "Nr Lokalu",
        "kraj_Kores.": "Kraj_Kores.",
        "miejscowosc_Kores.": "Miejs_Kores.",
        "kodPocztowy_Kores.": "Kod pocztowy_Kores.",
        "ulica_Kores.": "Ilica_Kores.",
        "numerPorzadkowy_Kores.":  "Nr por._Kores.",
        "numerLokalu_Kores.": "Nr Lokalu_Kores.",
        "IDM": "IDM",
        "grupaRejestrowa": "Gr. Rejestrowa",
        "idJednostkiRejestrowej": "Jedn. Rejestrowa",
        "idPunktu": "Punkt",
        "sposobPozyskania": "SPD",
        "spelnienieWarunkowDokl": "ISD",
        "rodzajStabilizacji": "STB",
        "oznWMaterialeZrodlowym": "OZR",
        "numerOperatuTechnicznego": "Nr Operatu Technicznego",
        "dodatkoweInformacje": "Dodatkowe informacje",
        "geometria_punkt": "WSP",
        "rodzajWgKST": "KST",
        "liczbaKondygnacjiNadziemnych": "l.kond.nad.",
        "liczbaKondygnacjiPodziemnych": "l.kond.podz.",
        "powZabudowy": "pow.zab.",
        "lacznaPowUzytkowaLokaliWyodrebnionych": "łacz.pow.uż.wyodr.",
        "lacznaPowUzytkowaLokaliNiewyodrebnionych": "łacz.pow.uż.niewyodr.",
        "lacznaPowUzytkowaPomieszczenPrzynaleznych": "łacz.pow.uż.przyn.",
        "dokumentWlasnosci": "dok.wł.",
        "dodatkoweInformacje": "dod.inf."
        
        
        }
        
        return df.rename(columns=column_dictionary)

    def column_stripping(self, df, strip_id_on_columns=None):
        df = df.copy()

        if strip_id_on_columns is None:
            return df

        strip = True
        if strip:
            for col in df.columns:
                if col in strip_id_on_columns:
                    df[col] = df[col].str.rsplit('.', n=1).str.get(-1)
        return df

    def visualize_data_in_Table(self, df):
        try:
            if not self.comboBox.currentText() == "Wybierz Działkę.":
                df = df[df['idDzialki'].isin([self.comboBox.currentText()])]  # Sortuj przed mapowaniem kolumn.
        except Exception as e:
            logging.exception(e)
            print(e)

        if self.settings.value('AddObreb', False, type=bool) == True:
            df.insert(0, "Obręb", df["idDzialki"].str.rsplit('.', n=1).str.get(0))

        if self.settings.value('StripID', True, type=bool) == True:
            df = self.column_stripping(df, strip_id_on_columns=["idDzialki", "idJednostkiRejestrowej", "idPunktu", "idBudynku"])
        
        try:  # Replace  ['NaN', 'None', 'nan'] on ""
            df = df.replace([None, "NaN", "None", "nan"], "").fillna("")
        except Exception as e:
            logging.exception(e)
            print(e)

        self.clean()
        self.table_widget.clear()
        self.table_widget.setObjectName(None)
        
        df = self.column_mapping(df)

        self.table_widget.setColumnCount(len(df.columns))
        self.table_widget.setHorizontalHeaderLabels(df.columns.astype(str).tolist())
        for r in range(len(df.index)):  # self.table_widget.setRowCount(len(df)) ---> speed up?
            self.table_widget.insertRow(r)
            for k in range(len(df.columns)):
                self.table_widget.setItem(r, k, QTableWidgetItem(str(df.iat[r, k])))

        self.table_widget.resizeColumnsToContents()

    def adjustTableColumnWidth(self):
        table_width = self.width()

        column_count = self.table_widget.columnCount()
        column_width = table_width // column_count
        
        table_name = self.table_widget.objectName()

        if table_name == "True":
            for column in range(column_count):
                self.table_widget.setColumnWidth(column, column_width)


    def import_from_path(self):
        path = QFileDialog.getOpenFileName(self, 'open file', os.path.expanduser("~/Desktop"), 'GML File(*.gml)')

        try:
            obiekt = (f"GML Readere   Obiekt: {os.path.splitext(os.path.basename(self.input_gml_path))[0]}")
            self.setWindowTitle(obiekt)
            self.settings.setValue("Tytuł", obiekt)
        except Exception as e:
            logging.exception(e)

        if path == ('', ''):
            return
        
        self.input_gml_path = path[0]
        self.import_GML()

    def import_GML(self):
        path = self.input_gml_path
        if path is not None:
            try:
                if Path(path).exists():
                    copy_file(path, gml_file_path)
            except Exception as e:
                logging.exception(e)
                self.result_output("Parse GML Error!", "#ab2c0c")
                return

        try:
            S = time.perf_counter()

            self.gml = GMLParser(gml_file_path)
            if not self.gml.valid:
                self.update_statusBar("Niepoprawna ścieżka do pliku GML")
                return
            self.gml.initialize_gml_parse()
            self.gml.initialize_graphic_data()
            self.gml.initialize_personal_data()
            self.gml.initialize_additional_data()
            self.gml.initialize_documents_data()
            self.gml_handler.GML = self.gml.df_GML_personal_data

            self.save_dataframe()

            E = time.perf_counter()

            print(f"{E-S:.4}")
            logging.info(f"Import GML time: {E-S:.4}")

        except Exception as e:
            logging.exception(e)
            print(e)
            self.result_output("GML Reader Error!", "#ab2c0c")
            return
        
        self.comboBox_Update()

        #if self.settings.value('UproszczonaMapa', True, type=bool) == True:
        self.refresh_map_view()

        self.input_gml_path = gml_file_path
        
        self.result_output("GML wczytany.", "#77C66E")
        self.last_window()

    def run_e_operat(self):
        try:
            self.open_e_operat = e_operat(MainWindow)
            self.open_e_operat.gml_path_selected.connect(self.run_gml_from_project)
            self.open_e_operat.db.tags_changed.connect(self.gml_handler.receve_table_content)
            self.open_e_operat.db.tags_changed.connect(self.docx_gui.table_model.update_from_dict)
            self.open_e_operat.show()
        except Exception as e:
            logging.exception(e)
            print(e)


    @Slot(Path)
    def run_gml_from_project(self, path: Path):
        self.input_gml_path = path
        self.import_GML()

    def import_dataframe_on_start(self):
        try:
            with open(data_base_file_path, "rb") as f:
                df_dict = pd.read_pickle(f)
                self.gml.restory_dataframes(df_dict)
                self.gml_handler.GML = self.gml.df_GML_personal_data
            logging.debug("Dataframe restored.")
        except Exception as e:
            logging.exception(e)
        self.comboBox_Update()

    def save_dataframe(self):
        try:
            df = self.gml.story_dataframes()
            with open(data_base_file_path, "wb") as f:
                pd.to_pickle(df, f)
        except Exception as e:
            logging.exception(e)


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
        if self.lastwindow == "GML":
            self.visualize_osoby()
        elif self.lastwindow == "BUDYNKI":
            self.visualize_budynki()
        elif self.lastwindow == "DZIALKI":
            self.visualize_dzialki()
        elif self.lastwindow == "UZYTKI":
            self.visualize_uzytki()
        elif self.lastwindow == "PUNKTY":
            self.visualize_punkty()
        elif self.lastwindow == "DOKUMENTY":
            self.visualize_dekumenty()
        else:
            self.visualize_osoby()

    def settings_menu(self):
        self.sett = SettingsWindow(MainWindow, dark_mode_enabled, VERSION)
        self.sett.show()


    def import_Excel(self):
        file_exists = exists(sys.path[0] + "\\GML\\GML.xlsx")
        if file_exists == False:
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


    def GMLTable(self):  # Wprowadź dane do tabeli
        for row in range(5):
            for column in range(16):
                item = QTableWidgetItem("Zaimportuj GML")
                self.table_widget.setItem(row, column, item)

    def run_my_window_map(self):
        if self.input_gml_path == None:
            self.update_statusBar("Najpierw wczytaj plik GML.")
            return
        else:
            try:
                self.window_map = WindowMap(MainWindow, self.input_gml_path, self.prased_gml, xlsx_target_path)
                self.window_map.item_signal.connect(self.receive_item)
                self.window_map.show()
            except Exception as e:
                logging.exception(e)
                print(e)

    def comboBox_Update(self):
        df = self.gml.df_GML_sorted_działki.copy()
        
        if df.empty:
            self.update_statusBar("Brak danych do wyświetlenia.")
            return
        
        self.comboBox.clear()
        self.comboBox.addItem("Wybierz Działkę.")
        
        działki_gml_list = df['idDzialki']
        
        działki_gml_list.reset_index(drop=True, inplace=True)
        działki_gml_list.fillna('',inplace=True)
        lists = działki_gml_list.values.tolist()
        self.comboBox.addItems(lists)

    def punkty_GML(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly  # Optionally, set options as needed
        fname_p = QFileDialog.getSaveFileName(None, "Save File", os.path.expanduser("~/Desktop"), "Text Files (*.txt);;All Files (*)", options=options)        
        if fname_p[0] == '':
            self.update_statusBar("Nie wybrano ścieżki.")
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

        except Exception as e:
            logging.exception(e)
            return
        PunktyGr.to_csv(fname_p[0], sep=' ', index=False)

    def punkty_w_dzialkach(self):
        if self.comboBox.currentText() == "Wybierz Działkę.":
            self.update_statusBar("Wybierz najpierw działkę.")
            return

        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly  # Optionally, set options as needed
        fname_p = QFileDialog.getSaveFileName(None, "Save File", os.path.expanduser("~/Desktop"), "Text Files (*.txt);;All Files (*)", options=options)        
        if fname_p[0] == '':
            self.update_statusBar("Nie wybrano ścieżki.")
            return
        try:
            df_działki = punkty_w_dzialkach(gml_file_path)  # >>> Dzialka + ID Path
            df_punkty = punkt_graniczny(gml_file_path)  # Path
            df_punkty_działki = df_działki.merge(df_punkty, how = 'outer', on=['ID'])
            df_punkty_działki.drop('ID', axis=1, inplace=True)
        except Exception as e:
            logging.exception(e)
            return
        
        if not self.comboBox.currentText() == "Wybierz Działkę.":
            df_punkty_działki = df_punkty_działki[df_punkty_działki['Działka'].isin([self.comboBox.currentText()])]
            df_punkty_działki.drop('Działka', axis=1, inplace=True)
        else:
            self.update_statusBar("Wybierz najpierw działkę.")
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
            self.update_statusBar("Wybierz najpierw działkę.")
            return

        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly  # Optionally, set options as needed
        fname_p = QFileDialog.getSaveFileName(None, "Save File", os.path.expanduser("~/Desktop"), "Text Files (*.txt);;All Files (*)", options=options)        
        if fname_p[0] == '':
            self.update_statusBar("Nie wybrano ścieżki.")
            return
        try:
            df_działki = punkty_w_dzialkach(gml_file_path)  # >>> Dzialka + ID Path
            df_punkty = punkt_graniczny(gml_file_path) # Path
            df_punkty_działki = df_działki.merge(df_punkty, how = 'outer', on=['ID'])
        except Exception as e:
            logging.exception(e)
            return
        if not self.comboBox.currentText() == "Wybierz Działkę.":
            df_punkty_działki = df_punkty_działki[df_punkty_działki['Działka'].isin([self.comboBox.currentText()])]
        else:
            self.update_statusBar("Wybierz najpierw działkę.")
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

    def clean_all(self):
        table_name = self.table_widget.objectName()
        #print(table_name)
        if table_name == "True" or table_name == "":
            self.table_widget.setObjectName("True")
            self.adjustTableColumnWidth()

        self.comboBox.setItemText(0, "Wybierz Działkę.")
        for i in range(self.table_widget.rowCount()):
            self.table_widget.removeRow(0)
   
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

    def color_duplicates_pastel(self, tableWidget, column_index):
        
        data = []

        for row in range(tableWidget.rowCount()):
            item = tableWidget.item(row, column_index)
            data.append(item.text() if item is not None else "")  # Sprawdź, czy komórka jest pusta

        unique_values = set()  # color_map = {}
        for value in data:
            if value != "":
                if value in unique_values:
                    if value in self.color_dict:
                        unique_color = self.color_dict[value]
                    else:
                        unique_color = self.generate_pastel_color()
                        self.color_dict[value] = unique_color

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
            self.input_gml_path = file_path
            copy_file(file_path, gml_file_path)

            try:
                obiekt = (f"GML Readere   Obiekt: {os.path.splitext(os.path.basename(self.input_gml_path))[0]}")
                self.setWindowTitle(obiekt)
                self.settings.setValue("Tytuł", obiekt)
            except Exception as e:
                logging.exception(e)
                pass

            self.result_output("Offline.", "#686868")


    def result_output(self, Text = None, color = "#686868"):  # green -> "#77C66E" | red -> "#ab2c0c" | purple -> "#975D9F" | black -> "#686868"
        try:
            if self.toggle_button.isChecked():
                self.toggle_button.setChecked(False)
            else:
                self.toggle_button.setChecked(True)
            ToggleButton.updateIndicatorColor(self.toggle_button, QColor(color)) #FFD700
        except Exception as e:
            logging.exception(e)

    def receive_item(self, id=None):
        if id is None:
            return

        # Zachowujemy tekst w polu wyszukiwania
        search_text = self.line_comboBox_search.text()

        # Szukamy indeksu elementu w ComboBox
        index_to_select = self.comboBox.findText(id, QtCore.Qt.MatchFixedString)
        if index_to_select != -1:
            self.comboBox.setCurrentIndex(index_to_select)
        else:
            # Jeśli element nie istnieje, dodajemy go na koniec
            self.comboBox.addItem(id)
            index_to_select = self.comboBox.count() - 1
            self.comboBox.setCurrentIndex(index_to_select)

        self.line_comboBox_search.setText(search_text)

        self.last_window()

        self.update_statusBar(f"Znaleziono działkę: {id}.")
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

        print("Copy data complete.")

    def search_kw(self):
        selected_items = self.table_widget.selectedItems()
        if selected_items:  # Check if a cell is selected
            value = selected_items[0].text()  # Get the text of the first selected cell
            self.kw_signal.emit(value)  # Send the value to KW_Handler
        else:
            print("No cell selected. Please select a cell.")


    def context_menu(self, pos):
        context_menu = QMenu(self)
        copy_action = context_menu.addAction("Kopiuj")
        copy_action.triggered.connect(self.copy_to_clipboard)
        kw_action = context_menu.addAction("Szukaj KW")
        kw_action.triggered.connect(self.search_kw)
        context_menu.exec(QCursor.pos())


    def init_graphic_map_view(self):
        self.map_handler = MapHandler(parent_window=self, path=gml_file_path)
        self.map_handler.init_graphic_map_view(self.map_widget, self.map_layout)

        if Path(gml_file_path).exists() and self.settings.value('LastGML', True, type=bool) == True:
            try:
                self.map_handler.refresh_map_view()  
            except Exception as e:
                logging.exception(e)
                print(e)

    def refresh_map_view(self):
        try:
            self.map_handler.refresh_map_view()
        except Exception as e:
            logging.exception(e)
            print(e)

    def remove_gfs_file(self):
        try:
            root, ext = os.path.splitext(gml_file_path)
            os.remove(root + ".gfs")
            #print(root + ".gfs")
        except Exception as e:
            logging.exception(e)
            print("GFS file not removed.")


    def find_parcel_in_geoportal(self):
        MapHandler.find_polygon_in_web(self)


if __name__ == '__main__':
    #QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication( sys.argv )

    argv_path = None
    if len(sys.argv) > 1:
        argv_path = sys.argv[1]

    dark_mode_enabled = settings.value('DarkMode', False, type=bool)

    try:
        if dark_mode_enabled:
            app.setStyleSheet(Path(file_manager.get_stylesheets_folder_path('Darkmode.qss')).read_text())
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