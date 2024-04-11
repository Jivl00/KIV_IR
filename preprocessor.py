import re
from unidecode import unidecode
from simplemma.langdetect import lang_detector
import simplemma
import utils.stemmer_cs
import utils.stemmer_sk

def to_lower(text):
    """
    Converts text to lowercase
    :param text: input text
    :return: text in lowercase
    """
    return text.lower()


def remove_html_tags(text):
    """
    Removes html tags from the text
    :param text: input text
    :return: text without html tags
    """
    return re.sub(r"<.*?>", "", text)


def remove_in_text_citation_marks(text):
    """
    Removes in text citation marks from the text, e.g. [12]
    :param text: input text
    :return: text without in text citation marks
    """
    return re.sub(r"\[\d+\]", "", text)


def remove_parentheses(text):
    """
    Removes parentheses from the text () or [] or {}
    :param text: input text
    :return: text without parentheses
    """
    # remove also single parentheses
    return re.sub(r"[\(\)\[\]\{\}]", "", text)


def remove_stop_words(stop_words_file, tokens):
    """
    Removes stop words from the tokens
    :param stop_words_file: file with stop words to remove
    :param text: input tokens
    :return: tokens without stop words
    """
    with open(stop_words_file, "r", encoding="utf-8") as file:
        stop_words = file.read().splitlines()
    return [token for token in tokens if token not in stop_words]


def tokenize(text):
    """
    Tokenizes the text using regexs for urls, dates, times, emails and words with stars and default regex
    :param text: input text
    :return: list of tokens
    """
    default_regex = r"(\d+[.,]\d+?)|([\w]+)"  # default regex - numbers and words
    url_regex = r"(https?:\/\/[^\s]+)"
    date_regex = r"(\d{1,2}\.\d{1,2}\.\d{4})"  # date in format dd.mm.yyyy
    time_regex = r"(\d{1,2}:\d{1,2})"  # time in format hh:mm
    email_regex = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
    words_with_stars = r"(\w+\*\w+)"

    tokenized = []
    for word in text.split(' '):
        word = word.replace("-", " ").replace("_", " ")
        if re.match(url_regex, word) or re.match(date_regex, word) or re.match(time_regex, word) or re.match(
                email_regex, word) or re.match(words_with_stars, word):
            tokenized.append(word)
        else:
            matched = re.match(default_regex, word)
            if matched:
                tokenized.append(matched.group())

    return tokenized


def stem(line, tokens, aggressive=True):
    """
    Stems the tokens in the line using czech or slovak stemmer
    :param line: input line for language detection
    :param tokens: tokenized line
    :param aggressive: whether to use aggressive stemming
    :return: list of stemmed tokens
    """
    language = lang_detector(line, lang=('cs', 'sk'))  # detect language
    language = dict(language)
    try:
        if language['cs'] > language['sk']:  # if czech
            return [utils.stemmer_cs.stem(word, aggressive) for word in tokens]
        return [utils.stemmer_sk.stem(word, aggressive) for word in tokens]
    except KeyError:  # if no language detected
        return [utils.stemmer_cs.stem(word, aggressive) for word in tokens]


def lemmatize(line, tokens):
    """
    Lemmatizes the tokens using simplemma library
    :param line: input line for language detection
    :param tokens: input tokens
    :return: list of lemmatized tokens
    """

    lemmatized = [simplemma.lemmatize(word, lang=("cs", "sk"), greedy=True) for word in tokens]


    # don't lemmatize urls and emails
    url_regex = r"(https?:\/\/[^\s]+)"
    email_regex = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
    for i, token in enumerate(lemmatized):
        if re.match(url_regex, token) or re.match(email_regex, token):
            lemmatized[i] = tokens[i]
    return lemmatized
