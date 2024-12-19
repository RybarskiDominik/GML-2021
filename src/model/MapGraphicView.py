from PySide6.QtWidgets import (QApplication, QGraphicsLineItem, QMainWindow,
                               QGraphicsItem, QCheckBox, QGraphicsEllipseItem,
                               QApplication, QMainWindow, QGraphicsView,
                               QGraphicsScene, QGraphicsPolygonItem, QGraphicsTextItem,
                               QFileDialog, QStyleOptionGraphicsItem, QWidget, QGraphicsRectItem, QGraphicsSimpleTextItem)
from PySide6.QtGui import (QFont, QPolygonF, QPolygonF, QPainter, QFont,
                           QColor, QBrush, QPen, QIcon, QPainterPath, QFontMetrics)
from shapely.geometry import Polygon, MultiPolygon, Point, MultiLineString, LineString
from PySide6.QtCore import Qt, QPointF, QPoint, QRectF, QTimer, Signal, QSettings
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtSvg import QSvgRenderer
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from PySide6 import QtCore
from pathlib import Path
import geopandas as gpd
import pandas as pd

from function.search_in_geoportal import open_parcel_in_geoportal
from function.search_in_street_view import open_parcel_in_street_view
from model.GML_processing_by_ET import GMLParser

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
    def __init__(self, scene=None, parent=None):
        super().__init__(scene, parent)

        self.minZoom = 0
        self.maxZoom = 80.0

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

        #self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

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
                open_parcel_in_street_view(self.last_x_y_position, EPSG=data.EPSG)
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
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
        else:
            super().mouseMoveEvent(event)
   

class DraggableTextItem(QGraphicsSimpleTextItem):
    def __init__(self, text, parent=None):
        super(DraggableTextItem, self).__init__(text, parent)
        self.setFlag(QGraphicsSimpleTextItem.ItemIsMovable)
       
        #self.text = text

    def test_boundingRect(self):
        
        font_metrics = QFontMetrics(self.font())
        rect = font_metrics.boundingRect(self.text)
        rect = QRectF(rect.x(), rect.y(), rect.width(), rect.height())
        #return rect
    
        #rect = font_metrics.boundingRect(self.toPlainText())
        #return QRectF(rect)

        #rect = text_item.get_boundingRect()
        #text_item.boundingRect = lambda: rect

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


class connect:
    EmitID: str = None


@dataclass
class data:
    EPSG = None

    search_parcel_by_id = False
    search_in_street_view = False
    parsed_gml = None

    mark = []

    KonturUzytkuGruntowego = []
    KonturKlasyfikacyjny = []
    KonturUzytkuGruntowego = []
    DzialkaEwidencyjna = []
    PunktGraniczny = []
    PunktGraniczny_STB = []
    Ogrodzenia = []
    Budynek = []
    Budowle = []
    AdresNieruchomosci = []


