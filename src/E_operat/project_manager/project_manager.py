from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QGridLayout, QLineEdit, QTextEdit, QLabel, QPushButton,
    QComboBox, QDateEdit, QMessageBox, QFileDialog, QMenu, QSpacerItem,
    QSizePolicy, QTableWidget, QTableWidgetItem, QAbstractItemView, QTabWidget,
    QProxyStyle
)
from PySide6.QtCore import Qt, QDate, Signal, QObject
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtGui import QAction

from pathlib import Path
from datetime import datetime
import logging
import sqlite3
import shutil
import uuid
import json
import sys
import re
import os

from odfdo import Document, Paragraph

import re


from FileManager.FileManager import file_manager
#file_manager = FileManager()

logger = logging.getLogger(__name__)

DB_FILE = "DATABASE.db"
GML_FILE = "PZGIK.gml"
GML_STATUS = "Plik *.gml zaimportowany poprawnie!"


class Database(QObject): #  DATABASE
    tags_changed = Signal(dict)
    def __init__(self, db_file=DB_FILE):
        super().__init__()
        self.db_file = db_file

        #db_dir = os.path.dirname(self.db_file)
        #if not os.path.exists(db_dir):
            #os.makedirs(db_dir, exist_ok=True)
            #print(f"Utworzono katalog: {db_dir}")

        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self.create_table()
        self.repair_schema()

    def _validate_path(self, path: Path) -> Path:
        if not path or not isinstance(path, str):
            return False

        db_path = Path(path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        return Path(db_path)

    def backup_db(self):
        backup_file = f"{self.db_file}.bak"
        shutil.copy(self.db_file, backup_file)
        print(f"Backup created: {backup_file}")

    def create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            "ID" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Nazwa projektu" TEXT,
            "Identyfikator" TEXT,
            "Status" TEXT DEFAULT 'W trakcie',
            "Cel pracy" TEXT,
            "Zleceniodawca" TEXT,
            "Adres zleceniodawcy" TEXT,
            "Telefon" TEXT,
            "E-mail" TEXT,
            "Wykonawca" TEXT,
            "Opis" TEXT,
            "Termin rozpoczęcia" TEXT,
            "Termin zakończenia" TEXT,
            "Relative Path" INTEGER DEFAULT 1,
            "Path project" TEXT,
            "GML Status" TEXT,
            "Data" JSON,
            "Deleted" INTEGER DEFAULT 0
        )
        """)
        self.conn.commit()


    def add_project(self, project_data, relative_Path, path_project, gml_status):
        #if not project_data.get("project_name") or not project_data.get("project_identifier"):
            #print("Error: missing project name or identifier")
            #return
        try:
            #self.backup_db()
            self.cursor.execute("""
                INSERT INTO projects (
                    "Nazwa projektu", "Identyfikator", "Status", "Cel pracy", "Zleceniodawca",
                    "Adres zleceniodawcy", "Telefon", "E-mail", "Wykonawca", "Opis",
                    "Termin rozpoczęcia", "Termin zakończenia", "Relative Path", "Path project", "GML Status", "Data"
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_data.get("Nazwa projektu"),
                project_data.get("Identyfikator"),
                project_data.get("Status", "W trakcie"),
                project_data.get("Cel pracy"),
                project_data.get("Zleceniodawca"),
                project_data.get("Adres zleceniodawcy"),
                project_data.get("Telefon"),
                project_data.get("E-mail"),
                project_data.get("Wykonawca"),
                project_data.get("Opis"),
                project_data.get("Termin rozpoczęcia"),
                project_data.get("Termin zakończenia"),
                relative_Path,
                path_project,
                gml_status,
                json.dumps(project_data)
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.exception(e)
            print(f"Error adding project: {e}")

    def update_project(self, project_id, relative_Path, project_data, path_project, gml_status):
        try:
            self.cursor.execute("""
                UPDATE projects
                SET "Nazwa projektu"=?, "Identyfikator"=?, "Status"=?, "Cel pracy"=?, "Zleceniodawca"=?,
                    "Adres zleceniodawcy"=?, "Telefon"=?, "E-mail"=?, "Wykonawca"=?, "Opis"=?,
                    "Termin rozpoczęcia"=?, "Termin zakończenia"=?, "Relative Path"=?, "Path project"=?, "GML Status"=?, "Data"=?
                WHERE "ID"=?
            """, (
                project_data.get("Nazwa projektu"),
                project_data.get("Identyfikator"),
                project_data.get("Status", "W trakcie"),
                project_data.get("Cel pracy"),
                project_data.get("Zleceniodawca"),
                project_data.get("Adres zleceniodawcy"),
                project_data.get("Telefon"),
                project_data.get("E-mail"),
                project_data.get("Wykonawca"),
                project_data.get("Opis"),
                project_data.get("Termin rozpoczęcia"),
                project_data.get("Termin zakończenia"),
                relative_Path,
                path_project,
                gml_status,
                json.dumps(project_data),
                project_id
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.exception(e)
            print(f"Error updating project: {e}")

    def delete_project(self, project_id):
        """Usuwa projekt o podanym ID i tworzy backup bazy."""
        try:
            self.backup_db()
            self.cursor.execute('DELETE FROM projects WHERE "ID"=?', (project_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.exception(e)
            print(f"Error deleting project: {e}")


    def export_projects(self, export_file="projects_export.json"):  # Eksport 
        self.cursor.execute("SELECT * FROM projects WHERE Deleted = 0")
        columns = [desc[0] for desc in self.cursor.description]
        data = [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Exported {len(data)} projects to {export_file}")

    def import_projects(self, import_file="projects_export.json"):  # Import
        with open(import_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for project in data:
            placeholders = ", ".join("?" * len(project))
            columns = ", ".join(project.keys())
            values = tuple(project.values())
            self.cursor.execute(
                f"INSERT OR REPLACE INTO projects ({columns}) VALUES ({placeholders})",
                values,
            )
        self.conn.commit()
        print(f"Imported {len(data)} projects from {import_file}")


    def get_projects(self):
        try:
            self.cursor.execute("""
                SELECT "ID", "Nazwa projektu", "Identyfikator", "Status", "Cel pracy", "Zleceniodawca",
                    "Adres zleceniodawcy", "Telefon", "E-mail", "Wykonawca", "Opis", "Termin rozpoczęcia",
                    "Termin zakończenia", "Relative Path", "Path project", "GML Status", "Data"
                FROM projects
            """)
            rows = self.cursor.fetchall()
            projects = []
            for r in rows:
                try:
                    data = json.loads(r[16]) if r[16] else {}
                except (json.JSONDecodeError, TypeError):
                    data = {}  # jeśli brak lub błędny JSON → pusty dict

                projects.append({
                    "ID": r[0],
                    "Nazwa projektu": r[1],
                    "Identyfikator": r[2],
                    "Status": r[3],
                    "Cel pracy": r[4],
                    "Zleceniodawca": r[5],
                    "Adres zleceniodawcy": r[6],
                    "Telefon": r[7],
                    "E-mail": r[8],
                    "Wykonawca": r[9],
                    "Opis": r[10],
                    "Termin rozpoczęcia": r[11],
                    "Termin zakończenia": r[12],
                    "Relative Path": r[13],
                    "Path project": r[14],
                    "GML Status": r[15],
                    "Data": data
                })
            return projects
        except sqlite3.Error as e:
            print(f"Error reading projects: {e}")
            return []

    def get_project(self, project_id):
        self.cursor.execute("""
            SELECT "ID", "Nazwa projektu", "Identyfikator", "Status", "Cel pracy", "Zleceniodawca",
                    "Adres zleceniodawcy", "Telefon", "E-mail", "Wykonawca", "Opis", "Termin rozpoczęcia",
                   "Termin zakończenia", "Relative Path", "Path project", "GML Status", "Data"
            FROM projects
            WHERE "ID"=?
        """, (project_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                "ID": row[0],
                "Nazwa projektu": row[1],
                "Identyfikator": row[2],
                "Status": row[3],
                "Cel pracy": row[4],
                "Zleceniodawca": row[5],
                "Adres zleceniodawcy": row[6],
                "Telefon": row[7],
                "E-mail": row[8],
                "Wykonawca": row[9],
                "Opis": row[10],
                "Termin rozpoczęcia": row[11],
                "Termin zakończenia": row[12],
                "Relative Path": row[13],
                "Path project": row[14],
                "GML Status": row[15],
                "Data": json.loads(row[16])
            }
        return None

    def update_status(self, project_id, new_status):
        try:
            self.cursor.execute('UPDATE projects SET "Status"=? WHERE "ID"=?', (new_status, project_id))
            
            #self.backup_db()
            #self.cursor.execute('UPDATE projects SET status=? WHERE id=? AND deleted=0', (new_status, project_id))

            self.conn.commit()
        
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.exception(e)
            print(f"Error adding project: {e}")
        
    def get_project_tags(self, project_id):
        
        project = self.get_project(project_id)
        if not project:
            tags = {}
        else:
            tags = project.get("Data", {}) or {}

        self.tags_changed.emit(tags)
        return tags
    
        """
        project = self.get_project(project_id)
        if not project:
            return []

        tags = []

        data = project["Data"]
        for key, value in data.items():
            tags.append(f"{key}: {value}")
        return tags"""

    def get_project_details(self, project_id):
        self.cursor.execute("""
            SELECT "Nazwa projektu", "Relative Path", "Path project", "GML Status"
            FROM projects
            WHERE "ID"=?
        """, (project_id,))
        row = self.cursor.fetchone()

        if not row:
            return None

        project_name = row[0]
        relative_flag = row[1]
        path_project = row[2]
        gml_status = row[3]

        # 🔧 Automatyczne ustalenie właściwej ścieżki
        if relative_flag == 1:
            full_path = file_manager.projects_folder_path / project_name
        else:
            full_path = Path(path_project) / project_name

        return {
            "Nazwa projektu": project_name,
            "Relative Path": relative_flag,
            "Path project": str(full_path),
            "GML Status": gml_status
        }

    def get_paths_old(self, project_id):
        self.cursor.execute("""
            SELECT "Nazwa projektu", "Relative Path", "Path project", "GML Status"
            FROM projects
            WHERE "ID"=?
        """, (project_id,))
        row = self.cursor.fetchone()
        if row:
            return {
                "Nazwa projektu": row[0],
                "Relative Path": row[1],
                "Path project": row[2],
                "GML Status": row[3]
            }
        return None

    def repair_schema(self):
        """
        Sprawdza kolumny w tabeli projects i dodaje brakujące.
        Dzięki temu można zmieniać strukturę w kodzie, a baza się dostosuje.
        """
        # definicja docelowej struktury tabeli
        expected_columns = {
            "ID": 'INTEGER PRIMARY KEY AUTOINCREMENT',
            "Nazwa projektu": 'TEXT',
            "Identyfikator": 'TEXT',
            "Status": "TEXT DEFAULT 'W trakcie'",
            "Cel pracy": "TEXT",
            "Zleceniodawca": "TEXT",
            "Adres zleceniodawcy": "TEXT",
            "Telefon": "TEXT",
            "E-mail": "TEXT",
            "Wykonawca": "TEXT",
            "Opis": "TEXT",
            "Termin rozpoczęcia": "TEXT",
            "Termin zakończenia": "TEXT",
            "Relative Path": "INTEGER DEFAULT 1",
            "Path project": "TEXT",
            "GML Status": "TEXT",
            "Data": "JSON",
            "Deleted": "INTEGER DEFAULT 0"
        }

        # pobranie istniejących kolumn
        self.cursor.execute("PRAGMA table_info(projects)")
        existing_columns = {row[1] for row in self.cursor.fetchall()}  # row[1] = nazwa kolumny

        # dodaj brakujące kolumny
        for col, col_type in expected_columns.items():
            if col not in existing_columns:
                try:
                    self.cursor.execute(f'ALTER TABLE projects ADD COLUMN "{col}" {col_type}')
                    print(f"[repair_schema] Dodano brakującą kolumnę: {col}")
                except sqlite3.Error as e:
                    print(f"[repair_schema] Błąd przy dodawaniu kolumny {col}: {e}")

        self.conn.commit()

    def close(self):
        self.conn.close()


    def get_projectsv2(self):
        self.cursor.execute("SELECT * FROM projects")
        rows = self.cursor.fetchall()
        return [dict(r) for r in rows]

    def get_projectv2(self, project_id):
        self.cursor.execute("SELECT * FROM projects WHERE ID=?", (project_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None


    def add_project_old(self, project_data, path_project, gml_status):
        #if not project_data.get("project_name") or not project_data.get("project_identifier"):
            #print("Error: missing project name or identifier")
            #return
        try:
            self.backup_db()
            self.cursor.execute("""
                INSERT INTO projects (
                    "Nazwa projektu", "Identyfikator", "Status", "Cel pracy", "Zleceniodawca",
                    "Adres zleceniodawcy", "Telefon", "E-mail", "Wykonawca", "Opis",
                    "Termin rozpoczęcia", "Termin zakończenia", "Path project", "GML Status", "Data"
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_data.get("Nazwa projektu"),
                project_data.get("Identyfikator"),
                project_data.get("Status", "W trakcie"),
                project_data.get("Cel pracy"),
                project_data.get("Zleceniodawca"),
                project_data.get("Adres zleceniodawcy"),
                project_data.get("Telefon"),
                project_data.get("E-mail"),
                project_data.get("Wykonawca"),
                project_data.get("Opis"),
                project_data.get("Termin rozpoczęcia"),
                project_data.get("Termin zakończenia"),
                path_project,
                gml_status,
                json.dumps(project_data)
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.exception(e)
            print(f"Error adding project: {e}")

    def update_project_old(self, project_id, project_data, path_project, gml_status):
        try:
            #self.backup_db()
            self.cursor.execute("""
                UPDATE projects
                SET "Nazwa projektu"=?, "Identyfikator"=?, "Status"=?, "Cel pracy"=?, "Zleceniodawca"=?,
                    "Adres zleceniodawcy"=?, "Telefon"=?, "E-mail"=?, "Wykonawca"=?, "Opis"=?,
                    "Termin rozpoczęcia"=?, "Termin zakończenia"=?, "Path project"=?, "GML Status"=?, "Data"=?
                WHERE "ID"=?
            """, (
                project_data.get("Nazwa projektu"),
                project_data.get("Identyfikator"),
                project_data.get("Status", "W trakcie"),
                project_data.get("Cel pracy"),
                project_data.get("Zleceniodawca"),
                project_data.get("Adres zleceniodawcy"),
                project_data.get("Telefon"),
                project_data.get("E-mail"),
                project_data.get("Wykonawca"),
                project_data.get("Opis"),
                project_data.get("Termin rozpoczęcia"),
                project_data.get("Termin zakończenia"),
                path_project,
                gml_status,
                json.dumps(project_data),
                project_id
            ))
            self.conn.commit()
        
        except sqlite3.Error as e:
            self.conn.rollback()
            logging.exception(e)
            print(f"Error adding project: {e}")

    def delete_project_old(self, project_id):
        try:
            self.cursor.execute('DELETE FROM projects WHERE "ID"=?', (project_id,))

            #self.backup_db()
            #self.cursor.execute('UPDATE projects SET deleted=1 WHERE id=?', (project_id,))
            
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Error deleting project: {e}")

    def get_projects_old(self):
        try:
            self.cursor.execute("""
                SELECT "ID", "Nazwa projektu", "Identyfikator", "Status", "Cel pracy", "Zleceniodawca",
                        "Adres zleceniodawcy", "Telefon", "E-mail", "Wykonawca", "Opis", "Termin rozpoczęcia",
                    "Termin zakończenia", "Path project", "GML Status", "Data"
                FROM projects
            """)
            rows = self.cursor.fetchall()
            projects = []
            for r in rows:
                projects.append({
                    "ID": r[0],
                    "Nazwa projektu": r[1],
                    "Identyfikator": r[2],
                    "Status": r[3],
                    "Cel pracy": r[4],
                    "Zleceniodawca": r[5],
                    "Adres zleceniodawcy": r[6],
                    "Telefon": r[7],
                    "E-mail": r[8],
                    "Wykonawca": r[9],
                    "Opis": r[10],
                    "Termin rozpoczęcia": r[11],
                    "Termin zakończenia": r[12],
                    "Path project": r[13],
                    "GML Status": r[14],
                    "Data": json.loads(r[15])
                })
            return projects
        except sqlite3.Error as e:
            self.get_projectsv2()
            print(f"Error deleting project: {e}")



class ProjectEditor(QMainWindow): #  JOB EDITOR
    def __init__(self, db: Database, job=None, callback=None):
        super().__init__()
        self.setWindowTitle("Edytor pracy")
        self.setMinimumSize(600, 700)
        self.gml_status = False
        self.valid_nazwa = False
        self.db = db
        self.job = job
        self.callback = callback
        self.status = job['Status'] if job else "W trakcie"
        self.fields = {}  # słownik dla dynamicznych pól w tabach

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        # ---------- Tab Widget ----------
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Tab główny (podstawowe dane)
        self.main_tab = QWidget()
        self._create_main_tab()
        self.tabs.addTab(self.main_tab, "Podstawowe")

        # Tab projektu
        self.project_tab = QWidget()
        self._create_project_tab()
        self.tabs.addTab(self.project_tab, "Projekt")

        # Tab zawiadomień
        #self.notifications_tab = QWidget()
        #self._create_notifications_tab()
        #self.tabs.addTab(self.notifications_tab, "Zawiadomienia")
        
        # Tab Notes
        self.notes_tab = QWidget()
        self._create_notes_tab()
        self.tabs.addTab(self.notes_tab, "Notatki")

        # Tab TAG
        #self.tags_tab = QWidget()
        self._create_tags_tab()
        #self.tabs.addTab(self.tags_tab, "TAG's")

        # Zapis / Anuluj
        btn_layout = QHBoxLayout()

        self.save_btn = QPushButton("Zapisz")
        self.save_btn.setFixedSize(80, 30)
        self.save_btn.clicked.connect(self.save_job)

        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.setFixedSize(80, 30)
        self.cancel_btn.clicked.connect(self.close)
        
        self.load_odt_btn = QPushButton("Wczytaj ze zgłoszenia (.odt)")
        self.load_odt_btn.clicked.connect(self.open_odt)
        btn_layout.addWidget(self.load_odt_btn)
        btn_layout.addStretch(4)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
        btn_layout.addWidget(self.cancel_btn)

        self.layout.addLayout(btn_layout)

        self.setLayout(self.layout)

        if job:
            self.load_job()
            self.load_tags()

    # ------------------- TABY -------------------
    def _create_main_tab(self):
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop)
        # --- 1. TWORZENIE WIDGETÓW ---

        # Nazwa projektu
        self.nazwa_input = QLineEdit()
        self.nazwa_input.setPlaceholderText("Wprowadź nazwę projektu (wymagana)")
        self.nazwa_input.textChanged.connect(self.validate_nazwa)

        # Identyfikator
        self.id_input = QLineEdit()

        # Status
        self.status_combo = QComboBox()
        self.status_combo.setFixedWidth(90)
        self.status_combo.addItems(["W trakcie", "Zakończony", "Anulowany"])
        self.status_combo.setCurrentText(self.status)

        # Cel pracy
        self.cel_combo = QComboBox()
        self.cel_combo.addItems([
            "Wybierz cel pracy.",
            "sporządzenie mapy do celów projektowych",
            "geodezyjna inwentaryzacja powykonawcza obiektów budowlanych",
            "wznowienie znaków granicznych, wyznaczenie punktów granicznych lub ustalenie przebiegu granic działek ewidencyjnych",
            "sporządzenie mapy z projektem podziału nieruchomości",
            "sporządzenie projektu scalenia i podziału nieruchomości",
            "sporządzenie innej mapy do celów prawnych",
            "sporządzenie projektu scalenia lub wymiany gruntów",
            "sporządzenie dokumentacji geodezyjnej na potrzeby rozgraniczenia nieruchomości",
            "wykonanie innych czynności niż wymienione powyżej"
        ])

        # Kontakt
        self.telefon_input = QLineEdit()
        self.email_input = QLineEdit()

        # Zleceniodawca
        self.zleceniodawca_input = QLineEdit()
        self.adres_zleceniodawcy_input = QLineEdit()

        # Wykonawca
        self.wykonawca_input = QLineEdit()

        # Opis pracy
        self.opis_input = QTextEdit()
        self.opis_input.setPlaceholderText("Opisz zakres pracy, szczegóły, uwagi...")
        self.opis_input.setFixedHeight(60)

        # Daty
        self.data_rozpoczecia = QDateEdit(QDate.currentDate())
        self.data_zakonczenia = QDateEdit(QDate.currentDate())

        # Ścieżki
        self.path_project_input = QLineEdit()
        self.browse_project_btn = QtWidgets.QPushButton("Wybierz")
        self.browse_project_btn.clicked.connect(self.choose_project_path)

        self.GML_status_input = QLineEdit()
        self.GML_status_input.setDisabled(True)
        self.browse_GML_btn = QtWidgets.QPushButton("Wybierz")
        self.browse_GML_btn.clicked.connect(self.choose_gml_path)


        layout.addWidget(QLabel("Nazwa projektu"), 0, 0)
        layout.addWidget(self.nazwa_input, 0, 1)

        layout.addWidget(QLabel("Identyfikator"), 0, 2)
        layout.addWidget(self.id_input, 0, 3)

        layout.addWidget(QLabel("Cel pracy:"), 2, 0)
        layout.addWidget(self.cel_combo, 3, 0, 1, 3)

        layout.addWidget(QLabel("Status projektu:"), 2, 3)
        layout.addWidget(self.status_combo, 3, 3, 1, 3)

        row = 4
        layout.addWidget(QLabel("Zleceniodawca"), row, 0)
        layout.addWidget(self.zleceniodawca_input, row, 1, 1, 1)

        row
        layout.addWidget(QLabel("Telefon kontaktowy"), row, 2)
        layout.addWidget(self.telefon_input, row, 3, 1, 1)

        row += 1
        layout.addWidget(QLabel("Adres zleceniodawcy"), row, 0)
        layout.addWidget(self.adres_zleceniodawcy_input, row, 1, 1, 1)

        row
        layout.addWidget(QLabel("Adres e-mail"), row, 2)
        layout.addWidget(self.email_input, row, 3, 1, 1)

        row += 1
        layout.addWidget(QLabel("Wykonawca"), row, 0)
        layout.addWidget(self.wykonawca_input, row, 1, 1, 3)

        row += 1
        #layout.addWidget(QLabel("Opis pracy"), row, 0)
        layout.addWidget(self.opis_input, row, 0, 2, 2)  # 2 wiersze wysokie, 3 kolumny szerokie

        row
        layout.addWidget(QLabel("Termin rozpoczęcia"), row, 2)
        layout.addWidget(self.data_rozpoczecia, row, 3, 1, 3)

        row += 1
        layout.addWidget(QLabel("Termin zakończenia"), row, 2)
        layout.addWidget(self.data_zakonczenia, row, 3, 1, 3)

        # --- Ścieżka projektu ---
        row += 1
        layout.addWidget(QLabel("Ścieżka do plików proj."), row, 0)

        project_layout = QHBoxLayout()
        project_layout.addWidget(self.path_project_input)
        project_layout.addWidget(self.browse_project_btn)
        self.reset_project_btn = QPushButton("Resetuj")
        self.reset_project_btn.clicked.connect(self.reset_project_path)
        project_layout.addWidget(self.reset_project_btn)
        layout.addLayout(project_layout, row, 1, 1, 3)

        # --- Ścieżka GML ---
        row += 1
        layout.addWidget(QLabel("Ścieżka do pliku GML"), row, 0)
        gml_layout = QHBoxLayout()
        gml_layout.addWidget(self.GML_status_input)
        gml_layout.addWidget(self.browse_GML_btn)
        layout.addLayout(gml_layout, row, 1, 1, 3)

        self.main_tab.setLayout(layout)

    def _create_project_tab(self):
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignTop)

        fields_data = [
            ("Numer działki", '', 0, 0),
            ("KW", '', 1, 0),
            ("Województwo", '', 2, 0),
            ("Powiat", '', 3, 0),
            ("Jed. ewid.", '', 4, 0),
            ("ID Jed. ewid.", '', 4, 2),
            ("Obręb", '', 5, 0),
            ("ID Obrębu", '', 5, 2),
            ("Arkusz", '', 6, 0),
            ("Punkt osnowy nr 1", '', 7, 0),
            ("Punkt osnowy nr 2", '', 7, 2),
            ("Data sporządzenia", '', 8, 0),
            ("Wykonawca", '', 9, 0),
            ("Uczestnik prac", '', 9, 2),
            ("Kierownik", '', 10, 0),
            ("Nr upr. kierownika", '', 10, 2),
            ("Data zawiadomienia", '', 12, 0),
        ]

        for key, default, row, col in fields_data:
            label = QLabel(key)
            widget = QLineEdit(default)
            widget.setFixedWidth(200)
            self.fields[key] = widget

            layout.addWidget(label, row, col)
            layout.addWidget(widget, row, col + 1)

        self.project_tab.setLayout(layout)

    def _create_notifications_tab(self):
        layout = QFormLayout()
        fields_data = [
            ("Data ", ''),
        ]
        for key, default in fields_data:
            widget = QLineEdit(default)
            layout.addRow(QLabel(key), widget)
            self.fields[key] = widget
        self.notifications_tab.setLayout(layout)

    def _create_notes_tab(self):
        layout = QFormLayout()

        fields_data = [
            ("Notes", ''),  # etykieta + domyślna wartość
        ]

        for key, default in fields_data:
            widget = QTextEdit()
            widget.setPlainText(default)
            widget.setPlaceholderText("Enter notes about the project here...")

            # 🔹 Dodaj menu kontekstowe (Copy, Paste, Cut, Select All)
            widget.setContextMenuPolicy(Qt.ActionsContextMenu)

            copy_action = QAction("Copy", widget)
            copy_action.triggered.connect(widget.copy)
            widget.addAction(copy_action)

            paste_action = QAction("Paste", widget)
            paste_action.triggered.connect(widget.paste)
            widget.addAction(paste_action)

            cut_action = QAction("Cut", widget)
            cut_action.triggered.connect(widget.cut)
            widget.addAction(cut_action)

            select_all_action = QAction("Select All", widget)
            select_all_action.triggered.connect(widget.selectAll)
            widget.addAction(select_all_action)

            layout.addRow(QLabel(key), widget)
            self.fields[key] = widget

        self.notes_tab.setLayout(layout)

    def _create_tags_tab(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel(
            'TAG należy umieścić w pliku *.DOCX (Microsoft Word), w formacie '
            '<span style="color:purple; font-weight:bold; font-size:12px;">$[</span>'
            '<span style="color:red; font-weight:bold; font-size:12px;">TAG</span>'
            '<span style="color:purple; font-weight:bold; font-size:12px;">]</span>'
        ))
        layout.addWidget(QLabel("Project Tags:"))
        
        # Widget do wyświetlania tagów i ich wartości w formie tabeli
        self.tags_table = QTableWidget()
        self.tags_table.setColumnCount(2)
        self.tags_table.setHorizontalHeaderLabels(["Tag", "Value"])
        self.tags_table.horizontalHeader().setStretchLastSection(True)
        self.tags_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # tylko do odczytu
        layout.addWidget(self.tags_table)
        
        # Dodanie menu kontekstowego z kopiowaniem wartości
        copy_action = QAction("Copy", self.tags_table)
        copy_action.triggered.connect(self.copy_tag_cell)
        self.tags_table.addAction(copy_action)
        self.tags_table.setContextMenuPolicy(Qt.ActionsContextMenu)
        
        self.tags_tab = QWidget()
        self.tags_tab.setLayout(layout)
        self.tabs.addTab(self.tags_tab, "Tags")


    def copy_tag_cell(self):
        selected = self.tags_table.currentItem()
        if selected:
            clipboard = QApplication.clipboard()
            clipboard.setText(selected.text())

    def load_tags(self):
        """Ładuje tagi z self.job['Data'] do tabeli"""
        if not self.job:
            return
        
        data = self.job.get("Data", {})
        self.tags_table.setRowCount(len(data))
        
        for row, (key, value) in enumerate(data.items()):
            self.tags_table.setItem(row, 0, QTableWidgetItem(key))
            self.tags_table.setItem(row, 1, QTableWidgetItem(str(value)))

    def reset_project_path(self):
        """Resetuje ścieżkę projektu do domyślnej (Relative Path = 1)"""
        self.path_project_input.clear()
        self.path_project_input.setStyleSheet("background-color: lightgray;")
        self.relative_path_flag = 1  # domyślnie 1
        QMessageBox.information(self, "Reset", "Ścieżka projektu została zresetowana do domyślnej.")


    # ------------------- FUNKCJE -------------------
    def validate_nazwa(self):
        text = self.nazwa_input.text().strip()

        # Niedozwolone znaki w nazwach folderów (dla Windows + ogólne)
        invalid_chars = r'[\\/:*?"<>|]'

        if not text or re.search(invalid_chars, text):
            self.nazwa_input.setStyleSheet("background-color: salmon;")
            self.valid_nazwa = False
        else:
            self.nazwa_input.setStyleSheet("background-color: lightgreen;")
            self.valid_nazwa = True

        # Opcjonalnie sprawdzenie czy folder już istnieje
        #folder_path = os.path.join(self.base_dir, text)
        #if self.valid_nazwa and os.path.exists(folder_path):
            #self.nazwa_input.setStyleSheet("background-color: orange;")  # folder już istnieje
            #self.valid_nazwa = False

    def choose_project_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder")
        if folder:
            self.path_project_input.setText(folder)
            #folder_name = os.path.basename(folder)
            #self.nazwa_input.setText(folder_name)

    def choose_gml_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik GML",
            "",
            "GML Files (*.gml);;All Files (*)"
        )
        if file_path:
            self.GML_status_input.setText(file_path)

    def load_job(self):
        data = self.job["Data"]
        self.nazwa_input.setText(data.get("Nazwa projektu", ""))
        self.id_input.setText(data.get("Identyfikator", ""))
        self.cel_combo.setCurrentText(data.get("Cel pracy", self.cel_combo.currentText()))
        self.zleceniodawca_input.setText(data.get("Zleceniodawca", ""))
        self.adres_zleceniodawcy_input.setText(data.get("Adres zleceniodawcy", ""))
        self.telefon_input.setText(data.get("Telefon", ""))
        self.email_input.setText(data.get("E-mail", ""))
        self.wykonawca_input.setText(data.get("Wykonawca", ""))
        self.opis_input.setText(data.get("Opis", ""))
        self.data_rozpoczecia.setDate(QDate.fromString(data.get("Termin rozpoczęcia", QDate.currentDate().toString("dd-MM-yyyy")), "dd-MM-yyyy"))
        self.data_zakonczenia.setDate(QDate.fromString(data.get("Termin zakończenia", QDate.currentDate().toString("dd-MM-yyyy")), "dd-MM-yyyy"))
        self.path_project_input.setText(self.job["Path project"])
        #self.GML_status_input.setText(self.job["GML Status"])
        self.gml_status = self.job["GML Status"]
        if self.gml_status == "1":
            self.GML_status_input.setText("Plik *.gml zaimportowany poprawnie!")
        else:
            self.GML_status_input.setText("Brak pliku GML")
        
        self.status_combo.setCurrentText(self.status)
        self.validate_nazwa()

        # Ładowanie danych do tab projektu
        for key, widget in self.fields.items():
            if key in data:
                widget.setText(data[key])

    def save_job(self):
        if not self.nazwa_input.text().strip():
            QMessageBox.warning(self, "Błąd", "Nazwa projektu jest wymagana!")
            return

        if not self.valid_nazwa:
            QMessageBox.warning(self, "Błąd", "Nazwa projektu zawiera niedozwolone znaki!")
            return

        path_has_changed = False
        name_has_changed = False
        relative_path_flag = 1

        old_project_name = self.job["Data"].get("Nazwa projektu", "") if self.job else None
        #old_project_path = Path(self.job["Path project"]) if self.job else None

        path_to_project = self.path_project_input.text().strip()
        project_name = self.nazwa_input.text().strip()

        path_to_GML = self.GML_status_input.text()

        if path_to_project:
            project_path = Path(path_to_project) / project_name
            path_to_project = Path(path_to_project)
            relative_path_flag = 0
        else:
            project_path = file_manager.projects_folder_path / project_name
            path_to_project = file_manager.projects_folder_path

        gml_path = project_path / GML_FILE

        #if old_project_path and path_to_project != old_project_path:
            #path_has_changed = True

        if old_project_name and project_name != old_project_name:
            name_has_changed = True
        
        if project_path.exists() and name_has_changed:
                QMessageBox.warning( self, "Błąd", f"Projekt o nazwie '{project_name}' już istnieje w podanej ścieżce!")
                return
        
        job_data = {
            "Nazwa projektu": self.nazwa_input.text(),
            "Identyfikator": self.id_input.text(),
            "Status": self.status_combo.currentText(),
            "Cel pracy": self.cel_combo.currentText(),
            "Zleceniodawca": self.zleceniodawca_input.text(),
            "Adres zleceniodawcy": self.adres_zleceniodawcy_input.text(),
            "Telefon": self.telefon_input.text(),
            "E-mail": self.email_input.text(),
            "Wykonawca": self.wykonawca_input.text(),
            "Opis": self.opis_input.toPlainText(),
            "Termin rozpoczęcia": self.data_rozpoczecia.date().toString("dd-MM-yyyy"),
            "Termin zakończenia": self.data_zakonczenia.date().toString("dd-MM-yyyy")
        }

        for key, widget in self.fields.items():
            if isinstance(widget, QTextEdit):
                job_data[key] = widget.toPlainText()
            else:
                job_data[key] = widget.text()

        #print(job_data)

        if self.job:
            if name_has_changed:
                result = file_manager.rename_folder(project_name, path_to_project, old_project_name)
                if result is False:
                    QMessageBox.warning( self, "Błąd", f"Projekt o nazwie '{project_name}' już istnieje w podanej ścieżce!")
                    return 
            project_path.mkdir(parents=True, exist_ok=True)
            if Path(path_to_GML).is_file():
                file_manager.copy_file_to_directory(Path(path_to_GML), gml_path)
                self.gml_status = True
            self.db.update_project(self.job["ID"], relative_path_flag, job_data, str(path_to_project), self.gml_status)
            print(f"Zaktualizowano projekt ID {self.job['ID']}")
        else:
            result = file_manager.create_folder(project_name, path_to_project)
            if result is False:
                    QMessageBox.warning( self, "Błąd", f"Projekt o nazwie '{project_name}' już istnieje w podanej ścieżce!")
                    return
            if Path(path_to_GML).is_file():
                file_manager.copy_file_to_directory(Path(path_to_GML), gml_path)
                self.gml_status = True
            self.db.add_project(job_data, relative_path_flag, str(path_to_project), self.gml_status)
            print(f"Dodano nowy projekt: {path_to_project} {project_name}")



        if self.callback:
            self.callback()
        self.close()


    def read_odt_text(self, path: str) -> str:
        """Wczytuje cały tekst z pliku ODT za pomocą odfdo."""
        doc = Document(path)   # otwieramy dokument
        return doc.get_formatted_text()

    def parse_zgloszenie(self, text: str) -> dict:
        """Wyciąga dane ze zgłoszenia prac geodezyjnych."""

        data = {}

        # IDENTYFIKATOR ZGŁOSZENIA
        m = re.search(r"GKN\.[0-9\.]+", text)
        if m:
            data["Identyfikator"] = m.group().strip()

        # Wykonawca
        m = re.search(r"Nazwa wykonawcy\s*\n\s*(.+)", text, re.I)
        if m:
            data["Wykonawca"] = m.group(1).strip()

        m = re.search(r"NIP\s*:\s*([0-9]+)", text)
        if m:
            data["NIP"] = m.group(1).strip()

        # Adres wykonawcy
        m = re.search(r"Nazwa wykonawcy.*?\n(?:\s*\n)*.*?([A-ZŁŚŻŹĆÓĘĄ0-9][^\n]+)", text, re.I)
        if m:
            data["Adres wykonawcy"] = m.group(1).strip()

        # Adresat zgłoszenia
        m = re.search(r"Adresat zgłoszenia.*?\n\s*(.+)", text, re.I)
        if m:
            data["Adresat"] = m.group(1).strip()

        # Numery działek
        m = re.search(r"dz\.\s*([\d,\s]+)", text)
        if m:
            data["Numer działki"] = m.group(1).strip()

        # Lokalizacja
        m = re.search(r"Województwo:\s*([^\[]+)", text)
        if m:
            data["Województwo"] = m.group(1).strip()

        m = re.search(r"Powiat:\s*([^\[]+)", text)
        if m:
            data["Powiat"] = m.group(1).strip()

        # Gmina (Jednostka ewidencyjna) – zachowaj nazwę bez zmian
        m = re.search(r"Gmina:\s*([^\[]+)", text)
        if m:
            data["Jed. ewid."] = m.group(1).strip()

        # ID Jednostki ewidencyjnej — zachowujemy nawiasy []
        m = re.search(r"Gmina:\s*[^\[]+(\[[0-9_]+\])", text)
        if m:
            data["ID Jed. ewid."] = m.group(1).strip()

        # OBRĘB i ID OBRĘBU
        m = re.search(r"Obręb:\s*([^\[]+)\s*(\[[0-9]+\])", text)
        if m:
            data["Obręb"] = m.group(1).strip()
            data["ID Obrębu"] = m.group(2).strip()

        dz = re.search(r"dz\.\s*([0-9/]+)", text)
        if dz: data["dzialka"] = dz.group(1).strip()

        # ARKUSZ (godło mapy)
        m = re.search(r"''2000''\s*:\s*(.*)", text)
        if m:
            data["Arkusz"] = m.group(1).strip()

        terminy = re.findall(r"(\d{2}-\d{2}-\d{4})", text)
        if len(terminy) >= 2:
            data["Termin rozpoczęcia"] = terminy[-2]
            data["Termin zakończenia"] = terminy[-1]
        else:
            data["Termin rozpoczęcia"] = ""
            data["Termin zakończenia"] = ""

        return data


    def load_from_odt(self, file_path: str):
        """Wczytuje dane ze zgłoszenia ODT i uzupełnia formularz."""
        try:
            text = self.read_odt_text(file_path)
            data = self.parse_zgloszenie(text)

            # Identyfikator zgłoszenia
            if "Identyfikator" in data:
                self.id_input.setText(data["Identyfikator"])

            # Wykonawca
            if "wykonawca" in data:
                self.wykonawca_input.setText(data["wykonawca"])

            # NIP
            if "NIP" in data:
                pass

            # Adres wykonawcy
            if "adres_wykonawcy" in data:
                self.adres_zleceniodawcy_input.setText(data["adres_wykonawcy"])


            def fill_field(key):
                """Pomocnicza funkcja wypełniająca self.fields[key] jeśli istnieje."""
                if key in data and key in self.fields:
                    self.fields[key].setText(str(data[key]))

            fill_field("Numer działki")
            fill_field("KW")
            fill_field("Województwo")
            fill_field("Powiat")
            fill_field("Jed. ewid.")
            fill_field("ID Jed. ewid.")
            fill_field("Obręb")
            fill_field("ID Obrębu")
            fill_field("Arkusz")
            fill_field("Punkt osnowy nr 1")
            fill_field("Punkt osnowy nr 2")
            fill_field("Data sporządzenia")
            fill_field("Kierownik")
            fill_field("Nr upr. kierownika")
            fill_field("Uczestnik prac")

            if "Cel pracy" in data:
                self.cel_combo.setCurrentText(data["Cel pracy"])

            # Terminy
            if "Termin rozpoczęcia" in data:
                d = QDate.fromString(data["Termin rozpoczęcia"], "dd-MM-yyyy")
                if d.isValid():
                    self.data_rozpoczecia.setDate(d)

            if "Termin zakończenia" in data:
                d = QDate.fromString(data["Termin zakończenia"], "dd-MM-yyyy")
                if d.isValid():
                    self.data_zakonczenia.setDate(d)

            QMessageBox.information(self, "OK", "Dane ze zgłoszenia zostały wczytane.")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wczytać pliku:\n{e}")

    def open_odt(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Wybierz zgłoszenie", "", "ODT (*.odt)")
        if file_path:
            self.load_from_odt(file_path)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = Database(DB_FILE)   # create a Database instance

    job_data = None

    # Pobranie projektu do edycji, np. o id=1
    project_id = 2
    job_data = db.get_project(project_id)  # zakładamy, że ta funkcja zwraca słownik z kluczami "id", "data" i "path"

    window = ProjectEditor(db, job=job_data)   # przekazanie istniejącego projektu

    window.show()
    sys.exit(app.exec())
