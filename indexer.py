import json
import time
# TODO pickle

import numpy as np
from collections import defaultdict
import preprocessing_pipelines
from boolean_parser import infix_to_postfix
from crud import load_documents, create_index, fields, create_index_from_folder, delete_document, create_document, \
    update_document, create_index_from_url, create_document_from_url

# PIPELINE
pipeline = preprocessing_pipelines.pipeline_stemmer


# pipeline = preprocessing_pipelines.pipeline_lemmatizer


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
                scores[docID] += query[word] * index[field][word]["docIDs"][docID]["tf-idf"]
    for docID in scores:
        scores[docID] /= (query_norm * document_norms[field][docID])  # cosine similarity
    return scores


def calculate_k_best_scores(scores, k):
    """
    Calculates the k best scores of the documents
    :param scores: scores of the documents
    :param k: number of best scores to return
    :return: k best scores
    """
    if k > len(scores):
        k = len(scores)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]


def boolean_search(query, field, index, docs):
    print("Searching for the query: {} using the boolean model".format(query))
    postfix_query = infix_to_postfix(query)
    print("Postfix query:", postfix_query)
    stack = []
    max_id = docs["max_id"]
    unused_ids = docs["unused_ids"]
    for token in postfix_query:
        if token not in ["AND", "OR", "NOT"]:
            token = pipeline(token)[0]
            if field == "":
                all_docIDs = set()
                for f in fields:
                    if token in index[f]:
                        all_docIDs.update(index[f][token]["docIDs"].keys())
                stack.append(list(all_docIDs))
            else:
                if token in index[field]:
                    stack.append(list(index[field][token]["docIDs"].keys()))
                else:
                    stack.append([])
        else:
            if token == "AND":
                stack.append(set(stack.pop()).intersection(stack.pop()))
            elif token == "OR":
                stack.append(set(stack.pop()).union(stack.pop()))
            elif token == "NOT":
                all_ids = set(map(str, range(max_id + 1)))
                dif = stack.pop()
                all_ids.difference_update(dif)
                all_ids.difference_update(unused_ids)
                stack.append(all_ids)
    result = stack.pop()
    print("Found", len(result), "documents:")
    for docID in result:
        print("Document", docID)
        print("Title:", docs["docs"][str(docID)]["title"])
        print("\n")


def search(query, field, k, index, model, document_norms, docs):
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
    if model == "boolean":
        boolean_search(query, field, index, docs)
        return None
    query_orig = query
    query = pipeline(query)
    if field == "":  # search in all fields
        print("Searching for the query: {} in all fields".format(query_orig))
        score_by_field = {}
        docs_found = set()
        for field in fields:  # search in all fields
            query_tf_idf, query_norm = query_prep(query, index[field])
            scores = calculate_scores(query_tf_idf, query_norm, index, document_norms, field)
            docs_found.update(scores.keys())
            k_best_scores = calculate_k_best_scores(scores, k * 2)
            score_by_field[field] = k_best_scores

        print("Found", len(docs_found), "documents in total")
        print("Top", k, "documents:")
        field_weights = {"title": 1.1, "table_of_contents": 1, "infobox": 0.5, "content": 0.5}  # weights for the fields
        k_best_scores = {}
        for field in score_by_field:  # combine the scores from all fields
            for docID, score in score_by_field[field]:
                if docID not in k_best_scores:
                    k_best_scores[docID] = 0
                k_best_scores[docID] += score * field_weights[field]  # add the score with the weight
        k_best_scores = calculate_k_best_scores(k_best_scores, k)
        for docID, score in k_best_scores:
            print("Document", docID, "with score", score)
            print("Title:", docs["docs"][str(docID)]["title"])
            print("\n")

    else:  # search in the specified field
        print("Searching for the query: {} in the field {}".format(query_orig, field))
        query_tf_idf, query_norm = query_prep(query, index[field])
        scores = calculate_scores(query_tf_idf, query_norm, index, document_norms, field)
        k_best_scores = calculate_k_best_scores(scores, k)
        print("Found", len(scores), "documents in total")
        print("Top", k, "documents:")
        for docID, score in k_best_scores:
            print("Document", docID, "with score", score)
            print("Title:", docs["docs"][str(docID)]["title"])
            print("\n")
        proximity_search(query, docs, index, field, k_best_scores, 7)

