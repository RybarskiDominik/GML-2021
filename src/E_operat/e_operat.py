from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QSplitter, QFrame, QStackedWidget,
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsPolygonItem,
    QGraphicsTextItem, QGraphicsPixmapItem,
    QFileDialog, QCheckBox, QTableWidget, QTableWidgetItem,
    QLineEdit, QTextEdit, QPushButton, QLabel, QProgressBar,
    QSplashScreen, QSpacerItem, QSizePolicy, QMenu, QHeaderView,
    QTableWidgetItem, QMessageBox
)

from PySide6.QtGui import (
    QAction, QFont, QPolygonF, QPainter, QColor, QTransform,
    QBrush, QPen, QIcon, QPainterPath, QPixmap, QPalette, QCursor,
    QKeySequence, QShortcut, QDesktopServices
)

from PySide6.QtCore import (
    Signal, QSettings, Qt, QRectF, QThread, QByteArray, QUrl
)

from dataclasses import dataclass
from os.path import exists
from pathlib import Path
import pandas as pd
import webbrowser
import logging
import random
import shutil
import stat
import time
import sys
import os


from E_operat.project_manager.project_manager import Database, ProjectEditor, DB_FILE, GML_FILE
from E_operat.pdf_manager.pdf_manager import PDF

from FileManager.workspace_settings_window import WorkspaceSettingsWindow
from FileManager.FileManager import file_manager
#file_manager = FileManager()


logger = logging.getLogger(__name__)


