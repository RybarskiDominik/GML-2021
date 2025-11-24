from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QHBoxLayout
)
from PySide6.QtCore import Signal
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class WorkspaceSettingsWindow(QMainWindow):
    settings_win_closed = Signal()
    def __init__(self, file_manager, parent=None):
        super().__init__(parent)
        self.fm = file_manager
        self.parent_window = parent  # zapisujemy rodzica
        self.setWindowTitle("Ustawienia Workspace")
        self.resize(600, 300)
        self.init_ui()

    def init_ui(self):
        # Create a central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # === BAZA DANYCH ===
        main_layout.addWidget(QLabel("Folder do bazy danych:"))
        self.database_line = QLineEdit(str(self.fm.database_folder_path))
        database_row = QHBoxLayout()
        database_row.addWidget(self.database_line)

        btn_change_db = QPushButton("Zmień")
        btn_change_db.clicked.connect(self.change_database)
        database_row.addWidget(btn_change_db)

        btn_reset_db = QPushButton("Reset")
        btn_reset_db.clicked.connect(self.reset_database)
        database_row.addWidget(btn_reset_db)

        main_layout.addLayout(database_row)

        # === OBSZAR ROBOCZY ===
        main_layout.addWidget(QLabel("Wskaż lokalizację (obszar roboczy), w której znajduje się lub zostanie utworzony folder z projektami."))
        self.workspace_line = QLineEdit(str(self.fm.current_workspace_dir))
        workspace_row = QHBoxLayout()
        workspace_row.addWidget(self.workspace_line)

        btn_change_workspace = QPushButton("Zmień")
        btn_change_workspace.clicked.connect(self.change_workspace)
        workspace_row.addWidget(btn_change_workspace)

        btn_reset_workspace = QPushButton("Reset")
        btn_reset_workspace.clicked.connect(self.reset_workspace)
        workspace_row.addWidget(btn_reset_workspace)

        main_layout.addLayout(workspace_row)
        main_layout.addSpacing(10)

        # === FORMATKI ===
        main_layout.addWidget(QLabel("Ścieżka do folderu z formatkami (.docx) pogrupowanymi w podfolderach."))
        self.templates_line = QLineEdit(str(self.fm.templates_folder_path))
        templates_row = QHBoxLayout()
        templates_row.addWidget(self.templates_line)

        btn_change_templates = QPushButton("Zmień")
        btn_change_templates.clicked.connect(self.change_templates)
        templates_row.addWidget(btn_change_templates)

        btn_reset_templates = QPushButton("Reset")
        btn_reset_templates.clicked.connect(self.reset_templates)
        templates_row.addWidget(btn_reset_templates)

        main_layout.addLayout(templates_row)

        # === Backup i Restore ===
        backup_restore_row = QHBoxLayout()
        backup_restore_row.addStretch()  # przesuwa przyciski na prawą stronę

        btn_backup = QPushButton("Backup")
        btn_backup.clicked.connect(self.perform_workspace_backup)
        backup_restore_row.addWidget(btn_backup)

        #btn_restore = QPushButton("Przywróć")
        #btn_restore.clicked.connect(self.perform_workspace_restore)
        #backup_restore_row.addWidget(btn_restore)

        main_layout.addLayout(backup_restore_row)

        # Stretch, aby reszta kontentu została przy górze
        main_layout.addStretch()

        # === RESET WSZYSTKIE / ZAMKNIJ ===
        bottom_row = QHBoxLayout()

        btn_reset_all = QPushButton("Resetuj wszystkie ustawienia")
        btn_reset_all.clicked.connect(self.reset_all)
        bottom_row.addWidget(btn_reset_all)  # lewa strona

        bottom_row.addStretch()  # rozsuwa przyciski

        btn_close = QPushButton("Zamknij")
        btn_close.clicked.connect(self.close)  # zamyka okno
        bottom_row.addWidget(btn_close)  # prawa strona

        main_layout.addLayout(bottom_row)


    def closeEvent(self, event):
        """Emitujemy sygnał, aby inne okna mogły zareagować."""
        self.settings_win_closed.emit()
        super().closeEvent(event)


    def perform_workspace_backup(self):
        """Uruchamia backup workspace i pokazuje informację użytkownikowi."""
        from PySide6.QtWidgets import QMessageBox, QFileDialog

        # Możliwość wyboru folderu docelowego
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder docelowy backupu")
        if not folder:  # użytkownik anulował
            return

        backup_root = Path(folder)

        try:
            backup_paths = self.fm.backup_workspace(backup_root)
            if backup_paths:
                msg = "Backup wykonany pomyślnie:\n"
                for k, v in backup_paths.items():
                    msg += f"{k}: {v}\n"
                QMessageBox.information(self, "Backup zakończony", msg)

                # Odśwież główne okno po zakończeniu
                if self.parent_window:
                    self.parent_window.refresh_after_settings()

            else:
                QMessageBox.warning(self, "Backup", "Nie znaleziono plików/folderów do backupu.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd backupu", f"Wystąpił błąd podczas tworzenia backupu:\n{e}")
            logger.error(f"Błąd backupu workspace: {e}")

    def perform_workspace_restore(self):
        """Pozwala użytkownikowi wybrać folder backupu i przywrócić workspace."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        backup_folder = QFileDialog.getExistingDirectory(self, "Wybierz folder backupu do przywrócenia")
        if not backup_folder:  # użytkownik anulował
            return

        try:
            restored_paths = self.fm.restore_backup(Path(backup_folder))
            if restored_paths:
                msg = "Przywrócono foldery:\n"
                for k, v in restored_paths.items():
                    msg += f"{k}: {v}\n"
                QMessageBox.information(self, "Przywracanie zakończone", msg)

                # Odśwież główne okno po zakończeniu
                if self.parent_window:
                    self.parent_window.refresh_after_settings()

            else:
                QMessageBox.warning(self, "Przywracanie", "Nie znaleziono folderów do przywrócenia w backupie.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd przywracania", f"Wystąpił błąd podczas przywracania:\n{e}")
            logger.error(f"Błąd restore workspace: {e}")



    # === OBSZAR ROBOCZY ===
    def change_workspace(self):
        new_path = QFileDialog.getExistingDirectory(self, "Wybierz nowy obszar roboczy")
        if new_path:
            self.fm.set_new_workspace_path(Path(new_path))
            self.workspace_line.setText(str(self.fm.current_workspace_dir))

    def reset_workspace(self):
        self.fm.reset_workspace_path()
        self.workspace_line.setText(str(self.fm.current_workspace_dir))

    # === FORMATKI ===
    def change_templates(self):
        new_path = QFileDialog.getExistingDirectory(self, "Wybierz folder z formatkami")
        if new_path:
            self.fm.set_custom_docx_path(Path(new_path))
            print("New templates path:", new_path)
            print("Updated templates path in FM:", self.fm.templates_folder_path)
            self.templates_line.setText(str(self.fm.templates_folder_path))

    def reset_templates(self):
        self.fm.reset_docx_path()
        self.templates_line.setText(str(self.fm.templates_folder_path))

    # === BAZA DANYCH ===
    def change_database(self):
        new_file = QFileDialog.getExistingDirectory(self, "Wybierz folder gdzie ma się znajdować baza danych")
        if new_file:
            print("New database path:", new_file)
            self.fm.set_custom_database_path(Path(new_file))
            self.database_line.setText(str(self.fm.database_folder_path))

    def reset_database(self):
        self.fm.reset_database_path()
        self.database_line.setText(str(self.fm.database_folder_path))

    # === RESET WSZYSTKIE ===
    def reset_all(self):
        self.reset_workspace()
        self.reset_templates()
        self.reset_database()
