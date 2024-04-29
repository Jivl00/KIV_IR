import time
# TODO pickle

import numpy as np
from collections import defaultdict
import preprocessing_pipelines
from boolean_parser import infix_to_postfix
from Index import Index

# PIPELINE
pipeline = preprocessing_pipelines.pipeline_stemmer
# pipeline = preprocessing_pipelines.pipeline_lemmatizer

fields = ["title", "table_of_contents", "infobox", "content"]


class SearchResult:
    def __init__(self, doc_id, score, title, snippet, lang):
        self.doc_id = doc_id
        self.score = score
        self.snippet = snippet
        self.title = title
        self.lang = lang
        self.detected_lang = {
            "cs": "Detekován český jazyk",
            "de": "Detekován německý jazyk",
            "en": "Detekován anglický jazyk",
            "es": "Detekován španělský jazyk",
            "fr": "Detekován francouzský jazyk",
            "it": "Detekován italský jazyk",
            "pl": "Detekován polský jazyk",
            "pt": "Detekován portugalský jazyk",
            "ru": "Detekován ruský jazyk",
            "sk": "Detekován slovenský jazyk",
        }.get(lang, "Detekován neznámý jazyk")

    def get_item(self):
        if self.score == 0:
            return [f"{self.title} (id: {self.doc_id}) - {self.detected_lang}", self.snippet]
        return [f"{self.title} (id: {self.doc_id} - score: {self.score:.3f}) - {self.detected_lang}", self.snippet]

    def __str__(self):
        return f"Document {self.doc_id} with score {self.score}\nTitle: {self.title}\nSnippet: {self.snippet}\n"


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
        if word in index.keys():
            query_tf_idf[word] = tf * index[word]["idf"]
        else:
            query_tf_idf[word] = 0
    query_norm = np.linalg.norm(list(query_tf_idf.values()))
    return query_tf_idf, query_norm


def calculate_scores(query, query_norm, index, field):
    """
    Calculates the scores for the documents based on the query
    :param query:  tf-idf of the query
    :param query_norm: norm of the query
    :param index:  index of the documents
    :param field: field to search in
    :return:  scores of the documents
    """
    scores = defaultdict(float)
    for word in query:
        if word in index.index[field]:
            for docID in index.index[field][word]["docIDs"]:
                if docID not in scores:
                    scores[docID] = 0
                scores[docID] += query[word] * index.index[field][word]["docIDs"][docID]["tf-idf"]
    for docID in scores:
        scores[docID] /= (query_norm * index.document_norms[field][docID])  # cosine similarity
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


def create_snippet(content, positions):
    """
    Creates a snippet from the content based on the positions
    :param content: content of the document
    :param positions: positions of the words in the snippet
    :return: snippet
    """
    WINDOW_SIZE = 30
    positions = np.array([item for sublist in positions for item in sublist])
    positions.sort()
    content_tokens = preprocessing_pipelines.pipeline_tokenizer(content, snippet=True)[1]
    print("Positions:", positions)
    if len(positions) == 0:
        return " ".join(content_tokens[:min(len(content_tokens), 2 * WINDOW_SIZE)])
    start = end = max_count = 0
    best_window = None

    while end < len(positions):
        if positions[end] - positions[start] > WINDOW_SIZE:
            start += 1
        else:
            if end - start + 1 > max_count:
                max_count = end - start + 1
                best_window = (positions[start], positions[end])
            end += 1
    print("Best window:", best_window)
    # for i in range(best_window[0], best_window[1] + 1):
    #     # content_tokens[i] = f"**{content_tokens[i]}**"
    #     # ('<span style="color:#8bb6e0;">' + title + '</span>')
    #     if i in positions:
    #         content_tokens[i] = f'<span style="background-color:#4B77BE;">{content_tokens[i]}</span>'
    # snippet = " ".join(content_tokens[max(0, best_window[0] - WINDOW_SIZE):min(len(content_tokens), best_window[1] + WINDOW_SIZE)])
    #
    snippet = ""
    for i in range(max(0, best_window[0] - WINDOW_SIZE),
                   min(len(content_tokens), best_window[1] + WINDOW_SIZE)):  # highlight the words
        if i in positions:
            content_tokens[i] = f'<span style="background-color:#4B77BE;">{content_tokens[i]}</span>'
        snippet += content_tokens[i] + " "

    return "... " + snippet + " ..."


