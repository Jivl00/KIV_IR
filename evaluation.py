import csv
import time
import pandas as pd

import preprocessing_pipelines
from Index import Index
from searcher import search

# PIPELINE
# pipeline = preprocessing_pipelines.pipeline_stemmer
# pipeline = preprocessing_pipelines.pipeline_lemmatizer
pipeline = preprocessing_pipelines.pipeline_lemmatizer2


def load_queries():
    """
    Loads the queries from eval_data/czechTopics.csv
    :return: list of queries
    """
    queries = {}
    queries_file = "eval_data/czechTopics.csv"
    df = pd.read_csv(queries_file, delimiter="|", encoding="utf-8")
    for index, row in df.iterrows():
        queries[row["Id"]] = row["Title"] # TODO: try other fields
    return queries



def load_documents():
    """
    Loads the documents from eval_data/czechData.csv
    :return: list of documents
    """
    documents_file = "eval_data/czechData.csv"
    df = pd.read_csv(documents_file, delimiter="|", encoding="utf-8", quoting=csv.QUOTE_NONE)
    # throw away the last column - Date
    df = df.iloc[:, :-1]
    df.columns = ["id", "title", "content"]
    df["table_of_contents"] = ""
    df["infobox"] = ""
    # if value is NaN, replace it with empty string
    df = df.fillna("")
    # print(df)

    return df.to_dict(orient="records")
def create_doc_cache(Index_obj, eval_docs):
    """
    Loads documents from the data folder and saves them to a cache
    :param Index_obj: Index object
    :param eval_docs: list of documents
    """
    Index_obj.docs = {"docs": {}, "unused_ids": [], "max_id": 0}
    index = 0
    for data in eval_docs:
        Index_obj.docs["docs"][str(index)] = data
        index += 1
    Index_obj.docs["max_id"] = index - 1
    print("Loaded", len(Index_obj.docs["docs"]), "documents")



time_start = time.time()
queries = load_queries()
print(queries)
eval_docs = load_documents()
time_end = time.time()
print("Loaded documents in", time_end - time_start, "seconds")
time_start = time.time()
eval_index = Index(pipeline, "eval_index_lem2", "eval_index")

# create_doc_cache(eval_index, eval_docs)
# preped_docs = []
# for doc_id in eval_index.docs["docs"].keys():
#     preped_docs.append(preprocessing_pipelines.preprocess(eval_index.docs["docs"][doc_id], doc_id, eval_index.pipeline, remove_stopwords=True))
# time_end = time.time()
# print("Preprocessed documents in", time_end - time_start, "seconds")
# time_start = time.time()
# eval_index.create_index(preped_docs)
# time_end = time.time()
# print("Created index in", time_end - time_start, "seconds")
# time_start = time.time()
# eval_index.save_index()
# time_end = time.time()
# print("Saved index in", time_end - time_start, "seconds")

time_start = time.time()
eval_index.load_index()
time_end = time.time()
print("Loaded index in", time_end - time_start, "seconds")
model = "tf-idf"
time_start = time.time()
eval_results = ""
for query_id in queries.keys():
    result_objs, num = search(queries[query_id], "", 100000, eval_index, model)
    if num == 0:
        # t.getId() + " Q0 " + "abc" + " " + "99" + " " + 0.0 + " runindex1");
        line = query_id + " Q0 " + "abc" + " " + "99" + " " + str(0.0) + " runindex1"
        continue
    for rank, result in enumerate(result_objs):
        # line = query.id + " Q0 " + doc.id + " " + result.rank + " " + result.score + " runindex1"
        true_doc_id = eval_index.docs["docs"][result.doc_id]["id"]
        line = query_id + " Q0 " + true_doc_id + " " + str(rank + 1) + " " + str(result.score) + " runindex1"
        eval_results += line + "\n"

with open("eval_data/eval_results_lem2.txt", "w", encoding="utf-8") as file:
    file.write(eval_results)



"""
STEMMING
---------------------------------------
Loaded documents in 3.176795244216919 seconds
Loaded 81735 documents
Preprocessed documents in 478.4098148345947 seconds
Created index in 94.56351232528687 seconds
Saved index in 112.15081214904785 seconds

map             all     0.0895

LEMMATIZATION lemmagen3 
---------------------------------------
Loaded 81735 documents
Preprocessed documents in 409.73852705955505 seconds
Created index in 96.42285346984863 seconds
Saved index in 116.01357436180115 seconds
Loaded index in 74.79287338256836 seconds

map             all     0.0176


LEMMATIZATION - czech and slovak
---------------------------------------
Loaded 81735 documents
Preprocessed documents in 368.571417093277 seconds
Created index in 98.80106329917908 seconds
Saved index in 116.73172044754028 seconds
Loaded index in 83.92605090141296 seconds

map             all     0.0283

"""


