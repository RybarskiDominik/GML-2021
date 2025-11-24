from PySide6.QtWidgets import (QApplication, QMainWindow, QCheckBox,
                               QApplication, QMainWindow, QLabel,
                               QFrame, QGroupBox, QVBoxLayout, QWidget, QPushButton)
from PySide6.QtCore import Qt,QRect, QSettings, QCoreApplication
from PySide6.QtGui import QIcon
from PySide6 import QtWidgets
from pathlib import Path
import logging
import sys
import os

#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from networking.update_checker import check_app_update_status
from FileManager.workspace_settings_window import WorkspaceSettingsWindow
from FileManager.FileManager import file_manager

logger = logging.getLogger(__name__)

class SettingsWindow(QMainWindow):
    def __init__(self, parent=None, dark_mode_enabled=None, version=None):
        super(SettingsWindow, self).__init__(parent)
        self.version = version
        app_update_status = None
        self.settings = QSettings('GML', 'GML Reader')

        if dark_mode_enabled:
            self.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                }
            QGroupBox {
                color: #ffffff;
                }
            """)

        self.setFixedSize(350, 400)
        self.setWindowTitle(f'GML Reader wersja: {self.version}')
        self.setWindowIcon(QIcon(r'gui\Stylesheets\GML.ico'))
        
        self.config()
        
        self.init_UI()
        
        self.check_update()

    def config(self):
        
        save_value = []

        for i in self.settings.allKeys():
            value = self.settings.value(i)
            save_value.append((i, value))
        self.save_value = save_value  # save settings for recovery
        if self.save_value:
            #print(self.save_value)
            pass
    
    def init_UI(self):
        group_main = QGroupBox("GML", self)
        group_main.setGeometry(5, 0, 190, 160)
        
        group_app = QGroupBox("Wygląd", self)
        group_app.setGeometry(200, 0, 145, 160)

        group_map = QGroupBox("Mapa", self)
        group_map.setGeometry(5, 160, 190, 200)

        group_points = QGroupBox("Punkty", self)
        group_points.setGeometry(200, 160, 145, 135)

        self.button_path_update = QtWidgets.QPushButton('Ścieżki programu', self)
        self.button_path_update.setGeometry(200, 300, 145, 28)
        self.button_path_update.clicked.connect(self.change_path_settings)

        self.button_check_update = QtWidgets.QPushButton('Check Update', self)
        self.button_check_update.setGeometry(200, 330, 145, 28)
        self.button_check_update.clicked.connect(self.check_update)


        self.last_gml = QCheckBox('Wczytaj ostatni GML', self)
        if self.settings.value('LastGML', True, type=bool) == True:
            self.last_gml.setChecked(True)
        self.last_gml.setToolTip("Wyłącz wczytywanie ostatniego GML na starcie programu.")

        self.strip_gml = QCheckBox('Skróć id w GML', self)
        if self.settings.value('StripID', True, type=bool) == True:
            self.strip_gml.setChecked(True)
        self.strip_gml.setToolTip("Skraca id w GML.")

        self.short_owner_addr = QCheckBox('Łącz (właściciele/adresu)', self)
        if self.settings.value('ShortOwnerAddr', True, type=bool) == True:
            self.short_owner_addr.setChecked(True)
        self.short_owner_addr.setToolTip("Łączy kolumny właściciela i adresu")

        self.add_obreb_coll = QCheckBox('Dodaj columnę obrębu', self)
        if self.settings.value('AddObreb', False, type=bool) == True:
            self.add_obreb_coll.setChecked(True)
        self.add_obreb_coll.setToolTip("Dodaje columnę obrębu.")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.last_gml)
        layout.addWidget(self.strip_gml)
        layout.addWidget(self.short_owner_addr)
        layout.addWidget(self.add_obreb_coll)
        group_main.setLayout(layout)


        self.dark_mode = QCheckBox('DarkMode', self)
        if self.settings.value('DarkMode', False, type=bool) == True:
            self.dark_mode.setChecked(True)

        self.full_scene = QCheckBox('Full Screen', self)
        if self.settings.value('FullScreen', True, type=bool) == True:
            self.full_scene.setChecked(True)
        
        """
        self.uproszczona_mapa = QCheckBox('Uproszczona mapa?', self)
        if self.settings.value('UproszczonaMapa', True, type=bool) == True:
            self.uproszczona_mapa.setChecked(True)
        """

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.dark_mode)
        layout.addWidget(self.full_scene)
        #layout.addWidget(self.uproszczona_mapa)

        group_app.setLayout(layout)


        self.map_flag = QCheckBox('Mapa zawsze na wierzchu.', self)
        if self.settings.value('MapStaysOnTopHint', False, type=bool) == True:
            self.map_flag.setChecked(True)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.map_flag)
        group_map.setLayout(layout)

        self.points_id = QCheckBox('Pełne ID', self)
        if self.settings.value('FullID', False, type=bool) == True:
            self.points_id.setChecked(True)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.points_id)
        group_points.setLayout(layout)

        self.button_Reset = QtWidgets.QPushButton(self)
        self.button_Reset.setText("Reset Settings")
        self.button_Reset.setGeometry(5, 365, 95, 30)
        self.button_Reset.clicked.connect(self.reset)

        self.button_Reset = QtWidgets.QPushButton(self)
        self.button_Reset.setText("Zapisz")
        self.button_Reset.setGeometry(155, 365, 95, 30)
        self.button_Reset.clicked.connect(self.zapisz)

        self.button_Reset = QtWidgets.QPushButton(self)
        self.button_Reset.setGeometry(250, 365, 95, 30)
        self.button_Reset.setText("Anuluj")
        self.button_Reset.clicked.connect(self.anuluj)


    def check_update(self, version=None):
        if version:
            self.version = version

        app_update_status = None

        try:
            app_update_status = check_app_update_status(self.version)
        except Exception as e:
            logging.exception(e)

        if app_update_status == True:  
            self.button_check_update.setText("Dostępna jest aktualizacja.") 
            self.button_check_update.setStyleSheet('background-color: "#975D9F"')  
        if app_update_status == False:
            self.button_check_update.setText("Wersja aktualna.")
            self.button_check_update.setStyleSheet('background-color: "#77C66E"')
        if app_update_status == "Offline":
            self.button_check_update.setText("Brak Internetu!")
            self.button_check_update.setStyleSheet('')
        if app_update_status == None:
            self.button_check_update.setText("Błąd!")
            self.button_check_update.setStyleSheet('background-color: "#ab2c0c"')

    def simple_check_update(self, version=None):
        app_update_status = None
        
        try:
            app_update_status = check_app_update_status(version)
        except Exception as e:
            logging.exception(e)

        if app_update_status == True:  
            return app_update_status  

    def reset(self):
        self.settings.clear()
        self.close()

    def zapisz(self):
        self.settings.setValue("LastGML", self.last_gml.isChecked())
        self.settings.setValue("StripID", self.strip_gml.isChecked())
        self.settings.setValue("ShortOwnerAddr", self.short_owner_addr.isChecked())
        self.settings.setValue("AddObreb", self.add_obreb_coll.isChecked())
        self.settings.setValue("DarkMode", self.dark_mode.isChecked())
        self.settings.setValue("MapStaysOnTopHint", self.map_flag.isChecked())
        self.settings.setValue("FullID", self.points_id.isChecked())
        self.settings.setValue("FullScreen", self.full_scene.isChecked())
        #self.settings.setValue("UproszczonaMapa", self.uproszczona_mapa.isChecked())
        #settings.setValue("windowSize", self.size())
        self.close()

    def anuluj(self):
        for i, k in self.save_value:
            self.settings.setValue(i, k)
        self.close()

    def change_path_settings(self):
        if not hasattr(self, 'settings_window') or self.settings_window is None:
            self.settings_window = WorkspaceSettingsWindow(file_manager, parent=self)
            self.settings_window.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()


if __name__ == '__main__':
    app = QApplication( sys.argv )

    settings = QSettings('GML', 'GML Reader')
    dark_mode_enabled = settings.value('DarkMode', False, type=bool)

    try:
        if settings.value('DarkMode', True, type=bool):
            app.setStyleSheet(Path('Stylesheets/Darkmode.qss').read_text())        
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

    ConfigWindow = SettingsWindow(dark_mode_enabled=dark_mode_enabled)
    ConfigWindow.show()
    sys.exit(app.exec())
