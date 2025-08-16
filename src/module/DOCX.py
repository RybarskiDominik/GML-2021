from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QPushButton,
    QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QMessageBox,
    QLabel, QHeaderView, QFileDialog, QComboBox, QSpacerItem,
    QSizePolicy, QMenu
)
from PySide6.QtGui import QStandardItem, QStandardItemModel, QCursor
from PySide6.QtCore import QSettings, Qt, Signal
from PySide6 import QtCore
from model.DOCX_processing import select_folder_and_process
from function.FileMenager import FileManager
file_management = FileManager()
import pandas as pd

import os, sys, json, logging

logger = logging.getLogger(__name__)

class DataFrameTableModel(QStandardItemModel):
    send_dict = Signal(object)
    def __init__(self, df=None):
        super().__init__()
        self._df = df #if df is not None else pd.DataFrame(columns=["Name", "Tag", "Data"])
        #self.history = [self._df.copy()]
        self.default_df = None
        self.history = []
        self.add_to_history_flag = False
        self.add_default_value = False

        self.itemChanged.connect(self.on_item_changed)

        self.update_view()

    def update_view(self):
        """Synchronize the view with the DataFrame."""
        if self._df is None:
            self._df = pd.DataFrame(columns=['Name', 'Tag', 'Data'])

        self.clear()
        self.setHorizontalHeaderLabels(self._df.columns.tolist())
        self.setRowCount(len(self._df))
        self.setColumnCount(len(self._df.columns))

        for row in range(len(self._df)):
            for col in range(len(self._df.columns)):
                value = self._df.iat[row, col]
                self.setItem(row, col, QStandardItem(str(value)))
        
        if not self.add_to_history_flag:
            self.add_to_history()  # Only add to history when it's not an undo action
        else:
            self.add_to_history_flag = False  # Reset the flag after adding history

    def add_to_history(self):
        """Add current state of the DataFrame to history."""
        self.history.append(self._df.copy())
        #print(self.history)

    def undo(self):
        """Undo the last change by reverting to the previous DataFrame."""

        if len(self.history) > 1:
            self.history.pop()  # Usuwamy ostatnią wersję
            self._df = self.history[-1].copy()  # Przywracamy poprzednią wersję
            self.add_to_history_flag = True
            self.update_view()  # Aktualizujemy widok
        else:
            QMessageBox.warning(None, "Error", "No more changes to undo.")

    def add_row(self, name, tag):
        """Add a new tag to the table."""

        if tag in self._df["Tag"].values:
            QMessageBox.warning(None, "Error", f"Tag '{tag}' already exists.")
            return

        new_row = pd.DataFrame([[name, tag, ""]], columns=self._df.columns)
        self._df = pd.concat([self._df, new_row], ignore_index=True)
        self.add_to_history_flag = True
        self.update_view()

    def on_item_changed(self, item):
        if self.add_default_value and not self.add_to_history_flag:
            row = item.row()
            col = item.column()
            value = item.text()
            self._df.iat[row, col] = value
            self.add_to_history()
            self.send_dictionary()
            #print(f"Changed row {row}, column {col} to {value}")

    def add_default_df(self, default_df):
        """Set the default values for the DataFrame."""
        self.default_df = default_df.copy()
        self._df = default_df.copy()
        self.history.clear()  # Clear history
        #self.add_to_history()  # Add the default state to history
        self.update_view()
        self.add_default_value = True
        #self.send_dictionary()

    def reset_to_default(self):
        """Reset the DataFrame to its default state."""
        if self.default_df is not None:
            self._df = self.default_df.copy()
            self.add_to_history_flag = True
            self.update_view()
        else:
            QMessageBox.warning(None, "Error", "Default values not set.")

    def remove_row(self, tag):
        """Remove a row with a given tag."""
        if tag not in self._df["Tag"].values:
            QMessageBox.warning(None, "Error", f"Tag '{tag}' not found.")
            return

        self._df = self._df[self._df["Tag"] != tag].reset_index(drop=True)
        self.add_to_history_flag = True
        self.update_view()

    def flags(self, index):
        """Override to make the first column non-editable."""
        
        if index.column() == 0 or index.column() == 1:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable  # Disable editing for the first column
        else:
            return super().flags(index)  # Keep default behavior for other columns

    def resize_columns(self, table_view):
        """Method to resize columns based on their index."""
        header = table_view.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Resize first column (Tag) to fit contents
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Resize first column (Tag) to fit contents
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Stretch second column (Data) to take the remaining space

    def get_dataframe(self):
        """Return the current DataFrame."""
        return self._df

    def send_dictionary(self):
        df = self.get_dataframe()
        dictionaries = {}
        for _, row in df.iterrows():
            dictionaries[row.iloc[1]] = row.iloc[2]
        self.send_dict.emit(dictionaries)
        #print(dictionaries)
        return dictionaries

