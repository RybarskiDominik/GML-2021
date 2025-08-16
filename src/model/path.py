from pathlib import Path
import tempfile
import logging
import sys


logger = logging.getLogger(__name__)


class PathManager:
    def __init__(self):
        if getattr(sys, 'frozen', False):
           self.base_path = Path(sys.executable).parent
        else:
            self.base_path = Path(sys.path[0])

        if not self._has_write_permissions(self.base_path):
            # print("Insufficient permissions in base path. Using a temporary directory.")
            temp_dir = Path(tempfile.gettempdir()) / "GMLReader"
            temp_dir.mkdir(parents=True, exist_ok=True)
            self.relative_path = temp_dir
        else:
            self.relative_path = self.base_path

        # Relative path
        self.templates_folder_path = self.relative_path / "DOCX"
        self.docx_notification_folder_path = self.relative_path / "DOCX" / "Zawiadomienia"
        self.gml_folder_path = self.relative_path / "GML"
        self.log_file_path = self.relative_path / "log.log"
        self.gml_file_path = self.relative_path / "GML" / "Parsed_GML.gml"
        self.data_base_file_path = self.relative_path / "GML" / "GML_DataBase.pkl"
        self.xlsx_target_path = self.relative_path / "GML" / "GML.xlsx"

        # Base folder path
        self.icons_path = self.base_path / 'Icons'
        self.stylesheets_path = self.base_path / 'gui' / 'Stylesheets' / 'images_dark-light'
        self.stylesheets_folder_path = self.base_path / 'gui' / "Stylesheets"

    def get_base_path(self):
        return str(self.base_path)

    def get_log_file_path(self):
        return str(self.log_file_path)

    def get_gml_file_path(self):
        return str(self.gml_file_path)
    
    def get_data_base_file_path(self):
        return Path(self.data_base_file_path)
    
    def get_gml_folder_path(self):
        return str(self.gml_folder_path)

    def get_docx_folder_path(self):
        return str(self.templates_folder_path)
    
    def get_docx_notification_folder_path(self):
        return str(self.docx_notification_folder_path)
    
    def get_xlsx_target_path(self):
        return str(self.xlsx_target_path)

    def get_icons_path(self, icon_name):
        return str(self.icons_path / icon_name)
    
    def get_stylesheets_folder_path(self, icon_name):
        return str(self.stylesheets_folder_path / icon_name)

    def get_stylesheets_path(self, icon_name):
        return str(self.stylesheets_path / icon_name)


    def _has_write_permissions(self, path):
        """Check if the script has write permissions for the given path."""
        try:
            test_file = path / ".test_permission"
            with open(test_file, 'w') as f:
                f.write("test_permission")
            test_file.unlink()  # Remove test file
            return True
        except (PermissionError, IOError):
            return False


if __name__ == '__main__':
    pass