import os
import faiss
import numpy as np
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key="youw own api key") # or you can use .env file to keep the api key safe using api_key=os.getenv("GEMINI_API_KEY")

EMBED_MODEL = "gemini-embedding-001"

def load_regulatory_text():
    with open("app/regulatory_text/own_funds.txt", "r") as f:
        return f.read().split("\n\n")

def embed_text(text, task_type="RETRIEVAL_DOCUMENT"):
    response = client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
        config={
            "task_type": task_type
        }
    )
    return np.array(response.embeddings[0].values).astype("float32")

texts = load_regulatory_text()

embeddings = np.vstack([
    embed_text(t, task_type="RETRIEVAL_DOCUMENT")
    for t in texts
])

dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

def retrieve(query, k=3):
    query_embedding = embed_text(query, task_type="RETRIEVAL_QUERY")
    query_vector = np.array([query_embedding]).astype("float32")

    distances, indices = index.search(query_vector, k)

    return [texts[i] for i in indices[0]]