class DOCX(QMainWindow):
    def __init__(self, Path=None):
        super().__init__()
        self.dict = None
        self.resize(650, 735)
        self.setBaseSize(650, 735)

        self.Path = file_management.templates_folder_path
        self.setWindowTitle("Tag Data Manager")

        self.df = pd.DataFrame()
        self.settings = QSettings('GML', 'GML Reader')

        if self.settings.value('DefaultListTAG', None, type=bool) == True:
            data = self.settings.value('ListTAG')
            self.df = pd.DataFrame(data, columns=["Name", "Tag", "Data"])
        else:
            self.df = self.default_list()

        # Create main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(1, 2, 1, 1)
        #layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Input fields for adding a tag
        self.main_docx_path = QComboBox(self)
        self.main_docx_path.setFixedWidth(155)
        self.main_docx_path.addItem("Select path to docx files")  # Add default item
        self.main_docx_path.setToolTip("Folder nadrzędny, w którym są umieszczone foldery podrzędne z plikami *.DOCX")
        
        if self.settings.value('DocxPath') is not None:
            self.Path = self.settings.value('DocxPath')
            self.set_folder_name_in_QComboBox(self.Path)
        elif self.Path is not None:
            self.set_folder_name_in_QComboBox(self.Path)

        self.edit_main_docx_path = QPushButton("DOCX")
        #self.edit_main_docx_path.setFixedHeight(26)
        self.edit_main_docx_path.setFixedWidth(45)
        self.edit_main_docx_path.setToolTip("Można wybrać własną ścieżkę do folderów z plikami *.DOCX")
        self.edit_main_docx_path.clicked.connect(self.edit_path)

        self.reset_main_docx_path = QPushButton("Reset")
        #self.reset_main_docx_path.setFixedHeight(26)
        self.reset_main_docx_path.setFixedWidth(40)
        self.reset_main_docx_path.setToolTip("Resetuje ścieżkę do plików *.DOCX")
        self.reset_main_docx_path.clicked.connect(self.reset_path)

        self.import_button = QPushButton("Import")
        self.import_button.setFixedWidth(50)
        self.import_button.setToolTip("Importuje TAGI")
        self.import_button.clicked.connect(self.import_dict)
        self.import_button

        self.export_button = QPushButton("Export")
        self.export_button.setFixedWidth(50)
        self.export_button.setToolTip("Exportuje TAGI")
        self.export_button.clicked.connect(self.export_dict)

        self.save_button = QPushButton("Save")
        self.save_button.setFixedWidth(40)
        self.save_button.setToolTip("Zapiszuje obecne dane z tabeli do pamięci.")
        self.save_button.clicked.connect(self.save_list)

        self.reset_button = QPushButton("default")
        self.reset_button.setFixedWidth(50)
        self.reset_button.setToolTip("Resetuje dane w tabeli.")
        self.reset_button.clicked.connect(self.reset_list)

        self.undo_button = QPushButton("Undo")
        #self.undo_button.setDisabled(True)
        self.undo_button.setFixedWidth(40)
        self.undo_button.clicked.connect(self.undo_change)
        self.undo_button.setToolTip("Eksperymentalna funkcja")

        self.modify_button = QPushButton("Modify DOCX")
        self.modify_button.setFixedWidth(80)
        self.modify_button.setToolTip("""Modyfikuje pliki *.DOCX w oparciu o dane w tabeli.
                                      Należy podać ścieżkę do miejsca zapisu zmodyfikowanych plików *.DOCX""")
        self.modify_button.clicked.connect(self.modify_docx)
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.main_docx_path)
        input_layout.addWidget(self.edit_main_docx_path)
        input_layout.addWidget(self.reset_main_docx_path)
        input_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        input_layout.addStretch(1)
        input_layout.addWidget(self.import_button)
        input_layout.addWidget(self.export_button)
        input_layout.addWidget(self.save_button)
        input_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        input_layout.addWidget(self.reset_button)
        input_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        input_layout.addStretch(1)
        input_layout.addWidget(self.undo_button)
        input_layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        input_layout.addStretch(1) 
        input_layout.addWidget(self.modify_button)
        layout.addLayout(input_layout)

        # Create table view
        self.table_model = DataFrameTableModel()
        self.table_model.add_default_df(self.df)

        self.dict = self.table_model.send_dictionary()

        self.table_view = QTableView()
        self.table_view.setModel(self.table_model)
        #self.table_view.setEditTriggers(QTableView.DoubleClicked)
        self.table_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.context_menu)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.table_view)


        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter new Name")
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Enter new tag")
        self.add_button = QPushButton("Add Tag")
        self.add_button.clicked.connect(self.add_tag)
        self.remove_button = QPushButton("Remove Tag")
        self.remove_button.clicked.connect(self.remove_tag)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.name_input)
        input_layout.addWidget(self.tag_input)
        input_layout.addWidget(self.add_button)
        input_layout.addWidget(self.remove_button)
        layout.addLayout(input_layout)
        # Main widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.table_model.resize_columns(self.table_view)

    def set_folder_name_in_QComboBox(self, path_to_folder):
        # Clear the QComboBox
        self.main_docx_path.clear()
        
        # Check if the path exists and is a directory
        if os.path.isdir(path_to_folder):
            # Get a list of all subfolders in the path
            subfolders = [folder_name for folder_name in os.listdir(path_to_folder) 
                        if os.path.isdir(os.path.join(path_to_folder, folder_name))]
            
            # Add each folder to the QComboBox
            for folder_name in subfolders:
                full_path = os.path.join(path_to_folder, folder_name)
                self.main_docx_path.addItem(folder_name, full_path)
            # Optionally set the first folder as the current text, if any exist
            if subfolders:
                self.main_docx_path.setCurrentText(subfolders[0])
        else:
            # Handle case where the provided path is not valid
            self.main_docx_path.addItem("Invalid Path")
            self.main_docx_path.setCurrentText("Invalid Path")

    def edit_path(self):
        try:
            path_to_folder = QFileDialog.getExistingDirectory(self, "Select Folder", str(self.Path))
        except:
            path_to_folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        
        if not path_to_folder:
            return

        self.settings.setValue("DocxPath", path_to_folder)
        self.Path = path_to_folder
        self.set_folder_name_in_QComboBox(path_to_folder)

    def reset_path(self):
        self.Path = file_management.templates_folder_path
        self.settings.setValue("DocxPath", self.Path)
        self.main_docx_path.clear()
        self.set_folder_name_in_QComboBox(self.Path)

    def add_tag(self):
        """Handle adding a new tag."""
        name = self.name_input.text().strip()
        tag = self.tag_input.text().strip()
        if not tag:
            QMessageBox.warning(self, "Error", "Tag cannot be empty.")
            return

        self.table_model.add_row(name ,tag)
        self.table_model.resize_columns(self.table_view)

        self.name_input.clear()
        self.tag_input.clear()

    def remove_tag(self):
        tag = self.tag_input.text().strip()

        if not tag:
            QMessageBox.warning(self, "Error", "Tag cannot be empty.")
            return

        self.table_model.remove_row(tag)
        self.tag_input.clear()
        self.table_model.resize_columns(self.table_view)

    def undo_change(self):
            """Handle undoing the last change."""
            self.table_model.undo()
            self.table_model.resize_columns(self.table_view)

    def modify_docx(self):
        current_index = self.main_docx_path.currentIndex()
        path = self.main_docx_path.itemData(current_index)

        self.df = self.table_model.get_dataframe()
        dictionaries = {}
        for _, row in self.df.iterrows():
            dictionaries[row.iloc[1]] = row.iloc[2]
        
        result = select_folder_and_process(path_to_docx=path, data=dictionaries)
        if result == 0:
            logging.error("ERROR on modify docx.")

    def import_dict(self):
        """Import a dictionary and update the table model."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Dictionary File", "", "JSON Files (*.json);;All Files (*)")
        if not file_name:
            return

      
        with open(file_name, "r", encoding="utf-8") as f:
            imported_data = json.load(f)

        # Create a DataFrame from the imported data
        new_data = [(entry.get("Name", ""), entry.get("Tag", ""), entry.get("Data", "")) for entry in imported_data]
        self.df = pd.DataFrame(new_data, columns=["Name", "Tag", "Data"])
        self.table_model._df = self.df
        self.table_model.update_view()
        
        self.table_model.resize_columns(self.table_view)

    def export_dict(self):
        """Export the current data to a JSON file."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Dictionary File", "", "JSON Files (*.json);;All Files (*)")
        if not file_name:
            return

        try:
            self.df = self.table_model.get_dataframe()
            data_list = [{"Name": row["Name"], "Tag": row["Tag"], "Data": row["Data"]} for _, row in self.df.iterrows()]

            with open(file_name, "w", encoding="utf-8") as f:  # Save the data to a file
                json.dump(data_list, f, ensure_ascii=False, indent=4)

        except Exception as e:
            logging.exception(e)
            print(e)
            QMessageBox.warning(self, "Error", f"Failed to export dictionary: {e}")

    def save_list(self):
        self.df = self.table_model.get_dataframe()
        data_list = [{"Name": row["Name"], "Tag": row["Tag"], "Data": row["Data"]} for _, row in self.df.iterrows()]
        self.settings.setValue("DefaultListTAG", True)
        self.settings.setValue("ListTAG", data_list)

    def default_list(self):
        data = [
        (('Numer działki'),'NR_DZIALKI', ''),
        (('KW'),'KW', ''),
        (('Identyfikator'),'IDENTYFIKATOR', ''),
        
        (('Województwo'),'WOJ', ''),
        (('Powiat'),'POW', ''),
        (('Jed. ewid.'),'JEWID', ''),
        (("ID Jed. ewid."),'JEWID_ID', ''),
        (("Obręb"),'OBR', ''),
        (("ID Obrębu"),'OBR_ID', ''),

        (('Arkusz'),'ARKUSZ', ''), 
        (('Punkt osnowy nr 1'),'OSN1', ''), 
        (('Punkt osnowy nr 2'),'OSN2', ''), 

        (('Data sporządzenia'),'DATA', ''),
        #(('Data z czynności'),'DATA_C', ''),

        (('Cel pracy'),'CEL', ''),
        (('Wykonawca'),'WYKONAWCA', ''),
        (('Kierownik'),'KIEROWNIK', ''),
        (('Nr upr. kierownika'),'KIEROWNIK_UPR', ''),
        (('Uczestnik prac'),'UPRAC', ''),
        (('Termin rozpoczęcia'),'TERMIN_R', ''),
        (('Termin zakończenia'),'TERMIN_Z', ''),
        ]
        self.df = pd.DataFrame(data, columns=["Name", "Tag", "Data"])
        return self.df

    def reset_list(self):
        self.table_model._df = self.default_list()
        self.table_model.update_view()
        
        self.table_model.resize_columns(self.table_view)

        self.settings.setValue("DefaultListTAG", False)
        print("Reset")


    def context_menu(self, pos):
        context_menu = QMenu(self)

        copy_action = context_menu.addAction("Kopiuj")
        copy_action.triggered.connect(self.copy_to_clipboard)

        paste_action = context_menu.addAction("Wklej")
        paste_action.triggered.connect(self.paste_from_clipboard)

        context_menu.exec(QCursor.pos())

    def copy_to_clipboard(self):
        selection_model = self.table_view.selectionModel()
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

            copied_data += self.table_view.model().data(index)
            if index.column() < self.table_view.model().columnCount() - 1:
                copied_data += '\t'  # Tab delimiter between columns

        clipboard = QApplication.clipboard()
        clipboard.setText(copied_data)

        print("Copy data complete.")

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if not text:
            print("No data in clipboard.")
            return

        rows = text.split('\n')
        data = [row.split('\t') for row in rows if row]

        selection_model = self.table_view.selectionModel()
        indexes = selection_model.selectedIndexes()

        if not indexes:
            QMessageBox.warning(self, "Paste Error", "Please select a starting cell.")
            return

        start_row = indexes[0].row()
        start_col = indexes[0].column()

        model = self.table_view.model()

        for r, row_data in enumerate(data):
            for c, value in enumerate(row_data):
                model_index = model.index(start_row + r, start_col + c)
                if model_index.isValid() and model.flags(model_index) & Qt.ItemIsEditable:
                    model.setData(model_index, value)


if __name__ == "__main__":
    pass