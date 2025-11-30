from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re

model = SentenceTransformer("all-MiniLM-L6-v2")

def clean_text(t):
    """Clean and normalize text"""
    t = t.lower()
    t = re.sub(r"[^a-zA-Z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t)  # Remove extra whitespace
    return t.strip()

def extract_topic(docs):
    """Extract top keywords from documents in a cluster"""
    if not docs:
        return "No topic"

    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=3000, min_df=1)
        X = vectorizer.fit_transform(docs)
        
        if X.shape[0] == 0 or X.shape[1] == 0:
            return "No topic"
        
        terms = vectorizer.get_feature_names_out()
        sums = np.asarray(X.sum(axis=0)).ravel()
        
        # Get top 3 terms
        top_indices = sums.argsort()[::-1][:3]
        top = terms[top_indices]
        
        return ", ".join(top) if len(top) > 0 else "No topic"
    except Exception as e:
        print(f"Error extracting topic: {e}")
        return "No topic"

def run_document_clustering(documents, k):
    """Cluster documents using K-Means on sentence embeddings"""
    
    # VALIDATE INPUT
    if not documents or len(documents) == 0:
        raise ValueError("No documents provided")
    
    # CLEAN DOCS - keep track of original indices
    cleaned = []
    original_indices = []
    for i, d in enumerate(documents):
        if d.strip():
            cleaned.append(clean_text(d))
            original_indices.append(i)
    
    if len(cleaned) < k:
        raise ValueError(f"Number of clusters ({k}) cannot exceed number of documents ({len(cleaned)})")

    # EMBEDDINGS
    print(f"Encoding {len(cleaned)} documents...")
    embeddings = model.encode(cleaned)

    # KMEANS CLUSTERING
    print(f"Clustering into {k} clusters...")
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
    labels = kmeans.fit_predict(embeddings)

    # BUILD CLUSTER RESPONSE
    clusters = {}
    topics = {}

    for cid in range(k):
        docs_in_cluster = [documents[original_indices[i]] for i in range(len(cleaned)) if labels[i] == cid]
        topic = extract_topic(docs_in_cluster)

        clusters[cid] = {
            "topic": topic,
            "docs": docs_in_cluster
        }
        print(f"Cluster {cid}: {len(docs_in_cluster)} documents - Topic: {topic}")

    return labels, topics, clusters
