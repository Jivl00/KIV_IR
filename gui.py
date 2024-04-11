from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QFormLayout, QCompleter, \
    QListWidgetItem, QListWidget
import json
from functools import cached_property

from PyQt5.QtGui import QFont, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QApplication, QCompleter, QLineEdit


user_search_history = []
query = ""

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
        layout = QVBoxLayout()

        self.search_bar = LineEdit()
        self.search_bar.setPlaceholderText("Enter search query...")

        # List of words for auto-suggestion
        with open("index.json", "r", encoding="utf-8") as file:
            self.index = json.load(file)

        words = list(self.index['content'].keys())
        self.search_bar.add_words(words)


        # Connect the returnPressed signal to the perform_search method
        self.search_bar.returnPressed.connect(self.perform_search)

        layout.addWidget(self.search_bar)

        self.result_display = QListWidget()
        layout.addWidget(self.result_display)

        self.settings_form = QFormLayout()
        # Add various settings input fields and buttons here
        layout.addLayout(self.settings_form)

        self.setLayout(layout)

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



if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    window = SearchEngineGUI()
    window.showMaximized()

    sys.exit(app.exec_())
