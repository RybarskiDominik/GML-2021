from PySide6.QtWidgets import (QApplication, QGraphicsLineItem, QMainWindow,
                               QGraphicsItem, QFileDialog, QCheckBox, QTableWidget,
                               QGraphicsEllipseItem, QTableWidgetItem, QLineEdit,
                               QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
                               QGraphicsPolygonItem, QGraphicsTextItem, QSpacerItem,
                               QProgressBar, QSplashScreen, QSizePolicy, QPushButton,
                               QGraphicsPixmapItem, QMenu, QSplitter, QApplication,
                               QMainWindow, QWidget, QTextEdit, QPushButton, QGridLayout,
                               QSplitter, QFrame, QVBoxLayout, QHBoxLayout, QListWidget,
                               QListWidgetItem)
    
from PySide6.QtGui import (QFont, QPolygonF, QPolygonF, QPainter, QFont, QColor, QTransform,
                           QBrush, QPen, QIcon, QPainterPath, QPixmap, QPalette, QCursor,
                           QKeySequence, QShortcut, QIntValidator)
from PySide6.QtCore import Signal, QSettings, Qt, QRectF, QThread, QByteArray, QRect
from PySide6 import QtCore, QtWidgets, QtGui
from dataclasses import dataclass
from os.path import exists
from pathlib import Path
import pandas as pd
import unicodedata
import subprocess

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

from module.KW.kw_generator import kw_generator
from module.KW.Lista_kw import lista_items_kw
from module.KW.Lista_kw import city_names
from FileManager.FileManager import file_manager


logger = logging.getLogger(__name__)


