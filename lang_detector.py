import pickle


class LangDetector:
    def __init__(self, only_czech_slovak=False):
        if only_czech_slovak:
            self.languages = ['cs', 'sk']
            self.model = self.load_model('models/model_czsk.bin')
            self.label2lang = {i: lang for i, lang in enumerate(self.languages)}
        else:
            self.languages = ['cs', 'de', 'en', 'es', 'fr', 'it', 'pl', 'pt', 'ru', 'sk']
            self.model = self.load_model('models/model_all.bin')
            self.label2lang = {i: lang for i, lang in enumerate(self.languages)}

    def predict(self, sentences):
        """
        Predict language for a given sentence with a given model.

        :param sentences: sentence to be predicted
        :return: predicted label
        """
        if not isinstance(sentences, list):
            sentences = [sentences]

        y_pred = self.model.predict(sentences)

        labels = []
        for y in y_pred:
            labels.append(self.label2lang[y])
        return labels

    def load_model(self, path):
        """
        Load a model from a given path.
        :param path: path to the model
        :return: loaded model
        """
        with open(path, 'rb') as f:
            return pickle.load(f)


if __name__ == "__main__":
    lang_detector = LangDetector(only_czech_slovak=True)
    print(lang_detector.predict("hello"))