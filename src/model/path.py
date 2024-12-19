from pathlib import Path
import sys
import logging

logger = logging.getLogger(__name__)


class PathManager:
    def __init__(self):
        if getattr(sys, 'frozen', False):
           self.base_path = Path(sys.executable).parent
        else:
            self.base_path = Path(sys.path[0])

        self.log_file_path = self.base_path / "log.log"
        self.gml_file_path = self.base_path / "GML" / "Parsed_GML.gml"
        self.gml_folder_path = self.base_path / "GML"
        self.docx_folder_path = self.base_path / "DOCX"
        self.xlsx_target_path = self.base_path / "GML" / "GML.xlsx"
        self.stylesheets_path = self.base_path / 'gui' / 'Stylesheets' / 'images_dark-light'
        self.stylesheets_folder_path = self.base_path / 'gui' / "Stylesheets"
        self.icons_path = self.base_path / 'Icons'

    def get_base_path(self):
        return str(self.base_path)

    def get_log_file_path(self):
        return str(self.log_file_path)

    def get_gml_file_path(self):
        return str(self.gml_file_path)
    
    def get_gml_folder_path(self):
        return str(self.gml_folder_path)

    def get_docx_folder_path(self):
        return str(self.docx_folder_path)
    
    def get_xlsx_target_path(self):
        return str(self.xlsx_target_path)

    def get_icons_path(self, icon_name):
        return str(self.icons_path / icon_name)
    
    def get_stylesheets_folder_path(self, icon_name):
        return str(self.stylesheets_folder_path / icon_name)

    def get_stylesheets_path(self, icon_name):
        return str(self.stylesheets_path / icon_name)


if __name__ == '__main__':
    # Przykład użycia
    manager = PathManager()
    print(manager.get_gml_file_path())