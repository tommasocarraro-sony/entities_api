"""
Fuzzy search against an existing MovieLens vector store.

Examples
--------
Single query:
    python search_movielens.py --store vect_I1KhGs8LkHJbbNh4fuKYDQ \
                               --query "90s romantic drama movie"

Interactive REPL:
    python search_movielens.py --store vect_I1KhGs8LkHJbbNh4fuKYDQ
"""
import argparse, os, sys
from dotenv import load_dotenv
from projectdavid import Entity

load_dotenv()


def lookup(store_id: str, q: str, filters: dict, top_k: int = 5):
    client = Entity(
        base_url=os.getenv("BASE_URL", "http://localhost:9000"),
        api_key=os.getenv("ENTITIES_API_KEY"),
    )
    embedder = client.vectors.file_processor.embedding_model
    qvec = embedder.encode(
        [q], convert_to_numpy=True, normalize_embeddings=True,
        truncate="model_max_length"
    )[0].tolist()
    hits = client.vectors.vector_manager.query_store(
        store_name=store_id, query_vector=qvec, top_k=top_k, filters=filters
    )
    for i, h in enumerate(hits, 1):
        m = h["metadata"]
        genres = m["genres"] if m["genres"] is not None else "Unknown genre"
        year = m["release_date"] if m["release_date"] is not None else "Unknown release date"
        director = m["director"] if m["director"] is not None else "Unknown director"
        description = m["description"] if m["description"] is not None else "Unknown description"
        print(f"{i}. 🎬 {m['title']} — {genres} ({year}) score={h['score']:.3f} - Director: {director} - Description: {description}")


def main(store: str, query: str | None, filters: dict | None, top_k: int):
    if query:
        lookup(store, query, filters, top_k)
    else:
        print("Entering interactive mode (Ctrl‑D to exit)\n")
        try:
            while True:
                q = input("🔍 > ").strip()
                if not q:
                    continue
                lookup(store, q, filters, top_k)
                print()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)


if __name__ == "__main__":
    query = "A sci-fi movie with aliens and a female main character."
    filters = {
        "must": [
            # {
            #     "key": "actors",
            #     "match": {
            #         "value": "Tom Cruise"  # note this is exact matching. Better to use IMDb data to be sure -> very difficult to obtain accurate results here
            #     }
            # },
            {
                "key": "release_date",
                "range": {
                    "lt": 1980
                }
            }
        ]
    }
    topk = 10
    main(os.getenv('ENTITIES_VECTOR_STORE_ID'), query, None, topk)

    # todo design a new system prompt for only vector store searches
    # todo understand how to generate the examples for the vector store search, like the ones frankie put
    # todo use function calling to perform vector store searches
    # todo enlarge the output of the function with the description and everything of the items so that they can be directly used for explanation
    # todo I just have to provide examples on how to use the filters -> I need a retry mechanism in the case the query did not return anything with the filters, I just try with the text
    # todo I just have to explain the LLM how to create proper filters -> see examples of Frankie in the system prompt -> remember to design another system prompt
    # todo retrieve IDs and pass them to the recsys
    # todo a con is that not all item IDs are retrieved, instead, with SQL queries, all the items are retrieved and then the recsys is used. Vector store search does a lot of filtering already and then the recsys is called on a few items
    # todo which is the best of the two solutions??
    # todo good for not exact filtering but just exploritary tasks

    # todo when you know what you want, you use SQL queries and then the recommender system (e.g., provide me 5 movie recommendation starring Tom Cruise and released prior to 1996) -> implement very basic fuzzy matching for textual fields
    # todo when you do not know exactly what you want, you can instead use vector store search providing a description of what you are looking for (e.g., provide me movies that have a strange plot where ghosts combat against Barbies)
    # todo in some cases, you can also use Qdrant filters plus vector store searches

    # todo look at the other file on fuzzy matches for genres, director, producer, actors, then everything remains as it was. I just have to design the SQL queries and everything is done
    # todo I use the same for both qdrant and SQL queries -> the call can create the same filters, then it's up to me to move prepare the correct filters for Qdrant or SQL
