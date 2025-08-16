from PySide6.QtWidgets import (QApplication, QGraphicsLineItem, QMainWindow,
                               QGraphicsItem, QCheckBox, QGraphicsEllipseItem,
                               QApplication, QMainWindow, QGraphicsView,
                               QGraphicsScene, QGraphicsPolygonItem, QGraphicsTextItem,
                               QFileDialog, QPushButton)
from PySide6.QtGui import (QFont, QPolygonF, QPolygonF, QPainter, QFont,
                           QColor, QBrush, QPen, QIcon, QPainterPath, QIcon)
from shapely.geometry import Polygon, MultiPolygon, Point, MultiLineString, LineString
from PySide6.QtCore import Qt, QPointF, QPoint, QRectF, QTimer, Signal, QSettings
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtSvg import QSvgRenderer
from dataclasses import dataclass
from PySide6 import QtCore
from pathlib import Path
import geopandas as gpd
import pandas as pd

from function.search_in_geoportal import open_parcel_in_geoportal
from function.search_in_street_view import open_parcel_in_street_view
from function.EPSG import read_EPSG

from model.path import PathManager

import logging
import math
import sys
import os

logger = logging.getLogger(__name__)

path_manager = PathManager()

if getattr(sys, 'frozen', False):
    path_icons = os.path.dirname(sys.executable) + '\\gui\\Icons\\'    
else:
    folder = os.path.basename(sys.path[0])
    if folder == "src":
        path_icons = sys.path[0] + '\\gui\\Icons\\' 
    else:
        path_icons = sys.path[0] + '\\Icons\\'


class connect:
    MapWindow: str = None
    path_to_map: str = None
    target_xlsx: str = None


@dataclass
class data:
    EPSG: str = None
    
    search_parcel_by_id: bool = False
    search_in_street_view: bool = False


    parsed_gml: str = None

    kontury = []
    dzialki = []
    punkty = []
    ogrodzenia = []
    budynki = []
    numery_budynkow = []
    murki = []


