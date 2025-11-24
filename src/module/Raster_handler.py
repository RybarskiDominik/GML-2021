from PySide6.QtWidgets import (QApplication, QGraphicsLineItem, QMainWindow,
                               QGraphicsItem, QFileDialog, QCheckBox, QTableWidget,
                               QGraphicsEllipseItem, QTableWidgetItem, QLineEdit,
                                QMainWindow, QGraphicsView, QGraphicsScene,
                               QGraphicsPolygonItem, QGraphicsTextItem, QSpacerItem,
                               QProgressBar, QSplashScreen, QSizePolicy, QPushButton,
                               QGraphicsPixmapItem, QMenu, QSplitter,
                               QMainWindow, QWidget, QTextEdit, QGridLayout,
                               QSplitter, QFrame, QVBoxLayout, QHBoxLayout)
    
from PySide6.QtGui import (QFont, QPolygonF, QPolygonF, QPainter, QFont, QColor, QTransform,
                           QBrush, QPen, QIcon, QPainterPath, QPixmap, QPalette, QCursor,
                           QKeySequence, QShortcut)
from PySide6.QtCore import Signal, QSettings, Qt, QRectF, QThread, QByteArray, QTimer
from PySide6 import QtCore, QtWidgets, QtGui

import rasterio
from io import BytesIO
import requests
import pandas as pd
from model.WMS_processing import WMS_processing
import os
import sys
import logging

logger = logging.getLogger(__name__)

