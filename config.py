import preprocessing_pipelines
from Index import Index

# --------------------------------------------------
# ----------------- CONFIGURATION ------------------
# Window size for the sliding window when creating snippets
WINDOW_SIZE = 30

# PIPELINE - choose between stemmer and lemmatizer
pipeline = preprocessing_pipelines.pipeline_stemmer
# pipeline = preprocessing_pipelines.pipeline_lemmatizer

# --------------------------------------------------
# ----------------- INDEXES ------------------------
# List of indexes for the GUI
indexes = []

# Main index created from the crawled data
index1 = Index(pipeline, "index", "ES_index")
index1.load_index()
index1.set_keywords()
indexes.append(index1) # ! add index to the list of indexes for the GUI