class DraggableTextItem(QGraphicsTextItem):
    def __init__(self, text, parent=None):
        super(DraggableTextItem, self).__init__(text, parent)
        self.setFlag(QGraphicsTextItem.ItemIsMovable)
        #self.setBoundingRegionGranularity(0.0)

    def boundingRect(self):
        rect = super(DraggableTextItem, self).boundingRect()
          # Adjust the bounding rectangle to the text boundary
        adjusted_rect = QRectF(rect.x() + 3.6, rect.y() + 4.45, rect.width() - 7.2, rect.height() - 8.40)
        #adjusted_rect.moveCenter(rect.center())
        return adjusted_rect

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            pass  # Obsługa przesuwania tekstu za pomocą lewego przycisku
        super(DraggableTextItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        pass # self.setCursor(Qt.OpenHandCursor)
        super(DraggableTextItem, self).mouseReleaseEvent(event)

    def shape(self):
        # Create a QPainterPath object
        path = QPainterPath()
        # Add the bounding rectangle of the text to the path
        path.addRect(self.boundingRect())
        return path


class GraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super(GraphicsView, self).__init__(parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        #self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)  # Włącz wybieranie elementów
        self.minZoom = 0.1
        self.maxZoom = 80.0
        self.middle_mouse_button_pressed = False
        self.last_mouse_position = QPoint()
        self.last_x_y_position = QPoint()

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

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.middle_mouse_button_pressed = True
            self.last_mouse_position = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            if data.search_in_street_view:
                data.search_in_street_view = False
                self.last_x_y_position = self.mapToScene(event.position().toPoint())
                open_parcel_in_street_view(self.last_x_y_position,EPSG=data.EPSG)
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.middle_mouse_button_pressed = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.middle_mouse_button_pressed:
            # Oblicz przesunięcie myszy
            offset = self.last_mouse_position - event.position().toPoint()
            self.last_mouse_position = event.position().toPoint()

            # Przesuń widok
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + offset.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + offset.y())
        else:
            super().mouseMoveEvent(event)

    def get_last_mouse_position(self):
        return self.last_x_y_position


class QGraphicsPolygonItem(QGraphicsPolygonItem):
    polygon_clicked = Signal(str)
    def __init__(self, polygon, id=None, parent=None):
        super(QGraphicsPolygonItem, self).__init__(polygon, parent)
        self.id = id

        self.color_timer = QTimer()
        self.color_timer.timeout.connect(self.resetPolygonColor)

        self.setFlag(QGraphicsItem.ItemStacksBehindParent, False)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.id != None:

                if isinstance(connect.MapWindow, WindowMap):
                    connect.MapWindow.send_item(self.id)
                    print(f"Polygon {self.id} clicked.")
                
                if data.search_parcel_by_id:
                    open_parcel_in_geoportal(self.id)
                    print(f"Searching {self.id} in browser...")
                    data.search_parcel_by_id = False
                self.setColorForDuration(QtCore.Qt.green, 500)
            else:
                return
        super().mousePressEvent(event)
        self.last_mouse_position = event.scenePos()

    def setColorForDuration(self, color, duration): # Set color for selected polygon
        self.setBrush(QBrush(color))
        self.setZValue(-10)
        self.color_timer.start(duration)  # Start the timer to reset the color after the specified duration
    
    def resetPolygonColor(self):  # Reset the polygon color
        self.setBrush(QBrush())
        self.setZValue(5)
        self.color_timer.stop()

    def paint(self, painter, option, widget):
        if self.isSelected():
            self.setBrush(QBrush())
            # Customize the highlight appearance
            highlight_color = QColor(255, 255, 0)  # Yellow color for highlight
            highlight_pen = QPen(highlight_color, 2, Qt.SolidLine)
            painter.setPen(highlight_pen)
            painter.setBrush(QBrush())
            painter.drawPolygon(self.polygon())
        else:
            super().paint(painter, option, widget)


class EmitMapW(QMainWindow):
    item_signal = Signal(str)

    def __init__(self):
        super().__init__()
        connect.EmitID = self

    def send_item(self, id):
        self.item_signal.emit(id)


class WindowMap(QMainWindow):
    item_signal = Signal(str)
    def __init__(self, parent=None, path_to_map=None, parsed_gml=None, target_xlsx=None): 
        super(WindowMap, self).__init__(parent)
        self.setWindowTitle("GML Map")
        self.setWindowIcon(QIcon(r'gui\Stylesheets\GML.ico'))
        
        self.settings = QSettings('GML', 'GML Reader')
        if self.settings.value('MapStaysOnTopHint', False, type=bool):
            self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        
        connect.MapWindow = self
        connect.path_to_map = path_to_map
        connect.target_xlsx = target_xlsx

        data.parsed_gml = parsed_gml

        self.setMinimumSize(1000, 500)
        self.adjustSize()
        
        self.init_UI()
        self.init_button()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjustButtons()

    def adjustButtons(self):
        win_width = self.width()  # Correct method call
        self.browse_in_geoportal.setGeometry(win_width - 162, 5, 140, 28)
        self.browse_in_street_view.setGeometry(win_width - 162, 36, 140, 28)
    
    def init_button(self):
        self.browse_in_geoportal = QPushButton(self)
        self.browse_in_geoportal.setIcon(QtGui.QIcon(path_manager.get_stylesheets_folder_path("Geoportal.svg")))
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
        self.browse_in_geoportal.clicked.connect(self.find_parcel_in_geoportal)
        self.browse_in_geoportal.setToolTip("Po naciśnięciu tego przycisku wybierz działkę, która ma zostać otwarta w Geoportalu Krajowy.")
        
        self.browse_in_street_view = QPushButton(self)
        self.browse_in_street_view.setIcon(QtGui.QIcon(path_manager.get_stylesheets_folder_path("StreetView.svg")))
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
        self.browse_in_street_view.clicked.connect(self.find_parcel_in_street_view)
        self.browse_in_street_view.setToolTip("Po naciśnięciu tego przycisku wybierz działkę drogową, która ma zostać otwarta w StreetView.")

    def init_UI(self):
        self.graphic()

        self.remove_dzi_button = QCheckBox('Działki', self)
        self.remove_dzi_button.setChecked(True)
        self.remove_dzi_button.move(10, 0)
        self.remove_dzi_button.stateChanged.connect(lambda state: self.dzialki_mapa() if state == 2 else self.remove_dzialki())
        
        self.remove_dzi_button = QCheckBox('Poligon', self)
        self.remove_dzi_button.move(100, 00)
        self.remove_dzi_button.stateChanged.connect(lambda state: self.turn_on_polygon_selection() if state == 2 else self.find_touching_polygons())  # turn_off_polygon_selection

        self.remove_dzi_button = QCheckBox('Użytki', self)
        #self.remove_dzi_button.setChecked(True)
        self.remove_dzi_button.move(10, 20)
        self.remove_dzi_button.stateChanged.connect(lambda state: self.uzytki_mapa() if state == 2 else self.remove_uzytki())

        self.remove_dzi_button = QCheckBox('Zawiadomienia', self)
        self.remove_dzi_button.move(100, 20)
        self.remove_dzi_button.stateChanged.connect(lambda state: self.turn_on_polygon_selection() if state == 2 else self.find_polygons())  # turn_off_polygon_selection

        self.remove_dzi_button = QCheckBox('Punkty', self)
        #self.remove_dzi_button.setChecked(True)
        self.remove_dzi_button.move(10, 40)
        self.remove_dzi_button.stateChanged.connect(lambda state: self.punkty_mapa() if state == 2 else self.remove_punkty())

        self.remove_dzi_button = QCheckBox('Budynki', self)
        #self.remove_dzi_button.setChecked(True)
        self.remove_dzi_button.move(10, 60)
        self.remove_dzi_button.stateChanged.connect(lambda state: self.budynki_mapa() if state == 2 else self.remove_budynki())

        self.remove_dzi_button = QCheckBox('Ogrodzenia', self)
        #self.remove_dzi_button.setChecked(True)
        self.remove_dzi_button.move(10, 80)
        self.remove_dzi_button.stateChanged.connect(lambda state: self.ogrodzenia_mapa() if state == 2 else self.remove_ogrodzenia())

        self.remove_dzi_button = QCheckBox('Murek', self)
        #self.remove_dzi_button.setChecked(True)
        self.remove_dzi_button.move(10, 100)
        self.remove_dzi_button.stateChanged.connect(lambda state: self.murek_mapa() if state == 2 else self.remove_murek())

    def graphic(self): 
        self.scene = QGraphicsScene()
        try:
            data.EPSG = read_EPSG(connect.path_to_map)
        except Exception as e:
            logging.exception(e)
            print(e)
            
        try:
            działki_wizualizacja(self.scene, connect.path_to_map)
        except Exception as e:
            logging.exception(e)
            print(e)
        try:
            text_wizualizacja(self.scene, connect.path_to_map)
        except Exception as e:
            logging.exception(e)
            print(e)
        try:
            działki_punkty_stabilizacja(self.scene, connect.path_to_map)
        except Exception as e:
            logging.exception(e)
            print(e)
        self.remove_gfs_file()

        self.gview = GraphicsView(self)  # Store gview as an instance variable
        self.gview.setScene(self.scene)
        #self.gview.setGeometry(0, 0, 1000, 500)
        
        self.setCentralWidget(self.gview)  # Ustawienie widoku jako centralnego widgetu okna

        expanded_scene_rect = self.scene.sceneRect().adjusted(-1000, -1000, 1000, 1000)
        self.scene.setSceneRect(expanded_scene_rect)
        self.gview.setSceneRect(expanded_scene_rect)

    def find_parcel_in_geoportal(self):
        data.search_parcel_by_id = True

    def find_parcel_in_street_view(self):
        data.search_in_street_view = True

    def dzialki_mapa(self):
        self.remove_dzialki()
        try:
            działki_wizualizacja(self.scene, connect.path_to_map)
        except Exception as e:
            logging.exception(e)
            print(e)
        self.remove_gfs_file()

    def uzytki_mapa(self):
        self.remove_uzytki()
        try:
            działki_kontury(self.scene, connect.path_to_map)
        except Exception as e:
            logging.exception(e)
            print(e)
        self.remove_gfs_file()

    def punkty_mapa(self):
        self.remove_punkty()
        try:
            działki_punkty(self.scene, connect.path_to_map)
        except Exception as e:
            logging.exception(e)
            print(e)
        self.remove_gfs_file()

    def budynki_mapa(self):
        self.remove_budynki()
        try:
            budynki_wizualizacja(self.scene, connect.path_to_map)
        except Exception as e:
            logging.exception(e)
            print(e)
        try:
            numery_budynkow_wizualizacja(self.scene, connect.path_to_map)
        except Exception as e:
            logging.exception(e)
            print(e)  
        self.remove_gfs_file()

    def ogrodzenia_mapa(self):
        self.remove_ogrodzenia()
        try:
            ogrodzenia_wizualizacja(self.scene, connect.path_to_map)
        except Exception as e:
            logging.exception(e)
        self.remove_gfs_file()

    def murek_mapa(self):
        self.remove_murek()
        try:
            murek_wizualizacja(self.scene, connect.path_to_map)
        except Exception as e:
            logging.exception(e)
        self.remove_gfs_file()

    def remove_gfs_file(self):
        try:
            root, ext = os.path.splitext(connect.path_to_map)
            os.remove(root + ".gfs")
        except Exception as e:
            logging.exception(e)
            print("GFS file not removed.")

    def remove_dzialki(self):
        for polygon in data.dzialki:
            self.scene.removeItem(polygon)
        data.dzialki = []

    def remove_uzytki(self):
        for polygon in data.kontury:
            self.scene.removeItem(polygon)
        data.kontury = []

    def remove_punkty(self):
        for text_item in data.punkty:
            self.scene.removeItem(text_item)  # Remove the item from the scene
        data.punkty = []  # Clear the list of text items

    def remove_budynki(self):
        for item in data.budynki:
            self.scene.removeItem(item)  # Remove the item from the scene
        data.budynki = []

    def remove_ogrodzenia(self):
        for item in data.ogrodzenia:
            self.scene.removeItem(item)  # Remove the item from the scene
        data.ogrodzenia = []

    def remove_murek(self):
        for item in data.murki:
            self.scene.removeItem(item)  # Remove the item from the scene
        data.murki = []

    def remove_items(self, items):
        for item in items:
            self.scene.removeItem(item)  # Remove the item from the scene
        items = []

    def add_selected_polygon_to_list(self):
        selected_polygons = {}  # Create a dictionary to store selected polygons with their IDs
        for polygon in data.dzialki:
            if polygon.isSelected():
                selected_polygons[polygon.id] = polygon  # Store selected polygons by their IDs
        return selected_polygons  # Return the dictionary of selected polygons

    def turn_on_polygon_selection(self):
        for polygon in data.dzialki:
            polygon.setAcceptHoverEvents(True)
            polygon.setFlag(QGraphicsPolygonItem.ItemIsSelectable)
            polygon.hoverEnter = lambda event, p=polygon: self.polygon_hover_enter(polygon)
            polygon.hoverLeave = lambda event, p=polygon: self.polygon_hover_leave(polygon)
    
    def turn_off_polygon_selection(self):
        for polygon in data.dzialki:
            polygon.setAcceptHoverEvents(False)
            polygon.setFlag(QGraphicsPolygonItem.ItemIsSelectable, False)
    
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

    def find_touching_polygons(self):
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
        self.turn_off_polygon_selection()
        columns = ['ID', 'Działka']
        df_overlap_polygons = pd.DataFrame(bordering_polygons, columns=columns)
        try:
            overlap_polygons(df_overlap_polygons)
        except Exception as e:
            logging.exception(e) 

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

        self.turn_off_polygon_selection()

        columns = ['Działka']
        bordering_polygons = pd.DataFrame(bordering_polygons, columns=columns)
        try:
            overlap_polygons(bordering_polygons)
        except Exception as e:
            logging.exception(e)

    def send_item(self, id):
        self.item_signal.emit(id)


def działki_wizualizacja(scene, path_to_map=None):
    df_dz_Dzi = gpd.read_file(path_to_map, layer='EGB_DzialkaEwidencyjna', schema=None)
    
    geometry_dz = df_dz_Dzi['geometry']
    for id, geom in zip(df_dz_Dzi['idDzialki'], geometry_dz):
        if isinstance(geom, Polygon):
            x, y = geom.exterior.coords.xy  # Pobierz współrzędne x, y wielokąta
            # x = [-i for i in x]
            y = [-i for i in y]  # Odwróć osie X i Y, mnożąc wszystkie wartości przez -1
            coords = list(zip(x, y))  # Utwórz listę współrzędnych wielokąta
            polygon = QGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]), id)  # Dodaj wielokąt do sceny
            pen = QPen(Qt.black)
            pen.setWidthF(0.2)  
            polygon.setPen(pen)
            polygon.setZValue(-1)

            scene.addItem(polygon)
            data.dzialki.append(polygon)  # Store for later removal

