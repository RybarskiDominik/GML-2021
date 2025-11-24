from PySide6.QtWidgets import (QApplication, QGraphicsLineItem, QMainWindow,
                               QGraphicsItem, QCheckBox, QGraphicsEllipseItem,
                               QApplication, QMainWindow, QGraphicsView,
                               QGraphicsScene, QGraphicsPolygonItem, QGraphicsTextItem,
                               QFileDialog, QStyleOptionGraphicsItem, QWidget, 
                               QGraphicsRectItem, QGraphicsSimpleTextItem,
                               QGraphicsPixmapItem, QMenu)
from PySide6.QtGui import (QFont, QPolygonF, QPolygonF, QPainter, QFont, QImage,
                           QColor, QBrush, QPen, QIcon, QPainterPath, QFontMetrics,
                           QPixmap, QAction)
from shapely.geometry import Polygon, MultiPolygon, Point, MultiLineString, LineString
from PySide6.QtCore import Qt, QPointF, QPoint, QRectF, QTimer, Signal, QSettings, QLineF, QSizeF
from PySide6.QtCore import QObject, Slot
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtSvg import QSvgRenderer
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from PySide6 import QtCore
from pathlib import Path
import geopandas as gpd
from io import BytesIO
import pandas as pd
import requests
import numpy as np

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

import rasterio
from rasterio.warp import transform
import rasterio.transform
from pyproj import CRS

from function.search_in_geoportal import open_parcel_in_geoportal
from function.search_in_street_view import open_parcel_in_street_view
from GML_processing.GML_processing_by_ET_Main_obf import GMLParser
from map_view.GraphicView_list import DraggableItemFrame

import logging
import math
import sys
import os

logger = logging.getLogger(__name__)

if getattr(sys, 'frozen', False):
    path_icons = os.path.dirname(sys.executable) + '\\gui\\Icons\\'    
else:
    folder = os.path.basename(sys.path[0])
    if folder == "src":
        path_icons = sys.path[0] + '\\gui\\Icons\\' 
    else:
        path_icons = sys.path[0] + '\\Icons\\'


class QDMGraphicsView(QGraphicsView):
    position_clicked = Signal(QPointF)
    rectangle_selected = Signal(QRectF)
    def __init__(self, scene=None, parent=None):
        super().__init__(scene, parent)
        self.setAcceptDrops(True)

        self.setDragMode(QGraphicsView.RubberBandDrag)

        #"""
        self.zoom_in_factor = 1.25
        #self.zoom_out_factor = 1 / 1.15
        self.zoom_clamp = True
        self.zoom_step = 1
        self.zoom = 10
        self.zoom_range = [0, 25]
        #"""

        #self.minZoom = 0
        #self.maxZoom = 80.0

        self.selecting_position = False

        self.selecting_rect = False
        self.rubber_band_origin = QPoint()
        self.rubber_band_rect_item = None

        self.middle_mouse_button_pressed = False
        self.last_mouse_position = QPoint()
        self.last_x_y_position = QPoint()

        self.initUI()
    
    def initUI(self):
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)

        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    
    def reset_zoom(self):
        """Reset zoom and transform to default scale."""
        self.resetTransform()
        self.zoom = 10

    def wheelEvent(self, event):
        zoom_out_factor = 1 / self.zoom_in_factor
    
        if event.angleDelta().y() > 0:  # Scroll up
            zoom_factor = self.zoom_in_factor
            self.zoom += self.zoom_step
        else:  # Scroll down
            zoom_factor = zoom_out_factor
            self.zoom -= self.zoom_step

        clamped = False
        if self.zoom < self.zoom_range[0]: self.zoom, clamped = self.zoom_range[0], True
        if self.zoom > self.zoom_range[1]: self.zoom, clamped = self.zoom_range[1], True


        if not clamped or self.zoom_clamp is False:
            self.scale(zoom_factor, zoom_factor)
    
    """
    def wheelEvent(self, event):
        delta = event.angleDelta().y()  # Pobierz kierunek obrotu kółka myszy
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)  # Przesuń widok tak, aby kursor myszy był w centrum
        if delta > 0:  # Przybliż, jeśli kółko myszy jest obracane do przodu
            factor = 1.25
            if self.transform().m11() * factor < self.maxZoom:
                self.scale(factor, factor)
        else:  # Oddal, jeśli kółko myszy jest obracane do tyłu
            factor = 0.8
            if self.transform().m11() * factor > self.minZoom:
                self.scale(factor, factor)
        self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)  # Przywróć kotwicę przekształcenia do domyślnej wartości
    """

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.middle_mouse_button_pressed = True
            self.last_mouse_position = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.RightButton:
            # NIE wywołuj super().mousePressEvent(event)
            self.contextMenuEvent(event)  # Ręcznie wywołujemy menu kontekstowe
        elif event.button() == Qt.LeftButton and self.selecting_rect:
            self.rubber_band_origin = event.position().toPoint()
            if self.rubber_band_rect_item:
                self.scene().removeItem(self.rubber_band_rect_item)
            self.rubber_band_rect_item = QGraphicsRectItem(QRectF(self.mapToScene(self.rubber_band_origin),
                                                                   self.mapToScene(self.rubber_band_origin)))
            self.rubber_band_rect_item.setPen(QPen(Qt.blue, 1, Qt.DashLine))
            self.scene().addItem(self.rubber_band_rect_item)
        else:
            if self.selecting_position:
                self.selecting_position = False
                self.last_x_y_position = self.mapToScene(event.position().toPoint())
                print(self.last_x_y_position)
                self.position_clicked.emit(self.last_x_y_position)
            if data.search_in_street_view:
                data.search_in_street_view = False
                self.last_x_y_position = self.mapToScene(event.position().toPoint())
                open_parcel_in_street_view(self.last_x_y_position, EPSG=data.EPSG)
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.selecting_rect:
            if self.rubber_band_rect_item:
                rect = self.rubber_band_rect_item.rect()
                self.rectangle_selected.emit(rect)  # emitujemy bbox w jednostkach sceny
                self.scene().removeItem(self.rubber_band_rect_item)
                self.rubber_band_rect_item = None
                self.stop_rect_selection()
        if event.button() == Qt.MiddleButton:
            self.middle_mouse_button_pressed = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def get_last_mouse_position(self):
        return self.last_x_y_position

    def mouseMoveEvent(self, event):
        if self.middle_mouse_button_pressed:
            # Oblicz przesunięcie myszy
            offset = self.last_mouse_position - event.position().toPoint()
            self.last_mouse_position = event.position().toPoint()

            # Przesuń widok
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + offset.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + offset.y())
        elif self.selecting_rect and self.rubber_band_rect_item:
            # aktualizacja rozmiaru prostokąta
            rect = QRectF(self.mapToScene(self.rubber_band_origin),
                          self.mapToScene(event.position().toPoint())).normalized()
            self.rubber_band_rect_item.setRect(rect)
        else:
            super().mouseMoveEvent(event)

    def dragEnterEvent(self, event):
        self.parent().dragEnterEvent(event)

    def dropEvent(self, event):
        self.parent().dropEvent(event)

    def contextMenuEvent(self, event):
        # Pokaż menu kontekstowe
        menu = QMenu(self)
        copy_action = QAction("Kopiuj zaznaczone działki", self)
        copy_action.triggered.connect(self.copy_selected_parcels)
        menu.addAction(copy_action)

        check_action = QAction("Kopiuj zaznaczone punkty", self)
        check_action.triggered.connect(self.check_selected_points)
        menu.addAction(check_action)

        menu.exec(event.globalPos())

    def copy_selected_parcels(self):
        selected_ids = []
        for item in self.scene().selectedItems():
            if isinstance(item, MyQGraphicsPolygonItem) and item.id is not None:
                parcel_number = item.id.split(".")[-1]
                selected_ids.append(parcel_number)

        if selected_ids:
            QApplication.clipboard().setText(", ".join(map(str, selected_ids)))
            print("Skopiowano do schowka:", selected_ids)
        else:
            print("Brak zaznaczonych działek.")

    def check_selected_points(self):
        selected = []
        for item in self.scene().items():
            if isinstance(item, CustomEllipse) and item.isSelected():
                selected.append(item.parent_item.id_punktu.split(".")[-1])

        if selected:
            QApplication.clipboard().setText(", ".join(map(str, selected)))
            print("Zaznaczone ID punktów:", selected)
        else:
            print("Brak zaznaczonych punktów.")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            # usuń zaznaczenie wszystkich działek
            for item in self.scene().selectedItems():
                if isinstance(item, MyQGraphicsPolygonItem):
                    item.setSelected(False)
            print("❌ Usunięto zaznaczenie działek")
        else:
            super().keyPressEvent(event)

    def set_external_signal(self, signal):
        """Podłączamy zewnętrzny sygnał wysyłający id działki"""
        signal.connect(self.highlight_parcel_by_id)

    def highlight_parcel_by_id(self, parcel_id):
        # szukamy poligonu po ID
        for item in self.scene().items():
            if isinstance(item, MyQGraphicsPolygonItem) and item.id == parcel_id:
                # ustaw kolor tymczasowy
                item.setColorForDuration(QtCore.Qt.green, 1000)
                
                # przybliżenie / centrum widoku na poligon
                if hasattr(self, 'centerOn'):  # jeśli self jest QGraphicsView
                    self.centerOn(item)
                    # opcjonalnie skalowanie, np. 2x zoom:
                    # self.resetTransform()
                    # self.scale(2, 2)
                break

    def start_rect_selection(self):
        """Wywołaj tę funkcję, aby włączyć tryb wyboru prostokątem."""
        self.selecting_rect = True

    def stop_rect_selection(self):
        """Wywołaj tę funkcję, aby wyłączyć tryb wyboru prostokątem."""
        self.selecting_rect = False
        if self.rubber_band_rect_item:
            self.scene().removeItem(self.rubber_band_rect_item)
            self.rubber_band_rect_item = None