def boolean_search(query, field, index):
    print("Searching for the query: {} using the boolean model".format(query))
    postfix_query = infix_to_postfix(query)
    print("Postfix query:", postfix_query)
    stack = []
    max_id = index.docs["max_id"]
    unused_ids = index.docs["unused_ids"]
    words = set()
    for token in postfix_query:
        if token not in ["AND", "OR", "NOT"]:
            if token == "":
                continue
            token = pipeline(token)[0]
            words.add(token)
            if field == "":
                all_docIDs = set()
                for f in fields:
                    if token in index.index[f]:
                        all_docIDs.update(index.index[f][token]["docIDs"].keys())
                stack.append(list(all_docIDs))
            else:
                if token in index.index[field]:
                    stack.append(list(index.index[field][token]["docIDs"].keys()))
                else:
                    stack.append([])
        else:
            if token == "AND" and len(stack) >= 2:
                stack.append(set(stack.pop()).intersection(stack.pop()))
            elif token == "OR" and len(stack) >= 2:
                stack.append(set(stack.pop()).union(stack.pop()))
            elif token == "NOT" and len(stack) >= 1:
                all_ids = set(map(str, range(max_id + 1)))
                dif = stack.pop()
                all_ids.difference_update(dif)
                all_ids.difference_update(unused_ids)
                stack.append(all_ids)
    if len(stack) != 1:
        print("Error in the query")
        return [], 0
    result = stack.pop()
    result_obj = []
    print("Found", len(result), "documents:")
    for docID in result:
        print("Document", docID)
        print("Title:", index.docs["docs"][str(docID)]["title"])
        print("\n")
        positions = []
        for word in words:
            if word in index.index["content"]:
                positions.append(index.index["content"][word]["docIDs"][docID]["pos"])
        snippet = create_snippet(index.docs["docs"][str(docID)]["content"], positions)
        print(snippet)
        result_obj.append(SearchResult(docID, 0, index.docs["docs"][str(docID)]["title"],
                                       snippet,
                                       index.docs["docs"][str(docID)]["lang_all"]))

    return result_obj, len(result)


def search(query, field, k, index, model):
    """
    Searches for the query in the index and prints the k best documents
    :param query:  query to search for
    :param field:  field to search in, if empty search in all fields
    :param k: number of best documents to return
    :param index:  index of the documents
    :param model:  model to use for the search
    :return: None (prints the k best documents)
    """
    print("=" * 50)
    if model == "boolean":
        if "\"" in query or "~" in query:
            query = query.replace("\"", "").split("~")[0]
            print(query)
            print("Proximity search is not supported in the boolean model")
        return boolean_search(query, field, index)
    query_orig = query
    query = pipeline(query)
    result_obj = []
    results_total = 0
    if field == "":  # search in all fields
        print("Searching for the query: {} in all fields".format(query_orig))
        score_by_field = {}
        docs_found = set()
        for field in fields:  # search in all fields
            query_tf_idf, query_norm = query_prep(query, index.index[field])
            scores = calculate_scores(query_tf_idf, query_norm, index, field)
            docs_found.update(scores.keys())
            k_best_scores = calculate_k_best_scores(scores, k * 2)
            score_by_field[field] = k_best_scores

        print("Found", len(docs_found), "documents in total")
        results_total = len(docs_found)
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
            print("Title:", index.docs["docs"][str(docID)]["title"])
            print("\n")
            result_obj.append(SearchResult(docID, score, index.docs["docs"][str(docID)]["title"],
                                           index.docs["docs"][str(docID)]["content"][0:1000],
                                           index.docs["docs"][str(docID)]["lang_all"]))

    else:  # search in the specified field
        print("Searching for the query: {} in the field {}".format(query_orig, field))
        query_tf_idf, query_norm = query_prep(query, index.index[field])
        scores = calculate_scores(query_tf_idf, query_norm, index, field)
        k_best_scores = calculate_k_best_scores(scores, k)
        print("Found", len(scores), "documents in total")
        results_total = len(scores)
        print("Top", k, "documents:")
        for docID, score in k_best_scores:
            print("Document", docID, "with score", score)
            print("Title:", index.docs["docs"][str(docID)]["title"])
            print("\n")
            result_obj.append(SearchResult(docID, score, index.docs["docs"][str(docID)]["title"],
                                           index.docs["docs"][str(docID)]["content"][0:1000],
                                           index.docs["docs"][str(docID)]["lang_all"]))

    return result_obj, results_total
    # proximity_search(query, docs, index, field, k_best_scores, 7)


