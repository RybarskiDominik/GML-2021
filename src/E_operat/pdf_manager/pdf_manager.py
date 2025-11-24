import os, sys, json, subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QFileDialog, QTableView, QMessageBox
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer

# Importy dla łączenia PDF
try:
    import pikepdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class FileItem:
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.size = os.path.getsize(path)
        self.type = self._get_type()
        self.to_pdf = False

    def _get_type(self):
        import mimetypes
        type_, _ = mimetypes.guess_type(self.path)
        return type_ or "Unknown"

    def is_pdf(self):
        """Sprawdza czy plik jest PDF"""
        return self.path.lower().endswith('.pdf') or self.type == 'application/pdf'

    def to_list(self):
        return [self.name, round(self.size / (1024 * 1024), 2), self.type, self.to_pdf]


class FileTableModel(QAbstractTableModel):
    HEADERS = ["Nazwa", "Rozmiar (MB)", "Typ", "Do PDF"]

    def __init__(self, files=None, parent_view=None, json_path=None):
        super().__init__()
        self._files = files or []
        self.parent_view = parent_view
        self._sort_order = None  # None, 'asc', 'desc'
        self.json_path = json_path

    def rowCount(self, parent=QModelIndex()):
        return len(self._files)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        file = self._files[index.row()]

        if role == Qt.DisplayRole:
            if index.column() == 1:
                size_mb = file.size / (1024 * 1024)
                return f"{size_mb:.2f}"
            elif index.column() == 0:
                return file.name
            elif index.column() == 2:
                return file.type
            elif index.column() == 3:
                return ""  # Nie wyświetlaj tekstu w kolumnie checkbox
        
        if role == Qt.CheckStateRole and index.column() == 3:
            result = Qt.Checked if file.to_pdf else Qt.Unchecked
            return result
        
        if role == Qt.UserRole:
            return file.path
        
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        if index.column() == 3 and role == Qt.CheckStateRole:
            file = self._files[index.row()]
            old_value = file.to_pdf

            new_value = (value == Qt.Checked.value) 

            file.to_pdf = new_value
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])

            if self.json_path:
                print(1)
                self.save_to_json(self.json_path)

            return True

        return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            header_text = self.HEADERS[section]
            if section == 0:  # Kolumna "Nazwa"
                if self._sort_order == 'asc':
                    header_text += " ↑"
                elif self._sort_order == 'desc':
                    header_text += " ↓"
            return header_text
        return super().headerData(section, orientation, role)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsDropEnabled
        
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        
        if index.column() == 3:
            flags |= Qt.ItemIsUserCheckable
        
        return flags

    def supportedDropActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        return ['application/x-qabstractitemmodeldatalist']

    def insertRows(self, row, count, parent=QModelIndex()):
        return super().insertRows(row, count, parent)

    def add_files(self, file_items: list):
        row = self.rowCount()
        self.beginInsertRows(QModelIndex(), row, row + len(file_items) - 1)
        self._files.extend(file_items)
        self.endInsertRows()

    def moveRowUp(self, row):
        if row <= 0 or row >= len(self._files):
            return
        self.beginMoveRows(QModelIndex(), row, row, QModelIndex(), row - 1)
        self._files[row - 1], self._files[row] = self._files[row], self._files[row - 1]
        self.endMoveRows()

    def moveRowDown(self, row):
        if row < 0 or row >= len(self._files) - 1:
            return
        self.beginMoveRows(QModelIndex(), row, row, QModelIndex(), row + 2)
        self._files[row + 1], self._files[row] = self._files[row], self._files[row + 1]
        self.endMoveRows()

    def sort_by_name(self, ascending=True):
        """Sortuje pliki po nazwie"""
        if not self._files:
            return
        
        self.beginResetModel()
        self._files.sort(key=lambda file: file.name.lower(), reverse=not ascending)
        self._sort_order = 'asc' if ascending else 'desc'
        self.endResetModel()

    def toggle_sort_by_name(self):
        """Przełącza sortowanie po nazwie: None -> asc -> desc -> asc..."""
        if self._sort_order is None or self._sort_order == 'desc':
            self.sort_by_name(ascending=True)
        else:
            self.sort_by_name(ascending=False)


    def dropMimeData(self, data, action, row, column, parent):
        if action == Qt.IgnoreAction:
            return False

        if not self.parent_view:
            return False

        selected_rows = sorted({i.row() for i in self.parent_view.selectedIndexes()})
        if not selected_rows:
            return False

        # Obsługa pustego miejsca (np. rzucono po prawej stronie kolumny)
        if parent.isValid():
            drop_row = parent.row()
        else:
            drop_row = self.rowCount()

        # Jeśli przeciągnięcie do tego samego miejsca — anuluj
        if drop_row in selected_rows or drop_row == selected_rows[-1] + 1:
            return False

        # Wyciągnij elementy z listy (musimy zachować kolejność)
        moving_items = [self._files[i] for i in selected_rows]

        # Usuń je z oryginalnych pozycji
        for i in reversed(selected_rows):
            self._files.pop(i)

        # Dostosuj pozycję docelową po usunięciu elementów przed nią
        if drop_row > selected_rows[-1]:
            drop_row -= len(selected_rows)

        # Wstawiamy wszystkie przenoszone elementy w nowym miejscu
        self.beginResetModel()
        for i, item in enumerate(moving_items):
            self._files.insert(drop_row + i, item)
        self.endResetModel()

        # Zaznacz ponownie przeniesione wiersze
        self.parent_view.clearSelection()
        for i in range(drop_row, drop_row + len(moving_items)):
            self.parent_view.selectRow(i)

        return True


    def dropMimeData_old(self, data, action, row, column, parent):
        if action == Qt.IgnoreAction:
            return False

        if not self.parent_view:
            return False

        selected_indexes = self.parent_view.selectedIndexes()
        if not selected_indexes:
            return False

        source_row = selected_indexes[0].row()

        # Obsługa pustego miejsca (np. rzucono po prawej stronie kolumny)
        if parent.isValid():
            row = parent.row()
        else:
            row = self.rowCount()

        # Nie pozwalamy przenieść do tej samej pozycji
        if row == source_row: # or row == source_row + 1:
            return False

        # Qt wymaga destination_row + 1 przy przenoszeniu w dół
        if row > source_row:
            destination_row = row + 1
            insert_pos = row
        else:
            destination_row = row
            insert_pos = row


        if destination_row > self.rowCount():
            destination_row = self.rowCount()
            
        if row == destination_row and source_row == destination_row - 1:
            return False

        self.beginMoveRows(QModelIndex(), source_row, source_row, QModelIndex(), destination_row)
        item = self._files.pop(source_row)
        self._files.insert(insert_pos, item)
        self.endMoveRows()

        self.parent_view.selectRow(insert_pos)
        return True


    def get_pdf_files(self):
        """Zwraca listę plików PDF w kolejności z tabeli, które mają zaznaczony checkbox 'Do PDF'"""
        return [file for file in self._files if file.is_pdf() and file.to_pdf]

    def save_to_json(self, json_path=None):
        json_path = json_path or self.json_path or "file_list.json"
        data = [{"path": f.path, "to_pdf": f.to_pdf} for f in self._files]
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True, f"Zapisano listę plików do {json_path}"
        except Exception as e:
            return False, str(e)

    def load_from_json(self, json_path=None):
        """Wczytuje listę plików z JSON w folderze self.path lub podanym json_path"""
        json_path = json_path or getattr(self, "json_path", None) or "file_list.json"
        
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            items = []
            for entry in data:
                path = entry.get("path")
                if not path or not os.path.exists(path):
                    continue  # pomijamy brakujące pliki
                file_item = FileItem(path)
                file_item.to_pdf = entry.get("to_pdf", False)
                items.append(file_item)

            if items:
                self.beginResetModel()
                self._files = items
                self.endResetModel()
                return True, f"Wczytano {len(items)} plików z {json_path}"
            else:
                return False, "Nie udało się wczytać żadnych plików."

        except FileNotFoundError:
            return False, f"Plik {json_path} nie istnieje."
        except Exception as e:
            return False, str(e)


