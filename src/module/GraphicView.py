from PySide6.QtWidgets import (QApplication, QGraphicsLineItem, QMainWindow,
                               QGraphicsItem, QCheckBox, QGraphicsEllipseItem,
                               QApplication, QMainWindow, QGraphicsView,
                               QGraphicsScene, QGraphicsPolygonItem, QGraphicsTextItem,
                               QFileDialog)
from PySide6.QtGui import (QFont, QPolygonF, QPolygonF, QPainter, QFont,
                           QColor, QBrush, QPen, QIcon, QPainterPath)
from shapely.geometry import Polygon, MultiPolygon, Point, MultiLineString, LineString
from PySide6.QtCore import Qt, QPointF, QPoint, QRectF, QTimer, Signal, QSettings
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtSvg import QSvgRenderer
from dataclasses import dataclass
from PySide6 import QtCore
from pathlib import Path
import geopandas as gpd
import pandas as pd

from function.search_in_geoportal import open_parcel_in_geoportal

import logging
import math
import sys
import os


class connect:
    EmitID: str = None

    MapWindow: str = None
    path_to_map: str = None
    target_xlsx: str = None


@dataclass
class data:
    EPSG: str = None

    search_parcel_by_id: bool = False
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
            self.last_x_y_position = self.mapToScene(event.position().toPoint())
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

    def __init__(self, polygon, id=None, parent=None):
        super(QGraphicsPolygonItem, self).__init__(polygon, parent)
        self.id = id

        self.color_timer = QTimer()
        self.color_timer.timeout.connect(self.resetPolygonColor)

        self.setFlag(QGraphicsItem.ItemStacksBehindParent, False)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.id != None:

                connect.EmitID.send_item(self.id)
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


class EmitMap(QMainWindow):
    item_signal = Signal(str)
    def __init__(self): 
        super().__init__()
        
        connect.EmitID = self

    def send_item(self, id):
        self.item_signal.emit(id)


class MapHandler():
    def __init__(self):
        super().__init__()

    def find_polygon_in_web(self):
        data.search_parcel_by_id = True

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


    def remove_gfs_file(Path):
        try:
            root, ext = os.path.splitext(Path)
            os.remove(root + ".gfs")
        except Exception as e:
            logging.exception(e)
            print("GFS file not removed.")

    def remove_dzialki(scene):
        for polygon in data.dzialki:
            scene.removeItem(polygon)
        data.dzialki = []

    def remove_uzytki(scene):
        for polygon in data.kontury:
            scene.removeItem(polygon)
        data.kontury = []

    def remove_punkty(scene):
        for text_item in data.punkty:
            scene.removeItem(text_item)  # Remove the item from the scene
        data.punkty = []  # Clear the list of text items

    def remove_budynki(scene):
        for item in data.budynki:
            scene.removeItem(item)  # Remove the item from the scene
        data.budynki = []

    def remove_ogrodzenia(scene):
        for item in data.ogrodzenia:
            scene.removeItem(item)  # Remove the item from the scene
        data.ogrodzenia = []

    def remove_murek(scene):
        for item in data.murki:
            scene.removeItem(item)  # Remove the item from the scene
        data.murki = []

    def remove_items(scene, items):
        for item in items:
            scene.removeItem(item)  # Remove the item from the scene
        items = []


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

    geometry = df_ogrodzenia['geometry']
    for geom, line_id in zip(geometry, ids):
        if isinstance(geom, LineString):
            x, y = geom.coords.xy
            x = list(x) 
            y = [-i for i in list(y)]
            coords = list(zip(x, y))
 
            for i in range(len(coords) - 1):
                x1, y1 = coords[0]
                x2, y2 = coords[1]
                delta_x = x2 - x1
                delta_y = y2 - y1
                parallel_line_distance = 0.2
                line_length = (delta_x ** 2 + delta_y ** 2) ** 0.5
                offset_x = parallel_line_distance * delta_y / line_length
                offset_y = -parallel_line_distance * delta_x / line_length
                new_start_point = (x1 - offset_x, y1 - offset_y)
                new_end_point = (x1 + offset_x, y1 + offset_y)
                outline_start = QGraphicsLineItem(new_start_point[0], new_start_point[1], new_end_point[0], new_end_point[1])
                pen_start = QPen(color)
                pen_start.setWidthF(width)
                pen_start.setCapStyle(Qt.RoundCap)
                pen_start.setJoinStyle(Qt.RoundJoin)
                outline_start.setPen(pen_start)

                scene.addItem(outline_start)
                data.murki.append(outline_start)

                x1, y1 = coords[-2]
                x2, y2 = coords[-1]
                delta_x = x2 - x1
                delta_y = y2 - y1
                line_length = (delta_x ** 2 + delta_y ** 2) ** 0.5
                offset_x = parallel_line_distance * delta_y / line_length
                offset_y = -parallel_line_distance * delta_x / line_length
                new_start_point = (x2 - offset_x, y2 - offset_y)
                new_end_point = (x2 + offset_x, y2 + offset_y)
                outline_end = QGraphicsLineItem(new_start_point[0], new_start_point[1], new_end_point[0], new_end_point[1])
                pen_end = QPen(color)
                pen_end.setWidthF(width)
                pen_end.setCapStyle(Qt.RoundCap)
                pen_end.setJoinStyle(Qt.RoundJoin)
                outline_end.setPen(pen_end)

                scene.addItem(outline_end)
                data.murki.append(outline_end)
                
                x1, y1 = coords[i] 
                x2, y2 = coords[i + 1]

                line_item = QGraphicsLineItem(x1, y1, x2, y2)
                pen = QPen(color)
                pen.setWidthF(width)
                line_item.setPen(pen)
                #scene.addItem(line_item)

                delta_x = x2 - x1
                delta_y = y2 - y1
                parallel_line_distance = 0.2
                line_length = (delta_x ** 2 + delta_y ** 2) ** 0.5
                offset_x = parallel_line_distance * delta_y / line_length
                offset_y = -parallel_line_distance * delta_x / line_length
                new_start_point = (x1 + offset_x, y1 + offset_y)
                new_end_point = (x2 + offset_x, y2 + offset_y)
                outline = QGraphicsLineItem(new_start_point[0], new_start_point[1], new_end_point[0], new_end_point[1])
                pen = QPen(color)
                pen.setWidthF(width)
                pen.setCapStyle(Qt.RoundCap)
                pen.setJoinStyle(Qt.RoundJoin)
                outline.setPen(pen)

                scene.addItem(outline)
                data.murki.append(outline)
                
                x1, y1 = coords[i + 1]
                x2, y2 = coords[i]
                delta_x = x2 - x1
                delta_y = y2 - y1
                line_length = (delta_x ** 2 + delta_y ** 2) ** 0.5
                offset_x = parallel_line_distance * delta_y / line_length
                offset_y = -parallel_line_distance * delta_x / line_length
                new_start_point = (x1 + offset_x, y1 + offset_y)
                new_end_point = (x2 + offset_x, y2 + offset_y)
                outline = QGraphicsLineItem(new_start_point[0], new_start_point[1], new_end_point[0], new_end_point[1])
                pen = QPen(color)
                pen.setWidthF(width)
                pen.setCapStyle(Qt.RoundCap)
                pen.setJoinStyle(Qt.RoundJoin)
                outline.setPen(pen)
                
                scene.addItem(outline)
                data.murki.append(outline)


if __name__ == '__main__':
    pass