class MapHandler:
    def __init__(self, scene=None, path=None):
        self.scene = scene
        self.path = path

        self.data = data()

    def find_parcel_in_geoportal(self):
        data.search_parcel_by_id = True

    def find_parcel_in_street_view(self):
        data.EPSG= self.data.EPSG
        data.search_in_street_view = True


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

        self.turn_off_polygon_selection()

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
        self.turn_off_polygon_selection()
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

        self.turn_off_polygon_selection()

        columns = ['Działka']
        bordering_polygons = pd.DataFrame(bordering_polygons, columns=columns)
        return bordering_polygons


    def remove_items(self, items):
        for item in items:
            if item.scene() == self.scene:
                self.scene.removeItem(item)
        items = []

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

    def add_mark(self, x, y, color="white"):
        square_size = 0.1
        square = QGraphicsRectItem(QRectF(x - square_size / 2, y - square_size / 2, square_size, square_size))
        square.setBrush(QBrush(QColor(color)))
        square.setPen(QPen(QColor('black'), 0.02))
        square.setZValue(40)
        self.scene.addItem(square)
        self.data.mark.append(square)


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

    def set_alignment(self, x=None, y=None, rect=None, alignment='center'):
        if alignment in ['center', '5']:
            pos_x = x - rect.center().x()
            pos_y = y - rect.center().y()
        elif alignment in ['left', '4']:
            pos_x = x - rect.left()
            pos_y = y - rect.center().y()
        elif alignment in ['right', '6']:
            pos_x = x - rect.right()
            pos_y = y - rect.center().y()
        elif alignment in ['top', '8']:
            pos_x = x - rect.center().x()
            pos_y = y - rect.top()
        elif alignment in ['bottom', '2']:
            pos_x = x - rect.center().x()
            pos_y = y - rect.bottom()
        elif alignment in ['top-left', '7']:
            pos_x = x - rect.left()
            pos_y = y - rect.top()
        elif alignment in ['top-right', '9']:
            pos_x = x - rect.right()
            pos_y = y - rect.top()
        elif alignment in ['bottom-left', '1']:
            pos_x = x - rect.left()
            pos_y = y - rect.bottom()
        elif alignment in ['bottom-right', '3']:
            pos_x = x - rect.right()
            pos_y = y - rect.bottom()
        else:
            pos_x = x - rect.center().x()
            pos_y = y - rect.center().y()
        
        return pos_x, pos_y


    def load_map(self, df):
        self.data.EPSG = GMLParser.get_crs_epsg(self.path)
        try:
            self.remove_items(self.data.mark)
            self.remove_items(self.data.PunktGraniczny_STB)
        except Exception as e:
            logging.exception(e)
            print(e)
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


    def add_DzialkaEwidencyjna(self, df):
        self.remove_items(self.data.DzialkaEwidencyjna)
        geometry = df['geometria']

        nr_dzialki = None
        if "tekst" in df.columns:
            nr_dzialki = df["tekst"]
        nr_dzialki = nr_dzialki.fillna(df["idDzialki"].str.rsplit('.', n=1).str.get(-1))

        for id, geom, point, nr, justyfikacja in zip(df['idDzialki'], geometry, df['pos'], nr_dzialki, df['justyfikacja']):
            if isinstance(geom, list) and all(isinstance(point, tuple) for point in geom):
                geom = Polygon(geom)
                y, x = geom.exterior.coords.xy  # Zamiana X/Y podczas importu jak w qgis.
                y = [-i for i in y]
                coords = list(zip(x, y))
                polygon = MyQGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]), id)
                pen = QPen(Qt.black)
                pen.setWidthF(0.2)
                polygon.setPen(pen)
                polygon.setZValue(-1)
                self.scene.addItem(polygon)
                self.data.DzialkaEwidencyjna.append(polygon)

            if isinstance(point, tuple) and len(point) == 2:
                y, x = point
                y = -y

                self.add_mark(x, y, 'green')

                text_item = DraggableTextItem(str(nr))
                font = QFont("Times New Roman", 2, QFont.Bold)
                text_item.setFont(font)

                justyfikacja = justyfikacja
                if not justyfikacja:
                    justyfikacja = 5

                rect = text_item.boundingRect()
                x, y = self.set_alignment(x, y, rect, alignment=str(justyfikacja))
                text_item.setPos(x, y)
                
                text_item.setBrush(QColor('red'))
                text_item.setZValue(1)

                self.scene.addItem(text_item)
                self.data.DzialkaEwidencyjna.append(text_item)

    def add_PunktGraniczny(self, df):
        self.remove_items(self.data.PunktGraniczny)
        geometry = df['geometria']
        nr_punktu = None
        if "tekst" in df.columns:
            nr_punktu = df["tekst"]
        nr_punktu = nr_punktu.fillna(df["idPunktu"].str.rsplit('.', n=1).str.get(-1)) #.rsplit('.', 1)[-1]

        rodzajStabilizacji = df["rodzajStabilizacji"].apply(pd.to_numeric, errors='coerce')

        for pos, nr, rodzajStabilizacji in zip(geometry, nr_punktu, rodzajStabilizacji):
            if isinstance(pos, tuple) and len(pos) == 2:
                y, x = pos
                y = -y

                self.add_mark(x, y, 'green')

                text_item = DraggableTextItem(str(nr))
                font = QFont('Times New Roman')
                font.setPointSizeF(1.2)
                text_item.setFont(font)

                rect = text_item.boundingRect()
                x, y = self.set_alignment(x, y, rect, alignment="top-left")
                text_item.setPos(x, y)
                
                text_item.setBrush(QColor('black'))
                text_item.setZValue(1)

                self.scene.addItem(text_item)
                self.data.PunktGraniczny.append(text_item)

                if 3 <= rodzajStabilizacji <= 6:
                    dot_size = 0.8
                    dot_item = QGraphicsEllipseItem(x - dot_size / 2, y - dot_size / 2, dot_size, dot_size)
                    dot_item.setBrush(QBrush(QColor('white')))
                    dot_item.setPen(QPen(QColor('black'), 0.2))
                    dot_item.setZValue(1)
                else:
                    dot_size = 0.5
                    dot_item = QGraphicsEllipseItem(x - dot_size / 2, y - dot_size / 2, dot_size, dot_size)
                    dot_item.setBrush(QBrush(QColor('black')))
                    dot_item.setPen(QPen(QColor('white'), 0.2))

                self.scene.addItem(dot_item)
                self.data.PunktGraniczny_STB.append(dot_item)

    def add_KonturKlasyfikacyjny(self, df):
        self.remove_items(self.data.KonturKlasyfikacyjny)
        geometry = df['geometria']

        nr_Konturu = None
        if "tekst" in df.columns:
            nr_Konturu = df["tekst"]

        nr_Konturu = nr_Konturu.fillna(df.apply(lambda row: f'{row["OZU"]}' if pd.isna(row["OZK"]) 
                            else f'{row["OZK"]}' if pd.isna(row["OZU"]) 
                            else f'{row["OZU"]} {row["OZK"]}', axis=1))

        for i, (geom, point) in enumerate(zip(geometry, df['pos'])):
            nr = nr_Konturu[i]
            if isinstance(geom, list) and all(isinstance(point, tuple) for point in geom):
                geom = Polygon(geom)
                y, x = geom.exterior.coords.xy  # Zamiana X/Y podczas importu jak w qgis.
                y = [-i for i in y]
                coords = list(zip(x, y))
                polygon = MyQGraphicsPolygonItem(QPolygonF([QPointF(*coord) for coord in coords]))

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

                self.add_mark(x, y, 'green')

                text_item = DraggableTextItem(str(nr))
                font = QFont('Times New Roman', 2, QFont.Normal)
                text_item.setFont(font)

                rect = text_item.boundingRect()
                x, y = self.set_alignment(x, y, rect, alignment="center")
                text_item.setPos(x, y)
                
                text_item.setBrush(QColor(Qt.green))
                text_item.setZValue(1)

                self.scene.addItem(text_item)
                self.data.KonturKlasyfikacyjny.append(text_item)

    def add_Budynek(self, df):
        self.remove_items(self.data.Budynek)
        df['liczbaKondygnacjiNadziemnych'] = df['liczbaKondygnacjiNadziemnych'].astype(str)
        df['rodzajBudynku'] = df['rodzajWgKST'] + df['liczbaKondygnacjiNadziemnych']
        geometria = (df['geometria'])
        for id, geom, point, justyfikacja in zip(df['rodzajBudynku'], geometria, df['pos'], df['justyfikacja']):
            if isinstance(geom, list) and all(isinstance(point, tuple) for point in geom):
                geom = Polygon(geom)
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
                    y, x = point
                    y = -y

                    self.add_mark(x, y, 'green')

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
                    x, y = self.set_alignment(x, y, rect, alignment=str(justyfikacja))
                    text_item.setPos(x, y)

                    self.scene.addItem(text_item)
                    self.data.Budynek.append(text_item)

    def add_AdresNieruchomosci(self, df):
        self.remove_items(self.data.AdresNieruchomosci)

        katObrotu = df["katObrotu"].apply(pd.to_numeric, errors='coerce')

        for pos, nr, katObrotu, justyfikacja in zip(df['pos'], df['numerPorzadkowy'], katObrotu, df['justyfikacja']):
            if isinstance(pos, tuple) and len(pos) == 2:
                y, x = pos
                y = -y

                self.add_mark(x, y, 'green')

                text_item = DraggableTextItem(str(nr))
                font = QFont('Times New Roman')
                font.setPointSizeF(1.2)
                text_item.setFont(font)
                
                if not justyfikacja:
                    justyfikacja = 2

                rect = text_item.boundingRect()
                x, y = self.set_alignment(x, y, rect, alignment = str(justyfikacja))
                text_item.setPos(x, y)

                try:
                    bottom_center_x = (rect.left() + rect.right()) / 2
                    bottom_center_y = rect.bottom()
                    text_item.setTransformOriginPoint(bottom_center_x, bottom_center_y)
                    katObrotu = float(katObrotu)
                    katObrotu = math.degrees(katObrotu)
                    if math.isnan(katObrotu):
                        pass
                    else:
                        text_item.setRotation(-katObrotu)
                except Exception as e:
                    print(e)
                
                text_item.setBrush(QColor('black'))
                text_item.setZValue(1)

                self.scene.addItem(text_item)
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