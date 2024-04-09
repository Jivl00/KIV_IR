# Several pipeline functions for preprocessing czech text
import json
import re

import preprocessor

# stopwords taken from Stopwords ISO: https://github.com/stopwords-iso
CZECH_STOPWORDS = "utils/stopwords-cs.txt"
SLOVAK_STOPWORDS = "utils/stopwords-sk.txt"


def pipeline_tokenizer(text):
    """
    Tokenizes the input text and removes stopwords
    :param text:  input text
    :return:  preprocessed text and list of tokens
    """
    preprocessed_text = preprocessor.to_lower(text)  # convert to lowercase
    preprocessed_text = preprocessor.remove_html_tags(preprocessed_text)  # remove html tags
    preprocessed_text = preprocessor.remove_in_text_citation_marks(
        preprocessed_text)  # remove in text citation marks e.g. [12]
    preprocessed_text = preprocessor.remove_parentheses(preprocessed_text)  # remove parentheses () or [] or {}
    preprocessed_text = re.sub(r'(\d)([a-zA-Z])|([a-zA-Z])(\d)', r'\1\3 \2\4',
                               preprocessed_text)  # add space between number and letter or letter and number

    tokens = preprocessor.tokenize(preprocessed_text)  # tokenize the text
    tokens = preprocessor.remove_stop_words(CZECH_STOPWORDS, tokens)
    tokens = preprocessor.remove_stop_words(SLOVAK_STOPWORDS, tokens)

    return preprocessed_text, tokens


def pipeline_stemmer(text):
    """
    Stems the input text and removes diacritics
    :param text:  input text
    :return:  list of stemmed tokens without diacritics
    """
    if not text:  # if the text isn't empty
        return []
    preprocessed_text, tokens = pipeline_tokenizer(text)  # tokenize the text
    stemmed = preprocessor.stem(preprocessed_text, tokens)  # stem the tokens
    return stemmed


def pipeline_lemmatizer(text):
    """
    Lemmatizes the input text and removes diacritics
    :param text:  input text
    :return:  list of lemmatized tokens without diacritics
    """
    if not text:  # if the text isn't empty
        return []
    preprocessed_text, tokens = pipeline_tokenizer(text)  # tokenize the text
    lemmatized = preprocessor.lemmatize(preprocessed_text, tokens)  # lemmatize the tokens
    return lemmatized


def preprocess_file(file_path, pipeline):
    """
    Preprocesses the file using the given pipeline and saves the preprocessed data to a new file
    :param file_path:  path to the file
    :param pipeline:  preprocessing pipeline
    :return:  preprocessed data
    """
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # this structure is assumed - output of the web crawler
    preprocessed_data = {"title": pipeline(data["title"]), "table_of_contents": data["table_of_contents"],
                         "infobox": pipeline(data["infobox"]), "content": pipeline(data["content"])}

    # preprocess the table of contents
    preprocessed_data["table_of_contents"] = preprocessed_data["table_of_contents"][
                                             1:]  # remove the first element: "Obsah"
    chapter_num = r"\b\d+(?:\.\d+)*\b"  # regex for chapter number
    preprocessed_data["table_of_contents"] = [pipeline(re.sub(chapter_num, "", chapter)) for chapter in
                                              preprocessed_data[
                                                  "table_of_contents"]]  # remove chapter numbers and preprocess the chapters

    # with open(file_path + "_preprocessed.json", "w", encoding="utf-8") as file:
    #     json.dump(preprocessed_data, file, ensure_ascii=False, indent=4)

    return preprocessed_data


if __name__ == "__main__":
    file_czech = "data/Skyrim.json"
    # file_slovak = "Cyrodilická ríša.json"

    # PIPELINES: pipeline_stemmer, pipeline_lemmatizer
    data_czech = preprocess_file(file_czech, pipeline_stemmer)
    # data_slovak = preprocess_file(file_slovak, pipeline_stemmer)

    print(data_czech)
    # print(data_slovak)
