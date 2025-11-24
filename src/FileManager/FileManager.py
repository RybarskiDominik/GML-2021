from PySide6.QtWidgets import QMessageBox, QApplication, QInputDialog
from PySide6.QtCore import QSettings, Signal, QObject
from datetime import datetime
from pathlib import Path
import platform
import tempfile
import logging
import shutil
import sys
import os

logger = logging.getLogger(__name__)
settings = QSettings('File', 'File Manager')

DB_FILE = "DATABASE.db"


class FileManager(QObject):
    path_changed = Signal()
    def __init__(self):
        super().__init__()
        self.workspace_folder_name = "Obszar_roboczy"

        self.base_path = self._determine_base_path()
        self.default_workspace_root_dir = self._get_default_dir()

        saved_workspace_path = settings.value("workspace_path", type=str)
        if saved_workspace_path:
            self.current_workspace_dir = Path(saved_workspace_path).expanduser().resolve()
            logger.info(f"Załadowano zapisany obszar roboczy: {self.current_workspace_dir}")
            #print(f"Załadowano zapisany obszar roboczy: {self.current_workspace_dir}")

            if not self.current_workspace_dir.drive or not self.current_workspace_dir.exists():
                self.current_workspace_dir = self.default_workspace_root_dir / self.workspace_folder_name
                logger.info(f"Z powodu błędnej ścieżki użyto domyślnego obszaru roboczego: {self.current_workspace_dir}")

        else:
            self.current_workspace_dir = self.default_workspace_root_dir / self.workspace_folder_name
            logger.info(f"Użyto domyślnego obszaru roboczego: {self.current_workspace_dir}")
            #print(f"Użyto domyślnego obszaru roboczego: {self.current_workspace_dir}")

        self._set_base_app_path()
        self._set_database_path()
        self._set_base_workspace_root_dir()

        self.check_workspace_structure()

    def _determine_base_path(self) -> Path:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        else:
            import __main__
            return Path(__main__.__file__).resolve().parent

    def _get_default_dir(self) -> Path:
        """Return a cross-platform writable base directory."""
        # Use executable folder if writable
        if self._has_write_permissions(self.base_path):
            return self.base_path

        system = platform.system().lower()

        if system == "windows":
            return Path(os.getenv("APPDATA", tempfile.gettempdir())) / "GMLReader"
        elif system == "darwin":
            return Path.home() / "Library" / "Application Support" / "GMLReader"
        else:  # Linux and other Unix-like OS
            return Path.home() / ".local" / "share" / "GMLReader"

    def _set_database_path(self):
        saved_db_path = settings.value("database_folder_path", type=str)
        if saved_db_path:
            self.database_folder_path = Path(saved_db_path).expanduser().resolve()
            logger.info(f"Załadowano zapisany plik bazy danych: {self.database_folder_path}")
        else:
            self.database_folder_path = self.base_path
            logger.info(f"Użyto domyślnej bazy danych: {self.database_folder_path}")

    def _set_base_app_path(self):
        self.icons_path = self.default_workspace_root_dir / 'Icons'
        self.log_file_path = self.default_workspace_root_dir / "log.log"
        self.stylesheets_path = self.default_workspace_root_dir / 'gui' / 'Stylesheets' / 'images_dark-light'
        self.stylesheets_folder_path = self.default_workspace_root_dir / 'gui' / "Stylesheets"

    def _set_base_workspace_root_dir(self):
        self.current_workspace_dir.mkdir(parents=True, exist_ok=True)

        saved_docx_path = settings.value("templates_folder_path", type=str)
        if saved_docx_path:
            self.templates_folder_path  = Path(saved_docx_path).expanduser().resolve()
            if not self.templates_folder_path.drive or not self.templates_folder_path.exists():
                self.templates_folder_path  = self.current_workspace_dir / "Formatki"
        else:
            self.templates_folder_path  = self.current_workspace_dir / "Formatki"

        self.templates_notification_folder_path = self.templates_folder_path  / "Zawiadomienia"
        self.projects_folder_path = self.current_workspace_dir / "Projekty"
        self.gml_folder_path = self.current_workspace_dir / "GML"

        self.gml_file_path = self.gml_folder_path / "Parsed_GML.gml"
        self.data_base_file_path = self.gml_folder_path / "GML_DataBase.pkl"
        self.xlsx_target_path = self.gml_folder_path / "GML.xlsx"


    def check_workspace_structure(self):
        """Tworzy wszystkie wymagane katalogi."""
        folders = [
            self.projects_folder_path,
            self.gml_folder_path,
            self.templates_folder_path,
            self.templates_notification_folder_path,
            self.database_folder_path
        ]

        subfolders = [
            'Budynek', 'MDCP', 'Podział', 'Wznowienie-Wyznaczenie-Ustalenie'
        ]

        for folder in folders:
            try:
                folder.mkdir(parents=True, exist_ok=True)
                #logger.debug(f"Utworzono lub istnieje: {folder}")
            except Exception as e:
                logger.exception(f"Błąd przy tworzeniu folderu: {folder} -> {e}")

        for name in subfolders:
            path = self.templates_folder_path / name
            path.mkdir(parents=True, exist_ok=True)


    def _has_write_permissions(self, path: Path) -> bool:
        """Check if the directory is writable."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            test_file = path / ".write_test"
            with test_file.open("w") as f:
                f.write("test")
            test_file.unlink(missing_ok=True)
            return True
        except Exception:
            return False


    def _format_info_lines(self) -> list:
        """Common formatting for info display."""
        return [
            "\n=== FileManager Info ===",
            f"Workspace folder name:          {self.workspace_folder_name}",
            f"Base application path:          {self.base_path}",
            f"Default workspace root dir:     {self.default_workspace_root_dir}",
            f"Icons directory:                {self.icons_path}",
            f"Log file path:                  {self.log_file_path}",
            f"Stylesheets folder:             {self.stylesheets_folder_path}",
            f"Stylesheet images path:         {self.stylesheets_path}",
            f"Current workspace directory:    {self.current_workspace_dir}",
            f"GML folder path:                {self.gml_folder_path}",
            f"Formatki folder path:           {self.templates_folder_path}",
            f"Formatki pow. folder path:      {self.templates_notification_folder_path}",
            f"Projekty folder path:           {self.projects_folder_path}",
            f"GML parsed file path:           {self.gml_file_path}",
            f"GML database file path:         {self.data_base_file_path}",
            f"GML Excel export path:          {self.xlsx_target_path}",
            "========================\n"
        ]

    def logger_info(self):
        for line in self._format_info_lines():
            logger.info(line)

    def print_info(self):
        """Wyświetla informacje o konfiguracji FileManager."""
        print("\n".join(self._format_info_lines()))


    def _update_paths_and_structure(self):
        """Update paths and recreate folder structure."""
        self._set_base_workspace_root_dir()
        self.check_workspace_structure()
        self.path_changed.emit()

    def set_custom_docx_path(self, path: Path):
        path = Path(path).expanduser().resolve()
        self.templates_folder_path = path
        self.templates_notification_folder_path = self.templates_folder_path / "Zawiadomienia"
        settings.setValue("templates_folder_path", str(self.templates_folder_path))
        logger.info(f"Zmieniono ścieżkę do bazy danych na: {self.templates_folder_path}")

        self._update_paths_and_structure()

    def reset_docx_path(self):
        settings.remove("templates_folder_path")
        self.current_workspace_dir = self.default_workspace_root_dir / self.workspace_folder_name
        self.templates_folder_path = self.current_workspace_dir / "Formatki"
        self.templates_notification_folder_path = self.templates_folder_path / "Zawiadomienia"

        self.templates_folder_path.mkdir(parents=True, exist_ok=True)
        self.templates_notification_folder_path.mkdir(parents=True, exist_ok=True)

        #settings.setValue("templates_folder_path", str(self.templates_folder_path))
        self._update_paths_and_structure()

    def set_custom_database_path(self, path: Path):
        path = Path(path).expanduser().resolve()
        self.database_folder_path = path
        settings.setValue("database_folder_path", str(path))
        logger.info(f"Zmieniono ścieżkę do bazy danych na: {path}")
        self._update_paths_and_structure()

    def reset_database_path(self):
        settings.remove("database_folder_path")
        self.database_folder_path = self.default_workspace_root_dir
        logger.info(f"Zresetowano ścieżkę bazy danych do domyślnej: {self.database_folder_path}")
        self._update_paths_and_structure()

    def set_new_workspace_path(self, path: Path):
        path = Path(path).expanduser().resolve()
        settings.setValue("workspace_path", str(path))
        self.current_workspace_dir = path
        logger.info(f"Zmieniono obszar roboczy: {path}")

        self._update_paths_and_structure()

    def reset_workspace_path(self):
        settings.remove("workspace_path")
        self.current_workspace_dir = self.default_workspace_root_dir / self.workspace_folder_name
        logger.info(f"Przywrócono domyślny obszar roboczy: {self.current_workspace_dir}")
        self._update_paths_and_structure()


    def move_workspace_path(self, new_path: Path):
        """Move workspace data to new location with conflict resolution."""
        old_workspace_dir = self.current_workspace_dir
        if not new_path or old_workspace_dir == Path(new_path).expanduser().resolve():
            return

        new_workspace_dir = Path(new_path).expanduser().resolve()

        logger.info(f"Przenoszenie obszaru roboczego...\nStary: {old_workspace_dir}\nNowy: {new_workspace_dir}")

        self.current_workspace_dir = new_workspace_dir
        self._set_base_workspace_root_dir()
        self.check_workspace_structure()

        app = QApplication.instance() or QApplication([])

        apply_to_all = False
        global_choice = None  # "overwrite", "skip", "rename"

        if old_workspace_dir.exists():
            try:
                for root, dirs, files in os.walk(old_workspace_dir):
                    rel_path = Path(root).relative_to(old_workspace_dir)
                    target_dir = new_workspace_dir / rel_path
                    target_dir.mkdir(parents=True, exist_ok=True)

                    for file in files:
                        src_file = Path(root) / file
                        dest_file = target_dir / file

                        if dest_file.exists():
                            if apply_to_all and global_choice:
                                choice = global_choice
                            else:
                                choice = self._handle_file_conflict(dest_file)
                                if choice == "cancel":
                                    logger.warning("Przerwano operację.")
                                    return
                                elif choice == "apply_all":
                                    global_choice, apply_to_all = self._handle_apply_all_dialog()
                                    if global_choice:
                                        choice = global_choice
                                    else:
                                        continue

                            self._execute_file_action(src_file, dest_file, target_dir, choice)
                        else:
                            shutil.copy2(src_file, dest_file)
                            logger.debug(f"Skopiowano: {dest_file}")

                # Opcjonalnie usuń stary workspace po pomyślnym przeniesieniu
                #if self._confirm_delete_old_workspace(old_workspace_dir):
                    #shutil.rmtree(old_workspace_dir)
                    #logger.info(f"Usunięto stary obszar roboczy: {old_workspace_dir}")
                    
            except Exception as e:
                logger.error(f"Błąd podczas przenoszenia workspace: {e}")
                return

        settings.setValue("workspace_path", str(new_workspace_dir))
        logger.info(f"Zmieniono obszar roboczy na: {new_workspace_dir}")

    def rename_folder(self, project_name: str, path_to_project: Path, old_project_name: str) -> bool:
        try:
            old_path = path_to_project / old_project_name
            new_path = path_to_project / project_name

            if not old_path.exists():
                print(f"Folder '{old_project_name}' does not exist.")
                return False

            if new_path.exists():
                print(f"A folder named '{project_name}' already exists.")
                return False

            old_path.rename(new_path)
            return True

        except Exception as e:
            print(f"Error renaming folder: {e}")
            return False

    def create_folder(self, folder_name: str, path: Path = None) -> bool:
        target = path / folder_name

        if not target.exists():
            target.mkdir(parents=True, exist_ok=False)
            print(f"Utworzono folder: {target}")
            return True
        else:
            print(f"Folder już istnieje: {target}")
            return False
        
    def copy_file_to_directory(self, path_to_file: Path = None, target_path_for_file: Path = None):
        try:
            shutil.copy(path_to_file, target_path_for_file)
            print(f"Plik został skopiowany do {target_path_for_file}.")
            return True
        except shutil.SameFileError:
            print("Źródłowy i docelowy plik są takie same. Kopiowanie pominięto.")
            return True
        except Exception as e:
            logging.exception(e)
            print(f"Wystąpił błąd podczas kopiowania pliku: {str(e)}")
            return False


    def _generate_unique_name(self, path: Path) -> Path:
        """Generuje unikalną nazwę pliku, jeśli plik istnieje."""
        directory = path.parent
        stem = path.stem
        suffix = path.suffix
        i = 1
        new_path = directory / f"{stem}_{i}{suffix}"
        while new_path.exists():
            i += 1
            new_path = directory / f"{stem}_{i}{suffix}"
        return new_path


    def _handle_file_conflict(self, dest_file: Path) -> str:
        """Obsługuje konflikt pliku i zwraca wybór użytkownika."""
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Konflikt pliku")
        msg_box.setText(f"Plik już istnieje:\n{dest_file}")
        msg_box.setInformativeText("Co chcesz zrobić?")
        
        overwrite = msg_box.addButton("Nadpisz", QMessageBox.AcceptRole)
        skip = msg_box.addButton("Pomiń", QMessageBox.RejectRole)
        rename = msg_box.addButton("Zmień nazwę", QMessageBox.ActionRole)
        cancel = msg_box.addButton("Anuluj", QMessageBox.DestructiveRole)
        apply_all_box = msg_box.addButton("Zastosuj dla wszystkich", QMessageBox.YesRole)
        
        msg_box.exec()
        clicked = msg_box.clickedButton()

        if clicked == cancel:
            return "cancel"
        elif clicked == overwrite:
            return "overwrite"
        elif clicked == skip:
            return "skip"
        elif clicked == rename:
            return "rename"
        elif clicked == apply_all_box:
            return "apply_all"
        
        return "skip"  # domyślna akcja

    def _handle_apply_all_dialog(self) -> tuple:
        """Obsługuje dialog 'Zastosuj dla wszystkich'."""
        sub_box = QMessageBox()
        sub_box.setWindowTitle("Zastosuj dla wszystkich")
        sub_box.setText("Wybierz akcję, którą zastosować dla wszystkich kolizji:")
        
        all_overwrite = sub_box.addButton("Nadpisz wszystkie", QMessageBox.AcceptRole)
        all_skip = sub_box.addButton("Pomiń wszystkie", QMessageBox.RejectRole)
        
        sub_box.exec()
        sub_clicked = sub_box.clickedButton()
        
        if sub_clicked == all_overwrite:
            return "overwrite", True
        elif sub_clicked == all_skip:
            return "skip", True
        
        return None, False

    def _execute_file_action(self, src_file: Path, dest_file: Path, target_dir: Path, choice: str):
        """Wykonuje wybraną akcję na pliku."""
        try:
            if choice == "overwrite":
                shutil.copy2(src_file, dest_file)
                logger.debug(f"Nadpisano: {dest_file}")
            elif choice == "skip":
                logger.debug(f"Pominięto: {src_file}")
            elif choice == "rename":
                new_name, ok = QInputDialog.getText(None, "Zmień nazwę pliku", "Podaj nową nazwę:")
                if ok and new_name.strip():
                    new_dest = target_dir / new_name.strip()
                    # Sprawdź czy nowa nazwa też nie koliduje
                    counter = 1
                    original_new_dest = new_dest
                    while new_dest.exists():
                        stem = original_new_dest.stem
                        suffix = original_new_dest.suffix
                        new_dest = target_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                    
                    shutil.copy2(src_file, new_dest)
                    logger.debug(f"Skopiowano jako: {new_dest}")
                else:
                    logger.debug(f"Pominięto (nie podano nazwy): {src_file}")
        except Exception as e:
            logger.error(f"Błąd podczas kopiowania pliku {src_file}: {e}")

    def _confirm_delete_old_workspace(self, old_workspace_dir: Path) -> bool:
        """Pyta użytkownika czy usunąć stary workspace."""
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Usuń stary obszar roboczy")
        msg_box.setText(f"Czy chcesz usunąć stary obszar roboczy?\n{old_workspace_dir}")
        msg_box.setInformativeText("Ta operacja jest nieodwracalna.")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        return msg_box.exec() == QMessageBox.Yes


    def get_icon_path(self, icon_name, is_dark_mode=True):
        """Zwraca ścieżkę do ikony w zależności od motywu."""
        suffix = "-light" if is_dark_mode else "-dark"
        return str(self.stylesheets_path / f"{icon_name}{suffix}")

    def get_stylesheets_path(self, icon_name):
        return str(self.stylesheets_path / icon_name)

    def get_stylesheets_folder_path(self, icon_name):
        return str(self.stylesheets_folder_path / icon_name)


    def backup_workspace(self, backup_root: Path = None) -> dict[str, Path]:
        """
        Tworzy kopię zapasową wszystkich głównych folderów workspace:
        - Projekty
        - GML
        - Formatki
        - Baza danych (jeśli plik istnieje)

        backup_root: folder docelowy dla backupu. Domyślnie: workspace/Backups/YYYYMMDD_HHMMSS
        Zwraca słownik {nazwa_folderu: Path_do_kopii}
        """
        backup_root = Path(backup_root) if backup_root else self.current_workspace_dir / "Backups"
        #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_root = backup_root / f"Backup_{timestamp}"
        backup_root.mkdir(parents=True, exist_ok=True)

        backup_paths = {}

        folders_to_backup = {
            "Projekty": self.projects_folder_path,
            "GML": self.gml_folder_path,
            "Formatki": self.templates_folder_path,
        }

        """
        for name, path in folders_to_backup.items():
            if path.exists():
                dest = backup_root / name
                shutil.copytree(path, dest)
                logger.info(f"Utworzono backup folderu {name}: {dest}")
                backup_paths[name] = dest
        """
        
        for name, path in folders_to_backup.items():
            if path.exists():
                # Skip copying backup folder into itself
                if backup_root in path.parents:
                    logger.warning(f"Pominięto folder {name}, aby uniknąć rekurencji")
                    continue
                
                dest = backup_root / name
                try:
                    shutil.copytree(path, dest, dirs_exist_ok=True, symlinks=False)
                    logger.info(f"Utworzono backup folderu {name}: {dest}")
                    backup_paths[name] = dest
                except Exception as e:
                    logger.error(f"Nie udało się wykonać backupu folderu {name}: {e}")

        # Kopia pliku bazy danych
        self.db_file_path = self.database_folder_path / DB_FILE
        if self.db_file_path.exists() and self.db_file_path.is_file():
            db_backup_path = backup_root / self.db_file_path.name
            shutil.copy2(self.db_file_path, db_backup_path)
            logger.info(f"Utworzono backup bazy danych: {db_backup_path}")
            backup_paths["Baza danych"] = db_backup_path

        return backup_paths

    def restore_backup(self, backup_path: Path, restore_folders: list[str] = None) -> dict[str, Path]:
        """
        Przywraca zawartość backupu do workspace.
        backup_path: ścieżka do folderu backupu (np. workspace/Backups/Backup_20251026_150000)
        restore_folders: lista folderów do przywrócenia ['Projekty', 'GML', 'Formatki', 'Baza danych'].
                        Domyślnie przywraca wszystkie dostępne foldery.
        Zwraca słownik {nazwa_folderu: Path_do_przywróconego_folderu}
        """
        backup_path = Path(backup_path)
        if not backup_path.exists():
            logger.warning(f"Backup nie istnieje: {backup_path}")
            return {}

        if restore_folders is None:
            restore_folders = ['Projekty', 'GML', 'Formatki', 'Baza danych']

        restored_paths = {}

        # Mapowanie folderów backupu do ścieżek w FileManager
        folder_map = {
            "Projekty": self.projects_folder_path,
            "GML": self.gml_folder_path,
            "Formatki": self.templates_folder_path,
            "Baza danych": self.database_folder_path,
        }

        for name in restore_folders:
            src = backup_path / name
            dest = folder_map.get(name)

            if not src.exists() or dest is None:
                logger.warning(f"Pominięto {name} – brak źródła lub ścieżki docelowej.")
                continue

            try:
                if name == "Baza danych":
                    # zawsze przywracamy konkretny plik DATABASE.db
                    src_file = backup_path / DB_FILE
                    if not src_file.exists():
                        logger.warning(f"Brak pliku bazy danych w backupie: {src_file}")
                        continue

                    if dest.is_dir():
                        db_dest = dest / DB_FILE
                    else:
                        db_dest = dest

                    shutil.copy2(src_file, db_dest)
                    restored_paths[name] = db_dest
                    logger.info(f"Przywrócono bazę danych z backupu: {db_dest}")

                else:
                    # Przywracanie folderów
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(src, dest)
                    restored_paths[name] = dest
                    logger.info(f"Przywrócono {name} z backupu: {dest}")

            except Exception as e:
                logger.error(f"Błąd przy przywracaniu {name}: {e}")

        return restored_paths


file_manager = FileManager()


if __name__ == '__main__':
        # Konfiguracja loggingu
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        #manager = FileManager()
        #manager.print_info()