class FileListView(QTableView):
    def __init__(self):
        super().__init__()
        #self.setEditTriggers(QTableView.CurrentChanged)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTableView.InternalMove)
        self.setSelectionBehavior(QTableView.SelectRows)
        #self.setSelectionMode(QTableView.SingleSelection)
        self.setSelectionMode(QTableView.ExtendedSelection)
        self.setDropIndicatorShown(True)
        
        # Podłączenie sygnału kliknięcia w nagłówek
        self.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
    
    def on_header_clicked(self, logical_index):
        """Obsługuje kliknięcie w nagłówek kolumny"""
        if logical_index == 0:  # Kolumna "Nazwa"
            self.model().toggle_sort_by_name()


class PDF(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lista Plików z Drag&Drop")
        self.resize(700, 400)

        self.click_timer = QTimer(self)
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.perform_single_click)

        self.pending_index = None

        self.view = FileListView()
        self.model = FileTableModel(parent_view=self.view)
        self.view.setModel(self.model)
        self.view.clicked.connect(self.on_clicked)
        self.view.doubleClicked.connect(self.on_double_click)

        self.btn_add = QPushButton("Dodaj pliki")
        self.btn_up = QPushButton("↑ Góra")
        self.btn_down = QPushButton("↓ Dół")
        self.btn_print = QPushButton("Print zaznaczony")
        self.btn_merge_pdf = QPushButton("Połącz PDF")

        self.btn_add.clicked.connect(self.add_files)
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down.clicked.connect(self.move_down)
        self.btn_print.clicked.connect(self.print_selected_row)
        self.btn_merge_pdf.clicked.connect(self.merge_pdf_files)

        # Sprawdź czy pikepdf jest dostępne
        if not PDF_AVAILABLE:
            self.btn_merge_pdf.setEnabled(False)
            self.btn_merge_pdf.setToolTip("pikepdf nie jest zainstalowane. Użyj: pip install pikepdf")

        layout_btn = QHBoxLayout()
        layout_btn.addWidget(self.btn_add)
        layout_btn.addWidget(self.btn_print)
        layout_btn.addWidget(self.btn_merge_pdf)
        layout_btn.addStretch()
        layout_btn.addWidget(self.btn_up)
        layout_btn.addWidget(self.btn_down)

        layout_main = QVBoxLayout()
        layout_main.addLayout(layout_btn)
        layout_main.addWidget(self.view)

        container = QWidget()
        container.setLayout(layout_main)
        self.setCentralWidget(container)

    def add_folder(self, folder_path):
        """Dodaje wszystkie pliki z folderu, zaznaczając 'Do PDF' dla Word/PDF/JPG/PNG.
        JSON jest zapisywany i wczytywany w tym samym folderze."""
        if not folder_path or not os.path.isdir(folder_path):
            #QMessageBox.warning(self, "Błąd", "Podana ścieżka nie jest folderem.")
            return
        
        self.path = folder_path
        json_path = os.path.join(self.path, "file_list.json")

        self.model.json_path = json_path

        supported_ext = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"}
        items = []

        # wczytaj istniejący JSON (jeśli istnieje)
        saved_map = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                saved_map = {entry["path"]: entry.get("to_pdf", False) for entry in saved}
            except Exception as e:
                QMessageBox.warning(self, "Błąd JSON", f"Nie udało się odczytać ustawień: {e}")

        # twórz listę plików z folderu
        for filename in os.listdir(folder_path):
            if filename == "file_list.json":  # pomijamy plik JSON używany do zapisów
                continue
            path = os.path.join(folder_path, filename)
            if os.path.isfile(path):
                file_item = FileItem(path)

                ext = os.path.splitext(path)[1].lower()
                if ext in supported_ext:
                    file_item.to_pdf = True

                # jeśli mamy zapamiętaną wartość to_pdf → nadpisz
                if path in saved_map:
                    file_item.to_pdf = saved_map[path]

                items.append(file_item)

        # reset tabeli i wstawienie nowych danych
        self.model.beginResetModel()
        self.model._files = items
        self.model.endResetModel()

        # zapisz nową listę do JSON
        self.model.save_to_json(json_path)

        if not items:
            return
            #QMessageBox.information(self, "Brak plików", "Folder nie zawiera plików do dodania.")


    def add_folder_old(self, folder_path):
        """Dodaje wszystkie pliki z folderu, zaznaczając 'Do PDF' dla Word/PDF/JPG/PNG"""
        if not folder_path or not os.path.isdir(folder_path):
            QMessageBox.warning(self, "Błąd", "Podana ścieżka nie jest folderem.")
            return

        supported_ext = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"}
        items = []

        for filename in os.listdir(folder_path):
            path = os.path.join(folder_path, filename)
            if os.path.isfile(path):
                file_item = FileItem(path)

                # automatyczne zaznaczenie dla wybranych typów
                ext = os.path.splitext(path)[1].lower()
                if ext in supported_ext:
                    file_item.to_pdf = True

                items.append(file_item)

        if items:
            self.model.add_files(items)
        else:
            QMessageBox.information(self, "Brak plików", "Folder nie zawiera plików do dodania.")

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Wybierz pliki")
        items = [FileItem(path) for path in paths]
        self.model.add_files(items)

    def move_up(self):
        index = self.view.currentIndex()
        if index.isValid():
            self.model.moveRowUp(index.row())
            self.view.selectRow(index.row() - 1)

    def move_down(self):
        index = self.view.currentIndex()
        if index.isValid():
            self.model.moveRowDown(index.row())
            self.view.selectRow(index.row() + 1)

    def sort_ascending(self):
        """Sortuje pliki w porządku A-Z"""
        self.model.sort_by_name(ascending=True)

    def sort_descending(self):
        """Sortuje pliki w porządku Z-A"""
        self.model.sort_by_name(ascending=False)

    def on_clicked(self, index):
        self.pending_index = index
        self.click_timer.start(250)  # czas w ms, dobrany eksperymentalnie

    def perform_single_click(self):
        path = self.pending_index.data(Qt.UserRole)
        if path:
            print(f"Single clicked path: {path}")
        self.pending_index = None

    def on_double_click(self, index):
        self.click_timer.stop()  # zatrzymujemy, żeby nie wykonywać pojedynczego kliknięcia
        path = index.data(Qt.UserRole)
        if path:
            print(f"Double clicked path: {path}")
            if sys.platform.startswith("win"):
                os.startfile(path)  # Windows
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", path])  # macOS
            else:
                subprocess.Popen(["xdg-open", path])  # Linux/Unix

    def on_clickedv1(self, index):
        path = index.data(Qt.UserRole)
        if path:
            print(f"Single clicked path: {path}")

    def on_double_clickv1(self, index):
        path = index.data(Qt.UserRole)
        if path:
            print(f"Double clicked path: {path}")

    def print_selected_row(self):
        index = self.view.currentIndex()
        if not index.isValid():
            print("Brak zaznaczonego wiersza.")
            return

        row = index.row()
        file = self.model._files[row]
        print("Zaznaczony plik:")
        print(f"  Nazwa: {file.name} Path: {file.path}")
        print(f"  Rozmiar: {file.size}")
        print(f"  Typ: {file.type}")
        print(f"  PDF zaznaczony: {file.to_pdf}")

    def merge_pdf_files(self):
        """Łączy pliki PDF w kolejności z tabeli - tylko te z zaznaczonym checkbox 'Do PDF'"""
        if not PDF_AVAILABLE:
            QMessageBox.warning(self, "Błąd", "pikepdf nie jest zainstalowane.\nUżyj: pip install pikepdf")
            return

        # Pobierz wszystkie pliki PDF z tabeli, które mają zaznaczony checkbox 'Do PDF'
        pdf_files = self.model.get_pdf_files()
        
        if not pdf_files:
            QMessageBox.information(self, "Brak plików", "Nie znaleziono plików PDF z zaznaczonym checkbox 'Do PDF'.")
            return

        if len(pdf_files) < 2:
            QMessageBox.information(self, "Za mało plików", "Do połączenia potrzeba co najmniej 2 plików PDF z zaznaczonym checkbox 'Do PDF'.")
            return

        # Wyświetl listę plików, które będą połączone
        file_names = [f.name for f in pdf_files]
        files_list = "\n".join([f"• {name}" for name in file_names])
        
        reply = QMessageBox.question(
            self, 
            "Potwierdzenie", 
            f"Czy chcesz połączyć następujące pliki PDF?\n\n{files_list}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return

        # Wybierz miejsce zapisu połączonego pliku
        output_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Zapisz połączony PDF", 
            "polaczony_pdf.pdf", 
            "Pliki PDF (*.pdf)"
        )
        
        if not output_path:
            return

        try:
            # Utwórz nowy pusty PDF
            merged_pdf = pikepdf.Pdf.new()
            
            # Dodaj strony z każdego pliku PDF
            for file_item in pdf_files:
                try:
                    print(f"Dodaję plik: {file_item.name}")
                    
                    # Otwórz plik PDF
                    with pikepdf.Pdf.open(file_item.path) as pdf:
                        # Dodaj wszystkie strony z tego pliku
                        merged_pdf.pages.extend(pdf.pages)
                        
                except Exception as e:
                    QMessageBox.warning(
                        self, 
                        "Błąd pliku", 
                        f"Nie można odczytać pliku {file_item.name}:\n{str(e)}"
                    )
                    continue

            # Zapisz połączony plik
            merged_pdf.save(output_path)
            merged_pdf.close()

            QMessageBox.information(
                self, 
                "Sukces", 
                f"Pomyślnie połączono {len(pdf_files)} plików PDF.\nZapisano jako: {output_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Błąd", 
                f"Wystąpił błąd podczas łączenia plików:\n{str(e)}"
            )


if __name__ == "__main__":
    pass