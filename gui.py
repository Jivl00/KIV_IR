from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QListView, QFormLayout, QCompleter, \
    QListWidgetItem
import json


class SearchEngineGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Enter search query...")

        # List of words for auto-suggestion
        with open("index.json", "r", encoding="utf-8") as file:
            self.index = json.load(file)

        words = list(self.index['content'].keys())

        # Create a completer object with the list of words
        completer = QCompleter(words)

        # Set the completer object for the search bar
        self.search_bar.setCompleter(completer)

        # Connect the returnPressed signal to the perform_search method
        self.search_bar.returnPressed.connect(self.perform_search)

        layout.addWidget(self.search_bar)

        self.result_display = QListView()
        layout.addWidget(self.result_display)

        self.settings_form = QFormLayout()
        # Add various settings input fields and buttons here
        layout.addLayout(self.settings_form)

        self.setLayout(layout)

    def search(self, query):
        # For now, just return "SAMPLE PAGE" concatenated with the query
        print("Query:", query)
        return ["SAMPLE PAGE: " + query]

    def perform_search(self):
        query = self.search_bar.text()
        print("Searching...")
        results = self.search(query)  # Call the search method here
        if results is not None and isinstance(results, list):
            print(self.result_display)
            if self.result_display is None:
                self.result_display = QListView()
            self.result_display.clear()
            for result in results:
                item = QListWidgetItem(result)
                print("Result:", result)
                self.result_display.addItem(item)
        else:
            print("Error: search did not return a list")


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    window = SearchEngineGUI()
    window.show()

    sys.exit(app.exec_())