class KW_Handler(QMainWindow):
    kw_signal = Signal(str)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KW Handler")
        self.setBaseSize(450, 430)
        self.setMinimumSize(350, 430)

        self.settings = QSettings('GML', 'GML Reader')

        self.initUI() 

    def initUI(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        font = QFont()
        font.setPointSize(18)
        int_validator = QIntValidator(0, 99999999)

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 5)

        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)
        top_layout.addStretch(1)

        # Layout siatki (WIERSZ 1 + WIERSZ 2) u góry
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        top_layout.addLayout(grid)   # <-- TERAZ jest na górze

        top_layout.addStretch(1)

        # --- DÓŁ: wyśrodkowane KW ---
        bottom_layout = QHBoxLayout()
        main_layout.addStretch(1)      # pusty obszar między górą a dołem
        main_layout.addLayout(bottom_layout)
        main_layout.addStretch(1)

        # --- WIERSZ 1 ---
        self.button_gen_kod = QtWidgets.QComboBox(self)
        self.button_gen_kod.addItem("kod sądu", None)
        self.button_gen_kod.setFixedWidth(75)
        for item_id, code in lista_items_kw:
            self.button_gen_kod.addItem(code, item_id)
        self.button_gen_kod.setToolTip("Tutaj można sprawdzić kod sądu.")
        self.button_gen_kod.currentIndexChanged.connect(self.update_tooltip)
        saved_kod_sadu = self.settings.value('KodSądu', None)
        if saved_kod_sadu is not None:
            index = self.button_gen_kod.findData(saved_kod_sadu)
            if index != -1:
                self.button_gen_kod.setCurrentIndex(index)

        self.label = QtWidgets.QLabel("/")
        self.label.setFont(font)
        #self.label.setFixedWidth(30)
        #self.label.setFixedHeight(22)

        self.button_gen_text_kw = QtWidgets.QLineEdit(self)
        self.button_gen_text_kw.setPlaceholderText("1-8")
        self.button_gen_text_kw.setFixedWidth(70)
        self.button_gen_text_kw.setMaxLength(8)
        self.button_gen_text_kw.setValidator(int_validator)
        self.button_gen_text_kw.setAlignment(Qt.AlignCenter)

        self.label_2 = QtWidgets.QLabel("/")
        self.label_2.setFont(font)
        #self.label.setFixedWidth(30)
        #self.label.setFixedHeight(22)

        self.liczba_kontrolna = QtWidgets.QLineEdit(self)
        self.liczba_kontrolna.setPlaceholderText("-")
        self.liczba_kontrolna.setFixedWidth(45)
        self.liczba_kontrolna.setMaxLength(1)
        self.liczba_kontrolna.setValidator(int_validator)
        self.liczba_kontrolna.setAlignment(Qt.AlignCenter)

        # --- WIERSZ 2 ---
        self.line_edit_szukaj = QtWidgets.QLineEdit(self)
        self.line_edit_szukaj.setPlaceholderText("Wyszukaj")
        self.line_edit_szukaj.setFixedWidth(75)
        self.line_edit_szukaj.setFixedHeight(26)
        self.line_edit_szukaj.setAlignment(Qt.AlignCenter)
        self.line_edit_szukaj.textChanged.connect(self.find_best_match)

        self.button_gen_generuj = QtWidgets.QPushButton("Generuj")
        self.button_gen_generuj.setFixedWidth(70)
        self.button_gen_generuj.setToolTip("Przycisk generuje KW.")
        self.button_gen_generuj.clicked.connect(self.generuj_kw)

        self.button_gen_copy = QtWidgets.QPushButton("Kopiuj")
        self.button_gen_copy.setToolTip("Przycisk kopiuje KW do schowka.")
        self.button_gen_copy.setFixedWidth(45)
        self.button_gen_copy.clicked.connect(self.kopiuj_kw)
        
        grid.addWidget(self.button_gen_kod, 0, 0)
        grid.addWidget(self.label, 0, 1)
        grid.addWidget(self.button_gen_text_kw, 0, 2)
        grid.addWidget(self.label_2, 0, 3)
        grid.addWidget(self.liczba_kontrolna, 0, 4)
        grid.addWidget(self.line_edit_szukaj, 1, 0)
        grid.addWidget(self.button_gen_generuj, 1, 2, 1, 1)
        grid.addWidget(self.button_gen_copy, 1, 4)

        # --- DÓŁ: wyśrodkowane KW ---
        #bottom_layout = QHBoxLayout()
        #center_layout.addLayout(bottom_layout)

        self.kw_textedit = QtWidgets.QLineEdit(self)
        self.kw_textedit.setPlaceholderText("----/--------/-")
        self.kw_textedit.setFixedWidth(100)
        self.kw_textedit.setFixedHeight(28)
        self.kw_textedit.setAlignment(Qt.AlignCenter)
        self.kw_textedit.returnPressed.connect(self.process_kw)

        self.kw_button = QPushButton('Szukaj KW.', self)
        self.kw_button.setFixedWidth(90)
        self.kw_button.setFixedHeight(30)
        self.kw_button.setIcon(QtGui.QIcon(file_manager.get_stylesheets_path("Chrome")))
        self.kw_button.setIconSize(QtCore.QSize(22, 22))
        self.kw_button.clicked.connect(self.process_kw)
        self.kw_button.setToolTip("Otwiera stronę eKW i wyszukuje podany numer KW.")

        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.kw_textedit)
        bottom_layout.addWidget(self.kw_button)
        bottom_layout.addStretch(1)


        # --- IMPORT LISTY KW ---
        self.button_import_kw = QPushButton("Importuj listę KW", self)
        self.button_import_kw.setFixedWidth(130)
        self.button_import_kw.clicked.connect(self.import_kw_list)
        self.button_import_kw.setToolTip("Import numerów KW do listy z pliku tekstowego.")

        import_layout = QHBoxLayout()
        main_layout.addLayout(import_layout)
        import_layout.addStretch(1)
        import_layout.addWidget(self.button_import_kw)
        import_layout.addStretch(1)

        # Lista wyświetlająca zaimportowane KW
        self.list_widget_kw = QListWidget(self)
        self.list_widget_kw.setFixedWidth(200)
        self.list_widget_kw.setMinimumHeight(220)
        #self.list_widget_kw.setMaximumHeight(160)
        self.list_widget_kw.itemClicked.connect(self.fill_kw_from_list)
        self.list_widget_kw.itemActivated.connect(self.run_kw_from_list)
        self.list_widget_kw.setToolTip(
            "Lista zaimportowanych numerów KW:\n"
            "- Pojedyncze kliknięcie: wczytuje numer do pola KW\n"
            "- Podwójne kliknięcie: otwiera numer w eKW\n"
            "- Naciśnięcie Enter: otwiera numer w eKW"
        )

        list_layout = QHBoxLayout()
        main_layout.addLayout(list_layout)
        list_layout.addStretch(1)
        list_layout.addWidget(self.list_widget_kw)
        list_layout.addStretch(1)


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
            for i in range(len(kw)):
                print(kw[i])

            if len(kw) < 2 or kw[1] == "":
                return None
            
            if len(kw) != 3 or kw[2] == "":
                kw = kw_generator(kw[0], str(kw[1]))

            self.open_kw_in_website(kw)

        except Exception as e:
            logging.exception(e)
            print(e)


    def kopiuj_kw(self):
        def setClipboardData(txt):
            cmd='echo '+txt.strip()+'|clip'
            return subprocess.check_call(cmd, shell=True)
        
        góra = self.button_gen_text_kw.text()
        if not góra:
            #self.info.setText("Brak numeru KW.")
            return
        
        current_index = self.button_gen_kod.currentIndex()
        key_id = self.button_gen_kod.itemData(current_index)
        key = self.button_gen_kod.currentText()
        if key_id is None:
            #self.info.setText("Brak kodu.")
            return

        i = kw_generator(key, góra)
        kw = f"{i[0]}/{i[1]}/{i[2]}"
        setClipboardData(kw)

    def generuj_kw(self):
        góra = self.button_gen_text_kw.text()
        if not góra:
            #self.info.setText("Brak numeru KW.")
            return
        
        current_index = self.button_gen_kod.currentIndex()
        key_id = self.button_gen_kod.itemData(current_index)
        key = self.button_gen_kod.currentText()
        if key_id is None:
            #self.info.setText("Brak kodu.")
            return

        k1 = kw_generator(key, góra)
        self.liczba_kontrolna.setText(k1[2])

    def update_tooltip(self):
        current_index = self.button_gen_kod.currentIndex()
        id = self.button_gen_kod.itemData(current_index)
        for item_id, city_name in city_names:
            if id is None:
                self.button_gen_kod.setToolTip("Tutaj można sprawdzić kod sądu.")
                self.setWindowTitle('eKW')
            elif id in item_id:
                self.button_gen_kod.setToolTip(city_name)
                self.setWindowTitle(f"eKW {city_name}")
                self.settings.setValue("KodSądu", id)

    def normalize_text(self, text):
        # Normalize Unicode text and convert to lowercase
        normalized_text = unicodedata.normalize('NFKD', text)
        return normalized_text.encode('ASCII', 'ignore').decode('ASCII').lower()

    def find_best_match(self, text):
        best_match_id = None

        for item_id, city_name in city_names:
            city_name = self.normalize_text(city_name)
            if self.normalize_text(text) in self.normalize_text(city_name):  # if text.lower() in city_name.lower():
                best_match_id = item_id
                break

        # If a match is found, set the QComboBox to the corresponding item
        if best_match_id:
            index = self.button_gen_kod.findData(best_match_id)
            if index != -1:
                self.button_gen_kod.setCurrentIndex(index)


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


    def import_kw_list(self):
        try:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Wybierz plik listy KW",
                "",
                "Pliki tekstowe (*.txt)"
            )
            if not path:
                return

            with open(path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()

            self.kw_list = []
            self.list_widget_kw.clear()

            for line in lines:
                kw = line.strip()
                if not kw:
                    continue

                # usuń spacje i dziwne znaki
                kw = re.sub(r'[^\w/]', '', kw)

                # dodaj do listy
                self.kw_list.append(kw)

                # dodaj do widoku
                item = QListWidgetItem(kw)
                item.setData(Qt.UserRole, kw)
                self.list_widget_kw.addItem(item)

        except Exception as e:
            logging.exception(e)
            print("Błąd importu:", e)

    def fill_kw_from_list(self, item):
        kw = item.data(Qt.UserRole)
        self.kw_textedit.setText(kw)

    def run_kw_from_list(self, item):
        kw = item.data(Qt.UserRole)
        self.kw_textedit.setText(kw)

        self.process_kw()

        self.mark_selected_item_done()


    def mark_selected_item_done(self):
        item = self.list_widget_kw.currentItem()
        if item is None:
            return
        
        icon_path = file_manager.get_stylesheets_path("OK")
        item.setIcon(QIcon(icon_path))


if __name__ == '__main__':
    pass