def działki_kontury(scene, path_to_map=None):
    df_dz_Kon = gpd.read_file(path_to_map, layer='EGB_KonturUzytkuGruntowego', schema=None)

    geometry_kon = df_dz_Kon['geometry']
    for id, geom in zip(df_dz_Kon['idUzytku'], geometry_kon):
        if isinstance(geom, Polygon):
            x, y = geom.exterior.coords.xy  # Pobierz współrzędne x, y wielokąta
            # x = [-i for i in x]
            y = [-i for i in y]  # Odwróć osie X i Y, mnożąc wszystkie wartości przez -1
            coords = list(zip(x, y))  # Utwórz listę współrzędnych wielokąta
            polygon = QGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]))  # Dodaj wielokąt do sceny
            pen = QPen(Qt.darkGreen)
            #pen.setStyle(Qt.DashLine)  # Set the pen style to dashed line
            pen.setWidthF(0.18)  # Set the width of the line
            pen.setDashPattern([2, 4])  # Set the dash pattern (1 pixel dash, 4 pixels space)
            polygon.setPen(pen)
            polygon.setFlag(QGraphicsItem.ItemIsFocusable, False)  # Make the polygon non-selectable
            polygon.setFlag(QGraphicsItem.ItemIsSelectable, False)
            polygon.setZValue(-1)

            scene.addItem(polygon)
            data.kontury.append(polygon)  # Store for later removal