class DraggableTextItem(QGraphicsSimpleTextItem):
    def __init__(self, text, parent=None):
        super(DraggableTextItem, self).__init__(text, parent)
        self.setFlag(QGraphicsSimpleTextItem.ItemIsMovable)
       
        #self.text = text

    def test_boundingRect(self):
        
        font_metrics = QFontMetrics(self.font())
        rect = font_metrics.boundingRect(self.text)
        rect = QRectF(rect.x(), rect.y(), rect.width(), rect.height())

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            pass  # Handle right-click if necessary
        super(DraggableTextItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        pass  # self.setCursor(Qt.OpenHandCursor)
        super(DraggableTextItem, self).mouseReleaseEvent(event)


class MyQGraphicsPolygonItem(QGraphicsPolygonItem):
    def __init__(self, polygon, id=None, parent=None):
        super(MyQGraphicsPolygonItem, self).__init__(polygon, parent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.id = id

        self.color_timer = QTimer()
        self.color_timer.timeout.connect(self.resetPolygonColor)

        self.setFlag(QGraphicsItem.ItemStacksBehindParent, False)
        self.highlight_brush = QBrush(QColor(255, 255, 0, 100))  # półprzezroczyste żółte
        self.highlight_z = -10  # pod poligonem
        self.temp_color_brush = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.id != None:
                modifiers = QApplication.keyboardModifiers()
                if modifiers & Qt.ShiftModifier:
                    self.setSelected(not self.isSelected())
                    event.ignore()  # przekaż do QGraphicsView, aby zaznaczanie działało
                    return

                """modifiers = QApplication.keyboardModifiers()
                if modifiers & Qt.ControlModifier:
                    # przełącz selekcję (toggle)
                    self.setSelected(not self.isSelected())
                elif modifiers & Qt.ShiftModifier:
                    # dodaj do selekcji
                    self.setSelected(True)
                else:
                    # odznacz inne i zaznacz tylko ten
                    for item in self.scene().selectedItems():
                        item.setSelected(False)
                    self.setSelected(True)"""

                connect.EmitID.send_item(self.id)
                print(f"Polygon {self.id} clicked.")
                
                if data.search_parcel_by_id:
                    open_parcel_in_geoportal(self.id)
                    print(f"Searching {self.id} in browser...")
                    data.search_parcel_by_id = False
                
                #self.setColorForDuration(QtCore.Qt.green, 500)

            else:
                return
        
        super(MyQGraphicsPolygonItem, self).mousePressEvent(event)
        #super().mousePressEvent(event)
        self.last_mouse_position = event.scenePos()

    def setColorForDuration(self, color, duration):
        self.temp_color_brush = QBrush(color)
        self.setZValue(10)  # na wierzch
        self.color_timer.start(duration)

    def resetPolygonColor(self):
        self.temp_color_brush = None
        self.setZValue(0)
        self.color_timer.stop()

    def paint(self, painter, option, widget):
        # Rysowanie highlight pod poligonem jeśli zaznaczony
        if self.isSelected():
            painter.save()
            painter.setBrush(self.highlight_brush)
            painter.setPen(Qt.NoPen)
            # narysuj pod poligonem
            painter.translate(0, 0)
            painter.drawPolygon(self.polygon())
            painter.restore()

        # Rysowanie samego poligonu
        if self.temp_color_brush:
            painter.setBrush(self.temp_color_brush)
        else:
            painter.setBrush(QBrush())

        #painter.setPen(QPen(Qt.black, 0.55))  # kontur poligonu
        painter.setPen(self.pen())
        painter.drawPolygon(self.polygon())


class SelectablePointItem:
    def __init__(self, scene, x, y, dot_size, text, font, color='black', id_punktu=None, attributes=None):
        self.scene = scene
        self.id_punktu = id_punktu
        self.attributes = attributes or {}

        # Tworzenie elipsy
        self.ellipse = CustomEllipse(self, x - dot_size / 2, y - dot_size / 2, dot_size, dot_size)
        self.ellipse.setBrush(QBrush(QColor(color)))
        self.ellipse.setPen(QPen(QColor('black' if color == 'white' else 'white'), 0.2))
        self.ellipse.setFlags(QGraphicsItem.ItemIsSelectable)
        self.ellipse.setZValue(1)

        # Tworzenie tekstu
        self.text = CustomText(self, text)
        self.text.setFont(font)
        self.text.setBrush(QBrush(QColor('black')))
        self.text.setPos(x + 0.3, y - 0.3)
        self.text.setZValue(1)
        self.text.setFlags(QGraphicsItem.ItemIsMovable)

        # Dodanie do sceny
        scene.addItem(self.ellipse)
        scene.addItem(self.text)

    def on_click(self):
        print(f"ID punktu: {self.id_punktu}")

        duration=300
        self.add_yellow_outline(duration) # ŻÓŁTA OBWÓDKA — tymczasowa

        #self.highlight_temporary()

    def add_yellow_outline(self, duration):
        rect = self.ellipse.rect().adjusted(-0.15, -0.15, 0.15, 0.15)  # Trochę większa
        outline = QGraphicsEllipseItem(rect)
        outline.setPen(QPen(QColor("yellow"), 0.2))
        outline.setBrush(Qt.NoBrush)
        outline.setZValue(self.ellipse.zValue() - 0.1)
        self.scene.addItem(outline)

        # Usunięcie obwódki po czasie
        QTimer.singleShot(duration, lambda: self.scene.removeItem(outline))

    def highlight_temporary(self, color=QColor("purple"), duration=300):
        # Ustaw fioletowy kolor
        self.text.setBrush(QBrush(color))

        # Przywróć po czasie
        QTimer.singleShot(duration, self.deselect)

    def deselect(self):
        # Przywróć standardowy wygląd
        self.text.setBrush(QBrush(QColor('black')))

    def open_info_window(self):
        """
        Otwiera dialog z informacjami o punkcie (self.attributes).
        Wyświetla klucz:wartość dla dostępnych pól.
        """
        # Jeśli brak danych, pokaż komunikat
        if not self.attributes:
            dlg = QDialog()
            dlg.setWindowTitle(f"Punkt {self.id_punktu}")
            layout = QVBoxLayout(dlg)
            layout.addWidget(QLabel("Brak dodatkowych danych."))
            dlg.exec()
            return

        dlg = QDialog()
        dlg.setWindowTitle(f"Punkt: {self.id_punktu}")
        dlg.setMinimumWidth(380)
        dlg.setMinimumHeight(400)
        layout = QVBoxLayout(dlg)

        # Lista pól, w preferowanej kolejności (uzupełnij jeśli chcesz inne nazwy)
        columns = ['idPunktu', 'geometria', 'sposobPozyskania',
                   'spelnienieWarunkowDokl', 'rodzajStabilizacji',
                   'oznWMaterialeZrodlowym', 'numerOperatuTechnicznego',
                   'dodatkoweInformacje']

        # Przygotuj tabelę - 2 kolumny: Pole / Wartość
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(['Pole', 'Wartość'])
        table.setRowCount(len(columns))

        for i, key in enumerate(columns):
            val = self.attributes.get(key, '')
            # Konwertuj np. numpy types / listy na string bezproblemowo
            try:
                val_str = str(val)
            except Exception:
                val_str = repr(val)

            key_item = QTableWidgetItem(str(key))
            key_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            val_item = QTableWidgetItem(val_str)
            val_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            table.setItem(i, 0, key_item)
            table.setItem(i, 1, val_item)

        table.horizontalHeader().setStretchLastSection(True)
        table.resizeColumnsToContents()

        layout.addWidget(table)

        # Przycisk zamykania
        btn_close = QPushButton("Zamknij")
        btn_close.clicked.connect(dlg.accept)
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

        dlg.exec()

# --- Elipsa z podpięciem do punktu ---
class CustomEllipse(QGraphicsEllipseItem):
    def __init__(self, parent, *args):
        super().__init__(*args)
        self.parent_item = parent

    def mousePressEvent(self, event):
        self.parent_item.on_click()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):  # Przy dwukliku otwieramy okno z informacjami
        try:
            self.parent_item.open_info_window()
        except Exception as e:
            logging.exception(e)
            print(e)
        event.accept()

# --- Tekst z podpięciem do punktu ---
class CustomText(QGraphicsSimpleTextItem):
    def __init__(self, parent, text):
        super().__init__(text)
        self.parent_item = parent

    def mousePressEvent(self, event):
        self.parent_item.on_click()
        #super().mousePressEvent(event)
  
        # Wymuszenie selekcji elipsy
        if not self.parent_item.ellipse.isSelected():
            self.parent_item.ellipse.setSelected(True)

        # NIE wywołujemy super() — aby zapobiec domyślnemu zachowaniu toggle
        event.accept()

    def mouseDoubleClickEvent(self, event):  # Przy dwukliku otwieramy okno z informacjami
        try:
            self.parent_item.open_info_window()
        except Exception as e:
            logging.exception(e)
            print(e)
        event.accept()


class EmitMap(QMainWindow):
    item_signal = Signal(str)
    def __init__(self): 
        super().__init__()
        
        connect.EmitID = self

    def send_item(self, id):
        self.item_signal.emit(id)


class connect:
    EmitID: str = None


@dataclass
class data:
    EPSG = None

    search_parcel_by_id = False
    search_in_street_view = False
    parsed_gml = None

    mark = []
    Archiwalne_obiekty_GML = []

    KonturKlasyfikacyjny = []
    KonturUzytkuGruntowego = []
    DzialkaEwidencyjna = []
    PunktGraniczny = []
    PunktGranicznyNumer = []
    PunktGranicznyOpis = []
    PunktGraniczny_STB = []
    Ogrodzenia = []
    Budynek = []
    Budynek_BDOT = []
    Budowle = []
    AdresNieruchomosci = []
    Raster2000 = []
    godło_rastra = []


class MapHandler:
    def __init__(self, scene=None, path=None, parent_window=None):
        self.scene = scene
        self.path = path
        self.parent_window = parent_window
        self.data = data()
        self.draggableFrame = None
        self.gview = None


    def init_graphic_map_view(self, map_widget, map_layout):  # === Tworzenie widoku mapy ===
        self.scene = QGraphicsScene()
        self.gview = QDMGraphicsView(map_widget)
        self.gview.setStyleSheet("""
                                 QGraphicsView {
                                     border: none;
                                     background-color: #e0e0e0;
                                 }""")
        self.gview.setScene(self.scene)
        self.gview.setGeometry(0, 0, 500, 500)
        self.gview.setAcceptDrops(True)
        map_layout.addWidget(self.gview, 0, 0, 1, 1)

        margin = 2000
        expanded_scene_rect = self.scene.sceneRect().adjusted(-margin, -margin, margin, margin)
        self.scene.setSceneRect(expanded_scene_rect)
        self.gview.setSceneRect(expanded_scene_rect)

        self.load_DraggableItemFrame(map_widget)  # Po inicjalizacji od razu dodaj DraggableFrame

    def load_visualizations(self, df):  # === Wczytanie wizualizacji (po imporcie GML) ===
        try:
            self.load_map(df)
            if self.draggableFrame:
                self.draggableFrame.update_list_widget(self._get_lista_warstw())
        except Exception as e:
            logging.exception(e)
            print(e)

    def load_DraggableItemFrame(self, map_widget):  # === Inicjalizacja ramki warstw ===
        #from GraphicView_list import DraggableItemFrame  # unikamy cyklicznego importu
        lista = self._get_lista_warstw()

        self.draggableFrame = DraggableItemFrame(x=5, y=5, h=270, lista=lista)
        self.draggableFrame.setParent(map_widget)
        self.draggableFrame.list_signal.connect(self.hide_items_by_list)
        self.draggableFrame.raise_()

    def _get_lista_warstw(self):  # === Pomocnicza funkcja budująca listę warstw ===
        return [
            ("EGB_DzialkaEwidencyjna", self.data.DzialkaEwidencyjna, True),
            ("EGB_PunktGraniczny", self.data.PunktGraniczny, True),
            ("EGB_PunktGranicznyNumer", self.data.PunktGranicznyNumer, False),
            ("EGB_PunktGranicznyOpis", self.data.PunktGranicznyOpis, False),
            ("EGB_KonturKlasyfikacyjny", self.data.KonturKlasyfikacyjny, False),
            ("EGB_KonturUzytkuGruntowego", self.data.KonturUzytkuGruntowego, False),
            ("EGB_Budynek", self.data.Budynek, True),
            ("EGB_AdresNieruchomosci", self.data.AdresNieruchomosci, True),
            ("BDOT_Budynek", self.data.Budynek_BDOT, True),
            ("OT_Ogrodzenia", self.data.Ogrodzenia, True),
            ("OT_Budowle", self.data.Budowle, True),
            ("Archiwalne obiekty GML", self.data.Archiwalne_obiekty_GML, True),
            ("Rastry", self.data.Raster2000, True),
            ("Mark points", self.data.mark, True)
        ]

    def refresh_layer_list(self):  # === Automatyczne odświeżenie listy warstw po dodaniu nowego elementu ===
        if self.draggableFrame:
            self.draggableFrame.update_list_widget(self._get_lista_warstw())

    def refresh_map_view(self):  # === Odświeżanie wizualizacji mapy oraz dostosowanie widoku ===
        try:
            if not hasattr(self, "gview") or self.gview is None:
                print("Brak obiektu QGraphicsView — nie można odświeżyć mapy.")
                return

            # Pobierz dane graficzne z GML
            if hasattr(self.parent_window, "gml"):
                df = self.parent_window.gml.df_GML_graphic_data
            else:
                print("Brak GML Parsera — nie można odświeżyć mapy.")
                return

            # Załaduj wizualizacje (czyści scenę i rysuje ponownie)
            self.load_visualizations(df)

            # Aktualizacja sceny i widoku
            self.scene.setSceneRect(self.scene.itemsBoundingRect())

            margin = 2000
            expanded_scene_rect = self.scene.sceneRect().adjusted(-margin, -margin, margin, margin)
            self.scene.setSceneRect(expanded_scene_rect)
            self.gview.setSceneRect(expanded_scene_rect)
            self.gview.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            self.gview.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

            # Ustaw widoczność warstw po odświeżeniu
            if self.draggableFrame:
                lista = self._get_lista_warstw()
                self.set_map_items_visible_by_list(lista)
                self.draggableFrame.update_list_widget(lista)

            # Reset powiększenia
            if hasattr(self.gview, "reset_zoom"):
                self.gview.reset_zoom()

        except Exception as e:
            logging.exception("Błąd podczas odświeżania widoku mapy: %s", e)
            print("Błąd przy odświeżaniu widoku mapy:", e)


    def find_parcel_in_geoportal(self):
        data.search_parcel_by_id = True

    def find_parcel_in_street_view(self):
        data.EPSG= self.data.EPSG
        data.search_in_street_view = True


    def add_layer(self, layer_name: str, items: list, visible: bool = True):
        """Dodaje nową warstwę do mapy i danych"""
        if not hasattr(self.data, layer_name):
            setattr(self.data, layer_name, [])

        layer_data = getattr(self.data, layer_name)
        layer_data.extend(items)

        # Ustaw widoczność elementów
        for item in items:
            item.setVisible(visible)
            item.setZValue(10)

        print(f"✅ Dodano warstwę: {layer_name} ({len(items)} elementów)")


    def add_selected_polygon_to_list(self):
        selected_polygons = {}
        for polygon in self.data.DzialkaEwidencyjna:
            if isinstance(polygon, MyQGraphicsPolygonItem) and polygon.scene() == self.scene:  # Separacja selekcji na różnych map.
                if polygon.isSelected():
                    selected_polygons[polygon.id] = polygon
        return selected_polygons

    def turn_on_polygon_selection(self):
        for polygon in self.data.DzialkaEwidencyjna:
            if polygon.scene() == self.scene:  # Separacja selekcji na różnych map.
                polygon.setAcceptHoverEvents(True)
                polygon.setFlag(MyQGraphicsPolygonItem.ItemIsSelectable)
                polygon.hoverEnter = lambda event, p=polygon: self.polygon_hover_enter(polygon)
                polygon.hoverLeave = lambda event, p=polygon: self.polygon_hover_leave(polygon)
    
    def turn_off_polygon_selection(self):
        for polygon in self.data.DzialkaEwidencyjna:
            if polygon.scene() == self.scene:  # Separacja selekcji na różnych map.
                polygon.setAcceptHoverEvents(False)
                polygon.setFlag(MyQGraphicsPolygonItem.ItemIsSelectable, False)
    
    def polygon_hover_enter(self, polygon):
        if polygon in self.selected_polygons:
            polygon.setBrush(QBrush(Qt.yellow))
        else:
            polygon.setBrush(QBrush(Qt.green))

    def polygon_hover_leave(self, polygon):
        if polygon in self.selected_polygons:
            polygon.setBrush(QBrush(Qt.yellow))
        else:
            polygon.setBrush(QBrush(Qt.NoBrush))

    def find_overlap_and_bordering_polygons(self):
        selected_polygons = self.add_selected_polygon_to_list()
        bordering_polygons_set = set()
        overlapping_pairs = []

        for id1, polygon1 in selected_polygons.items():
            for id2, polygon2 in selected_polygons.items():
                if id1 < id2 and polygon1.collidesWithItem(polygon2):
                    overlapping_pairs.append((id1, id2))
                    bordering_polygons_set.update([id1, id2])

        #self.turn_off_polygon_selection()

        # Prepare the DataFrame for overlapping pairs
        overlapping_data = [[i+1, pair[0]] for i, pair in enumerate(overlapping_pairs)]
        overlapping_data += [[i+1, pair[1]] for i, pair in enumerate(overlapping_pairs)]
        df_overlap_polygons = pd.DataFrame(overlapping_data, columns=['ID', 'Działka'])

        # Prepare the DataFrame for bordering polygons
        bordering_polygons = pd.DataFrame(list(bordering_polygons_set), columns=['Działka'])

        return bordering_polygons, df_overlap_polygons


    def find_overlap_polygons(self):
        selected_polygons = self.add_selected_polygon_to_list()
        bordering_polygons = []
        overlapping_pairs = []
        for id1, polygon1 in selected_polygons.items():
            for id2, polygon2 in selected_polygons.items():
                if id1 != id2 and id1 < id2:
                    if polygon1.collidesWithItem(polygon2):
                        overlapping_pairs.append((id1, id2))
                        #bordering_polygons[id1] = polygon1
                        #bordering_polygons[id2] = polygon2
        for id, pair in enumerate(overlapping_pairs, start=1):
            print(f"Overlap between polygons: {pair[0]} and {pair[1]}")
            bordering_polygons.append([id, pair[0]])
            bordering_polygons.append([id, pair[1]])
        #self.turn_off_polygon_selection()
        columns = ['ID', 'Działka']
        df_overlap_polygons = pd.DataFrame(bordering_polygons, columns=columns)
        return df_overlap_polygons

    def find_polygons(self):
        selected_polygons = self.add_selected_polygon_to_list()
        bordering_polygons = []
        overlapping_pairs = []

        for id1, polygon1 in selected_polygons.items():
            for id2, polygon2 in selected_polygons.items():
                if id1 != id2 and id1 < id2:  # Avoid checking a polygon against itself
                    if polygon1.collidesWithItem(polygon2):
                        overlapping_pairs.append((id1, id2))
                        if id1 not in bordering_polygons:
                            bordering_polygons.append(id1)
                        if id2 not in bordering_polygons:
                            bordering_polygons.append(id2)

        if not bordering_polygons and len(selected_polygons) == 1:
            bordering_polygons.append(next(iter(selected_polygons)))


        df_neighbors = self.find_neighboring_polygons()
        #self.turn_off_polygon_selection()

        columns = ['Działka']
        bordering_polygons = pd.DataFrame(bordering_polygons, columns=columns)

        bordering_polygons = bordering_polygons.merge(df_neighbors, on='Działka', how='left')

        return bordering_polygons

    def find_neighboring_polygons(self):
        selected_polygons = self.add_selected_polygon_to_list()  # {id: polygon}
        neighbors_dict = {id: set() for id in selected_polygons}  # słownik: id -> set sąsiadów

        # Sprawdzenie nakładania się / kolizji działek
        for id1, polygon1 in selected_polygons.items():
            for id2, polygon2 in selected_polygons.items():
                if id1 != id2 and id1 < id2:  # unikamy sprawdzania samego siebie i duplikatów
                    if polygon1.collidesWithItem(polygon2):
                        neighbors_dict[id1].add(id2)
                        neighbors_dict[id2].add(id1)

        # Jeśli wybrano tylko jedną działkę, dodaj ją do listy
        if not any(neighbors_dict.values()) and len(selected_polygons) == 1:
            only_id = next(iter(selected_polygons))
            neighbors_dict[only_id] = set()

        # Zamiana setów sąsiadów na listę lub string z numerami działek
        data_for_df = []
        for id, neighbors in neighbors_dict.items():
            neighbors_str = ', '.join([str(n).rsplit('.', 1)[-1] for n in sorted(neighbors)]) if neighbors else ''
            data_for_df.append([id, neighbors_str])

        columns = ['Działka', 'Sąsiadujące działki']
        df_neighbors = pd.DataFrame(data_for_df, columns=columns)

        return df_neighbors


    Slot()
    def turn_on_polygon_selection_slot(self):
        """Slot obsługujący żądanie włączenia wyboru poligonów."""
        #self.turn_on_polygon_selection()

    @Slot()
    def find_polygons_slot(self):
        """Slot obsługujący żądanie znalezienia poligonów."""
        polygons = self.find_polygons()
        self.gml_handler.polygons_found.emit(polygons)  # Emituj wyniki

    @Slot()
    def find_overlap_polygons_slot(self):
        """Slot obsługujący żądanie znalezienia nakładających się poligonów."""
        overlap_polygons = self.find_overlap_polygons()
        self.gml_handler.overlap_polygons_found.emit(overlap_polygons)  # Emituj wyniki


    def remove_items(self, items):
        try:
            for item in items:
                if item.scene() == self.scene:
                    self.scene.removeItem(item)
            items = []
        except Exception as e:
            logging.exception(e)
            print(e)

    def clear_scene(self):
        for item in self.scene.items():  # Pobiera wszystkie elementy sceny
            self.scene.removeItem(item)  # Usuwa każdy element


    def hide_items(self, items, hide: bool=True) -> bool:
        for item in items:
                item.setVisible(not hide)

    def hide_items_by_list(self, list) -> bool:
        if len(list) != 2:
            return
        if len(list) == 2:
            checked_items, un_checked_items = list
            for item_list in checked_items:
                for item in item_list:  # Iterujemy po każdym obiekcie w tej wewnętrznej liście
                    if item.scene() == self.scene:
                        item.setVisible(True)

            for item_list in un_checked_items:
                for item in item_list:  # Iterujemy po każdym obiekcie w tej wewnętrznej liście
                    if item.scene() == self.scene:
                        item.setVisible(False)

    def set_map_items_visible_by_list(self, items_list) -> bool:
        for _, data, visible in items_list:
            if visible:
                continue

            for item in data: 
                if item.scene() == self.scene:
                    item.setVisible(False)




    def add_graphics_item(self, item_type, coords):
        if item_type == "polygon":
            item = QGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]))
        elif item_type == "line":
            item = QGraphicsLineItem(QLineF(QPointF(*coords[0]), QPointF(*coords[1])))
        elif item_type == "point":
            item = QGraphicsEllipseItem(QRectF(QPointF(*coords) - QPointF(1, 1), QSizeF(2, 2)))
        else:
            return None  # Invalid type

        return item

    def add_polygon_to_scene(scene, coords, pen, id=None):
        polygon = MyQGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]), id)
        polygon.setPen(pen)
        polygon.setZValue(-1)
        scene.addItem(polygon)
        return polygon

    def add_polygon(self, coords, color=Qt.black):
        polygon = MyQGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]))
        pen = QPen(color)
        pen.setWidthF(0.2)
        polygon.setPen(pen)
        polygon.setBrush(QBrush(color, Qt.SolidPattern))
        polygon.setFlag(QGraphicsPolygonItem.ItemIsMovable, True)  # Umożliwia przesuwanie
        self.scene.addItem(polygon)
        self.polygons.append(polygon)  # Dodaj do listy poligonów
        return polygon

    def add_line(self, start, end, color=Qt.darkGreen):
        line = QGraphicsLineItem(QPointF(*start).x(), QPointF(*start).y(),
                                 QPointF(*end).x(), QPointF(*end).y())
        pen = QPen(color)
        pen.setWidthF(0.2)
        line.setPen(pen)
        line.setFlag(QGraphicsLineItem.ItemIsMovable, True)
        self.scene.addItem(line)
        self.lines.append(line)  # Dodaj do listy linii
        return line

    def add_point(self, position, color=Qt.red):
        point = QGraphicsEllipseItem(QRectF(QPointF(*position) - QPointF(1, 1), QSizeF(2, 2)))
        point.setBrush(QBrush(color))
        point.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.scene.addItem(point)
        self.points.append(point)  # Dodaj do listy punktów
        return point


    # Adjusts the position and origin for alignment based on the provided rect and alignment type.
    def set_alignment(self, x=None, y=None, rect=None, alignment='center'):
        delta_x=0
        delta_y=0
        if alignment in ['center', '5']:
            pos_x = x - rect.center().x()
            pos_y = y - rect.center().y()
            delta_x = rect.center().x()
            delta_y = rect.center().y()
        elif alignment in ['left', '4']:
            pos_x = x - rect.left()
            pos_y = y - rect.center().y()
            delta_x = rect.left()
            delta_y = rect.center().y()
        elif alignment in ['right', '6']:
            pos_x = x - rect.right()
            pos_y = y - rect.center().y()
            delta_x = rect.right()
            delta_y = rect.center().y()
        elif alignment in ['top', '8']:
            pos_x = x - rect.center().x()
            pos_y = y - rect.top()
            delta_x = rect.center().x()
            delta_y = rect.top()
        elif alignment in ['bottom', '2']:
            pos_x = x - rect.center().x()
            pos_y = y - rect.bottom()
            delta_x = rect.center().x()
            delta_y = rect.bottom()
        elif alignment in ['top-left', '7']:
            pos_x = x - rect.left()
            pos_y = y - rect.top()
            delta_x = rect.left()
            delta_y = rect.top()
        elif alignment in ['top-right', '9']:
            pos_x = x - rect.right()
            pos_y = y - rect.top()
            delta_x = rect.right()
            delta_y = rect.top()
        elif alignment in ['bottom-left', '1']:
            pos_x = x - rect.left()
            pos_y = y - rect.bottom()
            delta_x = rect.left()
            delta_y = rect.bottom()
        elif alignment in ['bottom-right', '3']:
            pos_x = x - rect.right()
            pos_y = y - rect.bottom()
            delta_x = rect.right()
            delta_y = rect.bottom()
        else:
            pos_x = x - rect.center().x()
            pos_y = y - rect.center().y()
            delta_x = rect.center().x()
            delta_y = rect.center().y()
        
        return pos_x, pos_y, delta_x, delta_y

    # Add mark of items.
    def add_mark(self, coordinates, color="white"):
        
        if not isinstance(coordinates, (tuple, list)) or len(coordinates) != 2:  # Validate input
            logging.error(f"Invalid coordinates: {coordinates}. Expected a tuple or list with two numeric values.")
            return

        try:
            y, x = float(coordinates[0]), float(coordinates[1])  # Ensure both are numbers
            y = -y  # Invert y if necessary
        except Exception as e:
            logging.error(f"Error converting coordinates: {coordinates}")
            logging.exception(e)
            print(e)
            return

        square_size = 0.1
        square = QGraphicsRectItem(QRectF(x - square_size / 2, y - square_size / 2, square_size, square_size))
        square.setBrush(QBrush(QColor(color)))
        square.setPen(QPen(QColor('black'), 0.02))
        square.setZValue(40)
        self.scene.addItem(square)
        self.data.mark.append(square)

    # Add polygons and id
    def add_polygon_id(self, geom, id, color, pen_width=0.2, z_value=0):
        """Helper to add polygons to the scene."""
        coords = self.swap_exterior_coords_xy(geom)
        if coords:
            polygon = MyQGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]), id)
            pen = QPen(color)
            pen.setWidthF(pen_width)
            polygon.setPen(pen)
            polygon.setZValue(z_value)
            self.scene.addItem(polygon)
            return polygon
        return None

    # Add polygons
    def add_polygon(self, geom, color, pen_width=0.2, z_value=0):
        """Helper to add polygons to the scene."""
        coords = self.swap_exterior_coords_xy(geom)
        if coords:
            polygon = QGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]))
            pen = QPen(color)
            pen.setWidthF(pen_width)
            polygon.setPen(pen)
            polygon.setZValue(z_value)
            self.scene.addItem(polygon)
            return polygon
        return None

    # Creates and adds a draggable text item to the scene.
    def create_text_item(self, text, coordinates, color, font_size, alignment=None, z_value=0, rotation=0, scale=1):
        try:
            y, x = self.swap_coords_xy(coordinates)

            text_item = DraggableTextItem(text)
            font = QFont("Times New Roman")
            font.setPointSizeF(font_size)
            text_item.setFont(font)
            text_item.setZValue(z_value)
            text_item.setBrush(QColor(color))
            text_item.setScale(scale)  # Adjust scale

            rect = text_item.boundingRect()
            x, y, x_origin, y_origin = self.set_alignment(x, y, rect, alignment = str(alignment))
            text_item.setPos(x, y)
            
            try:
                text_item.setTransformOriginPoint(x_origin, y_origin)
                rotation = float(rotation)
                rotation = math.degrees(rotation)
                if math.isnan(rotation):
                    pass
                else:
                    text_item.setRotation(-rotation)

            except Exception as e:
                logging.exception(e)
                print(e)

            self.scene.addItem(text_item)
            return text_item
        except Exception as e:
            logging.exception(e)
            print(e)


    def transform_crs(self, array, metadata, target_epsg):
        """Transform the raster array to the target EPSG using the metadata."""
        src_crs = metadata['crs']  # This is a rasterio.crs.CRS object
        #print(f"Source CRS: {src_crs}, type: {type(src_crs)}")
        
        # If the source CRS is already the target, no transformation is needed.
        if src_crs.to_epsg() == target_epsg:
            return array, metadata['transform'], src_crs

        # Define target CRS.
        target_crs = CRS.from_epsg(target_epsg)
        
        # Compute bounds from metadata using the current transform, width, and height.
        bounds = rasterio.transform.array_bounds(metadata['height'], metadata['width'], metadata['transform'])
        
        # Calculate the transform, width, and height for the new (target) CRS.
        transform_matrix, width, height = rasterio.warp.calculate_default_transform(
            src_crs, target_crs, metadata['width'], metadata['height'], *bounds
        )
        
        # Prepare an empty array for the reprojected data.
        count = metadata['count']  # Number of bands.
        dst_array = np.empty((count, height, width), dtype=array.dtype)
        
        # Reproject each band.
        for i in range(count):
            rasterio.warp.reproject(
                source=array[i],
                destination=dst_array[i],
                src_transform=metadata['transform'],
                src_crs=src_crs,
                dst_transform=transform_matrix,
                dst_crs=target_crs,
                resampling=rasterio.enums.Resampling.nearest
            )
        
        # Update metadata with the new transform, dimensions, and CRS.
        metadata['transform'] = transform_matrix
        metadata['width'] = width
        metadata['height'] = height
        metadata['crs'] = target_crs
        
        return dst_array, transform_matrix, target_crs

    def get_tif_from_url(self, url):
        """Pobiera plik TIFF bez zapisu na dysk i zwraca jego dane jako numpy array."""
        
        try:
            response = requests.get(url, timeout=30)  # Set a timeout for quicker failure in case of issues
            response.raise_for_status()  # Raise an exception for HTTP errors

            tif_data = BytesIO(response.content)  # Convert the content into memory
            with rasterio.open(tif_data) as dataset:
                # Read data directly for needed bands to minimize memory overhead
                array = dataset.read()  # You can also specify specific bands here (e.g., dataset.read([1, 2, 3])) for faster processing
                metadata = dataset.meta

            return array, metadata  # Return array and metadata
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download TIFF from {url}: {e}")
            return None, None
        except rasterio.errors.RasterioIOError as e:
            logging.error(f"Failed to process TIFF file from {url}: {e}")
            return None, None

    def add_tiff_to_scene_from_url(self, url, espg=None):
        try:
            # Download the TIFF file and get its data and metadata
            array, metadata = self.get_tif_from_url(url)

            if array is None:
                print("❌ Unable to download or process the TIFF file.")
                return
            
            dataset_crs = metadata['crs']
            #print(f"Dataset CRS: {dataset_crs}")

            if dataset_crs.to_epsg() != espg:
                print(f"CRS transformation needed. Current CRS: {dataset_crs}, Target CRS: EPSG:{espg}")
                array, transform, crs = self.transform_crs(array, metadata, espg)
                metadata['transform'] = transform
                metadata['crs'] = crs  # Store the target CRS in metadata

            # Check the number of bands
            num_bands = array.shape[0]
            
            # Read the bands into a list
            bands = [array[i] for i in range(num_bands)]

            # Handle grayscale or RGB based on the number of bands
            if num_bands == 1:  # Grayscale
                data = bands[0]
                data_normalized = self.normalize_data(data)

                # Convert normalized data to QImage
                qimage = QImage(data_normalized.data, data_normalized.shape[1], data_normalized.shape[0], 
                                data_normalized.shape[1], QImage.Format_Grayscale8)

            elif num_bands >= 3:  # RGB
                # Stack the first three bands to create an RGB image
                rgb_data = np.stack([self.normalize_data(bands[i]) for i in range(3)], axis=-1)
                qimage = QImage(rgb_data.data, rgb_data.shape[1], rgb_data.shape[0],
                                rgb_data.shape[1] * 3, QImage.Format_RGB888)

            else:
                print("Error on ruster.")
                raise ValueError("Unsupported number of bands for visualization.")

            # Create a QPixmap from QImage
            pixmap = QPixmap.fromImage(qimage)

            # Get georeferencing information from the metadata
            transform = metadata['transform']
            pixel_width = transform[0]  # Size of a pixel in the X direction
            pixel_height = -transform[4]  # Size of a pixel in the Y direction (negative)

            x_min = transform[2]  # X coordinate of upper-left corner
            y_max = transform[5]  # Y coordinate of upper-left corner

            # Create a pixmap item
            pixmap_item = QGraphicsPixmapItem(pixmap)

            # Set the position of the pixmap item based on georeferencing
            pixmap_item.setPos(x_min, -y_max)  # Set position correctly
            data = bands[0]
            height, width = data.shape
            # Calculate the scale for the pixmap item
            scene_width = width * pixel_width  # Geographic width in scene units
            scene_height = height * pixel_height  # Geographic height in scene units

            # Set the scale factors
            scale_x = scene_width / pixmap.width()
            scale_y = scene_height / pixmap.height()

            # Use the smaller scale factor to maintain aspect ratio
            scale_factor = min(scale_x, scale_y)
            pixmap_item.setScale(scale_factor)  # Set uniform scaling

            # Optional: Store the transformation and CRS for later use
            pixmap_item.transform = transform
            pixmap_item.crs = metadata['crs']

            pixmap_item.setZValue(-20)

            # Add the pixmap item to the scene
            self.scene.addItem(pixmap_item)
            self.data.Raster2000.append(pixmap_item)
            self.refresh_layer_list()
            
        except Exception as e:
            logging.exception(e)
            print(e)

    def add_tiff_to_scene_from_path(self, path, espg=None):
        try:
            # Load the TIFF file
            with rasterio.open(path) as src:
                # Check the number of bands
                num_bands = src.count
                
                # Read the bands into a list
                bands = [src.read(i + 1) for i in range(num_bands)]
                
                # Handle grayscale or RGB based on number of bands
                if num_bands == 1:  # Grayscale
                    data = bands[0]
                    data_normalized = self.normalize_data(data)

                    # Convert normalized data to QImage
                    qimage = QImage(data_normalized.data, data_normalized.shape[1], data_normalized.shape[0], 
                                    data_normalized.shape[1], QImage.Format_Grayscale8)

                elif num_bands >= 3:  # RGB
                    # Stack the first three bands to create an RGB image
                    rgb_data = np.stack([self.normalize_data(bands[i]) for i in range(3)], axis=-1)
                    qimage = QImage(rgb_data.data, rgb_data.shape[1], rgb_data.shape[0],
                                    rgb_data.shape[1] * 3, QImage.Format_RGB888)

                else:
                    raise ValueError("Unsupported number of bands for visualization.")

                # Create a QPixmap from QImage
                pixmap = QPixmap.fromImage(qimage)

                # Get georeferencing information
                transform = src.transform
                pixel_width = transform[0]  # Size of a pixel in the X direction
                pixel_height = -transform[4]  # Size of a pixel in the Y direction (negative)

                x_min = transform[2]  # X coordinate of upper-left corner
                y_max = transform[5]  # Y coordinate of upper-left corner

                # Create a pixmap item
                pixmap_item = QGraphicsPixmapItem(pixmap)

                # Set the position of the pixmap item based on georeferencing
                pixmap_item.setPos(x_min, -y_max)  # Set position correctly
                data = src.read(1)
                height, width = data.shape
                # Calculate the scale for the pixmap item
                scene_width = width * pixel_width  # Geographic width in scene units
                scene_height = height * pixel_height  # Geographic height in scene units

                # Set the scale factors
                scale_x = scene_width / pixmap.width()
                scale_y = scene_height / pixmap.height()
                
                # Use the smaller scale factor to maintain aspect ratio
                scale_factor = min(scale_x, scale_y)
                pixmap_item.setScale(scale_factor)  # Set uniform scaling

                # Optional: Store the transformation and CRS for later use
                pixmap_item.transform = transform
                pixmap_item.crs = src.crs

                pixmap_item.setZValue(-20)

                # Add the pixmap item to the scene
                pixmap_item = self.scene.addItem(pixmap_item)
                self.data.Raster2000.append(pixmap_item)

        except Exception as e:
            print(f"Error loading {path}: {e}")

    def normalize_data(self, data):
        """Normalize the data to 8-bit range [0, 255]."""
        if data.max() > data.min():  # Avoid division by zero
            return ((data - data.min()) / (data.max() - data.min()) * 255).astype('uint8')
        else:
            return np.zeros_like(data, dtype='uint8')  # If all data is the same, return black


    def add_tiff(self, url, espg=None):
        print(f"Url: {url}, EPSG: {espg}")
        print(f"Scene w map_handler: {self.scene}")
        self.add_tiff_to_scene_from_url(url, espg)


    def load_map(self, df):
        try:
            self.data.EPSG = GMLParser.get_crs_epsg(self.path)
        except Exception as e:
            logging.exception(e)
            print(e)
            
        try:
            self.remove_items(self.data.mark)
            self.remove_items(self.data.PunktGraniczny_STB)
            self.remove_items(self.data.Archiwalne_obiekty_GML)
        except Exception as e:
            logging.exception(e)
            print(e)

        self.clear_scene()

        for method, data_key in [
            (self.add_DzialkaEwidencyjna, "df_EGB_DzialkaEwidencyjna"),
            (self.add_PunktGraniczny, "df_EGB_PunktGraniczny"),
            #(self.add_PunktGranicznyNumer, "df_EGB_PunktGraniczny"),
            (self.add_PunktGranicznyOpis, "df_EGB_PunktGraniczny"),
            (self.add_KonturKlasyfikacyjny, "df_EGB_KonturKlasyfikacyjny"),
            (self.add_KonturUzytkuGruntowego, "df_EGB_KonturUzytkuGruntowego"),
            (self.add_Budynek, "df_EGB_Budynek"),
            (self.add_Budynek_BDOT, "df_OT_BudynekNiewykazanyWEGIB"),
            (self.add_AdresNieruchomosci, "df_EGB_AdresNieruchomosci"),
            (self.add_Ogrodzenia, "df_OT_Ogrodzenia"),
            (self.add_murek, "df_OT_Budowle")
            ]:

            try:
                if df[data_key].empty:
                    continue
                method(df[data_key])
            except Exception as e:
                logging.exception(e)
                print(e)

        """
        try:
            self.add_DzialkaEwidencyjna(df["df_EGB_DzialkaEwidencyjna"])
        except Exception as e:
            logging.exception(e)
            print(e)
        
        try:
            self.add_PunktGraniczny(df["df_EGB_PunktGraniczny"])
            self.add_KonturKlasyfikacyjny((df["df_EGB_KonturKlasyfikacyjny"]))
            self.add_Budynek(df["df_EGB_Budynek"])
            self.add_AdresNieruchomosci(df["df_EGB_AdresNieruchomosci"])
            self.add_Ogrodzenia(df["df_OT_Ogrodzenia"])
            self.add_murek(df["df_OT_Budowle"])
        except Exception as e:
            logging.exception(e)
            print(e)
        """


    def swap_exterior_coords_xy(self, coordinates):
        try:
            y, x = coordinates.exterior.coords.xy
            y = [-i for i in y]
            coords = list(zip(x, y))
        except Exception as e:
            logging.exception(e)
            print(e)
            return None
        return coords

    def swap_coords_xy(self, coordinates):
        try:
            y, x = float(coordinates[0]), float(coordinates[1])
            y = -y
            if y == 0 or x == 0:
                return None, None
        except Exception as e:
            logging.exception(e)
            print(e)
            return None, None
        return y, x


    def add_DzialkaEwidencyjna(self, df):
        self.remove_items(self.data.DzialkaEwidencyjna)
        geometry = df['geometria']

        nr_dzialki = None
        if "tekst" in df.columns:
            nr_dzialki = df["tekst"]
        nr_dzialki = nr_dzialki.fillna(df["idDzialki"].str.rsplit('.', n=1).str.get(-1))

        for id, geom, point, nr, justyfikacja, koniecWersjaObiekt in zip(df['idDzialki'], geometry, df['pos'], nr_dzialki, df['justyfikacja'], df["koniecWersjaObiekt"]):
            if isinstance(geom, list) and all(isinstance(point, tuple) for point in geom):
                try:
                    geom = Polygon(geom)
                except Exception as e:
                    logging.exception(e)
                    print(e)
                    continue

                if koniecWersjaObiekt is not None and pd.notna(koniecWersjaObiekt):
                    #print(f"Archiwalny obiekt: {id}, data: {koniecWersjaObiekt}")
                    polygon = self.add_polygon_id(geom, id, "white", 0.2, -1)
                    self.data.Archiwalne_obiekty_GML.append(polygon)
                    continue

                polygon = self.add_polygon_id(geom, id, "black", 0.2, -1)
                self.data.DzialkaEwidencyjna.append(polygon)

            if isinstance(point, tuple) and len(point) == 2:
                y, x = point
                y = -y

                self.add_mark(point, 'green')

                text_item = DraggableTextItem(str(nr))
                font = QFont("Times New Roman", 2, QFont.Bold)
                text_item.setFont(font)

                justyfikacja = justyfikacja
                if not justyfikacja:
                    justyfikacja = 5

                rect = text_item.boundingRect()
                x, y,_,_ = self.set_alignment(x, y, rect, alignment=str(justyfikacja))
                text_item.setPos(x, y)
                
                text_item.setBrush(QColor('red'))
                text_item.setZValue(1)

                self.scene.addItem(text_item)
                self.data.DzialkaEwidencyjna.append(text_item)


    def add_PunktGraniczny(self, df):
        self.remove_items(self.data.PunktGraniczny)
        self.remove_items(self.data.PunktGranicznyNumer)
        geometry = df['geometria']
        nr_punktu = None
        if "tekst" in df.columns:
            nr_punktu = df["tekst"]
        id_punktu = nr_punktu.fillna(df["idPunktu"])
        nr_punktu = nr_punktu.fillna(df["idPunktu"].str.rsplit('.', n=1).str.get(-1)) #.rsplit('.', 1)[-1]

        rodzajStabilizacji = df["rodzajStabilizacji"].apply(pd.to_numeric, errors='coerce')

        sposobPozyskania = df["sposobPozyskania"].apply(pd.to_numeric, errors='coerce')
        spelnienieWarunkowDokl = df["spelnienieWarunkowDokl"].apply(pd.to_numeric, errors='coerce')

        # iterujemy przy pomocy enumerate, aby móc pobrać oryginalny wiersz df.iloc[idx]
        for idx, (pos, nr, rodzajStabilizacji, sposobPozyskania, spelnienieWarunkowDokl, id, koniecWersjaObiekt) in enumerate(
                zip(geometry, nr_punktu, rodzajStabilizacji, sposobPozyskania, spelnienieWarunkowDokl, id_punktu, df["koniecWersjaObiekt"])):
            if isinstance(pos, tuple) and len(pos) == 2:
                y, x = self.swap_coords_xy(pos)
                if y is None or x is None:
                    continue

                self.add_mark(pos, 'green')

                # utwórz dict z oryginalnego wiersza (jeśli dostępny)
                try:
                    attributes = df.iloc[idx].to_dict()
                except Exception:
                    # fallback - tylko podstawowe pola
                    attributes = {
                        'geometria': pos,
                        'idPunktu': id,
                        'tekst': nr,
                        'rodzajStabilizacji': rodzajStabilizacji,
                        'sposobPozyskania': sposobPozyskania,
                        'spelnienieWarunkowDokl': spelnienieWarunkowDokl
                    }

                # ustawienia tekstu i rozmiaru
                font = QFont('Times New Roman')
                font.setPointSizeF(1.2)
                dot_size = 0.8 if 3 <= rodzajStabilizacji <= 6 else 0.5
                color = 'white' if 3 <= rodzajStabilizacji <= 6 else 'black'

                punkt_item = SelectablePointItem(
                    scene=self.scene,
                    x=x,
                    y=y,
                    dot_size=dot_size,
                    text=str(nr),
                    font=font,
                    color=color,
                    id_punktu=id,
                    attributes=attributes
                    )
                
                if koniecWersjaObiekt is not None and pd.notna(koniecWersjaObiekt):
                    self.data.Archiwalne_obiekty_GML.append(punkt_item.ellipse)
                    self.scene.removeItem(punkt_item.text)
                    continue

                self.data.PunktGraniczny.append(punkt_item.ellipse)
                self.data.PunktGranicznyNumer.append(punkt_item.text)

    def add_PunktGranicznyOpis(self, df):
        self.remove_items(self.data.PunktGranicznyOpis)
        
        geometry = df['geometria']

        rodzajStabilizacji = pd.to_numeric(df["rodzajStabilizacji"], errors='coerce')
        sposobPozyskania = pd.to_numeric(df["sposobPozyskania"], errors='coerce').fillna(0).astype(int)
        spelnienieWarunkowDokl = pd.to_numeric(df["spelnienieWarunkowDokl"], errors='coerce').fillna(0).astype(int)

        for pos, rodzajStabilizacji, sposobPozyskania, spelnienieWarunkowDokl in zip(geometry, rodzajStabilizacji, sposobPozyskania, spelnienieWarunkowDokl):
            if isinstance(pos, tuple) and len(pos) == 2:
                y, x = self.swap_coords_xy(pos)
                if y is None or x is None:
                    continue

                try:
                    sposobPozyskania = int(sposobPozyskania)
                    spelnienieWarunkowDokl = int(spelnienieWarunkowDokl)

                    fs = 1.2
                    scale = 0.5

                    brush_color = 'white'
                    pen_color = 'white'

                    if sposobPozyskania == 1:
                        text_item1 = self.create_text_item(("SPD"), pos, 'Green', fs, alignment=3, scale=scale)
                        brush_color = 'Green'
                    else:
                        text_item1 = self.create_text_item(("SPD"), pos, 'Red', fs, alignment=3, scale=scale)
                        brush_color = 'Red'
                    self.data.PunktGranicznyOpis.append(text_item1)

                    if spelnienieWarunkowDokl == 1:
                        text_item2 = self.create_text_item(("ISD"), pos, 'Green', fs, alignment=1, scale=scale)
                        pen_color = 'Green'
                    else:
                        text_item2 = self.create_text_item(("ISD"), pos, 'Red', fs, alignment=1, scale=scale)
                        pen_color = 'Red'
                    self.data.PunktGranicznyOpis.append(text_item2)
                    
                    text_item = self.create_text_item(str(int(rodzajStabilizacji)), pos, 'Purple', fs, alignment=9, scale=0.5)
                    self.data.PunktGranicznyOpis.append(text_item)
                    
                except Exception as e:
                    logging.exception(e)
                    print(e)

                dot_size = 0.4
                dot_item = QGraphicsEllipseItem(x - dot_size / 2, y - dot_size / 2, dot_size, dot_size)
                dot_item.setBrush(QBrush(QColor(brush_color)))
                dot_item.setPen(QPen(QColor(pen_color), 0.10))

                self.scene.addItem(dot_item)
                self.data.PunktGranicznyOpis.append(dot_item)

    def add_KonturKlasyfikacyjny(self, df):
        self.remove_items(self.data.KonturKlasyfikacyjny)
        #df = df.explode('geometria')
        geometry = df['geometria']

        nr_Konturu = None
        if "tekst" in df.columns:
            nr_Konturu = df["tekst"]

        nr_Konturu = nr_Konturu.fillna(df.apply(lambda row: f'{row["OZU"]}' if pd.isna(row["OZK"]) 
                            else f'{row["OZK"]}' if pd.isna(row["OZU"]) 
                            else f'{row["OZU"]} {row["OZK"]}', axis=1))

        for geom, point, nr, justyfikacja in zip(geometry, df['pos'], nr_Konturu, df['justyfikacja']):
            if isinstance(geom, list) and all(isinstance(point, tuple) for point in geom):
                try:
                    geom = Polygon(geom)
                except Exception as e:
                    logging.exception(e)
                    print(e)
                    continue
                y, x = geom.exterior.coords.xy  # Zamiana X/Y podczas importu jak w qgis.
                y = [-i for i in y]
                coords = list(zip(x, y))
                #coords = self.swap_exterior_coords_xy(geom)
                #polygon = self.add_polygon(geom,"green", 0.18, -1)
                polygon = QGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]))
                
                pen = QPen(Qt.green)
                #pen.setStyle(Qt.DashLine)  # Set the pen style to dashed line
                pen.setWidthF(0.18)  # Set the width of the line
                pen.setDashPattern([2, 4])  # Set the dash pattern (1 pixel dash, 4 pixels space)
                polygon.setPen(pen)
                #polygon.setFlag(QGraphicsItem.ItemIsFocusable, False)
                #polygon.setFlag(QGraphicsItem.ItemIsSelectable, False)
                polygon.setZValue(-1)

                self.scene.addItem(polygon)
                self.data.KonturKlasyfikacyjny.append(polygon)  # Store for later removal

            if isinstance(point, tuple) and len(point) == 2:
                y, x = point
                y = -y

                self.add_mark(point, 'green')

                text_item = DraggableTextItem(str(nr))
                font = QFont('Times New Roman', 2, QFont.Normal)
                text_item.setFont(font)
                
                if not justyfikacja:
                    justyfikacja = 5
                rect = text_item.boundingRect()
                x, y,_,_ = self.set_alignment(x, y, rect, alignment = str(justyfikacja))
                text_item.setPos(x, y)
                
                text_item.setBrush(QColor(Qt.green))
                text_item.setZValue(1)

                self.scene.addItem(text_item)
                self.data.KonturKlasyfikacyjny.append(text_item)

    def add_KonturUzytkuGruntowego(self, df):
        self.remove_items(self.data.KonturUzytkuGruntowego)
        #df = df.explode('geometria')
        geometry = df['geometria']

        nr_Konturu = None
        if "OFU" in df.columns:
            nr_Konturu = df["tekst"]

        for i, (geom, point, justyfikacja) in enumerate(zip(geometry, df['pos'], df['justyfikacja'])):
            nr = nr_Konturu[i]
            if isinstance(geom, list) and all(isinstance(point, tuple) for point in geom):
                try:
                    geom = Polygon(geom)
                except Exception as e:
                    logging.exception(e)
                    print(e)
                    continue
                y, x = geom.exterior.coords.xy  # Zamiana X/Y podczas importu jak w qgis.
                y = [-i for i in y]
                coords = list(zip(x, y))
                polygon = QGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]))

                pen = QPen(Qt.darkGreen)
                #pen.setStyle(Qt.DashLine)  # Set the pen style to dashed line
                pen.setWidthF(0.18)  # Set the width of the line
                pen.setDashPattern([2, 4])  # Set the dash pattern (1 pixel dash, 4 pixels space)
                polygon.setPen(pen)
                #polygon.setFlag(QGraphicsItem.ItemIsFocusable, False)
                #polygon.setFlag(QGraphicsItem.ItemIsSelectable, False)
                polygon.setZValue(-1)

                self.scene.addItem(polygon)
                self.data.KonturUzytkuGruntowego.append(polygon)  # Store for later removal

            if isinstance(point, tuple) and len(point) == 2:
                y, x = point
                y = -y

                self.add_mark(point, 'green')

                text_item = DraggableTextItem(str(nr))
                font = QFont('Times New Roman', 2, QFont.Normal)
                text_item.setFont(font)

                justyfikacja = justyfikacja
                if not justyfikacja:
                    justyfikacja = 5

                rect = text_item.boundingRect()
                x, y,_,_ = self.set_alignment(x, y, rect, alignment = str(justyfikacja))
                text_item.setPos(x, y)
                
                text_item.setBrush(QColor(Qt.darkGreen))
                text_item.setZValue(1)

                self.scene.addItem(text_item)
                self.data.KonturUzytkuGruntowego.append(text_item)

    def add_Budynek(self, df):
        self.remove_items(self.data.Budynek)
        df['liczbaKondygnacjiNadziemnych'] = df['liczbaKondygnacjiNadziemnych'].astype(str)
        df['rodzajBudynku'] = df['rodzajWgKST'] + df['liczbaKondygnacjiNadziemnych']
        geometria = (df['geometria'])
        for id, geom, point, justyfikacja in zip(df['rodzajBudynku'], geometria, df['pos'], df['justyfikacja']):
            if isinstance(geom, list) and all(isinstance(point, tuple) for point in geom):
                try:
                    geom = Polygon(geom)
                except Exception as e:
                    logging.exception(e)
                    print(e)
                    continue
                y, x = geom.exterior.coords.xy  # Zamiana X/Y podczas importu jak w qgis.
                y = [-i for i in y]
                coords = list(zip(x, y))
                multipolygon = QGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]))
                pen = QPen(Qt.black)
                pen.setWidthF(0.4)  
                multipolygon.setPen(pen)
                multipolygon.setZValue(-2)

                self.scene.addItem(multipolygon)
                self.data.Budynek.append(multipolygon)
                
                if id is not None:
                    y, x = self.swap_coords_xy(point)
                    if y is None or x is None:
                        continue

                    self.add_mark(point, 'green')

                    text_item = DraggableTextItem(str(id))
                    font = QFont("Times New Roman")
                    font.setPointSizeF(1.5)
                    text_item.setFont(font)

                    text_item.setBrush(QColor(Qt.magenta))
                    text_item.setZValue(1)

                    justyfikacja = justyfikacja
                    if not justyfikacja:
                        justyfikacja = 5

                    rect = text_item.boundingRect()
                    x, y,_,_ = self.set_alignment(x, y, rect, alignment=str(justyfikacja))
                    text_item.setPos(x, y)

                    self.scene.addItem(text_item)
                    self.data.Budynek.append(text_item)

    def add_Budynek_BDOT(self, df):
        self.remove_items(self.data.Budynek_BDOT)
        df['liczbaKondygnacjiNadziemnych'] = df['liczbaKondygnacjiNadziemnych'].astype(str)
        df['rodzajBudynku'] = df['rodzajWgKST'] + df['liczbaKondygnacjiNadziemnych']
        geometria = (df['geometria'])
        for id, geom, point, justyfikacja in zip(df['rodzajBudynku'], geometria, df['pos'], df['justyfikacja']):
            if isinstance(geom, list) and all(isinstance(point, tuple) for point in geom):
                try:
                    geom = Polygon(geom)
                except Exception as e:
                    logging.exception(e)
                    print(e)
                    continue
                y, x = geom.exterior.coords.xy  # Zamiana X/Y podczas importu jak w qgis.
                y = [-i for i in y]
                coords = list(zip(x, y))
                multipolygon = QGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]))
                pen = QPen(Qt.black)
                pen.setWidthF(0.4)  
                multipolygon.setPen(pen)
                multipolygon.setZValue(-2)

                self.scene.addItem(multipolygon)
                self.data.Budynek_BDOT.append(multipolygon)
                
                """
                if id is not None:
                    y, x = self.swap_coords_xy(point)
                    if y is None or x is None:
                        continue

                    self.add_mark(point, 'green')

                    text_item = DraggableTextItem(str(id))
                    font = QFont("Times New Roman")
                    font.setPointSizeF(1.5)
                    text_item.setFont(font)

                    text_item.setBrush(QColor(Qt.magenta))
                    text_item.setZValue(1)

                    justyfikacja = justyfikacja
                    if not justyfikacja:
                        justyfikacja = 5

                    rect = text_item.boundingRect()
                    x, y,_,_ = self.set_alignment(x, y, rect, alignment=str(justyfikacja))
                    text_item.setPos(x, y)

                    self.scene.addItem(text_item)
                    self.data.Budynek.append(text_item)
                """


    def add_AdresNieruchomosci(self, df):
        self.remove_items(self.data.AdresNieruchomosci)

        katObrotu = df["katObrotu"].apply(pd.to_numeric, errors='coerce')

        for pos, nr, katObrotu, justyfikacja in zip(df['pos'], df['numerPorzadkowy'], katObrotu, df['justyfikacja']):
            if isinstance(pos, tuple) and len(pos) == 2:
                self.add_mark(pos, 'green')
                text_item = self.create_text_item(nr, pos, 'black', 1.2, justyfikacja, 1, rotation=katObrotu)
                self.data.AdresNieruchomosci.append(text_item)

    def add_Ogrodzenia(self, df):
        self.remove_items(self.data.Ogrodzenia)

        id_line = {
            'o': (Qt.gray, 0.2, 1),  # Dodana szerokość linii
            'b': (Qt.blue, 0.1, 2),  # Dodana szerokość linii
            'f': (Qt.red, 0.1, 3),   # Dodana szerokość linii
            }

        dot_interval_cm = 10.0
        for geom, line_id in zip(df['geometria'], df['rodzajOgrodzenia']):
            if isinstance(geom, list):
                if len(geom) > 1:
                    geom = LineString(geom)
                else:
                    continue

                y, x = geom.coords.xy
                y = [-i for i in y]
                coords = list(zip(x, y))
                for i in range(len(coords) - 1):
                    x1, y1 = coords[i]
                    x2, y2 = coords[i + 1]
                    
                    segment_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

                    if line_id == 'o':
                        current_distance = 0
                        while current_distance < segment_length:
                            dot_x = x1 + (x2 - x1) * (current_distance / segment_length)
                            dot_y = y1 + (y2 - y1) * (current_distance / segment_length)
                            dot_item = QGraphicsEllipseItem(QRectF(dot_x - 0.15, dot_y - 0.15, 0.3, 0.3))
                            dot_item.setPen(QPen(Qt.gray, 0.2))
                            dot_item.setBrush(QBrush(Qt.gray))
                            dot_item.setZValue(0)
                            self.scene.addItem(dot_item)
                            self.data.Ogrodzenia.append(dot_item)
                            current_distance += dot_interval_cm

                    if line_id == 'f':

                        path_to_svg = path_icons + "Furtka.svg"
                        #path_to_svg = r"Icons\Furtka.svg"
                        svg_renderer = QSvgRenderer(path_to_svg)
                        svg_width = svg_renderer.defaultSize().width()
                        svg_height = svg_renderer.defaultSize().height()
                        new_anchor_x = svg_width
                        new_anchor_y = 0

                        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))  # Oblicz kąt pomiędzy dwiema liniami

                        svg_item = QGraphicsSvgItem(path_to_svg)  # Utwórz obiekt QGraphicsSvgItem i ustaw pozycję na końcu strzałki
                        svg_item.setTransformOriginPoint(new_anchor_x, new_anchor_y)
                        
                        skala = 0.07
                        svg_item.setScale(skala)
                        svg_item.setRotation(angle)

                        svg_item.setPos(x2 - new_anchor_x , y2)

                        self.scene.addItem(svg_item)
                        self.data.Ogrodzenia.append(svg_item)

                    if line_id == 'b':
                        x_mid = (x1 + x2) / 2
                        y_mid = (y1 + y2) / 2

                        path_to_svg = path_icons + "Brama.svg"
                        #path_to_svg = r"Icons\Brama.svg"
                        svg_renderer = QSvgRenderer(path_to_svg)
                        svg_width = svg_renderer.defaultSize().width()
                        svg_height = svg_renderer.defaultSize().height()
                        new_anchor_x = svg_width / 2
                        new_anchor_y = 0

                        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))  # Oblicz kąt pomiędzy dwiema liniami

                        
                        svg_item = QGraphicsSvgItem(path_to_svg)
                        svg_item.setTransformOriginPoint(new_anchor_x, new_anchor_y)
                        
                        skala = 0.07
                        svg_item.setScale(skala)
                        svg_item.setRotation(angle)

                        svg_item.setPos(x_mid - new_anchor_x , y_mid)

                        self.scene.addItem(svg_item)
                        self.data.Ogrodzenia.append(svg_item)

                    line_item = QGraphicsLineItem(x1, y1, x2, y2)
                    line_properties = id_line.get(line_id, (Qt.gray, 0.3, 1))
                    color, line_width, _ = line_properties
                    pen = QPen(color)
                    pen.setWidthF(line_width)
                    pen.setCapStyle(Qt.RoundCap)
                    pen.setJoinStyle(Qt.RoundJoin)
                    line_item.setPen(pen)

                    self.scene.addItem(line_item)
                    self.data.Ogrodzenia.append(line_item)

    def add_murek(self, df):
        self.remove_items(self.data.Budowle)

        color = Qt.black
        width = 0.1
        buffer_distance = 0.2
    
        for geom, line_id in zip(df['geometria'], df['rodzajBudowli']):
            if isinstance(geom, list) and all(isinstance(point, tuple) for point in geom):
                if len(geom) > 1:
                    geom = LineString(geom)
                else:
                    continue

                if line_id == 'n':
                    
                    buffered_polygon = geom.buffer(buffer_distance, cap_style='square', join_style='mitre')

                    if buffered_polygon.is_empty or not buffered_polygon.is_valid:
                        print(f"Skipping invalid or empty buffered polygon for line_id '{line_id}'")
                        continue

                    # Convert buffered polygon to QPolygonF
                    polygon_points = [QPointF(x, -y) for y, x in buffered_polygon.exterior.coords]
                    q_polygon = QPolygonF(polygon_points)

                    # Set up QGraphicsPolygonItem and pen
                    outline = QGraphicsPolygonItem(q_polygon)

                    pen = QPen(color)
                    pen.setWidthF(width)
                    pen.setCapStyle(Qt.FlatCap)
                    pen.setJoinStyle(Qt.BevelJoin)
                    outline.setPen(pen)
                    
                    # Add the polygon item to the scene
                    self.scene.addItem(outline)
                    self.data.Budowle.append(outline)


if __name__ == '__main__':
    pass