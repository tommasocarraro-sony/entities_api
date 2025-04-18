"""
Vector‑store movie‑recommendation demo
=====================================

1.  Create a store
2.  Ingest a CSV of movies (each row → one “document” with description + metadata)
3.  Define a user’s preference query + metadata filters
4.  Run a semantic + metadata‑filtered search for recommendations
"""
import os
import csv
from pathlib import Path

from dotenv import load_dotenv
from datetime import datetime

from projectdavid import Entity
from projectdavid_common import UtilsInterface
from projectdavid.clients.file_processor import FileProcessor

# --------------------------------------------------------------------- #
# 0. Setup
# --------------------------------------------------------------------- #
load_dotenv()  # reads .env in cwd

client = Entity(
    base_url=os.getenv("BASE_URL", "http://localhost:9000"),
    api_key=os.getenv("ENTITIES_API_KEY"),
)
log = UtilsInterface.LoggingUtility()

# We'll use the same FileProcessor the SDK uses under the hood:
processor = FileProcessor()

# --------------------------------------------------------------------- #
# 1. Create a vector store
# --------------------------------------------------------------------- #
# store = client.vectors.create_vector_store(
#     name="movie-recs-demo",
#     user_id=os.getenv("ENTITIES_USER_ID"),
# )
store = client.vectors.retrieve_vector_store(vector_store_id='vect_4At9qWhXk9bp0BvYmEPhXV')
# log.info("Store %s ready (collection %s)", store.id, store.collection_name)
#
# # --------------------------------------------------------------------- #
# # 2. Ingest movies.csv
# #    Expected columns: title, description, genres (comma‑sep), year, rating
# # --------------------------------------------------------------------- #
# CSV_PATH = Path("./data/toy_data/movies.csv")
# movies = []
# with CSV_PATH.open(newline="", encoding="utf-8") as f:
#     reader = csv.DictReader(f)
#     for row in reader:
#         # assemble each movie as one document:
#         movies.append({
#             "text": row["description"].strip(),
#             "metadata": {
#                 "id": int(row["id"]),
#                 "title": row["title"].strip(),
#                 # store genres as list for filtering
#                 "genres": [g.strip() for g in row["genres"].split(",") if g.strip()],
#                 "year": int(row["year"]),
#                 "rating": float(row["rating"]),
#                 # record when we ingested it
#                 "ingested_at": datetime.utcnow().isoformat(),
#             }
#         })
#
# # batch‑embed all descriptions
# texts = [m["text"] for m in movies]
# metas = [m["metadata"] for m in movies]
# vectors = processor.embedding_model.encode(
#     texts,
#     convert_to_numpy=True,
#     truncate="model_max_length",
#     normalize_embeddings=True,
# ).tolist()
#
# # upload into Qdrant via the SDK’s manager
# client.vectors.vector_manager.add_to_store(
#     store_name=store.collection_name,
#     texts=texts,
#     vectors=vectors,
#     metadata=metas,
# )
# log.info("Ingested %d movies into %s", len(movies), store.collection_name)

# --------------------------------------------------------------------- #
# 3. Define user preference + metadata filters
# --------------------------------------------------------------------- #
user_pref = "Provide all the action movies released prior to 2013." # "I love futuristic sci‑fi adventures with strong female leads"  # Provide the IDs of all the horror movies released prior to 2013.
# Only recommend sci‑fi movies rated ≥ 8.0, released after 2010
filters = {
    "must": [
        {"key": "genres",      "match": {"value": "Action"}},
        {"key": "year",        "range": {"lte": 2013}}
    ]
}

# --------------------------------------------------------------------- #
# 4. Run the recommendation search
# --------------------------------------------------------------------- #
hits = client.vectors.search_vector_store(
    vector_store_id=store.id,
    query_text=user_pref,
    top_k=10,
    filters=filters,
)

print(f"\nTop movie recommendations for: {user_pref!r}\n")
for i, hit in enumerate(hits, 1):
    md = hit["metadata"]
    id_ = md.get("id", "Unknown")
    title = md.get("title", "Unknown")
    genres = ", ".join(md.get("genres", []))
    year = md.get("year")
    rating = md.get("rating")
    snippet = hit["text"].replace("\n", " ")[:80]
    print(
        f"{i:>2}. Item ID: {id_} - {title} ({year}) [{genres}] "
        f"⭐ {rating:.1f}  score={hit['score']:.3f}\n"
        f"     → {snippet!r}\n"
    )
