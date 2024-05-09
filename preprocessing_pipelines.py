import json
import re

import utils.preprocessor as preprocessor

# stopwords taken from Stopwords ISO: https://github.com/stopwords-iso
CZECH_STOPWORDS = "utils/stopwords-cs.txt"
SLOVAK_STOPWORDS = "utils/stopwords-sk.txt"

def pipeline_tokenizer(text, snippet=False, remove_stopwords=False):
    """
    Tokenizes the input text and removes stopwords
    :param text:  input text
    :param snippet:  if the text is a snippet
    :param remove_stopwords:  if the stopwords should be removed
    :return:  preprocessed text and list of tokens
    """
    if snippet:
        preprocessed_text = text
    else:
        preprocessed_text = preprocessor.to_lower(text)  # convert to lowercase
    preprocessed_text = preprocessor.remove_html_tags(preprocessed_text)  # remove html tags
    preprocessed_text = preprocessor.remove_in_text_citation_marks(
        preprocessed_text)  # remove in text citation marks e.g. [12]
    preprocessed_text = preprocessor.remove_parentheses(preprocessed_text)  # remove parentheses () or [] or {}
    preprocessed_text = re.sub(r'(\d)([a-zA-Z])|([a-zA-Z])(\d)', r'\1\3 \2\4',
                               preprocessed_text)  # add space between number and letter or letter and number

    if snippet:
        tokens = preprocessor.tokenize_snippet(preprocessed_text)
    else:
        tokens = preprocessor.tokenize(preprocessed_text)  # tokenize the text
    if remove_stopwords:
        tokens = preprocessor.remove_stop_words(CZECH_STOPWORDS, tokens)
        tokens = preprocessor.remove_stop_words(SLOVAK_STOPWORDS, tokens)

    return preprocessed_text, tokens


def pipeline_stemmer(text, remove_stopwords=False):
    """
    Stems the input text and removes diacritics
    :param text:  input text
    :param remove_stopwords:  if the stopwords should be removed
    :return:  list of stemmed tokens without diacritics
    """
    if not text:  # if the text isn't empty
        return []
    preprocessed_text, tokens = pipeline_tokenizer(text, remove_stopwords=remove_stopwords)  # tokenize the text
    stemmed = preprocessor.stem(preprocessed_text, tokens)  # stem the tokens
    return stemmed


def pipeline_lemmatizer(text, remove_stopwords=False):
    """
    Lemmatizes the input text and removes diacritics
    :param text:  input text
    :param remove_stopwords:  if the stopwords should be removed
    :return:  list of lemmatized tokens without diacritics
    """
    if not text:  # if the text isn't empty
        return []
    preprocessed_text, tokens = pipeline_tokenizer(text, remove_stopwords=remove_stopwords)  # tokenize the text
    lemmatized = preprocessor.lemmatize(preprocessed_text, tokens)  # lemmatize the tokens
    return lemmatized


def pipeline_lemmatizer2(text, remove_stopwords=False):
    """
    Lemmatizes the input text and removes diacritics
    :param text:  input text
    :param remove_stopwords:  if the stopwords should be removed
    :return:  list of lemmatized tokens without diacritics
    """
    if not text:  # if the text isn't empty
        return []
    preprocessed_text, tokens = pipeline_tokenizer(text, remove_stopwords=remove_stopwords)  # tokenize the text
    lemmatized = preprocessor.lemmatize2(preprocessed_text, tokens)  # lemmatize the tokens
    return lemmatized


def preprocess_file(file_path, pipeline, remove_stopwords=False):
    """
    Preprocesses the file using the given pipeline and saves the preprocessed data to a new file
    :param file_path:  path to the file
    :param pipeline:  preprocessing pipeline
    :param remove_stopwords:  if the stopwords should be removed
    :return:  preprocessed data
    """
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # this structure is assumed - output of the web crawler
    preprocessed_data = {"title": pipeline(data["title"], remove_stopwords), "table_of_contents": data["table_of_contents"],
                         "infobox": pipeline(data["infobox"], remove_stopwords), "content": pipeline(data["content"], remove_stopwords)}

    # preprocess the table of contents
    preprocessed_data["table_of_contents"] = preprocessed_data["table_of_contents"][
                                             1:]  # remove the first element: "Obsah"
    chapter_num = r"\b\d+(?:\.\d+)*\b"  # regex for chapter number
    preprocessed_data["table_of_contents"] = [pipeline(re.sub(chapter_num, "", chapter), remove_stopwords) for chapter in
                                              preprocessed_data[
                                                  "table_of_contents"]]  # remove chapter numbers and preprocess the chapters
    return preprocessed_data


def preprocess(doc, doc_id, pipeline, remove_stopwords=False):
    """
    Preprocesses the document using the lemmatizer or stemmer pipeline
    :param doc: input document
    :param doc_id: id of the document
    :param pipeline: preprocessing pipeline
    :param remove_stopwords: if the stopwords should be removed
    :return: preprocessed document (tokenized, lowercased, without stopwords, etc.)
    """

    # this structure is assumed - output of the web crawler
    preprocessed_data = {"title": pipeline(doc["title"], remove_stopwords=remove_stopwords), "table_of_contents": doc["table_of_contents"],
                         "infobox": pipeline(doc["infobox"], remove_stopwords=remove_stopwords), "content": pipeline(doc["content"], remove_stopwords=remove_stopwords),
                         "id": doc_id}
    chapter_num = r"\b\d+(?:\.\d+)*\b"  # regex for chapter number
    preprocessed_data["table_of_contents"] = [word for chapter in preprocessed_data["table_of_contents"] for word in
                                              pipeline(re.sub(chapter_num, "",
                                                        chapter), remove_stopwords=remove_stopwords)]  # remove chapter numbers and preprocess the chapters
    return preprocessed_data