# k, model, index, field
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QGridLayout, QPushButton, QCheckBox
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QFormLayout, QCompleter, \
    QListWidgetItem, QListWidget, QComboBox, QLabel, QHBoxLayout
import json
from functools import cached_property
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QFont, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QApplication, QCompleter, QLineEdit
import qdarktheme


user_search_history = []
query = ""

# Set the font size
font = QFont()
font.setPointSize(20)

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


class SearchEngineGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Elder Scrolls Vyhledávač")
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
        self.search_button.setIconSize(QSize(50, 50))  # Set the icon size
        self.search_button.clicked.connect(self.perform_search)  # Connect the clicked signal to the perform_search method
        self.search_button.setFixedSize(100, 50)
        # self.search_button.setFont(font)

        # List of words for auto-suggestion
        with open("index.json", "r", encoding="utf-8") as file:
            self.index = json.load(file)

        words = list(self.index['content'].keys())
        self.search_bar.add_words(words)

        # Connect the returnPressed signal to the perform_search method
        self.search_bar.returnPressed.connect(self.perform_search)

        grid_layout.addWidget(self.search_bar, 0, 0)  # Add to first row, first column
        grid_layout.addWidget(self.search_button, 0, 1)  # Add to first row, second column

        # Add a combobox next to the search bar
        self.index_combobox = QComboBox()
        self.index_combobox.setFont(font)
        self.index_combobox.addItem("Option 1")
        self.index_combobox.addItem("Option 2")
        self.index_combobox.addItem("Option 3")

        self.description_label = QLabel("Select an option:")
        self.description_label.setFont(font)

        # Connect the currentIndexChanged signal to the print_selected_option method
        self.index_combobox.currentIndexChanged.connect(self.print_selected_option)

        grid_layout.addWidget(self.description_label, 0, 2)  # Add to first row, first column
        grid_layout.addWidget(self.index_combobox, 0, 4)  # Add to first row, second column


        # Add a combobox next to the search bar
        self.field_combobox = QComboBox()
        self.field_combobox.setFont(font)
        self.field_combobox.addItem("Option 1")
        self.field_combobox.addItem("Option 2")
        self.field_combobox.addItem("Option 3")

        self.description_label = QLabel("Select an option:")
        self.description_label.setFont(font)

        # Connect the currentIndexChanged signal to the print_selected_option method
        self.field_combobox.currentIndexChanged.connect(self.print_selected_option)

        grid_layout.addWidget(self.description_label, 1, 3)  # Add to first row, first column
        grid_layout.addWidget(self.field_combobox, 1, 4)  # Add to first row, second column

        # Add a combobox for model selection
        self.model_combobox = QComboBox()
        self.model_combobox.setFont(font)
        self.model_combobox.addItem("model1")
        self.model_combobox.addItem("model2")

        self.model_label = QLabel("Select a model:")
        self.model_label.setFont(font)

        # Connect the currentIndexChanged signal to the handle_model_selection method
        self.model_combobox.currentIndexChanged.connect(self.handle_model_selection)

        grid_layout.addWidget(self.model_label, 2, 2)  # Add to third row, third column
        grid_layout.addWidget(self.model_combobox, 2, 4)  # Add to third row, fifth column

        # Add an additional field for the selection of value k
        self.k_field = QLineEdit()
        self.k_field.setFont(font)
        self.k_field.setPlaceholderText("Enter value for k...")

        self.k_label = QLabel("Enter value for k:")
        self.k_label.setFont(font)

        grid_layout.addWidget(self.k_label, 3, 2)  # Add to fourth row, third column
        grid_layout.addWidget(self.k_field, 3, 4)  # Add to fourth row, fifth column

        # Initially hide the k field and its label
        self.k_field.hide()
        self.k_label.hide()

        # ... existing code ...







        self.checkbox_lang = QCheckBox('Detekce jazyka')
        self.checkbox_lang.setStyleSheet("QCheckBox::indicator { width: 30px; height: 30px; }")
        self.checkbox_lang.setFont(font)
        grid_layout.addWidget(self.checkbox_lang, 1, 0)




        # Add the QGridLayout to the main QVBoxLayout
        layout.addLayout(grid_layout)

        self.result_display = QListWidget()
        layout.addWidget(self.result_display)

        self.settings_form = QFormLayout()
        # Add various settings input fields and buttons here
        layout.addLayout(self.settings_form)

        self.setLayout(layout)

    def handle_model_selection(self):
        # If the selected model is "model1", show the k field and its label
        if self.model_combobox.currentText() == "model1":
            self.k_field.show()
            self.k_label.show()
        else:
            # Otherwise, hide the k field and its label
            self.k_field.hide()
            self.k_label.hide()

    def search(self, query):
        user_search_history.append(query)
        # For now, just return "SAMPLE PAGE" concatenated with the query
        print("Query:", query)
        print("User search history:", user_search_history)

        return ["SAMPLE PAGE: " + query] * 10

    def perform_search(self):
        query = self.search_bar.text()
        print("Searching...")
        results = self.search(query)  # Call the search method here
        self.result_display.clear()

        for result in results:
            item = QListWidgetItem(result)
            self.result_display.addItem(item)

    def print_selected_option(self):
        print("Selected option:", self.index_combobox.currentText())



if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    qdarktheme.setup_theme()

    window = SearchEngineGUI()
    window.showMaximized()

    sys.exit(app.exec_())
