from PySide6.QtWidgets import (QApplication, QGraphicsLineItem, QMainWindow,
                               QGraphicsItem, QFileDialog, QCheckBox, QTableWidget,
                               QGraphicsEllipseItem, QTableWidgetItem, QLineEdit,
                               QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
                               QGraphicsPolygonItem, QGraphicsTextItem, QSpacerItem,
                               QProgressBar, QSplashScreen, QSizePolicy, QPushButton,
                               QGraphicsPixmapItem, QMenu, QSplitter, QApplication,
                               QMainWindow, QWidget, QTextEdit, QPushButton, QGridLayout,
                               QSplitter, QFrame, QVBoxLayout, QHBoxLayout, QTableView, 
                               QMessageBox, QHeaderView, QStyledItemDelegate, QComboBox)
    
from PySide6.QtGui import (QFont, QPolygonF, QPolygonF, QPainter, QFont, QColor, QTransform,
                           QBrush, QPen, QIcon, QPainterPath, QPixmap, QPalette, QCursor,
                           QKeySequence, QShortcut)
from PySide6.QtCore import Signal, QSettings, Qt, QRectF, QThread, QByteArray, QModelIndex, QUrl
from PySide6.QtGui import QStandardItem, QStandardItemModel, QDesktopServices
from PySide6 import QtCore, QtWidgets, QtGui
from dataclasses import dataclass
from os.path import exists
from pathlib import Path
import pandas as pd
import numpy as np
import webbrowser
import logging
import random
import shutil
import time
import sys
import os
import re

logger = logging.getLogger(__name__)

from docx import Document
from model.python_docx_replace import docx_replace
from function.FileMenager import FileManager

file_management = FileManager()


class BooleanComboBoxDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(["True", "False"])
        return combo

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setCurrentText(str(value))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)


class DataFrameTableModel(QStandardItemModel):
    def __init__(self, df=None):
        super().__init__()
        self._df = df #if df is not None else pd.DataFrame(columns=["Name", "Tag", "Data"])
        #self.history = [self._df.copy()]
        self.default_df = None
        self.history = []
        self.add_to_history_flag = False
        self.add_default_value = False

        self.itemChanged.connect(self.on_item_changed)

        self.update_view()

    def update_view(self):
        """Synchronize the view with the DataFrame."""
        if self._df is None:
            self._df = pd.DataFrame(columns=['Name', 'Tag', 'Data'])

        self.clear()
        self.setHorizontalHeaderLabels(self._df.columns.tolist())
        self.setRowCount(len(self._df))
        self.setColumnCount(len(self._df.columns))

        for row in range(len(self._df)):
            for col in range(len(self._df.columns)):
                value = self._df.iat[row, col]
                self.setItem(row, col, QStandardItem(str(value)))
        
        if not self.add_to_history_flag:
            self.add_to_history()  # Only add to history when it's not an undo action
        else:
            self.add_to_history_flag = False  # Reset the flag after adding history

    def add_to_history(self):
        """Add current state of the DataFrame to history."""
        self.history.append(self._df.copy())
        #print(self.history)

    def undo(self):
        """Undo the last change by reverting to the previous DataFrame."""

        if len(self.history) > 1:
            self.history.pop()  # Usuwamy ostatnią wersję
            self._df = self.history[-1].copy()  # Przywracamy poprzednią wersję
            self.add_to_history_flag = True
            self.update_view()  # Aktualizujemy widok
        else:
            QMessageBox.warning(None, "Error", "No more changes to undo.")

    def add_row(self, name, tag):
        """Add a new tag to the table."""

        if tag in self._df["Tag"].values:
            QMessageBox.warning(None, "Error", f"Tag '{tag}' already exists.")
            return

        new_row = pd.DataFrame([[name, tag, ""]], columns=self._df.columns)
        self._df = pd.concat([self._df, new_row], ignore_index=True)
        self.add_to_history_flag = True
        self.update_view()

    def on_item_changed(self, item):
        if self.add_default_value and not self.add_to_history_flag:
            row = item.row()
            col = item.column()
            value = item.text()
            self._df.iat[row, col] = value
            self.add_to_history()
            #print(f"Changed row {row}, column {col} to {value}")

    def add_default_df(self, default_df):
        """Set the default values for the DataFrame."""
        self.default_df = default_df.copy()
        self._df = default_df.copy()
        self.history.clear()  # Clear history
        #self.add_to_history()  # Add the default state to history
        self.update_view()
        self.add_default_value = True

    def reset_to_default(self):
        """Reset the DataFrame to its default state."""
        if self.default_df is not None:
            self._df = self.default_df.copy()
            self.add_to_history_flag = True
            self.update_view()
        else:
            QMessageBox.warning(None, "Error", "Default values not set.")

    def remove_row(self, tag):
        """Remove a row with a given tag."""
        if tag not in self._df["Tag"].values:
            QMessageBox.warning(None, "Error", f"Tag '{tag}' not found.")
            return

        self._df = self._df[self._df["Tag"] != tag].reset_index(drop=True)
        self.add_to_history_flag = True
        self.update_view()

    def get_dataframe(self):
        """Return the current DataFrame."""
        return self._df


