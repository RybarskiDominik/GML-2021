from PySide6.QtWidgets import (QApplication, QGraphicsLineItem, QMainWindow,
                               QGraphicsItem, QFileDialog, QCheckBox, QTableWidget,
                               QGraphicsEllipseItem, QTableWidgetItem, QLineEdit,
                               QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
                               QGraphicsPolygonItem, QGraphicsTextItem, QSpacerItem,
                               QProgressBar, QSplashScreen, QSizePolicy, QPushButton,
                               QGraphicsPixmapItem, QMenu, QSplitter, QApplication,
                               QMainWindow, QWidget, QTextEdit, QPushButton, QGridLayout,
                               QSplitter, QFrame, QVBoxLayout, QHBoxLayout)
    
from PySide6.QtGui import (QFont, QPolygonF, QPolygonF, QPainter, QFont, QColor, QTransform,
                           QBrush, QPen, QIcon, QPainterPath, QPixmap, QPalette, QCursor,
                           QKeySequence, QShortcut)
from PySide6.QtCore import Signal, QSettings, Qt, QRectF, QThread, QByteArray
from PySide6 import QtCore, QtWidgets, QtGui
from dataclasses import dataclass
from os.path import exists
from pathlib import Path
import pandas as pd

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions  # as EC

import re
import time
import sys
import logging

from model.kw import kw_generator


logger = logging.getLogger(__name__)


class KW_Handler(QMainWindow):
    kw_signal = Signal(str)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KW Handler")
        self.setBaseSize(450, 430)
        self.setMinimumSize(450, 430)

        self.initUI() 

    def initUI(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.button_layout = QHBoxLayout(self.central_widget)

        self.kw_textedit = QtWidgets.QLineEdit(self)
        self.kw_textedit.setPlaceholderText("---------")
        self.kw_textedit.setFixedWidth(100)
        self.kw_textedit.setFixedHeight(28)
        self.kw_textedit.setAlignment(Qt.AlignCenter)

        self.kw_button = QPushButton('KW', self)
        self.kw_button.setFixedWidth(60)
        self.kw_button.setFixedHeight(30)
        self.kw_button.clicked.connect(self.process_kw)
        
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.kw_textedit)
        self.button_layout.addWidget(self.kw_button)
        self.button_layout.addStretch(1)
    

    def get_driver(self, main_browser="Chrome", img: bool = True):
        match main_browser:
            case "Chrome":  # Chrome
                try:
                    options = webdriver.ChromeOptions()
                    options.add_experimental_option("detach", True)

                    if img is not True:
                        prefs = {"profile.managed_default_content_settings.images": 2}
                        options.add_experimental_option("prefs", prefs)

                    options.add_argument("--disable-search-engine-choice-screen")

                    service = Service()
                    browser = webdriver.Chrome(service=service, options=options)

                    return browser
                except:
                    return self.get_driver(main_browser="Edge")
            case "Edge":  # Edge
                try:
                    options = webdriver.EdgeOptions()
                    options.add_experimental_option("detach", True)

                    if img is not True:
                        prefs = {"profile.managed_default_content_settings.images": 2}
                        options.add_experimental_option("prefs", prefs)

                    service = Service()
                    browser = webdriver.Edge(service=service, options=options)

                    return browser
                except:
                    return self.get_driver(main_browser="Chrome")
            case _:
                return None

    def process_kw(self, kw=False):
        try:
            if kw is False:
                kw = self.kw_textedit.text()

            kw = re.sub(r'[^\w\s/\\]', '', kw)
            
            kw = kw.split("/")
            print(kw)
            if len(kw) < 2 or kw[1] == "":
                return None
            
            if len(kw) != 3:
                kw = kw_generator(kw[0], str(kw[1]))

            result = self.open_kw_in_website(kw)
            if result is None:
                logging.error("ERROR KW")
                print("ERROR KW")
        
        except Exception as e:
            logging.exception(e)
            print(e)


    def search_kw(self, browser, kw):
        """browser.find_element(By.ID, 'kodWydzialuInput').send_keys(kw[0])  # Find the search box
        browser.find_element(By.NAME, 'numerKw').send_keys(kw[1])  # Find the search box
        browser.find_element(By.NAME, 'cyfraKontrolna').send_keys(kw[2])  # Find the search box
        browser.find_element(By.NAME, 'wyszukaj').send_keys(Keys.RETURN)  # Find the search box"""

        self.find_wait(browser, "#kodWydzialuInput").send_keys(kw[0])
        self.find_wait(browser, "#numerKsiegiWieczystej").send_keys(kw[1])
        self.find_wait(browser, "#cyfraKontrolna").send_keys(kw[2])
        self.find_wait(browser, "#wyszukaj").click()

    def find_wait(self, browser, value: str, by: By = By.CSS_SELECTOR, wait_seconds: int = 60):
        """Returns the element found by the given method and value after waiting for it to be present."""
        wdw = WebDriverWait(browser, wait_seconds)
        method = expected_conditions.presence_of_element_located
        return wdw.until(method((by, value)))

    def open_kw_in_website(self, kw):
        try:

            browser = self.get_driver()
            browser.get('https://przegladarka-ekw.ms.gov.pl/eukw_prz/KsiegiWieczyste/wyszukiwanieKW')

            time.sleep(1)
            
            WebDriverWait(browser, 10).until(expected_conditions.presence_of_element_located((By.ID, 'kodWydzialuInput')))

            elem = browser.find_element(By.ID, 'kodWydzialuInput')  # Find the search box
            elem.send_keys(kw[0])

            elem = browser.find_element(By.NAME, 'numerKw')  # Find the search box
            elem.send_keys(kw[1])

            elem = browser.find_element(By.NAME, 'cyfraKontrolna')  # Find the search box
            elem.send_keys(kw[2])

            elem = browser.find_element(By.NAME, 'wyszukaj')  # Find the search box
            elem.send_keys(Keys.RETURN)
            
            try:
                pass
                #elem = browser.find_element(By.NAME, 'przyciskWydrukZwykly')  # Find the search box
                #elem.send_keys(Keys.RETURN)
            except Exception as e:
                logging.exception(e)
                
            time.sleep(1)

        except Exception as e:
            logging.exception(e)
            print(e)

    def search_kw(self, kw):
        self.process_kw(kw)

if __name__ == '__main__':
    pass