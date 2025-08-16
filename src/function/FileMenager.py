from PySide6.QtWidgets import QMessageBox, QApplication, QInputDialog
from PySide6.QtCore import QSettings
from pathlib import Path
import tempfile
import logging
import shutil
import sys
import os


logger = logging.getLogger(__name__)
settings = QSettings('File', 'File Manager')


import sys
import tempfile
import platform
from pathlib import Path


class FileManager:
    def __init__(self):
        self.workspace_folder_name = "Obszar_roboczy"

        self.base_path = self._determine_base_path()
        self.default_workspace_root_dir = self._get_default_dir()

        saved_workspace_path = settings.value("workspace_path", type=str)
        if saved_workspace_path:
            self.current_workspace_dir = Path(saved_workspace_path).expanduser().resolve()
            logger.info(f"Załadowano zapisany obszar roboczy: {self.current_workspace_dir}")
            #print(f"Załadowano zapisany obszar roboczy: {self.current_workspace_dir}")
        else:
            self.current_workspace_dir = self.default_workspace_root_dir / self.workspace_folder_name
            logger.info(f"Użyto domyślnego obszaru roboczego: {self.current_workspace_dir}")
            #print(f"Użyto domyślnego obszaru roboczego: {self.current_workspace_dir}")

        self._set_base_app_path()
        self._set_base_workspace_root_dir()

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

    def _set_base_app_path(self):
        self.icons_path = self.default_workspace_root_dir / 'Icons'
        self.log_file_path = self.default_workspace_root_dir / "log.log"
        self.stylesheets_path = self.default_workspace_root_dir / 'gui' / 'Stylesheets' / 'images_dark-light'
        self.stylesheets_folder_path = self.default_workspace_root_dir / 'gui' / "Stylesheets"

    def _set_base_workspace_root_dir(self):
        self.current_workspace_dir.mkdir(parents=True, exist_ok=True)

        saved_docx_path = settings.value("templates_folder_path ", type=str)
        if saved_docx_path:
            self.templates_folder_path  = Path(saved_docx_path).expanduser().resolve()
        else:
            self.templates_folder_path  = self.current_workspace_dir / "Formatki"

        self.templates_notification_folder_path = self.templates_folder_path  / "Zawiadomienia"
        self.operaty_folder_path = self.current_workspace_dir / "Operaty"
        self.gml_folder_path = self.current_workspace_dir / "GML"

        self.gml_file_path = self.gml_folder_path / "Parsed_GML.gml"
        self.data_base_file_path = self.gml_folder_path / "GML_DataBase.pkl"
        self.xlsx_target_path = self.gml_folder_path / "GML.xlsx"
        
        self.check_workspace_structure()


    def check_workspace_structure(self):
        """Ensure the workspace folder structure exists."""
        folders_to_create = [
            (self.operaty_folder_path, "Operaty"),
            (self.gml_folder_path, "GML"),
            (self.templates_folder_path , "Formatki")
        ]

        for folder_path, folder_name in folders_to_create: # mainfolders
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Folder {folder_name} istnieje lub został utworzony: {folder_path}")
            except Exception as e:
                logging.exception(e)
        
        try: # subfolders
            self.templates_folder_path .mkdir(parents=True, exist_ok=True)
            self.templates_notification_folder_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.exception(e)

        
        try: # subfolders
            subfolders = ['Budynek', 'MDCP', 'Podział', 'Wznowienie-Wyznaczenie-Ustalenie']
            for name in subfolders:
                path = self.templates_folder_path  / name
                path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Podfolder Formatki istnieje lub został utworzony: {path}")
        except Exception as e:
            logging.exception(e)

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

    def logger_info(self):
        info_lines = [
            "\n=== FileManager Info ===",
            f"Workspace folder name:          {self.workspace_folder_name}",
            f"Base application path:          {self.base_path}",
            f"Default workspace root dir:     {self.default_workspace_root_dir}",
            f"Icons directory:                {self.icons_path}",
            f"Log file path:                  {self.log_file_path}",
            f"Stylesheets folder:             {self.stylesheets_folder_path}",
            f"Stylesheet images path:         {self.stylesheets_images_path}",
            f"Current workspace directory:    {self.current_workspace_dir}",
            f"GML folder path:                {self.gml_folder_path}",
            f"Formatki folder path:           {self.templates_folder_path}",
            f"Formatki pow. folder path:      {self.templates_notification_folder_path}",
            f"Operaty folder path:            {self.operaty_folder_path}",
            f"GML parsed file path:           {self.gml_file_path}",
            f"GML database file path:         {self.data_base_file_path}",
            f"GML Excel export path:          {self.xlsx_target_path}",
            "========================\n"
        ]

        for line in info_lines:
            logger.info(line)

    def print_info(self):
        """Wyświetla informacje o konfiguracji FileManager."""
        print("\n=== FileManager Information ===")
        print()
        print(f"Workspace folder name:          {self.workspace_folder_name}")
        print()
        print(f"Base application path:          {self.base_path}")
        print(f"Default workspace root dir:     {self.default_workspace_root_dir}")
        print()
        print(f"Icons directory:                {self.icons_path}")
        print(f"Log file path:                  {self.log_file_path}")
        print(f"Stylesheets folder:             {self.stylesheets_folder_path}")
        print(f"Stylesheet images path:         {self.stylesheets_path}")
        print()
        print(f"Current workspace directory:    {self.current_workspace_dir}")
        print()
        print(f"GML folder path:                {self.gml_folder_path}")
        print(f"Formatki folder path:           {self.templates_folder_path }")
        print(f"Formatki pow. folder path:      {self.templates_notification_folder_path }")
        print(f"Operaty folder path:            {self.operaty_folder_path}")
        print(f"GML parsed file path:           {self.gml_file_path}")
        print(f"GML database file path:         {self.data_base_file_path}")
        print(f"GML Excel export path:          {self.xlsx_target_path}")
        print("===================================\n")


    def set_custom_docx_path(self, path: Path):
        path = Path(path).expanduser().resolve()
        self.templates_folder_path  = path
        self.templates_notification_folder_path = self.templates_folder_path  / "Zawiadomienia"

        settings.setValue("templates_folder_path ", str(self.templates_folder_path ))
        self.check_workspace_structure()

    def reset_docx_path(self):
        settings.remove("templates_folder_path ")
        self.templates_folder_path  = self.current_workspace_dir / "Formatki"
        self.templates_notification_folder_path = self.templates_folder_path  / "Zawiadomienia"

        self.templates_folder_path .mkdir(parents=True, exist_ok=True)
        self.templates_notification_folder_path.mkdir(parents=True, exist_ok=True)

        settings.setValue("templates_folder_path ", str(self.templates_folder_path ))
        self.check_workspace_structure()

    def set_new_workspace_path(self, path: Path):
        """Zmień ścieżkę do obszaru roboczego i zapisz ją w ustawieniach."""
        path = Path(path).expanduser().resolve()
        self.current_workspace_dir = path
        settings.setValue("workspace_path", str(path))
        logger.info(f"Zmieniono obszar roboczy na: {self.current_workspace_dir}")
        self._set_base_workspace_root_dir()

    def reset_workspace_path(self):
        """Resetuje ścieżkę do domyślnego obszaru roboczego i usuwa zapisany path."""
        settings.remove("workspace_path")  # Usuwa zapisany path
        logger.info(f"Zresetowano obszar roboczy do: {self.current_workspace_dir}")
        self.current_workspace_dir = self.default_workspace_root_dir / self.workspace_folder_name
        self._set_base_workspace_root_dir()

    def move_workspace_path(self, new_path: Path):
        """Przenosi dane ze starego workspace do nowego, pytając o kolizje przez GUI."""
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

#file_manager = FileManager()

if __name__ == '__main__':
    pass