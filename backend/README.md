# Backend ingest helper

This folder contains `ingest.py`, a small helper to generate synthetic event data or fetch events from Airtable.

Quick usage

1. Install dependencies (recommended):

```bash
python3 -m pip install -r requirements.txt
```

2. Generate synthetic events:

```bash
python3 ingest.py --synthetic --count 200
```

This writes `synthetic_events.json` in the current folder. If `OPENAI_API_KEY` is set the script will attempt to build a FAISS vector store; if the build fails the script will print a helpful message and continue.

Notes
- If using Airtable, set `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID` in your environment or in a `.env` file.
- Embeddings/vector store require appropriate packages and OpenAI access; see the code comments in `ingest.py` for details.

Enable vector store build

- Set `OPENAI_API_KEY` in your environment (or in a `.env` file) so the script can call the OpenAI embeddings API.
- Optionally set `OPENAI_EMBEDDING_MODEL` to choose an embedding model (defaults to `text-embedding-3-small`).
- Make sure the required packages are installed (see `requirements.txt`) and that your OpenAI project has access to the chosen model.

If the vector build fails (for example due to missing packages or model access), the script will still write the JSON output and print a helpful message.