def działki_punkty(scene, path_to_map=None):
    df_dz_PunktGran = gpd.read_file(path_to_map, layer='EGB_PunktGraniczny', schema=None)

    for index, PGran in df_dz_PunktGran.iterrows():
        point = PGran.geometry
        numeric_value = PGran['idPunktu']
        numeric_value = numeric_value.rsplit('.', 1)[-1]
        screen_x = point.x
        screen_y = -point.y
        text_item = DraggableTextItem(str(numeric_value))

        text_size = 1.2
        font = QFont("Times New Roman")
        font.setPointSizeF(text_size)
        text_item.setFont(font)
        text_item.adjustSize()
        text_item.setPos(screen_x - text_size / 2 - 2.5, screen_y - text_size / 2 - 4)
        text_item.setDefaultTextColor(QColor('gray'))
        text_item.setZValue(1)

        scene.addItem(text_item)
        data.punkty.append(text_item)

def działki_punkty_stabilizacja(scene, path_to_map=None):
    df_dz_PunktGra_stab = gpd.read_file(path_to_map, layer='EGB_PunktGraniczny', schema=None)
    
    for index, PGran in df_dz_PunktGra_stab.iterrows():
        point = PGran.geometry
        rodzajStabilizacji = PGran['rodzajStabilizacji']
        
        screen_x = point.x
        screen_y = -point.y

        if 3 <= rodzajStabilizacji <= 6:
            dot_size = 0.8
            dot_item = QGraphicsEllipseItem(screen_x - dot_size / 2, screen_y - dot_size / 2, dot_size, dot_size)
            dot_item.setBrush(QBrush(QColor('white')))
            dot_item.setPen(QPen(QColor('black'), 0.2))
            dot_item.setZValue(1)
        else:
            dot_size = 0.5
            dot_item = QGraphicsEllipseItem(screen_x - dot_size / 2, screen_y - dot_size / 2, dot_size, dot_size)
            dot_item.setBrush(QBrush(QColor('black')))
            dot_item.setPen(QPen(QColor('white'), 0.2))

        scene.addItem(dot_item)