class GML_Handler(QMainWindow):
    turn_on_polygon_selection_signal = Signal()  # Sygnał do żądania włączenia wyboru poligonów
    find_polygons_signal = Signal()  # Sygnał do żądania find_polygons
    find_overlap_polygons_signal = Signal()  # Sygnał do żądania find_overlap_polygons
    polygons_found = Signal(object)  # Sygnał do przesyłania wyników find_polygons
    overlap_polygons_found = Signal(object)  # Sygnał do przesyłania wyników find_overlap_polygons
    def __init__(self, GML=None, proj_data=None):
        super().__init__()
        self.proj_data = proj_data
        self.df = pd.DataFrame()
        self.df = pd.DataFrame(columns=["Lp.", "NR", "Data"])
        self.settings = QSettings('GML', 'GML Reader')
        self.dark_mode_enabled = self.settings.value('DarkMode', False, type=bool)

        self.Path = file_management.templates_folder_path
        self.check_path()  # Check if the path is set correctly

        self.setWindowTitle("GML Handler")
        self.setBaseSize(450, 430)
        self.setMinimumSize(450, 430)

        self.GML = GML
        self.initUI()
        self._setup_icons()

    def initUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 2, 0, 0)  # Remove margins
        main_layout.setSpacing(2)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(0)
        
        # Input fields for adding a tag
        self.main_docx_path = QComboBox(self)
        self.main_docx_path.setFixedWidth(155)
        self.main_docx_path.addItem("Select path to docx files")  # Add default item
        self.main_docx_path.setToolTip("Folder w którym są umieszczone pliki *.DOCX służące jako formatka do zawiadomień")
        self.set_file_name_in_QComboBox()

        self.add_file = QPushButton(self)
        #self.add_file.setText("Formatki++")
        self.add_file.setFixedWidth(25)
        self.add_file.setFixedHeight(25)
        self.add_file.setToolTip("Dodaj formatki *.DOCX")
        self.add_file.clicked.connect(self.set_file_name_in_QComboBox)
        self.add_file.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self.Path)))

        self.refresh_button = QPushButton(self)
        #self.refresh_button.setText("Odśwież")
        self.refresh_button.setFixedWidth(25)
        self.refresh_button.setFixedHeight(25)
        self.refresh_button.setToolTip("Odśwież listę plików")
        self.refresh_button.clicked.connect(lambda: self.set_file_name_in_QComboBox)

        self.gml_button = QPushButton('Wypełnij', self)
        self.gml_button.setDisabled(True)
        self.gml_button.setFixedWidth(55)
        self.gml_button.setFixedHeight(25) 
        self.gml_button.move(300, 2)
        self.gml_button.clicked.connect(self.gml)
        self.gml_button.setToolTip("Wypełnia tabelę danymi osobowymi z pliku GML.")
        self.gml_button.clicked.connect(self.btn_handler)
        
        self.docx_button = QPushButton('DOCX', self)
        self.docx_button.setDisabled(True)
        self.docx_button.setFixedWidth(55)
        self.docx_button.setFixedHeight(25)
        self.docx_button.move(300, 2)
        self.docx_button.clicked.connect(self.fill_docx)
        self.docx_button.setToolTip('Wypełnia zawiadomienia danymi z tabeli. Plik "Zawaidomienie.docx" powinien być w folderze DOCX.')
        
        self.btn_upr = QCheckBox('Upr.', self)
        self.btn_upr.move(170, 20)
        self.btn_upr.setCheckState(Qt.Checked)
        self.btn_upr.setToolTip("Uproszczone dane w tabeli.")
    
        self.export_button = QPushButton('Exportuj', self)
        self.export_button.setFixedWidth(60)
        self.export_button.setFixedHeight(25)
        self.export_button.move(2, 2)
        self.export_button.clicked.connect(self.export)
        self.export_button.setToolTip("Eksportuje dane, zmiany z tabeli nie są brane pod uwagę.")

        self.btn_pol = QCheckBox('Ustalenie', self)
        self.btn_pol.move(102, 20)
        self.btn_pol.stateChanged.connect(lambda state: self.request_turn_on_polygon_selection() if state == 2 else self.request_find_overlap_polygons())  # turn_off_polygon_selection
        self.btn_pol.setToolTip("Po naciśnięciu tego przycisku wybierz działki z mapy.")
        self.btn_pol.stateChanged.connect(self.btn_handler)

        self.btn_zaw = QCheckBox('Zawiadomienia', self)
        self.btn_zaw.move(170, 20)
        self.btn_zaw.stateChanged.connect(lambda state: self.request_turn_on_polygon_selection() if state == 2 else self.request_find_polygons())  # turn_off_polygon_selection
        self.btn_zaw.setToolTip("Po naciśnięciu tego przycisku wybierz działki z mapy.")
        self.btn_zaw.stateChanged.connect(self.btn_handler)

        self.table_model = DataFrameTableModel()
        self.table_model.add_default_df(self.df)
        self.table_view = QTableView(self)  # Set the parent to self (the main window)
        self.table_view.setModel(self.table_model)
        #self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        button_layout.addWidget(self.main_docx_path)
        button_layout.addWidget(self.add_file)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.gml_button)
        button_layout.addWidget(self.docx_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.btn_upr)
        button_layout.addStretch(1)
        button_layout.addWidget(self.btn_pol)
        button_layout.addWidget(self.btn_zaw)
        
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.table_view)

    def _setup_icons(self):
        """Konfiguruje wszystkie ikony na podstawie motywu."""
        icon_size = QtCore.QSize(22, 22)
        
        # Mapa ikon z ich rozmiarami
        icons_config = [
            (self.add_file, "Folder", icon_size),
            (self.refresh_button, "Refresh", icon_size),
        ]
        
        # Ustaw ikony dla wszystkich przycisków
        for button, icon_name, size in icons_config:
            icon_path = file_management.get_icon_path(icon_name, self.dark_mode_enabled)
            button.setIcon(QtGui.QIcon(icon_path))
            button.setIconSize(size)

    def btn_handler(self):
        sender = self.sender()

        if sender == self.gml_button:
            self.docx_button.setDisabled(False)
        else:
            self.docx_button.setDisabled(True)
        
        self.gml_button.setDisabled(False)

    def set_file_name_in_QComboBox(self, path_to_folder=None):
        self.check_path()

        # Clear the QComboBox
        self.main_docx_path.clear()
        
        if not path_to_folder:
            path_to_folder = self.Path

        # Check if the path exists and is a directory
        if os.path.isdir(path_to_folder):
            # Get a list of all .docx files in the folder
            docx_files = [file_name for file_name in os.listdir(path_to_folder) 
                        if os.path.isfile(os.path.join(path_to_folder, file_name)) and file_name.lower().endswith('.docx')]
            if docx_files:
                # Add each .docx file to the QComboBox
                for file_name in docx_files:
                    full_path = os.path.join(path_to_folder, file_name)
                    self.main_docx_path.addItem(file_name, full_path)
                # Set the first file as the current selection
                self.main_docx_path.setCurrentText(docx_files[0])
            else:
                # No .docx files found
                self.main_docx_path.addItem("Dodaj formatkę")
                self.main_docx_path.setCurrentText("Dodaj formatkę")
        else:
            # Handle case where the provided path is not valid
            self.main_docx_path.addItem("Invalid Path")
            self.main_docx_path.setCurrentText("Invalid Path")

    def check_path(self):
        try:
            if self.settings.value('DocxPath') is not None:
                self.Path = self.settings.value('DocxPath')
                self.Path = Path(self.Path) / 'Zawiadomienia'
                self.Path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.exception(e)

    def fill_docx(self):
        path_to_docx = self.main_docx_path.currentData()

        if not path_to_docx or not os.path.exists(path_to_docx):
            path_to_docx, _ = QFileDialog.getOpenFileName( self, 'Open docx file', os.path.expanduser("~/Desktop"), 'DOCX File(*.docx)')
        if not path_to_docx:
            return

        output_dir = QFileDialog.getExistingDirectory(None, "Select Output Folder", os.path.expanduser("~/Desktop"))
        if not output_dir:
            return

        if os.path.abspath(path_to_docx) == os.path.abspath(output_dir):
            return

        try:
            for idx, row in self.df.iterrows():
                data = row.to_dict()

                if data.get("KORES") == "True":
                    data["ADRES"] = data.get("ADRES_KORES.")
                    data["MIEJSCOWOŚĆ"] = data.get("MIEJSCOWOŚĆ_KORES.")
                else:
                    data["ADRES"] = data.get("ADRES_PODMIOT")
                    data["MIEJSCOWOŚĆ"] = data.get("MIEJSCOWOŚĆ_PODMIOT")

                if self.proj_data is not None:
                    data = data | self.proj_data

                doc = Document(path_to_docx)
                docx_replace(doc, data)

                #dzialka = str(data.get("idDzialki", "")).strip()
                #dzialka = dzialka.split('.')[-1]
                #dzialka = re.sub(r'\W+', '_', dzialka)  # zamienia wszystko co nie jest \w (litera, cyfra, _) na _

                podmiot = str(data.get("PODMIOT", "")).strip()
                podmiot = re.sub(r'\W+', '_', podmiot)

                dzialka = str(data.get("idDzialki")).lstrip().replace('/', '_').replace('\\', '_')
                dzialka = dzialka.split('.')[-1]
                #podmiot = str(data.get("PODMIOT")).lstrip().replace('/', '_').replace('\\', '_')

                output_path = os.path.join(output_dir, f"{dzialka} - {podmiot}.docx")

                doc.save(output_path)
        except Exception as e:
            logging.exception(e)
            print("Error while filling docx:", e)

    def gml(self):

        default_columns = [
            "idDzialki", "Działka", "numerKW", "poleEwidencyjne", "dokladnoscReprezentacjiPola", "rodzajPrawa", 
            "udzialWlasnosci", "rodzajWladania", "udzialWladania", 'nazwaPelna', 'nazwaSkrocona',
            "pierwszeImie", "drugieImie", "pierwszyCzlonNazwiska", "drugiCzlonNazwiska", "imieOjca",
            "imieMatki", "plec", "pesel", "regon", "status", "informacjaOSmierci", "IDM", "kraj",
            "miejscowosc", "kodPocztowy", "ulica", "numerPorzadkowy", "numerLokalu", "KORES", "kraj_Kores.", 
            "miejscowosc_Kores.", "kodPocztowy_Kores.", "ulica_Kores.", "numerPorzadkowy_Kores.",
            "numerLokalu_Kores.", "grupaRejestrowa", "idJednostkiRejestrowej", "DZIALKA-ALL"
            ]
        
        easy_columns = [
            "idDzialki", "Działka", "numerKW", "PODMIOT", "ADRES_PODMIOT", "MIEJSCOWOŚĆ_PODMIOT", 
            "KORES", "ADRES_KORES.", "MIEJSCOWOŚĆ_KORES.", "DZIALKA-ALL"
        ]
        
        df = self.table_model.get_dataframe()
        df = df.copy()
        if "ID" in df.columns:
            default_columns = ["ID"] + default_columns

        try:
            self.df = pd.merge(df, self.GML, how='left', left_on='Działka', right_on='idDzialki')
            self.df = self.restore_df_columns(self.df, default_columns)
        except Exception as e:
            logging.exception(e)
            print(e)

        try: # łączenie danych
            kores_cols = [col for col in self.df.columns if col.endswith('_Kores.')]
            self.df["KORES"] = self.df[kores_cols].apply(lambda row: row.astype(str).str.strip().ne("").any(), axis=1)

            self.df["Działka"] = self.df["Działka"].str.split('.').str[-1]

            self.df["PODMIOT"] = self.df["nazwaPelna"].mask(
                self.df["nazwaPelna"] == "",
                self.df["pierwszeImie"] + " " + self.df["pierwszyCzlonNazwiska"]
                )
            
            self.df["ADRES_PODMIOT"] = (self.df["ulica"] + " " + self.df["numerPorzadkowy"] + 
                                        self.df["numerLokalu"].apply(lambda x: f" Lokal nr {x}" if pd.notna(x) and str(x).strip() != "" else "")
                                        )
            self.df["MIEJSCOWOŚĆ_PODMIOT"] = self.df["kodPocztowy"] + " " + self.df["miejscowosc"]  + " " + self.df["kraj"]

            self.df["ADRES_KORES."] = (self.df["ulica_Kores."] + " " + self.df["numerPorzadkowy_Kores."] + 
                                        self.df["numerLokalu_Kores."].apply(lambda x: f" Lokal nr {x}" if pd.notna(x) and str(x).strip() != "" else "")
                                        )
            self.df["MIEJSCOWOŚĆ_KORES."] = self.df["kodPocztowy_Kores."] + " " + self.df["miejscowosc_Kores."]  + " " + self.df["kraj_Kores."]

            dzialki_all = ", ".join(sorted(self.df["Działka"].astype(str).unique()))
            self.df["DZIALKA-ALL"] = dzialki_all

            #self.df["PODMIOT"] = self.df["nazwaPelna"].fill "" (self.df["pierwszeImie"] + " " + self.df["pierwszyCzlonNazwiska"])

        except Exception as e:
            logging.exception(e)
            print(e)
            print("Error while processing GML data.")
            self.df["PODMIOT"]  = None
            self.df["ADRES_PODMIOT"] = None
            self.df["MIEJSCOWOŚĆ_PODMIOT"] = None 

        if self.btn_upr.isChecked() == True:  # Sort columns
            columns = easy_columns
        else:
            columns = default_columns

        self.table_model._df = self.df[columns]
        self.table_model.update_view()

        #kores_col = df.columns.get_loc("KORES")
        #self.table_view.setItemDelegateForColumn(kores_col, BooleanComboBoxDelegate(self.table_view))
        
        self.table_view.resizeColumnsToContents()


    def restore_df_columns(self, df, default_columns):
        try:
            df = df.copy()
            for col in default_columns:
                if col not in df.columns:
                    df[col] = None

            df = df[default_columns]
        except Exception as e:
            logging.exception(e)
            print(e)

        return df


    def receve_table_content(self, data):
        self.proj_data = data
        #print(self.proj_data)

    def request_turn_on_polygon_selection(self):
        """Wysyła żądanie do MapGraphicView o włączenie wyboru poligonów."""
        self.turn_on_polygon_selection_signal.emit()

    def request_find_polygons(self):
        """Wysyła żądanie do MapGraphicView o znalezienie poligonów."""
        self.find_polygons_signal.emit()

    def request_find_overlap_polygons(self):
        """Wysyła żądanie do MapGraphicView o znalezienie nakładających się poligonów."""
        self.find_overlap_polygons_signal.emit()

    def handle_polygons_found(self, data):
        """Obsługuje wyniki znalezionych poligonów."""
        self.update_table(data)
        print("Polygons found:", data)

    def handle_overlap_polygons_found(self, data):
        """Obsługuje wyniki nakładających się poligonów."""
        self.update_table(data)
        print("Overlap polygons found:", data)

    def update_table(self, df):
        """Aktualizuje widok tabeli."""
        self.df = df
        self.table_model._df = self.df
        self.table_model.update_view()
        
        self.table_view.resizeColumnsToContents()

    def export(self):
        #print(self.proj_data)
        name = QFileDialog.getSaveFileName(self, 'select a file', os.path.expanduser("~/Desktop"),'Excel File(*.xlsx)')
        if name == ('', ''):
            return
        
        self.df.to_excel(name[0], index=True)

    def overlap_polygons(df_overlap_polygons):
        if data.parsed_gml is None or data.parsed_gml.empty:
            return
        else:
            try:
                parsed_gml_copy = data.parsed_gml.copy()
                parsed_gml_copy = parsed_gml_copy[parsed_gml_copy['Działka'].isin(df_overlap_polygons['Działka'])]
                parsed_gml_copy['Właściciele'] =parsed_gml_copy['Właściciele'] + ' ' + parsed_gml_copy['Nazwisko']
                parsed_gml_copy['Właściciele'] = parsed_gml_copy.groupby('Działka')['Właściciele'].transform(lambda x: ' '.join(x))
                parsed_gml_copy = parsed_gml_copy[['Działka', 'KW', 'Właściciele', 'Adres', 'Adres Korespodencyjny']]
                parsed_gml_copy = parsed_gml_copy.drop_duplicates(subset='Działka')

                df_overlap_polygons = df_overlap_polygons.merge( parsed_gml_copy, how='left', on='Działka')

            except Exception as e:
                logging.exception(e)
        try:
            df_overlap_polygons.to_excel(connect.target_xlsx, index = False)
            os.startfile(connect.target_xlsx)
        except Exception as e:
            logging.exception(e)
            print("Not saved to excel.")

    def overlap_polygons_auto(df_overlap_polygons):
        df_overlap_polygons.to_excel(connect.target_xlsx, index=False)

        # Otwórz plik Excel
        os.startfile(connect.target_xlsx)

        # Uzyskaj dostęp do arkusza w pliku Excel
        writer = pd.ExcelWriter(connect.target_xlsx, engine='xlsxwriter')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']  # 'Sheet1' to nazwa arkusza

        # Iteruj przez wszystkie kolumny i dostosuj szerokość
        for i, column in enumerate(df_overlap_polygons.columns):
            column_len = max(df_overlap_polygons[column].astype(str).str.len().max(), len(column))
            worksheet.set_column(i, i, column_len + 2)  # +2 dla lepszego wyglądu

        # Zapisz zmiany i zamknij plik Excel
        writer.save()


if __name__ == '__main__':
    pass