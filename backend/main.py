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
    n_results: int = 15

def _seed_lookup(question: str) -> tuple[list[str], list[dict], list[str]]:
    """Ask the LLM to name specific cards, then fetch them directly from ChromaDB."""
    seed_resp = ollama.chat(model="gemma4:e4b", messages=[{"role": "user", "content":
        f"Name up to 8 specific Magic: The Gathering card names that best match this query. "
        f"Output only card names, one per line, no explanation.\nQuery: {question}"}])
    candidate_names = [l.strip() for l in seed_resp["message"]["content"].splitlines() if l.strip()]

    if not candidate_names:
        return [], [], []

    seeded = collection.get(
        where={"name": {"$in": candidate_names}},
        include=["documents", "metadatas"],
    )
    return seeded.get("documents", []), seeded.get("metadatas", []), seeded.get("ids", [])


@app.post("/ask")
def ask(q: Query):
    # Parallel retrieval: name-seeded lookup + vector search with query rewrite
    rewrite = ollama.chat(model="gemma4:e4b", messages=[{"role": "user", "content":
        f"You are an MTG rules expert. Convert this query into 2-3 short oracle text fragments "
        f"that would appear on relevant Magic cards. Output only the fragments, comma-separated, no explanation.\n"
        f"Query: {q.question}"}])
    search_query = rewrite["message"]["content"].strip()

    seeded_docs, seeded_metas, seeded_ids = _seed_lookup(q.question)

    embedding = ollama.embeddings(model="mxbai-embed-large", prompt=search_query)["embedding"]
    vector_results = collection.query(
        query_embeddings=[embedding],
        n_results=q.n_results,
        where={"set_type": {"$ne": "funny"}},
    )

    # Merge: seeded cards first, then vector results, deduplicating by id
    seen = set(seeded_ids)
    merged_docs   = list(seeded_docs)
    merged_metas  = list(seeded_metas)
    merged_ids    = list(seeded_ids)
    for doc, meta, cid in zip(
        vector_results["documents"][0],
        vector_results["metadatas"][0],
        vector_results["ids"][0],
    ):
        if cid not in seen:
            seen.add(cid)
            merged_docs.append(doc)
            merged_metas.append(meta)
            merged_ids.append(cid)

    context = "\n\n".join(merged_docs)
    prompt = f"""You are an expert Magic: the Gathering assistant.
Use these cards as context:\n{context}\n\nAnswer: {q.question}"""

    response = ollama.chat(model="gemma4:e4b",
                           messages=[{"role": "user", "content": prompt}])
    return {
        "answer": response["message"]["content"],
        "cards": merged_metas,
        "card_names": merged_ids,
    }

@app.get("/cards/stats")
def stats():
    """Feed this to your D3/Chart.js visualizations"""
    results = collection.get(include=["metadatas"], limit=10000)
    return {"metadatas": results["metadatas"]}

# Run: uvicorn main:app --reload --port 8000