def text_wizualizacja(scene, path_to_map=None):
    df_text_wiz = gpd.read_file(path_to_map, layer='PrezentacjaGraficzna', schema=None)

    df_text_wiz = df_text_wiz[df_text_wiz['kodObiektu'].isin(['EGDE'])].reset_index(drop=True)

    for index, row in df_text_wiz.iterrows():
        # Extract the geometry (point) and numeric value from your GeoDataFrame
        point = row.geometry
        try:
            numeric_value = row['tekst']
        except:
            numeric_value = row['name']
        
        screen_x = point.x  # Convert geographic coordinates to screen coordinates (you may need to adjust this part)
        screen_y = -point.y

        text_item = DraggableTextItem(str(numeric_value))

        font = QFont("Times New Roman")
        font.setPointSize(3)
        text_item.setFont(font)
        rect = text_item.boundingRect()
        
        center_x = screen_x - rect.width() / 2
        center_y = screen_y - rect.height() / 2
        text_item.setPos(screen_x - text_item.boundingRect().width() / 2 - 3.6, screen_y - text_item.boundingRect().height() / 2 - 4.2)
        text_item.setDefaultTextColor(QColor('red'))
        #text_item.setFlag(QGraphicsTextItem.ItemIsSelectable, True)
        text_item.setZValue(1)
        
        scene.addItem(text_item)

