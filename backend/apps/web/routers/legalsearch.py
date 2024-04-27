from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import chromadb
from chromadb import Settings
from sentence_transformers import SentenceTransformer
import os 
from pathlib import Path
import markdown
import shutils
import requests

app = FastAPI()

# Initialize the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize the ChromaDB client
DATA_DIR = str(Path(os.getenv("DATA_DIR", "./data")).resolve())
db_client = chromadb.PersistentClient(path=f"{DATA_DIR}/data.db", settings=Settings(allow_reset=True, anonymized_telemetry=False))

class LegalQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    document_id: str
    score: float
    text: str

@app.post("/legalsearch", response_model=List[SearchResult])
def legal_search(query: LegalQuery):
    # Convert the query into an embedding
    query_embedding = model.encode(query.query)
    
    # Search ChromaDB for the closest matching documents
    results = db_client.query(embeddings=[query_embedding], top_k=5)
    
    # Format the search results
    search_results = []
    for result in results:
        for doc_id, score in zip(result["ids"][0], result["distances"][0]):
            document = db_client.get_document(doc_id)
            search_results.append(SearchResult(document_id=doc_id, score=score, text=document["text"]))
    
    return search_results
