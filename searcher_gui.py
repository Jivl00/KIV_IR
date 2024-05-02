from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QGridLayout, QPushButton, QCheckBox, QSpinBox, QTextBrowser, QTreeWidgetItem, QGroupBox, \
    QScrollBar, QAbstractItemView, QSpacerItem
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QFormLayout, QCompleter, \
    QListWidgetItem, QListWidget, QComboBox, QLabel, QHBoxLayout
from functools import cached_property
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QFont, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QApplication, QCompleter, QLineEdit
import qdarktheme

from lang_detector import LangDetector
from PyQt5.QtCore import Qt
from searcher import *


user_search_history = []
SEARCH_CONFIG = {
    "query": "",
    "index": indexes[0].index_name,
    "field": "Celý dokument",
    "model": "TF-IDF model",
    "k": 10,
    "lang": False
}

# Set the font size
font_size = 12
font = QFont()
font.setPointSize(font_size)


class LineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.completer.setWidget(self)
        self.completer.setModel(self.model)
        self.textChanged.connect(self.handle_text_changed)
        self.completer.activated.connect(self.handle_activated)

    @cached_property
    def model(self):
        return QStandardItemModel()

    @cached_property
    def completer(self):
        return QCompleter()

    def add_word(self, word):
        if not self.model.findItems(word):
            self.model.appendRow(QStandardItem(word))

    def add_words(self, words):
        self.completer = QCompleter(words)
        self.completer.setCaseSensitivity(0)
        self.completer.popup().setFont(font)
        self.completer.setWidget(self)
        self.completer.activated.connect(self.handle_activated)

    def handle_text_changed(self):
        text = self.text()[0 : self.cursorPosition()]
        if not text:
            self.completer.popup().hide()
            return
        words = text.split()
        if text.endswith(" "):
            for word in words:
                self.add_word(word)
            self.completer.popup().hide()
            return
        self.completer.setCompletionPrefix(words[-1])
        self.completer.complete()

    def handle_activated(self, text):
        prefix = self.completer.completionPrefix()
        extra = text[len(prefix) :]
        self.blockSignals(True)
        self.insert(extra)
        self.blockSignals(False)
        self.add_word(text)


class ResultText(QWidget):
    def __init__(self, title, content):
        super().__init__()

        # Create a QFont object and set its bold property to True
        font_bold = QFont()
        font_bold.setPointSize(font_size)
        font_bold.setBold(True)

        font_smaller = QFont()
        font_smaller.setPointSize(font_size - 2)

        # Create a QLabel for the title and set its font to the QFont object
        self.title_label = QLabel('<span style="color:#8bb6e0;">'+title +'</span>')
        self.title_label.setFont(font_bold)
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # Create a QLabel for the content
        self.content_label = QLabel(content)
        self.content_label.setFont(font_smaller)
        self.content_label.setWordWrap(True)
        self.content_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.content_label.setFixedWidth(int(monitor_width * 0.9))

        # Add the title and content labels to the layout of the custom widget
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.content_label)

        self.setLayout(self.layout)



class SearchEngineGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.lang_detector = LangDetector(only_czech_slovak=False)

    def initUI(self):
        self.setWindowTitle("Elder Scrolls Vyhledávač")
        self.setWindowIcon(QIcon('img/magnifying-glass-3-xxl.png'))
        layout = QVBoxLayout()

        # Set margins around the layout
        margin_horizontal = int(self.width() * 0.1)
        margin_vertical = int(self.height() * 0.1)
        layout.setContentsMargins(margin_horizontal, margin_vertical, margin_horizontal, margin_vertical)

        # Create a QGridLayout for the search bar and the combobox
        grid_layout = QGridLayout()

        self.search_bar = LineEdit()
        self.search_bar.setPlaceholderText("Zadejte hledaný výraz...")
        self.search_bar.setFont(font)

        # Add a search button next to the search bar
        self.search_button = QPushButton()
        self.search_button.setIcon(QIcon('img/magnifying-glass-3-xxl.png'))  # Set the icon
        self.search_button.setIconSize(QSize(30, 30))  # Set the icon size
        self.search_button.clicked.connect(self.perform_search)  # Connect the clicked signal to the perform_search method
        self.search_button.setFixedSize(80, 32)
        # self.search_button.setFont(font)

        # List of words for auto-suggestion
        with open("cache/keywords.txt", "r", encoding="utf-8") as file:
            words = file.read().splitlines()

        words = sorted(set(words))
        self.search_bar.add_words(words)

        # Connect the returnPressed signal to the perform_search method
        self.search_bar.returnPressed.connect(self.perform_search)

        grid_layout.addWidget(self.search_bar, 0, 0,1,3)
        grid_layout.addWidget(self.search_button, 0, 2)

        # Create a QSpacerItem
        spacer = QSpacerItem(200, 40)

        # Add the spacer to the grid layout at the desired column
        grid_layout.addItem(spacer, 0, 3)

        # Add a combobox next to the search bar
        self.index_combobox = QComboBox()
        self.index_combobox.setFont(font)
        for index in indexes:
            self.index_combobox.addItem(index.index_name)

        self.description_label = QLabel("Index:")
        self.description_label.setFont(font)

        # Connect the currentIndexChanged signal to the print_selected_option method
        self.index_combobox.currentIndexChanged.connect(self.update_selected_index)

        grid_layout.addWidget(self.description_label, 0, 4)  # Add to first row, first column
        grid_layout.addWidget(self.index_combobox, 0, 5)  # Add to first row, second column


        # Add a combobox next to the search bar
        self.field_combobox = QComboBox()
        self.field_combobox.setFont(font)
        self.field_combobox.addItem("Celý dokument")
        self.field_combobox.addItem("Nadpis")
        self.field_combobox.addItem("Obsah")
        self.field_combobox.addItem("Tabulka")
        self.field_combobox.addItem("Hlavní text")

        self.description_label = QLabel("Sekce:")
        self.description_label.setFont(font)

        # Connect the currentIndexChanged signal to the print_selected_option method
        self.field_combobox.currentIndexChanged.connect(self.update_selected_field)

        grid_layout.addWidget(self.description_label, 1, 4)  # Add to first row, first column
        grid_layout.addWidget(self.field_combobox, 1, 5)  # Add to first row, second column

        # Add a combobox for model selection
        self.model_combobox = QComboBox()
        self.model_combobox.setFont(font)
        self.model_combobox.addItem("TF-IDF model")
        self.model_combobox.addItem("Booleovský model")

        self.model_label = QLabel("Model:")
        self.model_label.setFont(font)

        # Connect the currentIndexChanged signal to the handle_model_selection method
        self.model_combobox.currentIndexChanged.connect(self.handle_model_selection)

        grid_layout.addWidget(self.model_label, 2, 4)  # Add to third row, third column
        grid_layout.addWidget(self.model_combobox, 2, 5)  # Add to third row, fifth column

        # Add an additional field for the selection of value k
        self.k_field = QSpinBox()
        self.k_field.setFont(font)
        self.k_field.setMinimum(1)
        self.k_field.setMaximum(100)
        self.k_field.setValue(10)

        self.k_label = QLabel("Počet vyhledaných\ndokumentů k zobrazení:")
        self.k_label.setFont(font)

        # Connect the valueChanged signal to the update_selected_k method
        self.k_field.valueChanged.connect(self.update_selected_k)

        grid_layout.addWidget(self.k_label, 3, 4)  # Add to fourth row, third column
        grid_layout.addWidget(self.k_field, 3, 5)  # Add to fourth row, fifth column


        self.checkbox_lang = QCheckBox('Detekce jazyka dotazu')
        self.checkbox_lang.setStyleSheet("QCheckBox::indicator { width: 30px; height: 30px; }")
        self.checkbox_lang.setFont(font)
        grid_layout.addWidget(self.checkbox_lang, 1, 0)

        self.checkbox_lang.stateChanged.connect(self.update_selected_lang)

        self.under_search_bar_text = QLabel("")
        self.under_search_bar_text.setFont(font)
        grid_layout.addWidget(self.under_search_bar_text, 1, 1)

        self.proximity_info = QLabel("Pro vyhledávání s využitím vzdáleností mezi slovy, zadejte dotaz ve formátu: <dotaz>~vzdálenost")
        self.proximity_info.setFont(font)
        grid_layout.addWidget(self.proximity_info, 2, 0)

        self.phrase_info = QLabel("Pro vyhledávání frází, zadejte dotaz ve formátu: \"<dotaz>\"")
        self.phrase_info.setFont(font)
        grid_layout.addWidget(self.phrase_info, 3, 0)




        # QTextBrowser for displaying the search results
        # Add the QGridLayout to the main QVBoxLayout
        layout.addLayout(grid_layout)


        self.result_display = QListWidget()
        self.result_display.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.result_display.setFont(font)
        self.result_display.setWordWrap(True)

        layout.addWidget(self.result_display)

        self.settings_form = QFormLayout()
        # Add various settings input fields and buttons here
        layout.addLayout(self.settings_form)

        self.setLayout(layout)

    def handle_model_selection(self):
        self.update_selected_model()
        if self.model_combobox.currentText() == "TF-IDF model":
            # self.k_field.show()
            # self.k_label.show()
            self.proximity_info.show()
            self.phrase_info.show()
        else:
            # Otherwise, hide the k field and its label
            # self.k_field.hide()
            # self.k_label.hide()
            self.proximity_info.hide()
            self.phrase_info.hide()

    def search_prep(self):
        user_search_history.append(SEARCH_CONFIG["query"])  # Append the query to the user search history
        print("Search config:", SEARCH_CONFIG)
        index_name = SEARCH_CONFIG["index"]
        index = [index for index in indexes if index.index_name == index_name][0]
        field = {"Celý dokument": "", "Nadpis": "title", "Obsah": "table_of_contents", "Tabulka": "infobox", "Hlavní text": "content"}.get(SEARCH_CONFIG["field"], "content")
        model = {"TF-IDF model": "tf-idf", "Booleovský model": "boolean"}.get(SEARCH_CONFIG["model"], "tfidf")
        result_obj, n = search(SEARCH_CONFIG["query"], field, SEARCH_CONFIG["k"], index, model)

        if n == 0:
            found = "Nenalezen žádný výsledek pro dotaz: " + SEARCH_CONFIG["query"]
            return found, []
        elif n == 1:
            found = "Nalezen 1 výsledek pro dotaz: " + SEARCH_CONFIG["query"]
        elif 1 < n < 5:
            found = "Nalezeno " + str(n) + " výsledky pro dotaz: " + SEARCH_CONFIG["query"]
        else:
            found = "Nalezeno " + str(n) + " výsledků pro dotaz: " + SEARCH_CONFIG["query"]
        ret = [result.get_item() for result in result_obj]
        return found, ret

    def perform_search(self):
        self.update_keywords()
        SEARCH_CONFIG["query"] = self.search_bar.text()
        num, results = self.search_prep()  # Call the search method here
        self.result_display.clear()
        item = QListWidgetItem()
        item.setText(num)
        self.result_display.addItem(item)

        for result in results:
            result_text = ResultText(result[0], result[1])
            item = QListWidgetItem()
            item.setSizeHint(result_text.sizeHint())
            self.result_display.addItem(item)
            self.result_display.setItemWidget(item, result_text)

        # Language detection
        if self.checkbox_lang.isChecked():
            language = self.lang_detector.predict(SEARCH_CONFIG["query"])[0]
            detected_lang = {
                "cs": "Detekován český jazyk",
                "de": "Detekován německý jazyk",
                "en": "Detekován anglický jazyk",
                "es": "Detekován španělský jazyk",
                "fr": "Detekován francouzský jazyk",
                "it": "Detekován italský jazyk",
                "pl": "Detekován polský jazyk",
                "pt": "Detekován portugalský jazyk",
                "ru": "Detekován ruský jazyk",
                "sk": "Detekován slovenský jazyk",
            }.get(language, "Detekován neznámý jazyk")
            self.under_search_bar_text.setText(detected_lang)

    def update_selected_field(self):
        SEARCH_CONFIG["field"] = self.field_combobox.currentText()
    def update_selected_index(self):
        SEARCH_CONFIG["index"] = self.index_combobox.currentText()

    def update_selected_model(self):
        SEARCH_CONFIG["model"] = self.model_combobox.currentText()

    def update_selected_k(self):
        SEARCH_CONFIG["k"] = self.k_field.value()

    def update_selected_lang(self):
        SEARCH_CONFIG["lang"] = self.checkbox_lang.isChecked()
        if not self.checkbox_lang.isChecked():
            self.under_search_bar_text.setText("")
    def update_keywords(self):
        # TODO resolve the segfault
        # with open("cache/keywords.txt", "r", encoding="utf-8") as file:
        #     words = file.read().splitlines()
        #
        # words = sorted(set(words))
        pass
        # self.search_bar.add_words(['prd', 'prdel'])



if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('img/magnifying-glass-3-xxl.png'))
    qdarktheme.setup_theme()

    window = SearchEngineGUI()
    window.showMaximized()
    monitor_width = app.desktop().screenGeometry().width()

    sys.exit(app.exec_())