def budynki_wizualizacja(scene, path_to_map=None):
    df_dz_Bud = gpd.read_file(path_to_map, layer='EGB_Budynek', schema=None)

    geometry_Bud  = df_dz_Bud['geometry']
    df_dz_Bud['liczbaKondygnacjiNadziemnych'] = df_dz_Bud['liczbaKondygnacjiNadziemnych'].astype(str)
    df_dz_Bud['rodzajBudynku'] = df_dz_Bud['rodzajWgKST'] + df_dz_Bud['liczbaKondygnacjiNadziemnych']
    for id, geom in zip(df_dz_Bud['rodzajBudynku'], geometry_Bud ):
        if isinstance(geom, MultiPolygon):
            for polygon_component in geom.geoms:
                x, y = polygon_component.exterior.coords.xy
                y = [-i for i in y]
                coords = list(zip(x, y))
                centroid_x = polygon_component.centroid.x
                centroid_y = -polygon_component.centroid.y
                multipolygon = QGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]))
                pen = QPen(Qt.black)
                pen.setWidthF(0.4)  
                multipolygon.setPen(pen)
                multipolygon.setZValue(-2)

                scene.addItem(multipolygon)
                data.budynki.append(multipolygon)

                if id is not None:
                    #id = id.split(".")[2].split("_")[0]
                    text_item = QGraphicsTextItem(str(id))
                    font = QFont("Times New Roman")
                    font.setPointSizeF(1.5)
                    text_item.setFont(font)
                    text_item.setDefaultTextColor(QColor('purple'))
                    text_item.setZValue(1)
                    text_rect = text_item.boundingRect()
                    text_x = centroid_x - text_rect.width() / 2
                    text_y = centroid_y - text_rect.height() / 2
                    text_item.setPos(text_x, text_y)

                    scene.addItem(text_item)
                    data.budynki.append(text_item)

