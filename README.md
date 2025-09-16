# OHNY Weekend Chatbot

AI-powered chatbot for OHNY Weekend.

## Features
- Frontend React widget (embed or standalone)
- Backend (FastAPI + optional LangChain + FAISS)
- Ingestion pipeline for Airtable/CSV/JSON event data
- Synthetic dataset (~200 events) for testing
- Scheduling-aware: answers time-specific queries

## Quickstart (local, minimal)
1. Clone repo or unzip the provided zip.
2. Backend setup:
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file in `backend/` (or set env vars). Example in `.env.example`.
   - For full AI features you will need an OpenAI API key (paid; free trial credits may exist).
4. Generate synthetic data and (optionally) a vector store:
   ```bash
   cd backend
   python ingest.py --synthetic
   ```
   This will create `synthetic_events.json`. Building the FAISS vector store requires OpenAI API keys and the packages from requirements.txt.
5. Run API:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
6. Frontend:
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```
7. Open the frontend page (Vite typically serves at http://localhost:5173) or embed the widget into any page.

## Notes
- The backend `main.py` will try to load a FAISS-based `vector_store.pkl` for semantic retrieval. If it's not present, it falls back to a simple keyword-based retriever over `synthetic_events.json` so you can try the system without OpenAI keys.
- To enable proper semantic retrieval and high-quality responses, set `OPENAI_API_KEY` in `backend/.env` and install the dependencies including `langchain`, `faiss-cpu` and `openai`, then re-run `python ingest.py --synthetic` to build `vector_store.pkl`.
