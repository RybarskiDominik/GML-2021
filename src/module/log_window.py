import logging
import sys
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                               QPushButton, QLabel, QCheckBox, QComboBox,
                               QApplication, QSplitter, QFrame, QMainWindow)
from PySide6.QtCore import QObject, Signal, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QTextCursor, QColor, QPalette


class LogSignal(QObject):
    """Sygnał do przekazywania logów między wątkami."""
    log_message = Signal(str, str, str)  # level, message, timestamp


class QtLogHandler(logging.Handler):
    """Handler loggingu przekazujący logi do Qt sygnału."""
    
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
    
    def emit(self, record):
        try:
            message = self.format(record)
            timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
            self.signal.log_message.emit(record.levelname, message, timestamp)
        except Exception:
            self.handleError(record)


class LogWindow(QMainWindow):
    """Okno do wyświetlania logów w czasie rzeczywistym."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Logi programu")
        self.setGeometry(100, 100, 800, 600)
        
        # Konfiguracja
        self.max_lines = 1000
        self.auto_scroll = True
        self.show_timestamps = True
        self.current_filter_level = "DEBUG"
        
        # Kolory dla różnych poziomów logowania
        self.level_colors = {
            'DEBUG': '#888888',
            'INFO': '#000000',
            'WARNING': '#FF8C00',
            'ERROR': '#FF0000',
            'CRITICAL': '#8B0000'
        }
        
        self.setup_ui()
        self.setup_logging()
        
        # Timer do okresowego czyszczenia starych logów
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_old_logs)
        self.cleanup_timer.start(10000)  # co 10 sekund
    
    def setup_ui(self):
        """Konfiguruje interfejs użytkownika."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Panel kontrolny
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Główny panel z logami
        main_panel = self.create_main_panel()
        layout.addWidget(main_panel, 1)
        
        # Panel statusu
        status_panel = self.create_status_panel()
        layout.addWidget(status_panel)
    
    def create_control_panel(self):
        """Tworzy panel kontrolny."""
        panel = QFrame()
        layout = QHBoxLayout(panel)
        
        # Checkbox - automatyczne przewijanie
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(self.auto_scroll)
        self.auto_scroll_cb.toggled.connect(self.toggle_auto_scroll)
        layout.addWidget(self.auto_scroll_cb)
        
        # Checkbox - pokazuj znaczniki czasu
        self.timestamps_cb = QCheckBox("Pokaż czas")
        self.timestamps_cb.setChecked(self.show_timestamps)
        self.timestamps_cb.toggled.connect(self.toggle_timestamps)
        layout.addWidget(self.timestamps_cb)
        
        # ComboBox - filtr poziomów
        layout.addWidget(QLabel("Poziom:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
        self.level_filter.setCurrentText(self.current_filter_level)
        self.level_filter.currentTextChanged.connect(self.change_filter_level)
        layout.addWidget(self.level_filter)
        
        layout.addStretch()
        
        # Przyciski
        clear_btn = QPushButton("Wyczyść")
        clear_btn.clicked.connect(self.clear_logs)
        layout.addWidget(clear_btn)
        
        save_btn = QPushButton("Zapisz logi")
        save_btn.clicked.connect(self.save_logs)
        layout.addWidget(save_btn)
        
        return panel
    
    def create_main_panel(self):
        """Tworzy główny panel z obszarem logów."""
        splitter = QSplitter(Qt.Vertical)
        
        # Obszar tekstowy dla logów
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        # Ustawienie czcionki monospace
        font = QFont("Consolas", 9)
        font.setStyleHint(QFont.TypeWriter)
        self.log_text.setFont(font)
        
        # Ustawienia obszaru tekstowego
        self.log_text.setLineWrapMode(QTextEdit.WidgetWidth)
        
        splitter.addWidget(self.log_text)
        splitter.setStretchFactor(0, 1)
        
        return splitter
    
    def create_status_panel(self):
        """Tworzy panel statusu."""
        panel = QFrame()
        layout = QHBoxLayout(panel)
        
        self.status_label = QLabel("Gotowy")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.log_count_label = QLabel("Logi: 0")
        layout.addWidget(self.log_count_label)
        
        return panel
    
    def setup_logging(self):
        """Konfiguruje system logowania."""
        # Utworzenie sygnału
        self.log_signal = LogSignal()
        self.log_signal.log_message.connect(self.add_log_message)
        
        # Utworzenie handlera
        self.log_handler = QtLogHandler(self.log_signal)
        
        # Formatter
        formatter = logging.Formatter(
            '%(name)s - %(levelname)s - %(message)s'
        )
        self.log_handler.setFormatter(formatter)
        
        # Dodanie handlera do root loggera
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.DEBUG)
        
        # Licznik logów
        self.log_count = 0
    
    def add_log_message(self, level, message, timestamp):
        """Dodaje nową wiadomość do okna logów."""
        if not self.should_show_level(level):
            return
        
        # Sprawdź czy nie przekroczyliśmy limitu linii
        if self.log_text.document().blockCount() > self.max_lines:
            self.cleanup_old_logs()
        
        # Formatowanie wiadomości
        if self.show_timestamps:
            formatted_message = f"[{timestamp}] [{level:8}] {message}"
        else:
            formatted_message = f"[{level:8}] {message}"
        
        # Dodanie koloru
        color = self.level_colors.get(level, '#000000')
        
        # Dodanie do obszaru tekstowego
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Ustawienie koloru
        format = cursor.charFormat()
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)
        
        cursor.insertText(formatted_message + '\n')
        
        # Auto-scroll
        if self.auto_scroll:
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # Aktualizacja licznika
        self.log_count += 1
        self.log_count_label.setText(f"Logi: {self.log_count}")
        
        # Aktualizacja statusu
        self.status_label.setText(f"Ostatni log: {level} o {timestamp}")
    
    def should_show_level(self, level):
        """Sprawdza czy dany poziom logowania powinien być wyświetlony."""
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        current_index = levels.index(self.current_filter_level)
        message_index = levels.index(level)
        return message_index >= current_index
    
    def toggle_auto_scroll(self, checked):
        """Przełącza automatyczne przewijanie."""
        self.auto_scroll = checked
    
    def toggle_timestamps(self, checked):
        """Przełącza wyświetlanie znaczników czasu."""
        self.show_timestamps = checked
    
    def change_filter_level(self, level):
        """Zmienia poziom filtrowania logów."""
        self.current_filter_level = level
    
    def clear_logs(self):
        """Czyści obszar logów."""
        self.log_text.clear()
        self.log_count = 0
        self.log_count_label.setText("Logi: 0")
        self.status_label.setText("Logi wyczyszczone")
    
    def cleanup_old_logs(self):
        """Usuwa stare logi gdy jest ich zbyt dużo."""
        document = self.log_text.document()
        if document.blockCount() > self.max_lines:
            # Usuń pierwsze 100 linii
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.Start)
            
            for _ in range(100):
                cursor.select(QTextCursor.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # usuń znak nowej linii
    
    def save_logs(self):
        """Zapisuje logi do pliku."""
        from PySide6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Zapisz logi", 
            f"logi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text files (*.txt);;All files (*.*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                self.status_label.setText(f"Logi zapisane: {filename}")
            except Exception as e:
                self.status_label.setText(f"Błąd zapisu: {str(e)}")
    
    def closeEvent(self, event):
        """Obsługuje zamykanie okna."""
        # Usunięcie handlera przy zamykaniu
        root_logger = logging.getLogger()
        if self.log_handler in root_logger.handlers:
            root_logger.removeHandler(self.log_handler)
        
        super().closeEvent(event)


if __name__ == '__main__':
    pass