class e_operat(QMainWindow):
    gml_path_selected = Signal(str)
    def __init__(self, parents):
        super(e_operat, self).__init__()
        self.setWindowTitle("E-Operat")
        DB_FILE_PATH = str(file_manager.database_folder_path / DB_FILE)
        logging.debug(DB_FILE_PATH)
        self.db = Database(DB_FILE_PATH)
        self.settings = QSettings('GML', 'E-Operat')
        self.setMinimumSize(1000, 400)
        self.setAcceptDrops(True)
        self.setWindowState(Qt.WindowMaximized)

        shortcut = QShortcut(QKeySequence(Qt.CTRL | Qt.Key_C), self)
        shortcut.activated.connect(self.copy_to_clipboard)

        self.init_ui()
        self.init_frames()

        self.restore_splitter_state()

        self.init_MainButton()
        self.load_data()

    def init_ui(self):  # Init function frame.
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

        # === Sub-widgets ===
        # Table Widget
        self.table_widget = QWidget(self)
        self.table_layout = QVBoxLayout(self.table_widget)
        self.table_layout.setContentsMargins(0, 0, 0, 0)

        # Map Widget
        self.map_widget = QWidget(self)
        self.map_layout = QGridLayout(self.map_widget)
        self.map_layout.setContentsMargins(0, 0, 0, 0)
        self.map_layout.setSpacing(0)

        # Function Widget
        self.function_widget = QWidget(self)
        self.function_layout = QVBoxLayout(self.function_widget)
        self.function_layout.setContentsMargins(0, 0, 0, 0)
        self.function_layout.setSpacing(0)

        # === Splitters ===
        # Horizontal Splitter (Function + Map)
        self.horizontal_splitter = QSplitter(Qt.Horizontal)
        self.horizontal_splitter.setHandleWidth(5)
        self.horizontal_splitter.splitterMoved.connect(self.onSplitterMoved)
        self.horizontal_splitter.addWidget(self.function_widget)
        self.horizontal_splitter.addWidget(self.map_widget)

        # Vertical Splitter (Table on top, Horizontal Splitter below)
        self.vertical_splitter = QSplitter(Qt.Vertical)
        self.vertical_splitter.setHandleWidth(5)
        self.vertical_splitter.splitterMoved.connect(self.onSplitterMoved)
        self.vertical_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #9b59b6;
            }
        """)
        self.vertical_splitter.addWidget(self.table_widget)
        self.vertical_splitter.addWidget(self.horizontal_splitter)

        # === View Containers ===
        # Main splitter view wrapped in a QWidget (for layouting)
        self.main_splitter_view = QWidget()
        self.main_splitter_layout = QVBoxLayout(self.main_splitter_view)
        self.main_splitter_layout.setContentsMargins(0, 0, 0, 0)
        self.main_splitter_layout.setSpacing(0)
        self.main_splitter_layout.addWidget(self.vertical_splitter)

        # Second dummy view for switching (placeholder)
        self.alt_view = QWidget()
        self.alt_layout = QVBoxLayout(self.alt_view)
        self.alt_layout.setContentsMargins(0, 0, 0, 0)
        self.alt_layout.setSpacing(0)

        # === QStackedWidget ===
        self.central_stack = QStackedWidget(self.central_widget)
        self.central_stack.addWidget(self.main_splitter_view)  # index 0
        self.central_stack.addWidget(self.alt_view)            # index 1

        # Add stack to layout
        self.main_layout.addWidget(self.central_stack, 1, 0, 1, 1)

        # Layout settings
        #self.button_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        #self.main_layout.setRowStretch(0, 0)
        #self.main_layout.setRowStretch(1, 1)

    def toggle_view(self):  # Method for switching views
        current_index = self.central_stack.currentIndex()
        new_index = 1 if current_index == 0 else 0
        self.central_stack.setCurrentIndex(new_index)


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

        self.pdf_manager = PDF()
        self.function_win_layout.addWidget(self.pdf_manager)

        # Add Frames to Layouts
        self.button_layout.addWidget(self.button_frame)
        self.table_layout.addWidget(self.table_frame)
        self.function_layout.addWidget(self.button_function_frame)
        self.function_layout.addWidget(self.function_frame)

    def onSplitterMoved(self, pos, index):
        pass

    def closeEvent(self, event):    # Zdarzenie zamknięcia okna
        self.save_splitter_state()  # Zapisz stan splitera przed zamknięciem aplikacji
        super().closeEvent(event)

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


    # -------------------- MAIN WINDOW --------------------
    def init_MainButton(self):
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nazwa projektu", "Identyfikator", "Status", "Cel pracy", "Zleceniodawca",
            "Adres zleceniodawcy", "Telefon", "E-mail", "Wykonawca", "Opis", "Termin rozpoczęcia",
            "Termin zakończenia", "Path project", "Path GML"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionsMovable(True)

        self.table.setSortingEnabled(True)
        self.table.cellClicked.connect(self.on_cell_click)
        self.table.cellDoubleClicked.connect(self.on_cell_double_click)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)


        # przyciski
        self.gml_btn = QPushButton("GML")
        self.gml_btn.setFixedWidth(35)
        self.gml_btn.clicked.connect(self.send_gml)
        self.gml_btn.setToolTip("Wyślij gml i ustaw tagi")

        self.btn_add = QPushButton("Dodaj pracę")
        self.btn_add.clicked.connect(self.add_job)

        self.btn_delete = QPushButton("Usuń pracę")
        self.btn_delete.clicked.connect(self.delete_job)

        self.project_btn = QPushButton("Projekt")
        self.project_btn.setFixedWidth(55)
        self.project_btn.setToolTip("Otwórz folder z projektami.")
        self.project_btn.clicked.connect(self.open_project)

        self.settings_btn = QPushButton("Setting")
        self.settings_btn.setFixedWidth(55)
        self.settings_btn.setToolTip("Zmiana ustawień menagera projektów.")
        self.settings_btn.clicked.connect(self.change_settings)

        """
        self.project_import = QPushButton("Import")
        self.project_import.setFixedWidth(55)
        self.project_import.clicked.connect(self.import_project)

        self.project_export = QPushButton("Export")
        self.project_export.setFixedWidth(55)
        self.project_export.clicked.connect(self.export_project)
        """

        self.button_frame_layout.addWidget(self.gml_btn)
        self.button_frame_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addWidget(self.btn_add)
        self.button_frame_layout.addSpacerItem(QSpacerItem(2, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addWidget(self.btn_delete)
        self.button_frame_layout.addSpacerItem(QSpacerItem(25, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addWidget(self.project_btn)
        self.button_frame_layout.addStretch(1)
        self.button_frame_layout.addWidget(self.settings_btn)
        self.button_frame_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        
        """
        self.button_frame_layout.addSpacerItem(QSpacerItem(25, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addWidget(self.project_import)
        self.button_frame_layout.addSpacerItem(QSpacerItem(2, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.button_frame_layout.addWidget(self.project_export)
        """

        #self.button_frame_layout.addStretch(1)

        self.table_frame_layout.addWidget(self.table)

    # -------------------- Event handlers --------------------
    def on_cell_click(self, row, col):
        id_item = self.table.item(row, 0)
        if not id_item:
            return

        project = self.db.get_project_details(id_item.text())
        if not project:
            return
        
        print("Path to project: ", project["Path project"])

        full_path = project["Path project"]
        Path(full_path).mkdir(parents=True, exist_ok=True)

        self.pdf_manager.add_folder(full_path)

        project_name = project.get("Nazwa projektu", "")
        if project_name:
            self.setWindowTitle(f"E-Operat – {project_name}")

        """
        id_item = self.table.item(row, 0)
        if id_item:
            paths = self.db.get_project_details(id_item.text())
            full_path = os.path.join(paths["Path project"], paths["Nazwa projektu"])
            #print("Project name: ", paths["Nazwa projektu"])
            #print("Path to project: ", paths["Path project"])
            #print("GML status: ", paths["GML Status"])

            Path(full_path).mkdir(parents=True, exist_ok=True)
            
            self.pdf_manager.add_folder(full_path)
        """
            

    def on_cell_double_click(self, row, col):
        job_id = int(self.table.item(row, 0).text())
        job = next((j for j in self.db.get_projects() if j["ID"] == job_id), None)
        if job:
            self.editor = ProjectEditor(db=self.db, job=job, callback=self.load_data)
            self.editor.show()


    # -------------------- Load data into table --------------------
    def load_data(self):
        self.table.setRowCount(0)
        projects = self.db.get_projects()
        self.table.setRowCount(len(projects))

        for row_idx, proj in enumerate(projects):
            values = [
                str(proj.get("ID", "")),
                proj.get("Nazwa projektu", ""),
                proj.get("Identyfikator", ""),
                proj.get("Status", ""),
                proj.get("Cel pracy", ""),
                proj.get("Zleceniodawca", ""),
                proj.get("Adres zleceniodawcy", ""),
                proj.get("Telefon", ""),
                proj.get("E-mail", ""),
                proj.get("Wykonawca", ""),
                proj.get("Opis", ""),
                proj.get("Termin rozpoczęcia", ""),
                proj.get("Termin zakończenia", ""),
                proj.get("Path project", "")
            ]

            # sprawdzenie GML
            gml_path = proj.get("GML Status", "")
            if gml_path:
                gml_status = "Plik *.gml zaimportowany poprawnie!"
            else:
                gml_status = "Brak pliku GML"

            values.append(gml_status)

            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.table.setItem(row_idx, col, item)

            self.table.setColumnHidden(0, True)

    # -------------------- Add / Delete job --------------------
    def send_gml(self):
        row = self.table.currentRow()
        if row >= 0:
            project_id = int(self.table.item(row, 0).text())
            paths = self.db.get_project_details(project_id)
            if not paths:
                print("Brak ścieżek dla projektu.")
                return

            # Ścieżka do pliku GML
            full_path = Path(paths["Path project"]) / GML_FILE
            gml_status = paths["GML Status"]

            if gml_status in (1, "1", True, "Plik *.gml zaimportowany poprawnie!"):
                self.gml_path_selected.emit(str(full_path))
                print("GML emit to MyWindow:", full_path)
            else:
                print("Brak pliku GML.")

            # Załaduj tagi projektu
            self.db.get_project_tags(project_id)
    
    def open_project(self):
        row = self.table.currentRow()
        if row >= 0:
            project_id = int(self.table.item(row, 0).text())
            paths = self.db.get_project_details(project_id)
            if not paths or not paths.get("Path project"):
                print("Brak ścieżki do projektu.")
                return

            # paths["Path project"] już zawiera pełną ścieżkę do folderu projektu
            project_path = Path(paths["Path project"])
            if not project_path.exists():
                project_path.mkdir(parents=True, exist_ok=True)

            QDesktopServices.openUrl(QUrl.fromLocalFile(str(project_path)))
        else:
            # Brak zaznaczonego wiersza → otwórz folder domyślny
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_manager.projects_folder_path)))

    def change_settings(self):
        if not hasattr(self, 'settings_window') or self.settings_window is None:
            self.settings_window = WorkspaceSettingsWindow(file_manager, parent=self)
            self.settings_window.settings_win_closed.connect(self.refresh_after_settings)
            self.settings_window.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def refresh_after_settings(self):
        """
        Wywoływane po zamknięciu okna ustawień.
        Odświeża bazę danych i tabelę.
        """
        print("Okno ustawień zamknięte. Odświeżanie danych...")
        DB_FILE_PATH = str(file_manager.database_folder_path / DB_FILE)
        self.db = Database(DB_FILE_PATH)
        print("Nowa ścieżka do bazy danych:", DB_FILE_PATH)
        self.load_data()


    def export_project(self):
        self.db.export_projects

    def import_project(self):
        self.db.import_projects


    def add_job(self):
        self.editor = ProjectEditor(db=self.db, callback=self.load_data)
        self.editor.show()

    def delete_job(self):
        selected_rows = set(idx.row() for idx in self.table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Błąd", "Nie wybrano żadnej pracy do usunięcia!")
            return

        confirm = QMessageBox.question(
            self, "Potwierdzenie", "Czy na pewno chcesz usunąć wybrane prace?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        for row in selected_rows:
            job_id = int(self.table.item(row, 0).text())
            
            # Pobieramy ścieżkę folderu projektu i nazwę projektu
            paths = self.db.get_project_details(job_id)
            if not paths or not paths.get("Path project"):
                print("Brak ścieżki do projektu.")
                return

            # paths["Path project"] już zawiera pełną ścieżkę do folderu projektu
            project_path = Path(paths["Path project"])

            # Pytamy użytkownika, czy usunąć konkretny folder
            confirm_folder = QMessageBox.question(
                self, "Potwierdzenie",
                f"Czy na pewno chcesz usunąć folder projektu:\n{project_path}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm_folder != QMessageBox.Yes:
                continue  # jeśli użytkownik nie zgadza się, pomijamy ten wiersz

            # Usuwamy folder tylko jeśli istnieje
            if os.path.exists(project_path):
                try:
                    shutil.rmtree(project_path)  # próbujemy usunąć folder
                except Exception as e:
                    logging.exception(e)
                    print(e)
                    try:
                        self.safe_rmtree(project_path)
                    except Exception as e:
                        logging.exception(e)
                        QMessageBox.warning(self, "Błąd", f"Nie udało się usunąć folderu: {e}")
                        print(e)
                        continue  # jeśli wystąpił błąd, przechodzimy do następnego wiersza, nic nie usuwamy

            # Sprawdzamy, czy folder został faktycznie usunięty
            if os.path.exists(project_path):
                QMessageBox.warning(self, "Błąd", f"Folder {project_path} nie został usunięty!")
                continue  # jeśli folder nadal istnieje, nie usuwamy danych z bazy

            # Usuwamy wpis z bazy danych tylko jeśli folder został usunięty
            self.db.delete_project(job_id)

        # Odświeżamy tabelę
        self.load_data()

    def remove_readonly(self, func, path, _):
        """Usuwa atrybut tylko do odczytu i ponawia próbę usunięcia."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def safe_rmtree(self, path: Path):
        if path.exists():
            try:
                shutil.rmtree(path, onexc=self.remove_readonly)
            except PermissionError as e:
                QMessageBox.warning(None, "Błąd", f"Odmowa dostępu: {path}\n{e}")
            except Exception as e:
                QMessageBox.warning(None, "Błąd", f"Nie udało się usunąć folderu: {path}\n{e}")


    # -------------------- Context menu for marking as finished --------------------
    def show_context_menu(self, position):
        indexes = self.table.selectedIndexes()
        if indexes:
            # Pobieramy ID projektu z pierwszej kolumny (załóżmy, że tam jest ID)
            row = indexes[0].row()
            project_id = int(self.table.item(row, 0).text())

            menu = QMenu()
            finish_action = menu.addAction("Oznacz jako zakończony")
            action = menu.exec(self.table.viewport().mapToGlobal(position))

            if action == finish_action:
                self.db.update_status(project_id, "Zakończony")
                self.load_data()


    def context_menu(self, pos):
        context_menu = QMenu(self)
        copy_action = context_menu.addAction("Kopiuj")
        copy_action.triggered.connect(self.copy_to_clipboard)

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    DB_FILE_PATH = str(file_manager.default_workspace_root_dir / DB_FILE)

    main_window = e_operat(DB_FILE_PATH)
    main_window.show()
    sys.exit(app.exec())