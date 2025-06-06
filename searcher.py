import itertools
import time
import numpy as np
from collections import defaultdict
from utils.boolean_parser import infix_to_postfix
from config import *

fields = ["title", "table_of_contents", "infobox", "content"]

class SearchResult:
    """
    Class representing the search result

    Attributes:
    doc_id: id of the document
    score: score of the document
    title: title of the document
    snippet: snippet of the document
    lang: language of the document - abbreviation
    detected_lang: detected language of the document - full name

    """

    def __init__(self, doc_id, score, title, snippet, lang="cs"):
        """
        Initializes the search result
        :param doc_id: id of the document
        :param score: score of the document
        :param title: title of the document
        :param snippet: snippet of the document
        :param lang: language of the document
        """
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
        """
        Returns the search result as a list
        :return: search result as a list
        """
        if self.score == 0:
            return [f"{self.title} (id: {self.doc_id}) - {self.detected_lang}", self.snippet]
        return [f"{self.title} (id: {self.doc_id} - score: {self.score:.3f}) - {self.detected_lang}", self.snippet]

    def __str__(self):
        """
        Returns the search result as a string
        :return: search result as a string
        """
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


def create_snippet(content, positions, prox_search=False):
    """
    Creates a snippet from the content based on the positions
    :param content: content of the document
    :param positions: positions of the words in the snippet
    :param prox_search: whether the search is proximity search
    :return: snippet
    """
    content_tokens = preprocessing_pipelines.pipeline_tokenizer(content, snippet=True)[1]

    # For proximity search, window is given by the first and last word
    if prox_search:
        best_window = [positions[0], positions[-1]]
    else:
        positions = np.array([item for sublist in positions for item in sublist])
        positions.sort()
        if len(positions) == 0:
            return " ".join(content_tokens[:min(len(content_tokens), 2 * WINDOW_SIZE)])
        start = end = max_count = 0
        best_window = None

        # Find the best window with the most highlightable words
        while end < len(positions):
            if positions[end] - positions[start] > WINDOW_SIZE:
                start += 1
            else:
                if end - start + 1 > max_count:
                    max_count = end - start + 1
                    best_window = (positions[start], positions[end])
                end += 1

    snippet = ""
    for i in range(max(0, best_window[0] - WINDOW_SIZE),
                   min(len(content_tokens), best_window[1] + WINDOW_SIZE)):  # highlight the words
        if i in positions:
            content_tokens[i] = f'<span style="background-color:#4B77BE;">{content_tokens[i]}</span>'
        snippet += content_tokens[i] + " "

    return "... " + snippet + " ..."


def boolean_search(query, field, k, index, verbose=False):
    """
    Searches for the query in the index using the boolean model
    :param query: query to search for
    :param field: field to search in (if empty search in all fields)
    :param k: number of best documents to return
    :param index: index of the documents
    :param verbose: whether to print the results
    :return: result_obj, len(result) - list of the search results and the number of found documents
    """
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
            prep = pipeline(token)
            if len(prep) == 0:
                continue
            token = prep[0]
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
    for docID in list(result)[:k]:
        positions = []
        for word in words:
            if word in index.index["content"]:
                if docID in index.index["content"][word]["docIDs"]:
                    positions.append(index.index["content"][word]["docIDs"][docID]["pos"])
        if verbose:
            print("Top", k, "documents:")
            print("Document", docID)
            print("Title:", index.docs["docs"][str(docID)]["title"])
            print("\n")
        if "lang_all" in index.docs["docs"][str(docID)]:
            snippet = create_snippet(index.docs["docs"][str(docID)]["content"], positions)
            result_obj.append(SearchResult(docID, 0, index.docs["docs"][str(docID)]["title"],
                                           snippet,
                                           index.docs["docs"][str(docID)]["lang_all"]))
        else:
            result_obj.append(SearchResult(docID, 0, index.docs["docs"][str(docID)]["title"],
                                           "snippet"))

    return result_obj, len(result)