def proximity_search(query, index, field, k_best_scores, proximity):
    """
    Searches for the proximity query in the documents and prints the k best documents
    :param query:  proximity query to search for
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
            if word not in index.index[field]:
                print("Word", word, "not found in the index")
                break
            elif docID not in index.index[field][word]["docIDs"]:
                print("Word", word, "not found in the document")
                break
            else:
                positions.append(index.index[field][word]["docIDs"][docID]["pos"])
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
            content = index.docs["docs"][str(docID)]["content"]
            content = preprocessing_pipelines.pipeline_tokenizer(content)[1]
            print(content)
            print(content[33])
            print(
                " ".join(content[max(0, proximity_positions[0] - 20):min(len(content), proximity_positions[-1] + 20)]))

            print("\n")


index1 = Index(pipeline, "index_1", "test_index")
index1.create_index_from_folder("data")
indexes = [index1]


def main():
    # index1 = Index(pipeline, "index_1", "test_index")
    # index1.create_index_from_folder("data")
    # ---------------------------------------------------------
    # -----------Searching for the query-----------------------
    query = "\"zbraň OR dýka\""
    query = "OR"
    model = "boolean"
    k = 3

    search(query, "", k, index1, model)
    # index1.delete_document(850)
    # search(query, "", k, index1, model)

    # ---------------------------------------------------------

    # search("nůž OR NOT dýka", "title", k, index1.index, model, index1.document_norms, index1.docs)
    # ---------------------------------------------------------
    model = "tf-idf"
    query = "Kdo je daedrický princ?"
    field = ""  # search in all fields
    k = 3

    search(query, field, k, index1, model)

    index1.delete_document(170)

    search(query, field, k, index1, model)

    # ---------------------------------------------------------
    query = "Příchod lidí a Noc Slz"
    field = "table_of_contents"  # search in the table of contents
    k = 3

    search(query, field, k, index1, model)
    # ---------------------------------------------------------
    query = "dýka"
    field = "content"  # search in the content
    k = 5

    search(query, field, k, index1, model)

    index1.create_document(
        {"title": "Nůž a dýka a prdel", "table_of_contents": [], "infobox": "", "content": "Nůž a dýka a prdel"})
    query = "dýka"
    model = "tf-idf"
    k = 3

    search(query, "content", k, index1, model)

    index1.delete_document(170)
    search(query, "content", k, index1, model)

    # ---------------------------------------------------------
    query = "Keening"

    search(query, "title", k, index1, model)

    index1.update_document(376, "Keening prdel", "title")
    search(query, "title", k, index1, model)

    index1.update_document(376, "Keening", "title")
    search(query, "title", k, index1, model)

    # ---------------------------------------------------------
    seed_url = 'https://theelderscrolls.fandom.com/cs/wiki/Speci%C3%A1ln%C3%AD:V%C5%A1echny_str%C3%A1nky?from=%22%C5%A0%C3%ADlenci%22+z+Pl%C3%A1n%C3%AD'
    index2 = Index(pipeline, "index2", "test_index2")
    index2.create_index_from_folder("data2")
    index2.create_document_from_url("/cs/wiki/Železná_dýka")
    search("dýka zbraň vyskytující", "content", 3, index2, "tf-idf")


if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
