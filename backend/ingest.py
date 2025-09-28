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
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


BOROUGHS = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
TAGS = ["architecture", "history", "family-friendly", "guided", "tour", "exhibit", "outdoor"]

# Real neighborhoods for each borough (not exhaustive, but representative)
NEIGHBORHOODS = {
    "Manhattan": [
        "Harlem", "Upper East Side", "Upper West Side", "Chelsea", "Greenwich Village", "SoHo", "Tribeca", "Lower East Side", "East Village", "Chinatown", "Financial District", "Midtown", "Morningside Heights", "Washington Heights"
    ],
    "Brooklyn": [
        "Williamsburg", "Brooklyn Heights", "Park Slope", "Bushwick", "Bedford-Stuyvesant", "DUMBO", "Crown Heights", "Red Hook", "Greenpoint", "Flatbush", "Sunset Park", "Prospect Heights", "Fort Greene"
    ],
    "Queens": [
        "Astoria", "Long Island City", "Flushing", "Forest Hills", "Jackson Heights", "Sunnyside", "Jamaica", "Ridgewood", "Corona", "Rego Park", "Woodside", "Elmhurst"
    ],
    "Bronx": [
        "Riverdale", "Fordham", "Kingsbridge", "Mott Haven", "Pelham Bay", "South Bronx", "Throgs Neck", "Belmont", "Morris Park"
    ],
    "Staten Island": [
        "St. George", "Tottenville", "Great Kills", "New Dorp", "Port Richmond", "Stapleton", "West Brighton", "Tompkinsville"
    ]
}

def generate_synthetic_events(n=200):
    base_date = datetime(2025, 10, 4, 9, 0)
    events = []
    for i in range(n):
        start = base_date + timedelta(hours=random.randint(0, 48))
        end = start + timedelta(hours=2)
        borough = random.choice(BOROUGHS)
        neighborhood = random.choice(NEIGHBORHOODS[borough])
        event = {
            "id": f"event_{i:04}",
            "title": f"Event {i} at {borough}",
            "description": f"Synthetic description for event {i}. This is a sample event for testing the OHNY Weekend chatbot.",
            "start_iso": start.isoformat(),
            "end_iso": end.isoformat(),
            "borough": borough,
            "neighborhood": neighborhood,
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
        # Try the most common langchain import paths first, then fall back to alternatives
        try:
            from langchain.embeddings import OpenAIEmbeddings
        except Exception:
            # older/newer packaging might expose this differently
            from langchain_openai import OpenAIEmbeddings

        try:
            from langchain.vectorstores import FAISS
        except Exception:
            from langchain_community.vectorstores import FAISS
    except Exception as e:
        print("Failed to import langchain/faiss:", e)
        return
    texts = [e["title"] + " \n Description: " + e["description"] + " \n Borough: " + e["borough"] + " \n Neighborhood: " + e["neighborhood"] + " \n Tags: " + ", ".join(e["tags"]) + " \n Accessible: " + str(e["accessibility"]) + " \n Kids-friendly: " + str(e["kid_friendly"]) + " \n Date: " + str(e["start_iso"]) for e in events]
    metadatas = [{"id": e["id"], "borough": e["borough"], "neighborhood": e["neighborhood"], "start": e["start_iso"], "end": e["end_iso"]} for e in events]
    try:
        # Instantiate embeddings with configurable model name. Different langchain wrappers
        # accept different parameter names across versions (model or model_name), so try both.
        try:
            embeddings = OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
        except TypeError:
            embeddings = OpenAIEmbeddings(model_name=OPENAI_EMBEDDING_MODEL)

        vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
        # Prefer LangChain's provided persistence API when available
        try:
            if hasattr(vectorstore, "save_local"):
                # LangChain v0.2+ usually exposes save_local
                vectorstore.save_local("vector_store")
                print("vector_store saved to directory 'vector_store' via LangChain.save_local()")
            elif hasattr(vectorstore, "save"):
                vectorstore.save("vector_store")
                print("vector_store saved to 'vector_store' via LangChain.save()")
            else:
                # Fallback: try FAISS native index write + metadata
                try:
                    import faiss
                    # attempt to locate the underlying FAISS index
                    faiss_index = getattr(vectorstore, "index", None) or getattr(vectorstore, "_index", None) or getattr(vectorstore, "faiss_index", None)
                    if faiss_index is not None:
                        faiss.write_index(faiss_index, "vector_store.index")
                        # save texts/metadatas for reconstruction
                        with open("vector_store_metadata.json", "w") as mf:
                            json.dump({"texts": texts, "metadatas": metadatas}, mf)
                        print("vector_store.index and vector_store_metadata.json written (FAISS native)")
                    else:
                        # Last resort: pickle (may fail for some wrappers)
                        with open("vector_store.pkl", "wb") as f:
                            pickle.dump(vectorstore, f)
                        print("vector_store.pkl written (pickle fallback)")
                except Exception as e:
                    print("Failed to persist vectorstore using FAISS native APIs:", e)
                    # Attempt pickle as a final fallback
                    try:
                        with open("vector_store.pkl", "wb") as f:
                            pickle.dump(vectorstore, f)
                        print("vector_store.pkl written (pickle fallback)")
                    except Exception as e2:
                        print("Failed to pickle vectorstore as final fallback:", e2)
        except Exception as e:
            print("Failed to save vectorstore via LangChain API:", e)
    except Exception as e:
        # If building the vector store fails, print a helpful message but don't crash the whole script
        print("Failed to build FAISS vector store:", e)
        # Provide more specific guidance for OpenAI errors
        if hasattr(e, 'args') and e.args:
            msg = str(e.args[0])
            if 'does not have access to model' in msg or 'model_not_found' in msg or '403' in msg:
                print("OpenAI returned a model access error. Check OPENAI_API_KEY and the embedding model name.")
                print(f"Current embedding model: {OPENAI_EMBEDDING_MODEL}")
        print("You can still use the generated JSON output without vector embeddings.")

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