def search(query, field, k, index, model, verbose=False):
    """
    Searches for the query in the index and prints the k best documents
    :param query:  query to search for
    :param field:  field to search in, if empty search in all fields
    :param k: number of best documents to return
    :param index:  index of the documents
    :param model:  model to use for the search
    :param verbose: whether to print the results
    :return: result_obj, results_total - list of the search results and the number of found documents
    """
    print("=" * 50)
    if model == "boolean":
        if "\"" in query or "~" in query:
            query = query.replace("\"", "").split("~")[0]
            print("Proximity search is not supported in the boolean model")
        return boolean_search(query, field, k, index, verbose)
    proximity = 0
    if "~" in query:
        proximity = query.split("~")[1]
        if not proximity.isdigit():
            print("Proximity must be a number")
            return [], 0
        proximity = int(proximity)
        query = query.split("~")[0]
    if "\"" in query:
        query = query.replace("\"", "")
        proximity = 1

    query_orig = query
    query = pipeline(query)
    result_obj = []
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

        results_total = len(docs_found)
        field_weights = {"title": 1.1, "table_of_contents": 1, "infobox": 0.5, "content": 0.5}  # weights for the fields
        k_best_scores = {}
        for field in score_by_field:  # combine the scores from all fields
            for docID, score in score_by_field[field]:
                if docID not in k_best_scores:
                    k_best_scores[docID] = 0
                k_best_scores[docID] += score * field_weights[field]  # add the score with the weight
        if proximity > 0 and len(query) > 1: # proximity search
            return proximity_search(query, index, "content", k_best_scores, proximity, k, verbose)
        print("Found", results_total, "documents in total")
        if verbose:
            print("Top", k, "documents:")
        k_best_scores = calculate_k_best_scores(k_best_scores, k)
        format_result(index, query, k_best_scores, result_obj, verbose)

    else:  # search in the specified field
        print("Searching for the query: {} in the field {}".format(query_orig, field))
        query_tf_idf, query_norm = query_prep(query, index.index[field])
        scores = calculate_scores(query_tf_idf, query_norm, index, field)

        if proximity > 0 and len(query) > 1:  # proximity search
            return proximity_search(query, index, "content", scores, proximity, k, verbose)
        k_best_scores = calculate_k_best_scores(scores, k)
        print("Found", len(scores), "documents in total")
        results_total = len(scores)
        if verbose:
            print("Top", k, "documents:")
        format_result(index, query, k_best_scores, result_obj, verbose)

    return result_obj, results_total


def format_result(index, query, k_best_scores, result_obj, verbose=True):
    """
    Formats the search results and prints them if verbose is True
    :param index: index of the documents
    :param query: query to search for
    :param k_best_scores: k best scores of the documents
    :param result_obj: list of the search results
    :param verbose: whether to print the results
    :return: None directly, but appends the search results to the result_obj
    """
    for docID, score in k_best_scores:
        if verbose:
            print(f"Document {docID} with score {score:.3f}")
            print("Title:", index.docs["docs"][str(docID)]["title"])
            print("\n")
        if "lang_all" in index.docs["docs"][str(docID)]:
            positions = []
            for word in query:
                if word in index.index["content"]:
                    if str(docID) in index.index["content"][word]["docIDs"]:
                        positions.append(index.index["content"][word]["docIDs"][str(docID)]["pos"])
            snippet = create_snippet(index.docs["docs"][str(docID)]["content"], positions)
            result_obj.append(SearchResult(docID, score, index.docs["docs"][str(docID)]["title"],
                                           snippet,
                                           index.docs["docs"][str(docID)]["lang_all"]))
        else:
            result_obj.append(SearchResult(docID, score, index.docs["docs"][str(docID)]["title"],
                                           "snippet"))


def proximity_search(query, index, field, scores, proximity, k, verbose=False):
    """
    Searches for the proximity query in the documents
    :param query:  proximity query to search for
    :param index:  index of the documents
    :param field:  field to search in
    :param scores:  scores of the documents
    :param proximity: max proximity between the words
    :param k: number of best documents to return
    :param verbose: whether to print the results
    :return: result_obj, results_total - list of the search results and the number of found documents
    """
    best_scores = defaultdict(float)
    doc_positions = defaultdict(list)
    for docID in scores:
        # print("Proximity search for the query: {} in the field {} in the document {}".format(query, field, docID))
        positions = []
        for word in query:
            if word not in index.index[field]: # word not found in the index
                break
            elif docID not in index.index[field][word]["docIDs"]: # word not found in the document
                break
            else:
                positions.append(index.index[field][word]["docIDs"][docID]["pos"])
        if len(positions) != len(query):
            continue
        def find_combinations(positions, current, i, proximity):
            if i == len(positions):
                if all(abs(current[j] - current[j - 1]) <= proximity for j in range(1, len(current))):
                    return current
                else:
                    return []
            else:
                for pos in positions[i]:
                    combination = find_combinations(positions, current + [pos], i + 1, proximity)
                    if combination:
                        return combination
                return []

        proximity_positions = find_combinations(positions, [], 0, proximity)
        proximity_positions = sorted(proximity_positions)

        # Post-filtering - check words consecutivness
        if len(proximity_positions) == len(positions):
            for p, pos in zip(proximity_positions, positions):
                if p not in pos:
                    proximity_positions[0] = -1
                    break
        else:
            proximity_positions.append(-1)

        if proximity_positions[0] != -1:
            best_scores[docID] = scores[docID]
            doc_positions[docID] = proximity_positions
    results_total = len(best_scores)
    if k > len(best_scores):
        k = len(best_scores)

    k_best_scores = dict(itertools.islice(best_scores.items(), k))
    result_obj = []
    for docID in k_best_scores.keys():
        snippet = create_snippet(index.docs["docs"][str(docID)]["content"], doc_positions[docID], prox_search=True)
        if verbose:
            print(f"Document {docID} with score {best_scores[docID]:.3f}")
            print("Title:", index.docs["docs"][str(docID)]["title"])
            print("\n")
            print(snippet)
        result_obj.append(SearchResult(docID, best_scores[docID], index.docs["docs"][str(docID)]["title"],
                                       snippet,
                                       index.docs["docs"][str(docID)]["lang_all"]))
    return result_obj, results_total
