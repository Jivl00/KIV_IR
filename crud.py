import json
import os
import re

import numpy as np
from collections import defaultdict
import preprocessing_pipelines
from lang_detector import LangDetector

fields = ["title", "table_of_contents", "infobox", "content"]
lang_detector1 = LangDetector(only_czech_slovak=False)
lang_detector2 = LangDetector(only_czech_slovak=True)


def load_documents(data_folder="data", cache_name="document_cache.json"):
    """
    Loads documents from the data folder
    :param data_folder:  path to the data folder
    :param cache_name:  name of the cache file
    :return:  list of documents
    """
    docs = {"docs": {}, "unused_ids": [], "max_id": 0}
    index = 0
    contents = []
    for filename in os.listdir(data_folder):
        if filename.endswith(".json"):
            with open(os.path.join(data_folder, filename), "r", encoding="utf-8") as file:
                data = json.load(file)
                docs["docs"][str(index)] = data
                index += 1
                contents.append(data["content"])
    langs1 = lang_detector1.predict(contents)
    langs2 = lang_detector2.predict(contents)
    for doc, lang1, lang2 in zip(docs["docs"].keys(), langs1, langs2):
        docs["docs"][doc]["lang_all"] = lang1
        docs["docs"][doc]["lang_cz_sk"] = lang2
    docs["max_id"] = index - 1
    with open(cache_name, "w", encoding="utf-8") as file:
        json.dump(docs, file, ensure_ascii=False, indent=1)
    print("Loaded", len(docs["docs"]), "documents")
    return docs


def create_index(docs):
    """
    Creates an inverted index from the documents
    :param docs: list of tokenized documents
    :return: None (saves the index to a file)
    """
    index = {}
    document_norms = {}
    N = len(docs)
    for field in fields:
        index_field = defaultdict(lambda: {"idf": 0, "df": 0, "docIDs": {}})  # default value of int is 0
        # document norms are needed for cosine similarity
        document_field_norms = defaultdict(int)  # default value of int is 0
        for doc in docs:
            for token in set(doc[field]):
                index_field[token]["df"] += 1  # count the number of documents containing the word
                tf = doc[field].count(token)  # term frequency
                index_field[token]["docIDs"][doc["id"]] = 1 + np.log10(tf)  # compute tf

        for token in index_field:
            index_field[token]["idf"] = np.log10(N / float(index_field[token]["df"]))  # compute idf
            for docID in index_field[token]["docIDs"]:
                index_field[token]["docIDs"][docID] *= index_field[token]["idf"]  # compute tf-idf
                document_field_norms[docID] += (index_field[token]["docIDs"][docID]) ** 2

        document_field_norms = {docID: np.sqrt(document_field_norms[docID]) for docID in document_field_norms}
        index[field] = index_field
        document_norms[field] = document_field_norms

    return index, document_norms


def create_index_from_folder(pipeline, data_folder="data", index_file="index.json",
                             document_norms_file="document_norms.json",
                             save_to_file=True):
    """
    Creates an inverted index from the documents in the data folder
    :param pipeline:  preprocessing pipeline
    :param data_folder:  path to the data folder
    :param index_file:  path to the index file
    :param document_norms_file:  path to the document norms file
    :param save_to_file:  whether to save the index to a file
    :return: None (saves the index to a file)
    """
    docs = load_documents(data_folder)
    preprocessing_pipelines.clear_keywords_cache()
    preped_docs = []
    for doc_id in docs["docs"].keys():
        preped_docs.append(preprocessing_pipelines.preprocess(docs["docs"][doc_id], doc_id, pipeline))

    index, document_norms = create_index(preped_docs)  # skip this step if the index is already created

    if save_to_file:
        with open(index_file, "w", encoding="utf-8") as file:  # save the index to a file
            json.dump(dict(index), file, ensure_ascii=False, indent=4)
        with open(document_norms_file, "w", encoding="utf-8") as file:  # save the document norms to a file
            json.dump(dict(document_norms), file, ensure_ascii=False, indent=4)
        print("Index created and saved to a file")
    return docs, index, document_norms


