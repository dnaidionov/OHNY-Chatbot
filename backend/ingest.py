# Ingest script: generate synthetic events or fetch from Airtable.
# Optionally builds a FAISS-based vector store using OpenAI embeddings (if OPENAI_API_KEY is set).
import os
import json
import random
import pickle
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BOROUGHS = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
TAGS = ["architecture", "history", "family-friendly", "guided", "tour", "exhibit", "outdoor"]

def generate_synthetic_events(n=200):
    base_date = datetime(2025, 10, 4, 9, 0)
    events = []
    for i in range(n):
        start = base_date + timedelta(hours=random.randint(0, 48))
        end = start + timedelta(hours=2)
        event = {
            "id": f"event_{i:04}",
            "title": f"Event {i} at {random.choice(BOROUGHS)}",
            "description": f"Synthetic description for event {i}. This is a sample event for testing the OHNY Weekend chatbot.",
            "start_iso": start.isoformat(),
            "end_iso": end.isoformat(),
            "borough": random.choice(BOROUGHS),
            "neighborhood": f"Neighborhood {random.randint(1,20)}",
            "address": f"{random.randint(1,500)} Example St",
            "tags": random.sample(TAGS, k=random.randint(1,3)),
            "kid_friendly": random.choice([True, False]),
            "accessibility": {"wheelchair": random.choice([True, False])},
            "signup_link": f"https://ohny.example.com/signup/{i}",
            "last_updated": datetime.utcnow().isoformat()
        }
        events.append(event)
    return events

def fetch_airtable_events():
    # Fetch records from Airtable (requires AIRTABLE_API_KEY, AIRTABLE_BASE_ID)
    import requests
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = os.getenv("AIRTABLE_TABLE_NAME", "Events")
    if not api_key or not base_id:
        raise RuntimeError("Airtable API key and base id must be set in environment variables to use --airtable")
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {"Authorization": f"Bearer {api_key}"}
    records = []
    offset = None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    events = []
    from dateutil import parser as dateparser
    for rec in records:
        f = rec.get("fields", {})
        try:
            start_dt = dateparser.parse(f.get("Start")) if f.get("Start") else datetime.utcnow()
        except Exception:
            start_dt = datetime.utcnow()
        try:
            end_dt = dateparser.parse(f.get("End")) if f.get("End") else (start_dt + timedelta(hours=2))
        except Exception:
            end_dt = start_dt + timedelta(hours=2)
        event = {
            "id": rec.get("id"),
            "title": f.get("Title", "Untitled Event"),
            "description": f.get("Description", ""),
            "start_iso": start_dt.isoformat(),
            "end_iso": end_dt.isoformat(),
            "borough": f.get("Borough", "Unknown"),
            "neighborhood": f.get("Neighborhood", ""),
            "address": f.get("Address", ""),
            "tags": f.get("Tags", []),
            "kid_friendly": f.get("Kid Friendly", False),
            "accessibility": {"wheelchair": f.get("Wheelchair Accessible", False)},
            "signup_link": f.get("Signup Link", ""),
            "last_updated": datetime.utcnow().isoformat()
        }
        events.append(event)
    return events

def build_vector_store(events):
    # Build FAISS vector store using OpenAI embeddings (requires langchain + faiss + openai installed)
    if not OPENAI_API_KEY:
        print("OPENAI_API_KEY not set: skipping vector store build. You can still use the fallback keyword retriever.")
        return
    try:
        from langchain.embeddings import OpenAIEmbeddings
        from langchain.vectorstores import FAISS
    except Exception as e:
        print("Failed to import langchain/faiss:", e)
        return
    texts = [e["title"] + ": " + e["description"] for e in events]
    metadatas = [{"id": e["id"], "borough": e["borough"], "neighborhood": e["neighborhood"], "start": e["start_iso"], "end": e["end_iso"]} for e in events]
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    with open("vector_store.pkl", "wb") as f:
        pickle.dump(vectorstore, f)
    print("vector_store.pkl written (FAISS)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--airtable", action="store_true")
    parser.add_argument("--count", type=int, default=200)
    args = parser.parse_args()
    if args.synthetic:
        events = generate_synthetic_events(n=args.count)
        with open("synthetic_events.json", "w") as f:
            json.dump(events, f, indent=2)
        print(f"Wrote synthetic_events.json ({len(events)} records)")
    elif args.airtable:
        events = fetch_airtable_events()
        with open("airtable_events.json", "w") as f:
            json.dump(events, f, indent=2)
        print(f"Wrote airtable_events.json ({len(events)} records)")
    else:
        print("Please use --synthetic or --airtable")
        raise SystemExit(1)
    build_vector_store(events)
