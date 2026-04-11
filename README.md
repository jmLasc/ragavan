# ragavan

A Magic: The Gathering Q&A app powered by local LLMs and vector search. Ask natural-language questions about MTG cards ("cheap removal in white", "asymmetric board wipes") and get answers grounded in real card data from Scryfall.

**How it works:** User queries are rewritten into oracle-text fragments (HyDE), embedded with `mxbai-embed-large`, and used to search a ChromaDB vector store. A parallel name-seeded lookup asks the LLM to name specific known cards and fetches them directly. Both result sets are merged and fed as context to `gemma4:e4b` for the final answer.

---

## Prerequisites

- **Python 3.11+**
- **[Ollama](https://ollama.com)** installed and running locally
- Required Ollama models:
  ```
  ollama pull gemma4:e4b
  ollama pull mxbai-embed-large
  ```

---

## Setup

**1. Clone and create a virtual environment**
```bash
python -m venv .venv
.venv/Scripts/activate      # Windows
# source .venv/bin/activate  # macOS/Linux
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Download Scryfall card data**
```bash
bash fetch_data.sh
# Saves oracle card data to data/scryfall_cards.json (~100MB)
```

**4. Build the vector store**
```bash
python backend/ingest.py
# Embeds all cards into ChromaDB under vectorstore/
# Takes several minutes on first run
```

---

## Running

**Ollama** (run once):
```bash
ollama serve
# Activates ollama's local capabilities
```


**Backend** (keep this terminal open):
```bash
uvicorn backend.main:app --reload --port 8000
```

**Frontend**: open `frontend/index.html` directly in a browser — no server needed.

---

## Who?

[This guy. 🐒](https://scryfall.com/card/mh2/315/ragavan-nimble-pilferer)