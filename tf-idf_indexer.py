import json
import os
import re
import time

import numpy as np
from collections import defaultdict
import preprocessing_pipelines

# PIPELINE
# pipeline = preprocessor.pipeline_stemmer
pipeline = preprocessing_pipelines.pipeline_lemmatizer


# FIELDS
# given by the web crawler
fields = ["title", "table_of_contents", "infobox", "content"]

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

    print("Loaded", len(docs), "documents")
    return docs

def preprocess(doc):
    """
    Preprocesses the document using the lemmatizer or stemmer pipeline
    :param doc: input document
    :return: preprocessed document (tokenized, lowercased, without stopwords, etc.)
    """

    # this structure is assumed - output of the web crawler
    preprocessed_data = {"title": pipeline(doc["title"]), "table_of_contents": doc["table_of_contents"],
                            "infobox": pipeline(doc["infobox"]), "content": pipeline(doc["content"]), "id": doc["id"]}
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

def query_prep(query, index):
    """
    Prepares the query for the search by computing tf-idf and query norm
    :param query: tokenized query
    :param index: index of the documents
    :return: query_tf_idf, query_norm
    """
    query_tf_idf = defaultdict(int)
    for word in set(query):
        tf = query.count(word)
        tf = 1 + np.log10(tf)
        if word in index:
            query_tf_idf[word] = tf * index[word]["idf"]
        else:
            query_tf_idf[word] = 0
    query_norm = np.linalg.norm(list(query_tf_idf.values()))
    return query_tf_idf, query_norm


def calculate_scores(query, query_norm, index, document_norms, field):
    """
    Calculates the scores for the documents based on the query
    :param query:  tf-idf of the query
    :param query_norm: norm of the query
    :param index:  index of the documents
    :param document_norms: norms of the documents
    :param field: field to search in
    :return:  scores of the documents
    """
    scores = defaultdict(float)
    for word in query:
        if word in index[field]:
            for docID in index[field][word]["docIDs"]:
                if docID not in scores:
                    scores[docID] = 0
                scores[docID] += query[word] * index[field][word]["docIDs"][docID]
    for docID in scores:
        scores[docID] /= (query_norm * document_norms[field][docID]) # cosine similarity
    return scores

def calculate_k_best_scores(scores, k):
    """
    Calculates the k best scores of the documents
    :param scores: scores of the documents
    :param k: number of best scores to return
    :return: k best scores
    """
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]


def search(query, field, k, index, document_norms, docs):
    """
    Searches for the query in the index and prints the k best documents
    :param query:  query to search for
    :param field:  field to search in, if empty search in all fields
    :param k: number of best documents to return
    :param index:  index of the documents
    :param document_norms:  norms of the documents
    :param docs:  list of documents
    :return: None (prints the k best documents)
    """
    print("=" * 50)
    if field == "": # search in all fields
        print("Searching for the query: {} in all fields".format(query))
        score_by_field = {}
        query = pipeline(query)
        for field in fields: # search in all fields
            query_tf_idf, query_norm = query_prep(query, index[field])
            scores = calculate_scores(query_tf_idf, query_norm, index, document_norms, field)
            k_best_scores = calculate_k_best_scores(scores, k)
            score_by_field[field] = k_best_scores
        print("Top", k, "documents:")
        field_weights = {"title": 1.1, "table_of_contents": 1, "infobox": 0.5, "content": 0.5} # weights for the fields
        k_best_scores = {}
        for field in score_by_field: # combine the scores from all fields
            for docID, score in score_by_field[field]:
                if docID not in k_best_scores:
                    k_best_scores[docID] = 0
                k_best_scores[docID] += score * field_weights[field] # add the score with the weight
        k_best_scores = calculate_k_best_scores(k_best_scores, k)
        for docID, score in k_best_scores:
            print("Document", docID, "with score", score)
            print("Title:", docs[int(docID)]["title"])
            print("\n")

    else: # search in the specified field
        print("Searching for the query: {} in the field {}".format(query, field))
        query = pipeline(query)
        query_tf_idf, query_norm = query_prep(query, index[field])
        scores = calculate_scores(query_tf_idf, query_norm, index, document_norms, field)
        k_best_scores = calculate_k_best_scores(scores, k)
        print("Top", k, "documents:")
        for docID, score in k_best_scores:
            print("Document", docID, "with score", score)
            print("Title:", docs[int(docID)]["title"])
            print("\n")

def main():
# -----------Loading and preprocessing the documents-------
    docs = load_documents()
    preped_docs = []
    for doc in docs:
        preped_docs.append(preprocess(doc))
# -----------Indexing the documents------------------------
    create_index(preped_docs) # skip this step if the index is already created
# -----------Loading the index and document norms-----------
    with open("index.json", "r", encoding="utf-8") as file:
        index = json.load(file)

    with open("document_norms.json", "r", encoding="utf-8") as file:
        document_norms = json.load(file)
# ---------------------------------------------------------
# -----------Searching for the query-----------------------
    query = "Kdo je daedrický princ?"
    field = "" # search in all fields
    k = 3

    search(query, field, k, index, document_norms, docs)
# ---------------------------------------------------------
    query = "Příchod lidí a Noc Slz"
    field = "table_of_contents" # search in the table of contents
    k = 2

    search(query, field, k, index, document_norms, docs)
# ---------------------------------------------------------
    query = "nůž a dýka"
    field = "content" # search in the content
    k = 5

    search(query, field, k, index, document_norms, docs)

if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))