def delete_document(index, document_norms, doc_id, docs, pipeline):
    """
    Removes the document from the index
    :param index:  inverted index
    :param document_norms:  norms of the documents
    :param doc_id:  id of the document to remove
    :param docs:  list of documents
    :return:  updated index and document norms and docs
    """
    doc_id = str(doc_id)
    print("Removing document \"{}\" with id {}".format(docs["docs"][doc_id]["title"], doc_id))
    docs["unused_ids"].append(doc_id)
    preprocessed_doc = preprocessing_pipelines.preprocess(docs["docs"][doc_id], doc_id, pipeline)
    N = len(docs["docs"]) - 1  # number of documents without the removed one
    for field in fields:
        for token in index[field]:
            # Remove the document from the index
            if doc_id in index[field][token]["docIDs"]:
                del index[field][token]["docIDs"][doc_id]
        if doc_id in document_norms[field]:
            # Remove the document from the document norms
            del document_norms[field][doc_id]
        # Update the idf and df
        tokens = preprocessed_doc[field]
        for token in set(tokens):
            old_idf = index[field][token]["idf"]
            index[field][token]["df"] -= 1
            df = index[field][token]["df"]
            if df > 0:
                idf = np.log10(N / float(df))
                index[field][token]["idf"] = idf
                docs_with_token = set(index[field][token]["docIDs"].keys())
                # Update the document norms
                for docID in docs_with_token:
                    old_tf_idf = index[field][token]["docIDs"][docID]
                    index[field][token]["docIDs"][docID] *= (idf / old_idf)
                    document_norms[field][docID] = np.sqrt(
                        document_norms[field][docID] ** 2 - (old_tf_idf ** 2) + (
                                    index[field][token]["docIDs"][docID] ** 2))
            else:
                # Remove the token from the index if it's not in any document
                index[field].pop(token)
    # Remove the document from the cache
    docs["docs"].pop(doc_id)
    return index, document_norms, docs

def create_document(doc, index, document_norms, docs, pipeline):
    """
    Adds the document to the index
    :param doc:  document to add - dictionary with fields: title, table_of_contents (list), infobox, content
    :param index:  inverted index
    :param document_norms:  norms of the documents
    :param docs:  list of documents
    :return:  updated index and document norms and docs
    """
    unused_ids = docs["unused_ids"]
    if len(unused_ids) > 0:
        doc_id = docs["unused_ids"].pop()
    else:
        doc_id = docs["max_id"] + 1
        docs["max_id"] = doc_id
    print("Adding document \"{}\" with id {}".format(doc["title"], doc_id))
    doc["lang_all"] = lang_detector1.predict([doc["content"]])[0]
    doc["lang_cz_sk"] = lang_detector2.predict([doc["content"]])[0]
    docs["docs"][doc_id] = doc
    preprocessed_doc = preprocessing_pipelines.preprocess(doc, doc_id, pipeline)
    N = len(docs["docs"])  # number of documents
    for field in fields:
        tokens = preprocessed_doc[field]
        for token in set(tokens):
            docs_with_token = set(index[field][token]["docIDs"].keys())
            if token not in index[field]:
                index[field][token] = {"idf": 0, "df": 0, "docIDs": {}}
            # Update the idf and df
            index[field][token]["df"] += 1
            df = index[field][token]["df"]
            old_idf = index[field][token]["idf"]
            idf = np.log10(N / float(df))
            index[field][token]["idf"] = idf
            # Update the tf-idf and norms of the documents affected by the change
            for docID in docs_with_token:
                old_tf_idf = index[field][token]["docIDs"][docID]
                index[field][token]["docIDs"][docID] *= (idf / old_idf)
                document_norms[field][docID] = np.sqrt(
                    document_norms[field][docID] ** 2 - (old_tf_idf ** 2) + (
                                index[field][token]["docIDs"][docID] ** 2))
            tf = tokens.count(token)
            tf_idf = (1 + np.log10(tf)) * idf
            index[field][token]["docIDs"][doc_id] = tf_idf
            document_norms[field][doc_id] = np.sqrt(tf_idf ** 2)
    return index, document_norms, docs
