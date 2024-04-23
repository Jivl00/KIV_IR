import json
import os
import re

import numpy as np
from collections import defaultdict

fields = ["title", "table_of_contents", "infobox", "content"]

# UNUSED IDs
unused_ids = []
max_id = 0

def load_documents(data_folder="data"):
    """
    Loads documents from the data folder
    :param data_folder:  path to the data folder
    :return:  list of documents
    """
    docs = []
    index = 0
    for filename in os.listdir(data_folder):
        if filename.endswith(".json"):
            with open(os.path.join(data_folder, filename), "r", encoding="utf-8") as file:
                data = json.load(file)
                data["id"] = str(index) # add document id
                index += 1
                docs.append(data)
    global max_id
    max_id = index
    print("Loaded", len(docs), "documents")
    return docs

def preprocess(doc, pipeline):
    """
    Preprocesses the document using the lemmatizer or stemmer pipeline
    :param doc: input document
    :param pipeline: preprocessing pipeline
    :return: preprocessed document (tokenized, lowercased, without stopwords, etc.)
    """

    # this structure is assumed - output of the web crawler
    preprocessed_data = {"title": pipeline(doc["title"], True), "table_of_contents": doc["table_of_contents"],
                            "infobox": pipeline(doc["infobox"], True), "content": pipeline(doc["content"], True), "id": doc["id"]}
    chapter_num = r"\b\d+(?:\.\d+)*\b"  # regex for chapter number
    preprocessed_data["table_of_contents"] = preprocessed_data["table_of_contents"] = [word for chapter in
                                             preprocessed_data["table_of_contents"] for word in pipeline(re.sub
                                            (chapter_num, "", chapter))]  # remove chapter numbers and preprocess the chapters
    return preprocessed_data

def create_index(docs):
    """
    Creates an inverted index from the documents
    :param docs: list of tokenized documents
    :return: None (saves the index to a file)
    """
    index = {}
    document_norms = {}
    for field in fields:
        index_field = defaultdict(lambda: {"idf": 0, "docIDs": {}})  # default value of int is 0
        # document norms are needed for cosine similarity
        document_field_norms = defaultdict(int)  # default value of int is 0
        N = len(docs)
        for doc in docs:
            for token in set(doc[field]):
                index_field[token]["idf"] += 1  # count the number of documents containing the word
                tf = doc[field].count(token)  # term frequency
                index_field[token]["docIDs"][doc["id"]] = 1 + np.log10(tf)  # compute tf

        for token in index_field:
            index_field[token]["idf"] = np.log10(N / float(index_field[token]["idf"]))  # compute idf
            for docID in index_field[token]["docIDs"]:
                index_field[token]["docIDs"][docID] *= index_field[token]["idf"] # compute tf-idf
                document_field_norms[docID] += index_field[token]["docIDs"][docID] ** 2

        document_field_norms = {docID: np.sqrt(document_field_norms[docID]) for docID in document_field_norms}
        index[field] = index_field
        document_norms[field] = document_field_norms

    with open("index.json", "w", encoding="utf-8") as file: # save the index to a file
        json.dump(dict(index), file, ensure_ascii=False, indent=4)
    with open("document_norms.json", "w", encoding="utf-8") as file: # save the document norms to a file
        json.dump(dict(document_norms), file, ensure_ascii=False, indent=4)
    print("Index created and saved to a file")