def proximity_search(query, docs, index, field, k_best_scores, proximity):
    """
    Searches for the proximity query in the documents and prints the k best documents
    :param query:  proximity query to search for
    :param docs:  list of documents
    :param index:  index of the documents\
    :param field:  field to search in
    :param k_best_scores:  k best documents
    :param proximity: max proximity between the words
    :return: None (prints the k best documents)
    """
    for docID, score in k_best_scores:
        print("Proximity search for the query: {} in the field {} in the document {}".format(query, field, docID))
        positions = []
        for word in query:
            if word not in index[field]:
                print("Word", word, "not found in the index")
                break
            elif docID not in index[field][word]["docIDs"]:
                print("Word", word, "not found in the document")
                break
            else:
                positions.append(index[field][word]["docIDs"][docID]["pos"])
        if len(positions) == 0:
            continue
        # print("Positions:", positions)
        proximity_positions = [-1]
        for i in range(len(positions) - 1):
            pos_list1 = positions[i]
            pos_list2 = positions[i + 1]
            for pos1 in pos_list1:
                for pos2 in pos_list2:
                    if proximity_positions[-1] < pos1 < pos2 and pos2 - pos1 <= proximity:
                        proximity_positions.append(pos1)
                        break
        proximity_positions.append(pos2)
        proximity_positions = proximity_positions[1:]
        # print("Proximity positions:", proximity_positions)
        if len(proximity_positions) == len(positions):
            print("Found the proximity query in the document", proximity_positions)
            print("Snippet:")
            content = docs["docs"][str(docID)]["content"]
            content = preprocessing_pipelines.pipeline_tokenizer(content)[1]
            print(content)
            print(content[33])
            print(" ".join(content[max(0, proximity_positions[0] - 20):min(len(content), proximity_positions[-1] + 20)]))

            print("\n")






def main():
    # # -----------Loading and preprocessing the documents-------
    # docs, index, document_norms = create_index_from_folder(pipeline)
    # # ---------------------------------------------------------
    # # -----------Searching for the query-----------------------
    # query = "nůž OR dýka"
    # model = "boolean"
    # k = 3
    #
    # search(query, "title", k, index, model, document_norms, docs)
    # index, document_norms, docs = delete_document(index, document_norms, 850, docs, pipeline)
    # search(query, "title", k, index, model, document_norms, docs)
    # # search("nůž OR NOT dýka", "title", k, index, model, document_norms, docs)
    # # ---------------------------------------------------------
    # model = "tf-idf"
    # query = "Kdo je daedrický princ?"
    # field = ""  # search in all fields
    # k = 3
    #
    # search(query, field, k, index, model, document_norms, docs)
    #
    # index, document_norms, docs = delete_document(index, document_norms, 170, docs, pipeline)
    #
    # search(query, field, k, index, model, document_norms, docs)
    #
    # # ---------------------------------------------------------
    # query = "Příchod lidí a Noc Slz"
    # field = "table_of_contents"  # search in the table of contents
    # k = 3
    #
    # search(query, field, k, index, model, document_norms, docs)
    # # ---------------------------------------------------------
    # query = "dýka"
    # field = "content"  # search in the content
    # k = 5
    #
    # search(query, field, k, index, model, document_norms, docs)
    #
    # index, document_norms, docs = create_document(
    #     {"title": "Nůž a dýka a prdel", "table_of_contents": [], "infobox": "", "content": "Nůž a dýka a prdel"}, index,
    #     document_norms, docs, pipeline)
    # query = "dýka"
    # model = "tf-idf"
    # k = 3
    #
    # search(query, "content", k, index, model, document_norms, docs)
    #
    # index, document_norms, docs = delete_document(index, document_norms, 170, docs, pipeline)
    # search(query, "content", k, index, model, document_norms, docs)
    #
    # # ---------------------------------------------------------
    # query = "Keening"
    #
    # search(query, "title", k, index, model, document_norms, docs)
    #
    # index, document_norms, docs = update_document(376, "Keening prdel", "title", index, document_norms, docs, pipeline)
    # search(query, "title", k, index, model, document_norms, docs)
    #
    #
    # index, document_norms, docs = update_document(376, "Keening", "title", index, document_norms, docs, pipeline)
    # search(query, "title", k, index, model, document_norms, docs)

    # ---------------------------------------------------------
    seed_url = 'https://theelderscrolls.fandom.com/cs/wiki/Speci%C3%A1ln%C3%AD:V%C5%A1echny_str%C3%A1nky?from=%22%C5%A0%C3%ADlenci%22+z+Pl%C3%A1n%C3%AD'
    docs, index, document_norms = create_index_from_folder(pipeline, data_folder="data2", index_file="index2.json", document_norms_file="document_norms2.json")
    index, document_norms, docs = create_document_from_url("/cs/wiki/Železná_dýka", index, document_norms, docs, pipeline)
    search("dýka zbraň vyskytující", "content", 3, index, "tf-idf", document_norms, docs)

if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
