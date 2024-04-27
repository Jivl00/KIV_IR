# k, model, index, field
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QGridLayout, QPushButton, QCheckBox, QSpinBox, QTextBrowser, QTreeWidgetItem, QGroupBox, \
    QScrollBar, QAbstractItemView
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QFormLayout, QCompleter, \
    QListWidgetItem, QListWidget, QComboBox, QLabel, QHBoxLayout
from functools import cached_property
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QFont, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QApplication, QCompleter, QLineEdit
import qdarktheme

from lang_detector import LangDetector
from PyQt5.QtCore import Qt


# Set the font size
font_size = 12
font = QFont()
font.setPointSize(font_size)


class IndexerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Index Manager k vyhledávači")
        layout = QVBoxLayout()

        # Set margins around the layout
        margin_horizontal = int(self.width() * 0.1)
        margin_vertical = int(self.height() * 0.1)
        layout.setContentsMargins(margin_horizontal, margin_vertical, margin_horizontal, margin_vertical)

        # Create a QGridLayout for the search bar and the combobox
        grid_layout = QGridLayout()

        self.doc_label = QLabel("Dokument")
        self.doc_label.setFont(font)
        grid_layout.addWidget(self.doc_label, 0, 0)

        self.title_label = QLabel("Název")
        self.title_label.setFont(font)
        grid_layout.addWidget(self.title_label, 1, 0)

        self.title_field = QListWidget()
        self.title_field.setFont(font)
        self.title_field.setFixedHeight(100)
        grid_layout.addWidget(self.title_field, 2, 0)

        self.table_of_contents_label = QLabel("Obsah")
        self.table_of_contents_label.setFont(font)
        grid_layout.addWidget(self.table_of_contents_label, 3, 0)

        self.table_of_contents_field = QListWidget()
        self.table_of_contents_field.setFont(font)
        self.table_of_contents_field.setFixedHeight(100)
        grid_layout.addWidget(self.table_of_contents_field, 4, 0)

        self.infobox_label = QLabel("Tabulka")
        self.infobox_label.setFont(font)
        grid_layout.addWidget(self.infobox_label, 5, 0)

        self.infobox_field = QListWidget()
        self.infobox_field.setFont(font)
        self.infobox_field.setFixedHeight(100)
        grid_layout.addWidget(self.infobox_field, 6, 0)

        self.content_label = QLabel("Hlavní text")
        self.content_label.setFont(font)
        grid_layout.addWidget(self.content_label, 7, 0)

        self.content_field = QListWidget()
        self.content_field.setFont(font)
        self.content_field.setFixedHeight(100)
        grid_layout.addWidget(self.content_field, 8, 0)




        layout.addLayout(grid_layout)
        self.setLayout(layout)
if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    qdarktheme.setup_theme()

    window = IndexerGUI()
    window.showMaximized()
    monitor_width = app.desktop().screenGeometry().width()

    sys.exit(app.exec_())