def numery_budynkow_wizualizacja(scene, path_to_map=None):    
    df_text_nr_bud = gpd.read_file(path_to_map, layer='PrezentacjaGraficzna', schema=None)
    df_text_nr_bud = df_text_nr_bud[df_text_nr_bud['kodObiektu'].isnull()].reset_index(drop=True)

    for idx, row_nr in df_text_nr_bud.iterrows():
        try:
            text_nr = str(row_nr['tekst'])
        except Exception as e:
            logging.exception(e)
        try:
            text_nr = str(row_nr['name'])
        except Exception as e:
            logging.exception(e)
        
        geom_nr = row_nr['geometry']
        if isinstance(geom_nr, Point):
            try:
                rotation_angle_radians_nr = row_nr['katObrotu']
            except Exception as e:
                logging.exception(e)
                rotation_angle_radians_nr = 0
            centroid_x_nr = geom_nr.centroid.x
            centroid_y_nr = -geom_nr.centroid.y
            text_item_nr = QGraphicsTextItem(text_nr)
            font_nr = QFont("Arial")
            font_nr.setPointSizeF(2)
            text_item_nr.setFont(font_nr)
            text_item_nr.setDefaultTextColor(QColor('purple'))
            text_item_nr.setZValue(1)
            text_item_nr.setTransformOriginPoint(text_item_nr.boundingRect().center())
            text_rect_nr = text_item_nr.boundingRect()
            text_x_nr = centroid_x_nr - text_rect_nr.width() / 2
            text_y_nr = centroid_y_nr - text_rect_nr.height() / 2
            text_item_nr.setPos(text_x_nr, text_y_nr)
            rotation_angle_nr = math.degrees(rotation_angle_radians_nr)
            text_item_nr.setRotation(-rotation_angle_nr)
            # scene.addItem(text_item_nr)
            # Mainwindow.data.budynki.append(text_item_nr)

def ogrodzenia_wizualizacja(scene, path_to_map=None):
    df_ogrodzenia = gpd.read_file(path_to_map, layer='OT_Ogrodzenia')
    geometry = df_ogrodzenia['geometry']
    ids = df_ogrodzenia['rodzajOgrodzenia']

    id_line = {
        'o': (Qt.gray, 0.2, 1),  # Dodana szerokość linii
        'b': (Qt.blue, 0.1, 2),  # Dodana szerokość linii
        'f': (Qt.red, 0.1, 3),   # Dodana szerokość linii
        }
    
    dot_interval_cm = 10.0
    for geom, line_id in zip(geometry, ids):
        if isinstance(geom, MultiLineString):
            for line in geom.geoms:
                x, y = line.coords.xy
                x = list(x)
                y = [-i for i in list(y)]
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
                            scene.addItem(dot_item)
                            data.ogrodzenia.append(dot_item)
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

                        scene.addItem(svg_item)
                        data.ogrodzenia.append(svg_item)

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

                        scene.addItem(svg_item)
                        data.ogrodzenia.append(svg_item)

                    line_item = QGraphicsLineItem(x1, y1, x2, y2)
                    line_properties = id_line.get(line_id, (Qt.gray, 0.3, 1))
                    color, line_width, _ = line_properties
                    pen = QPen(color)
                    pen.setWidthF(line_width)
                    pen.setCapStyle(Qt.RoundCap)
                    pen.setJoinStyle(Qt.RoundJoin)
                    line_item.setPen(pen)

                    scene.addItem(line_item)
                    data.ogrodzenia.append(line_item)

def murek_wizualizacja(scene, path_to_map=None):
    df_ogrodzenia = gpd.read_file(path_to_map, layer='OT_Budowle')
    ids = df_ogrodzenia['rodzajBudowli']
    
    color = Qt.black
    width = 0.1
    buffer_distance = 0.2

    geometry = df_ogrodzenia['geometry']
    for geom, line_id in zip(geometry, ids):
        if isinstance(geom, LineString):
            buffered_polygon = geom.buffer(buffer_distance, cap_style=2)
            
            # Convert the buffered polygon to QPolygonF format
            polygon_points = [QPointF(x, -y) for x, y in buffered_polygon.exterior.coords]
            q_polygon = QPolygonF(polygon_points)
            
            # Create the QGraphicsPolygonItem with the polygon shape
            outline = QGraphicsPolygonItem(q_polygon)
            
            # Set up the pen for the outline
            pen = QPen(color)
            pen.setWidthF(width)
            pen.setCapStyle(Qt.FlatCap)
            pen.setJoinStyle(Qt.BevelJoin)
            outline.setPen(pen)
            
            # Add the polygon item to the scene
            scene.addItem(outline)
            data.murki.append(outline)

# Tymczasowe rozwiązanie. Sensowniejsza będzie opcja wyboru określonych działek i dalsza analiza w głównym oknie.

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