class Raster_handler(QMainWindow):
    search_in_map = Signal()
    raster_signal = Signal(str, str)
    update_statusbar = Signal(str)
    update_statusbar_timeout = Signal()
    def __init__(self):
        super().__init__()
        self.df = pd.DataFrame()

        #self.setHorizontalHeaderLabels(["Dane", "Akcje"])

        self.setWindowTitle("Raster Handler")
        self.setMinimumSize(1000, 430)
        
        self.epsg = "EPSG::2177"

        self.init_UI()
        self.init_btn()

    def init_UI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 2, 0, 0)  # Remove margins
        self.main_layout.setSpacing(2)

        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(0)

        self.table_widget = QTableWidget(self)

    def init_btn(self):

        self.btn_wsp = QPushButton('WSP z Mapy', self)
        self.btn_wsp.setFixedWidth(80)
        self.btn_wsp.setFixedHeight(25)
        #self.btn_wsp.move(2, 2)
        self.btn_wsp.clicked.connect(self.emit_search_signal)
        self.btn_wsp.setToolTip("Po naciśnięciu przycisku wybierz miejsce na mapie, skąd ma być pobrana lista rastrów.")

        self.epsg_list = QtWidgets.QComboBox(self)
        my_epsg_list = ["EPSG::2176", "EPSG::2177", "EPSG::2178", "EPSG::2179"]
        self.epsg_list.addItems(my_epsg_list)
        self.epsg_list.setMaxVisibleItems(30)
        self.epsg_list.setCurrentIndex(1)
        #self.epsg_list.setFont()
        self.epsg_list.setView(QtWidgets.QListView())
        self.epsg_list.setFixedWidth(100)
        self.epsg_list.setFixedHeight(25)


        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.epsg_list)
        self.button_layout.addWidget(self.btn_wsp)
        
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addWidget(self.table_widget)


    def get_raster_from_WMS(self, position):
        try:
            x = position.x()  # Pobranie współrzędnej X
            y = abs(position.y())  # Pobranie współrzędnej Y
            epsg = self.epsg_list.currentText()  # Pobranie wybranego EPSG

            print(f"Pobieranie rastra dla: x={x}, y={y}, EPSG={epsg}")
            
            ORTOFOTOMAPA_WMS_URL = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/SkorowidzeWgAktualnosci?"
            wms = WMS_processing()
            data = wms.get_raster_from_wms(ORTOFOTOMAPA_WMS_URL, x, y, self.epsg)
            wms.repair_data(data)
            wms.create_and_sort_df()

            self.add_df(wms.df)

            self.update_statusbar.emit("WMS raster downloaded successfully.")
            QTimer.singleShot(5000, self.update_statusbar_timeout.emit)
        except Exception as e:
            logging.exception(e)
            print(e)

    def castom_df(self):
        data = [
            {"url": "https://opendata.geoportal.gov.pl/ortofotomapa/79045/79045_1298044_M-34-87-A-c-4-4.tif", "Układ": "PL-1992", "Rok": 2023, "Kolor": "RGB", "Piksel": 0.25, "Skala": "1:5000", "Godło": "M-34-87-A-c-4-4"},
            {"url": "https://opendata.geoportal.gov.pl/ortofotomapa/79045/79045_1298044_M-34-87-A-c-4-4.tif", "Układ": "PL-1992", "Rok": 2019, "Kolor": "RGB", "Piksel": 0.25, "Skala": "1:5000", "Godło": "M-34-87-A-c-4-4"},
            {"url": "https://opendata.geoportal.gov.pl/ortofotomapa/66701/66701_679814_6.113.31.16.tif", "Układ": "PL-2000:S6", "Rok": 2017, "Kolor": "RGB", "Piksel": 0.1, "Skala": "1:2000", "Godło": "6.113.31.16"},
            {"url": "https://opendata.geoportal.gov.pl/ortofotomapa/79045/79045_1298044_M-34-87-A-c-4-4.tif", "Układ": "PL-2000:S7", "Rok": 2017, "Kolor": "RGB", "Piksel": 0.1, "Skala": "1:5000", "Godło": "M-34-87-A-c-4-4"},
            {"url": "https://opendata.geoportal.gov.pl/ortofotomapa/66049/66049_515417_6.113.31.16.tif", "Układ": "PL-2000:S6", "Rok": 2015, "Kolor": "RGB", "Piksel": 0.1, "Skala": "1:2000", "Godło": "6.113.31.16"},
            {"url": "https://opendata.geoportal.gov.pl/ortofotomapa/79045/79045_1298044_M-34-87-A-c-4-4.tif", "Układ": "PL-2000:S7", "Rok": 2015, "Kolor": "CIR", "Piksel": 0.25, "Skala": "1:5000", "Godło": "M-34-87-A-c-4-4"},
            {"url": "https://opendata.geoportal.gov.pl/ortofotomapa/79045/79045_1298044_M-34-87-A-c-4-4.tif", "Układ": "PL-1992", "Rok": 2009, "Kolor": "RGB", "Piksel": 0.25, "Skala": "1:5000", "Godło": "M-34-87-A-c-4-4"},
            {"url": "https://opendata.geoportal.gov.pl/ortofotomapa/79045/79045_1298044_M-34-87-A-c-4-4.tif", "Układ": "PL-1992", "Rok": 2003, "Kolor": "B/W", "Piksel": 0.25, "Skala": "1:5000", "Godło": "M-34-87-A-c-4-4"},
            {"url": "https://opendata.geoportal.gov.pl/ortofotomapa/79045/79045_1298044_M-34-87-A-c-4-4.tif", "Układ": "PL-1992", "Rok": 2003, "Kolor": "RGB", "Piksel": 1.0, "Skala": "1:5000", "Godło": "M-34-87-A-c-4-4"},
            {"url": "https://opendata.geoportal.gov.pl/ortofotomapa/79045/79045_1298044_M-34-87-A-c-4-4.tif", "Układ": "PL-1992", "Rok": 1999, "Kolor": "RGB", "Piksel": 0.65, "Skala": "1:10000", "Godło": "M-34-87-A-c-4"}
            ]

        df = pd.DataFrame(data)
        df = df.sort_values(["Rok", "Układ"], ascending=[False, False])
        self.add_df(df)

    def add_df(self, df):
        self.df = df
        self.table_widget.clearContents()  # Usuwa zawartość komórek, ale zachowuje nagłówki
        self.table_widget.setRowCount(0)  # Usuwa wszystkie wiersze
        self.table_widget.clear()  
        self.table_widget.setColumnCount(len(df.columns) + 1)  # Dodatkowa kolumna na przyciski
        self.table_widget.setHorizontalHeaderLabels(df.columns.astype(str).tolist() + ["Akcje"])

        for r in range(len(df.index)):
            self.table_widget.insertRow(r)
            for k in range(len(df.columns)):
                self.table_widget.setItem(r, k, QTableWidgetItem(str(df.iloc[r, k])))

            btn_send, btn_pobierz = self.create_button_cell(r)

            # Jeśli w kolumnie "Układ" nie ma "PL-2000", dezaktywuj przycisk "Send"
            if "Układ" in df.columns: # and df.iloc[r]["Układ"].startswith("PL-2000"):
                btn_send.setDisabled(False)
                btn_send.setStyleSheet("background-color: green; color: white;")

            self.table_widget.setCellWidget(r, len(df.columns), self.create_button_layout(btn_send, btn_pobierz))

        self.table_widget.resizeColumnsToContents()

    def create_button_cell(self, row):
        btn_send = QPushButton("Send to MAP")
        btn_send.setDisabled(True)
        btn_pobierz = QPushButton("Pobierz")

        btn_send.clicked.connect(lambda: self.on_send_clicked(row))
        btn_pobierz.clicked.connect(lambda: self.on_pobierz_clicked(row))

        return btn_send, btn_pobierz

    def create_button_layout(self, btn_send, btn_pobierz):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(btn_send)
        layout.addWidget(btn_pobierz)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    def on_send_clicked(self, row):
        url = None
        try:
            url = self.df.loc[row, 'url']
            Godło = self.df.loc[row, 'Godło']
        except Exception as e:
            logging.exception(e)
            return
        self.send_raster_to_scen(url, Godło)

    def on_pobierz_clicked(self, row):
        """Handles the button click event to download a raster file."""
        try:
            url = self.df.loc[row, 'url']
            Godło = self.df.loc[row, 'Godło']
        except Exception as e:
            logging.exception(e)
            return

        self.download_raster(url)

    def download_raster(self, url):
        """Downloads a raster file from the given URL and processes it using add_tif."""
        filename = url.split("/")[-1]  # Extract filename from URL
        filename = filename.rsplit('_')[-1]
        print(filename)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Select a file', os.path.expanduser("~/Desktop") + f"/{filename}", 'TIF File (*.tif)'
        )

        if not file_path:  # If the user cancels, return early
            print("Download canceled.")
            return

        #print(f"Saving file as: {file_path}")

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an error for bad status codes (4xx, 5xx)

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            
            print(f"Raster downloaded successfully: {file_path}")

        except requests.RequestException as e:
            print(f"Failed to download raster: {e}")

    def send_raster_to_scen(self, url, godlo):
        epsg = self.epsg_list.currentText()
        epsg = epsg.split("::")[1]
        self.raster_signal.emit(url, epsg)

    def get_tif_from_url(url):
        """Pobiera plik TIFF bez zapisu na dysk i zwraca jego dane jako numpy array."""
        
        response = requests.get(url)
        if response.status_code == 200:
            tif_data = BytesIO(response.content)  # Konwersja na plik w pamięci
            
            with rasterio.open(tif_data) as dataset:
                array = dataset.read()  # Odczytuje dane rastrowe jako numpy array
                metadata = dataset.meta  # Pobiera metadane pliku

            return array, metadata  # Zwracamy dane jako numpy array + metadane
        
        else:
            print(f"❌ Błąd pobierania: {response.status_code}")
            return None, None

    def emit_search_signal(self):
        self.update_statusbar.emit("Wybierz miejsce na mapie, skąd ma być pobrana lista rastrów.")
        self.search_in_map.emit()

if __name__ == '__main__':

    # ['SkorowidzeOrtofotomapy2024', 'SkorowidzeOrtofotomapy2023', 'SkorowidzeOrtofotomapy2022', 'SkorowidzeOrtofotomapyStarsze', 'SkorowidzeOrtofotomapyZasiegi2024', 'SkorowidzeOrtofotomapyZasiegi2023', 'SkorowidzeOrtofotomapyZasiegi2022', 'SkorowidzeOrtofotomapyZasiegiStarsze']

    ORTOFOTOMAPA_WMS_URL = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/SkorowidzeWgAktualnosci?"
    LAYER_NAME = "SkorowidzeOrtofotomapy2022"
    LAYER_NAME = "SkorowidzeOrtofotomapyStarsze"

    url = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/SkorowidzeWgAktualnosci?SERVICE=WMS&REQUEST=GetCapabilities"

    x = 6580874.94
    y = 5486367.14

    app = QApplication(sys.argv)
    table = Raster_handler()
    table.show()
    sys.exit(app.exec())