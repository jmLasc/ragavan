from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import chromadb, ollama

BASE_DIR = Path(__file__).parent.parent

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

client = chromadb.PersistentClient(path=str(BASE_DIR / "vectorstore"))
collection = client.get_collection("mtg_cards")

class Query(BaseModel):
    question: str
    n_results: int = 5

@app.post("/ask")
def ask(q: Query):
    rewrite = ollama.chat(model="gemma4:e4b", messages=[{"role": "user", "content":
        f"You are an MTG expert. Rewrite this query as a description of what "
        f"the oracle text of relevant cards would say. Be concise, no explanation.\n"
        f"Query: {q.question}"}])
    search_query = rewrite["message"]["content"].strip()

    embedding = ollama.embeddings(model="mxbai-embed-large", prompt=search_query)["embedding"]
    results = collection.query(query_embeddings=[embedding], n_results=q.n_results)
    
    context = "\n".join(results["documents"][0])
    prompt = f"""You are an expert Magic: the Gathering assistant.
Use these cards as context:\n{context}\n\nAnswer: {q.question}"""
    
    response = ollama.chat(model="gemma4:e4b",
                           messages=[{"role": "user", "content": prompt}])
    return {
        "answer": response["message"]["content"],
        "cards": results["metadatas"][0],
        "card_names": results["ids"][0]
    }

@app.get("/cards/stats")
def stats():
    """Feed this to your D3/Chart.js visualizations"""
    results = collection.get(include=["metadatas"], limit=10000)
    return {"metadatas": results["metadatas"]}

# Run: uvicorn main:app --reload --port 8000