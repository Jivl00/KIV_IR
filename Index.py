import json
import os
import web_crawler
import numpy as np
from collections import defaultdict
import preprocessing_pipelines
from lang_detector import LangDetector

class Index:
    def __init__(self, pipeline, index_folder, index_name):
        self.pipeline = pipeline
        self.index_folder = index_folder
        self.index_name = index_name
        self.docs = {}
        self.index = {}
        self.document_norms = {}
        self.keywords = set()  # TODO: implement keyword extraction
        self.fields = ["title", "table_of_contents", "infobox", "content"]
        self.lang_detector_all = LangDetector(only_czech_slovak=False)
        self.lang_detector_cz_sk = LangDetector(only_czech_slovak=True)
        if not os.path.exists(index_folder):
            os.makedirs(index_folder)

    def save_index(self):
        """
        Saves the index to a file
        """
        with open(os.path.join(self.index_folder, self.index_name + "_index.json"), "w", encoding="utf-8") as file:
            json.dump(self.index, file, ensure_ascii=False, indent=1)
        with open(os.path.join(self.index_folder, self.index_name + "_document_norms.json"), "w", encoding="utf-8") as file:
            json.dump(self.document_norms, file, ensure_ascii=False, indent=1)
        with open(os.path.join(self.index_folder, self.index_name + "_docs.json"), "w", encoding="utf-8") as file:
            json.dump(self.docs, file, ensure_ascii=False, indent=1)
        with open(os.path.join(self.index_folder, self.index_name + "_keywords.json"), "w", encoding="utf-8") as file:
            json.dump(list(self.keywords), file, ensure_ascii=False, indent=1)

    def load_index(self):
        """
        Loads the index from a file
        """
        with open(os.path.join(self.index_folder, self.index_name + "_index.json"), "r", encoding="utf-8") as file:
            self.index = json.load(file)
        with open(os.path.join(self.index_folder, self.index_name + "_document_norms.json"), "r", encoding="utf-8") as file:
            self.document_norms = json.load(file)
        with open(os.path.join(self.index_folder, self.index_name + "_docs.json"), "r", encoding="utf-8") as file:
            self.docs = json.load(file)
        with open(os.path.join(self.index_folder, self.index_name + "_keywords.json"), "r", encoding="utf-8") as file:
            self.keywords = set(json.load(file))

    def create_doc_cache(self, data_folder="data"):
        """
        Loads documents from the data folder and saves them to a cache
        :param data_folder:  path to the data folder
        """
        self.docs = {"docs": {}, "unused_ids": [], "max_id": 0}
        index = 0
        contents = []
        for filename in os.listdir(data_folder):
            if filename.endswith(".json"):
                with open(os.path.join(data_folder, filename), "r", encoding="utf-8") as file:
                    data = json.load(file)
                    self.docs["docs"][str(index)] = data
                    index += 1
                    contents.append(data["content"])
        langs1 = self.lang_detector_all.predict(contents)
        langs2 = self.lang_detector_cz_sk.predict(contents)
        for doc, lang1, lang2 in zip(self.docs["docs"].keys(), langs1, langs2):
            self.docs["docs"][doc]["lang_all"] = lang1
            self.docs["docs"][doc]["lang_cz_sk"] = lang2
        self.docs["max_id"] = index - 1
        print("Loaded", len(self.docs["docs"]), "documents")

    def create_index(self, preped_docs):
        """
        Creates an inverted index from the documents
        """
        N = len(preped_docs)
        for field in self.fields:
            self.index[field] = defaultdict(
                lambda: {"idf": 0, "df": 0, "docIDs": defaultdict(lambda: {"tf": 0, "tf-idf": 0, "pos": []})})
            # document norms are needed for cosine similarity
            document_field_norms = defaultdict(int)
            for doc in preped_docs:
                seen = set()
                for pos, token in enumerate(doc[field]):
                    if token not in seen:
                        seen.add(token)
                        self.index[field][token]["df"] += 1  # count the number of documents containing the word
                        tf = doc[field].count(token)  # term frequency
                        tf = 1 + np.log10(tf)  # compute tf
                        self.index[field][token]["docIDs"][doc["id"]]["tf"] = tf  # store tf
                        self.index[field][token]["docIDs"][doc["id"]]["tf-idf"] = tf
                    self.index[field][token]["docIDs"][doc["id"]]["pos"].append(pos)

            for token in self.index[field]:
                self.index[field][token]["idf"] = np.log10(N / float(self.index[field][token]["df"]))  # compute idf
                for docID in self.index[field][token]["docIDs"]:
                    self.index[field][token]["docIDs"][docID]["tf-idf"] *= self.index[field][token][
                        "idf"]  # compute tf-idf
                    document_field_norms[docID] += (self.index[field][token]["docIDs"][docID]["tf-idf"]) ** 2

            document_field_norms = {docID: np.sqrt(document_field_norms[docID]) for docID in document_field_norms}
            self.document_norms[field] = document_field_norms

    def create_index_from_folder(self, data_folder="data"):
        """
        Creates an inverted index from the documents in the data folder
        :param data_folder:  path to the data folder
        """
        self.create_doc_cache(data_folder)
        preped_docs = []
        for doc_id in self.docs["docs"].keys():
            preped_docs.append(preprocessing_pipelines.preprocess(self.docs["docs"][doc_id], doc_id, self.pipeline))

        self.create_index(preped_docs)

    def create_index_from_url(self, seed_url, data_folder="data"):
        """
        Creates an inverted index for the documents crawled from the seed URL
        :param seed_url: URL of the seed page
        :param data_folder:  path to the data folder
        """
        topics_refs = web_crawler.crawl(seed_url, 1)

        if not os.path.exists(data_folder):
            os.makedirs(data_folder)

        web_crawler.scrape_urls(topics_refs, folder=data_folder, wait_time=1)
        self.create_index_from_folder(data_folder)

    def delete_document(self, doc_id):
        """
        Removes the document from the index
        :param doc_id:  id of the document to remove
        :return:  updated index and document norms and docs
        """
        doc_id = str(doc_id)
        print("Removing document \"{}\" with id {}".format(self.docs["docs"][doc_id]["title"], doc_id))
        self.docs["unused_ids"].append(doc_id)
        preprocessed_doc = preprocessing_pipelines.preprocess(self.docs["docs"][doc_id], doc_id, self.pipeline)
        N = len(self.docs["docs"]) - 1  # number of documents without the removed one
        for field in self.fields:
            for token in self.index[field]:
                # Remove the document from the index
                if doc_id in self.index[field][token]["docIDs"]:
                    del self.index[field][token]["docIDs"][doc_id]
            if doc_id in self.document_norms[field]:
                # Remove the document from the document norms
                del self.document_norms[field][doc_id]
            # Update the idf and df
            tokens = preprocessed_doc[field]
            for token in set(tokens):
                old_idf = self.index[field][token]["idf"]
                self.index[field][token]["df"] -= 1
                df = self.index[field][token]["df"]
                if df > 0:
                    idf = np.log10(N / float(df))
                    self.index[field][token]["idf"] = idf
                    docs_with_token = set(self.index[field][token]["docIDs"].keys())
                    # Update the document norms
                    for docID in docs_with_token:
                        old_tf_idf = self.index[field][token]["docIDs"][docID]["tf-idf"]
                        self.index[field][token]["docIDs"][docID]["tf-idf"] = (
                                self.index[field][token]["docIDs"][docID]["tf"] * idf)
                        self.document_norms[field][docID] = np.sqrt(
                            self.document_norms[field][docID] ** 2 - (old_tf_idf ** 2) + (
                                    self.index[field][token]["docIDs"][docID]["tf-idf"] ** 2))
                else:
                    # Remove the token from the index if it's not in any document
                    self.index[field].pop(token)
        # Remove the document from the cache
        self.docs["docs"].pop(doc_id)

    def create_document(self, doc):
        """
        Adds the document to the index
        :param doc:  document to add - dictionary with fields: title, table_of_contents (list), infobox, content
        """
        unused_ids = self.docs["unused_ids"]
        if len(unused_ids) > 0:
            doc_id = self.docs["unused_ids"].pop()
        else:
            doc_id = self.docs["max_id"] + 1
            self.docs["max_id"] = doc_id
        doc_id = str(doc_id)
        print("Adding document \"{}\" with id {}".format(doc["title"], doc_id))
        doc["lang_all"] = self.lang_detector_all.predict([doc["content"]])[0]
        doc["lang_cz_sk"] = self.lang_detector_cz_sk.predict([doc["content"]])[0]
        self.docs["docs"][doc_id] = doc
        preprocessed_doc = preprocessing_pipelines.preprocess(doc, doc_id, self.pipeline)
        N = len(self.docs["docs"])  # number of documents
        for field in self.fields:
            tokens = preprocessed_doc[field]
            for token in set(tokens):
                if token in self.index[field]:
                    docs_with_token = set(self.index[field][token]["docIDs"].keys())
                else:
                    docs_with_token = set()
                if token not in self.index[field]:
                    self.index[field][token] = {"idf": 0, "df": 0, "docIDs": defaultdict(lambda: {"tf": 0, "tf-idf": 0, "pos": []})}
                # Update the idf and df
                self.index[field][token]["df"] += 1
                df = self.index[field][token]["df"]
                old_idf = self.index[field][token]["idf"]
                idf = np.log10(N / float(df))
                self.index[field][token]["idf"] = idf
                # Update the tf-idf and norms of the documents affected by the change
                for docID in docs_with_token:
                    old_tf_idf = self.index[field][token]["docIDs"][docID]["tf-idf"]
                    self.index[field][token]["docIDs"][docID]["tf-idf"] = (
                            self.index[field][token]["docIDs"][docID]["tf"] * idf)
                    self.document_norms[field][docID] = np.sqrt(
                        self.document_norms[field][docID] ** 2 - (old_tf_idf ** 2) + (
                                self.index[field][token]["docIDs"][docID]["tf-idf"] ** 2))
                tf = tokens.count(token)
                if doc_id not in self.index[field][token]["docIDs"]:
                    self.index[field][token]["docIDs"][doc_id] = {"tf": 0, "tf-idf": 0, "pos": []}
                self.index[field][token]["docIDs"][doc_id]["tf"] = tf
                tf_idf = (1 + np.log10(tf)) * idf
                self.index[field][token]["docIDs"][doc_id]["tf-idf"] = tf_idf
                self.index[field][token]["docIDs"][doc_id]["pos"] = [pos for pos, t in enumerate(tokens) if t == token]
                if doc_id not in self.document_norms[field]:
                    self.document_norms[field][doc_id] = 0
                self.document_norms[field][doc_id] = np.sqrt(self.document_norms[field][doc_id] ** 2 + (tf_idf ** 2))


    def update_document(self, doc_id, replacement, field):
        """
        Updates the document in the index
        :param doc_id:  id of the document to update
        :param replacement:  replacement for the field
        :param field:  field to update
        """
        doc_id = str(doc_id)
        print("Updating document \"{}\" with id {}".format(self.docs["docs"][doc_id]["title"], doc_id))
        self.docs["docs"][doc_id][field] = replacement
        preprocessed_text = preprocessing_pipelines.preprocess(self.docs["docs"][doc_id], doc_id, self.pipeline)
        N = len(self.docs["docs"])  # number of documents
        for token in list(self.index[field].keys()):
            if doc_id in self.index[field][token]["docIDs"]:  # if the token is already associated with the document
                if token in preprocessed_text[field]:  # if the token is in the new text
                    # df has not changed
                    old_tf_idf = self.index[field][token]["docIDs"][doc_id]["tf-idf"]
                    tf = preprocessed_text[field].count(token)
                    tf_idf = (1 + np.log10(tf)) * self.index[field][token]["idf"]  # compute new tf-idf
                    self.index[field][token]["docIDs"][doc_id]["tf-idf"] = tf_idf
                    self.index[field][token]["docIDs"][doc_id]["pos"] = [pos for pos, t in enumerate(preprocessed_text[field]) if
                                                                    t == token]
                    self.document_norms[field][doc_id] = np.sqrt(
                        self.document_norms[field][doc_id] ** 2 - (old_tf_idf ** 2) + (tf_idf ** 2))
                else:  # if the token is not in the new text - it has been removed
                    old_tf_idf = self.index[field][token]["docIDs"][doc_id]["tf-idf"]
                    self.index[field][token]["docIDs"].pop(doc_id)
                    new_doc_norm = self.document_norms[field][doc_id] ** 2 - (old_tf_idf ** 2)
                    if new_doc_norm > 0:
                        self.document_norms[field][doc_id] = np.sqrt(new_doc_norm)
                    else:
                        self.document_norms[field][doc_id] = 0
                    self.index[field][token]["df"] -= 1
                    if self.index[field][token]["df"] == 0:
                        self.index[field].pop(token)
                        continue
                    df = self.index[field][token]["df"]
                    old_idf = self.index[field][token]["idf"]
                    idf = np.log10(N / float(df))
                    self.index[field][token]["idf"] = idf
                    for docID in self.index[field][token]["docIDs"]:
                        old_tf_idf = self.index[field][token]["docIDs"][docID]["tf-idf"]
                        self.index[field][token]["docIDs"][docID]["tf-idf"] = (
                                self.index[field][token]["docIDs"][docID]["tf"] * idf)
                        # update document norms
                        self.document_norms[field][docID] = np.sqrt(self.document_norms[field][docID] ** 2 - (old_tf_idf ** 2) + (
                                self.index[field][token]["docIDs"][docID]["tf-idf"] ** 2))

            else:  # if the token is not associated with the document
                if token in preprocessed_text[field]:  # if the token is in the new text
                    self.index[field][token]["df"] += 1
                    df = self.index[field][token]["df"]
                    old_idf = self.index[field][token]["idf"]
                    idf = np.log10(N / float(df))
                    self.index[field][token]["idf"] = idf
                    tf = preprocessed_text[field].count(token)
                    tf_idf = (1 + np.log10(tf)) * idf
                    self.index[field][token]["docIDs"][doc_id]["tf-idf"] = tf_idf
                    self.index[field][token]["docIDs"][doc_id]["pos"] = [pos for pos, t in enumerate(preprocessed_text[field]) if
                                                                    t == token]
                    self.document_norms[field][doc_id] = np.sqrt(tf_idf ** 2)
                    for docID in self.index[field][token]["docIDs"]:
                        old_tf_idf = self.index[field][token]["docIDs"][docID]["tf-idf"]
                        self.index[field][token]["docIDs"][docID]["tf-idf"] = (
                                self.index[field][token]["docIDs"][docID]["tf"] * idf)
                        self.document_norms[field][docID] = np.sqrt(self.document_norms[field][docID] ** 2 - (old_tf_idf ** 2) + (
                                self.index[field][token]["docIDs"][docID]["tf-idf"] ** 2))

        for token in set(preprocessed_text[field]):
            if token not in self.index[field]:  # new word
                self.index[field][token] = {"idf": 0, "df": 0, "docIDs": defaultdict(lambda: {"tf": 0, "tf-idf": 0, "pos": []})}
                self.index[field][token]["df"] += 1
                df = self.index[field][token]["df"]
                idf = np.log10(N / float(df))
                self.index[field][token]["idf"] = idf
                tf = preprocessed_text[field].count(token)
                tf_idf = (1 + np.log10(tf)) * idf
                self.index[field][token]["docIDs"][doc_id]["tf-idf"] = tf_idf
                self.index[field][token]["docIDs"][doc_id]["pos"] = [pos for pos, t in enumerate(preprocessed_text[field]) if
                                                                t == token]
                if doc_id not in self.document_norms[field]:
                    self.document_norms[field][doc_id] = 0
                old_doc_norm = self.document_norms[field][doc_id]
                self.document_norms[field][doc_id] = np.sqrt(old_doc_norm ** 2 + (tf_idf ** 2))



    def create_document_from_url(self, url):
        """
        Creates a document from the URL
        :param url:  URL of the document
        """
        doc = web_crawler.scrape_url(url)
        self.create_document(doc)


    def set_keywords(self):
        """
        Sets the keywords for the index
        :param keywords:  list of keywords
        """
        tokens = set()
        fields = ["title", "infobox", "content"]
        for docID in self.docs["docs"]:
            for field in fields:
                tokens.update(preprocessing_pipelines.pipeline_tokenizer(self.docs["docs"][docID][field])[1])
        self.keywords = tokens