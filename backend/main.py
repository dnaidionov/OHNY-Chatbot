from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os, pickle, json, functools, time
from datetime import datetime
from dateutil import parser as dateparser
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

STYLE_MAP = {
    "concierge": "prompts/style_concierge.txt",
    "tourguide": "prompts/style_tourguide.txt",
    "family": "prompts/style_family.txt",
    "friendly": "prompts/style_friendly.txt",
    "default": "prompts/style.txt",
}

# Try to load vectorstore; if missing, fall back to keyword retriever over synthetic_events.json
VECTOR_PATH = "vector_store.pkl"
vectorstore = None
if os.path.exists(VECTOR_PATH):
    try:
        with open(VECTOR_PATH, "rb") as f:
            vectorstore = pickle.load(f)
        print("Loaded vector_store.pkl")
    except Exception as e:
        print("Failed to load vector_store.pkl:", e)
        vectorstore = None

docs_cache = []
if not vectorstore:
    # Load synthetic events for keyword-based retrieval
    JSON_PATH = "synthetic_events.json"
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r") as f:
            events = json.load(f)
    else:
        events = []
    # Prepare simple docs with page_content and metadata
    class SimpleDoc:
        def __init__(self, page_content, metadata):
            self.page_content = page_content
            self.metadata = metadata
    docs_cache = [SimpleDoc(e.get("title", "") + ": " + e.get("description", ""), {"id": e.get("id"), "start": e.get("start_iso"), "end": e.get("end_iso"), "borough": e.get("borough")}) for e in events]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@functools.lru_cache(maxsize=1)
def _load_prompt(file_path: str, mtime: float):
    return Path(file_path).read_text().strip()

def get_prompt(file_path: str):
    """Reloads a prompt file whenever it changes."""
    mtime = os.path.getmtime(file_path)
    return _load_prompt(file_path, mtime)

def get_system_prompt():
    """Reloads the system prompt whenever system.txt is modified."""
    mtime = os.path.getmtime("prompts/system.txt")
    return _load_prompt(mtime, "system") + "\n\n" + _load_prompt(mtime, "style")

class MessageRequest(BaseModel):
    session_id: str
    message: str

class MessageResponse(BaseModel):
    reply: str
    context: List[Dict[str, Any]]

def naive_retriever(query, k=5):
    # Simple keyword overlap scoring for local testing
    q_tokens = set([t.lower() for t in query.split() if len(t) > 2])
    scored = []
    for d in docs_cache:
        text = d.page_content.lower()
        score = sum(1 for t in q_tokens if t in text)
        scored.append((score, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = [d for s,d in scored if s>0][:k]
    if not results:
        results = [d for _,d in scored][:k]
    return results

def filter_events_by_time(docs, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
    if not start_time and not end_time:
        return docs
    filtered = []
    for d in docs:
        try:
            doc_start = dateparser.parse(d.metadata.get("start"))
            doc_end = dateparser.parse(d.metadata.get("end"))
        except Exception:
            filtered.append(d)
            continue
        if start_time and doc_end < start_time:
            continue
        if end_time and doc_start > end_time:
            continue
        filtered.append(d)
    return filtered

# Try to use OpenAI for responses if key is present
USE_OPENAI = bool(OPENAI_API_KEY)
if USE_OPENAI:
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        print("OpenAI key loaded")
    except Exception as e:
        print("Failed to import openai:", e)
        USE_OPENAI = False

# def chat(msg: MessageRequest, start_time: Optional[str] = Query(None), end_time: Optional[str] = Query(None)):
#     start_dt = dateparser.parse(start_time) if start_time else None
#     end_dt = dateparser.parse(end_time) if end_time else None

@app.post("/v1/message", response_model=MessageResponse)
def chat(msg: MessageRequest, style: str = Query("default")):

    # Retrieve docs
    docs = None
    if vectorstore is not None:
        try:
            retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})
            docs = retriever.get_relevant_documents(msg.message)
        except Exception as e:
            print("Vector retrieval failed, falling back:", e)
            docs = naive_retriever(msg.message)
    else:
        docs = naive_retriever(msg.message)

    context = [d.metadata for d in docs]

    # Compose response
    if USE_OPENAI:
        # Build a simple prompt including top docs
        snippets = "\n".join([d.page_content for d in docs[:5]])
        user_prompt = f"User: {msg.message}\n\nEvent snippets:\n{snippets}"
    else:
        user_prompt = None

    if USE_OPENAI and user_prompt is not None:
        try:
            style_file = STYLE_MAP.get(style, STYLE_MAP["concierge"])
            system_prompt = get_prompt("prompts/system.txt")
            style_prompt = get_prompt(style_file)
            fallback_prompt = get_prompt("prompts/fallback.txt")

            messages = [
                {
                    "role": "system",
                    "content": f"{system_prompt}\n\n{style_prompt}\n\n{fallback_prompt}"
                },
                {"role": "user", "content": user_prompt},
            ]

            # model="gpt-4o-mini"
            model="gpt-5-mini"
            res = client.chat.completions.create(model=model,
                messages=messages,
                # max_tokens=400)
                max_completion_tokens=400)
            answer = res.choices[0].message.content
        except Exception as e:
            print("OpenAI call failed:", e)
            answer = "Here are some events I found:\n" + "\n".join([d.page_content for d in docs[:3]])
    else:
        if not docs:
            answer = "I couldn't find any matching events. Try a broader search or remove time filters."
        else:
            lines = [f"{i+1}. {d.page_content}" for i,d in enumerate(docs[:5])]
            answer = "Local results (no OpenAI key):\n" + "\n".join(lines)

    return MessageResponse(reply=answer, context=context)
