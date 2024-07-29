import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog, QPushButton, QVBoxLayout, QWidget,
    QLineEdit, QHBoxLayout, QPlainTextEdit, QProgressBar, QMessageBox, QStatusBar,
    QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor

class CatalogGeneratorThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, folder, include_hidden, file_types):
        super().__init__()
        self.folder = folder
        self.include_hidden = include_hidden
        self.file_types = file_types

    def run(self):
        catalog_text = self.create_catalog(self.folder)
        self.finished.emit(catalog_text)

    def create_catalog(self, folder):
        catalog_text = f"Catalog for: {os.path.basename(folder)}\n"
        catalog_text += "=" * 50 + "\n\n"

        total_items = sum([len(files) for _, _, files in os.walk(folder)])
        processed_items = 0

        for root, dirs, files in os.walk(folder):
            if not self.include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                files = [f for f in files if not f.startswith('.')]

            relative_path = os.path.relpath(root, folder)
            level = relative_path.count(os.sep)
            indent = "  " * level

            if relative_path != ".":
                catalog_text += f"{indent}{os.path.basename(root)}/\n"

            for file in files:
                if self.file_types == "All" or os.path.splitext(file)[1].lower() in self.file_types:
                    catalog_text += f"{indent}  {file}\n"
                
                processed_items += 1
                self.progress.emit(int((processed_items / total_items) * 100))

            if files:
                catalog_text += "\n"

        return catalog_text

class CatalogApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Folder Catalog Generator')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('folder_icon.png'))  # Make sure to have this icon file

        # Set the color scheme
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)

        layout = QVBoxLayout()

        # Input folder selection
        input_folder_layout = QHBoxLayout()
        self.input_folder_edit = QLineEdit(self)
        self.input_folder_edit.setReadOnly(True)
        self.input_folder_edit.setPlaceholderText("Select a folder or drag and drop here")
        input_folder_layout.addWidget(self.input_folder_edit)
        self.browse_button = QPushButton('Browse', self)
        self.browse_button.clicked.connect(self.select_folder)
        input_folder_layout.addWidget(self.browse_button)
        layout.addLayout(input_folder_layout)

        # File type filter
        file_type_layout = QHBoxLayout()
        file_type_layout.addWidget(QLabel('File Type:'))
        self.file_type_combo = QComboBox(self)
        self.file_type_combo.addItems(["All", ".txt", ".pdf", ".doc", ".docx"])
        file_type_layout.addWidget(self.file_type_combo)
        layout.addLayout(file_type_layout)

        # Include hidden files checkbox
        self.include_hidden_check = QCheckBox('Include Hidden Files', self)
        layout.addWidget(self.include_hidden_check)

        # Generate and Copy buttons
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton('Generate Catalog', self)
        self.generate_button.clicked.connect(self.generate_catalog)
        button_layout.addWidget(self.generate_button)
        self.copy_button = QPushButton('Copy Text', self)
        self.copy_button.clicked.connect(self.copy_text)
        button_layout.addWidget(self.copy_button)
        layout.addLayout(button_layout)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Result text area
        self.result_text = QPlainTextEdit(self)
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.setAcceptDrops(True)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Input Folder')
        if folder:
            self.input_folder_edit.setText(folder)
            self.statusBar.showMessage(f"Selected folder: {folder}")

    def generate_catalog(self):
        folder = self.input_folder_edit.text()
        if not folder:
            QMessageBox.warning(self, "Warning", "Please select an input folder.")
            return

        self.statusBar.showMessage("Generating catalog...")
        self.progress_bar.setValue(0)
        self.generate_button.setEnabled(False)

        file_types = self.file_type_combo.currentText()
        if file_types != "All":
            file_types = [file_types]

        self.catalog_thread = CatalogGeneratorThread(
            folder, 
            self.include_hidden_check.isChecked(),
            file_types
        )
        self.catalog_thread.progress.connect(self.update_progress)
        self.catalog_thread.finished.connect(self.catalog_generated)
        self.catalog_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def catalog_generated(self, catalog_text):
        if catalog_text:
            self.result_text.setPlainText(catalog_text)
            self.save_catalog_to_file(catalog_text)
            self.statusBar.showMessage("Catalog generated successfully and saved to file.")
        else:
            self.result_text.setPlainText("No files found in the selected folder.")
            self.statusBar.showMessage("No files found.")

        self.generate_button.setEnabled(True)

    def save_catalog_to_file(self, catalog_text):
        folder = self.input_folder_edit.text()
        file_path = os.path.join(folder, "folder_catalog.txt")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(catalog_text)
            QMessageBox.information(self, "Success", f"Catalog saved to {file_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save catalog: {str(e)}")

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.result_text.toPlainText())
        self.statusBar.showMessage("Text copied to clipboard.", 3000)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                folder_path = urls[0].toLocalFile()
                if os.path.isdir(folder_path):
                    self.input_folder_edit.setText(folder_path)
                    self.statusBar.showMessage(f"Dropped folder: {folder_path}")
                    self.generate_catalog()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for a modern look
    window = CatalogApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()