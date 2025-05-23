import json
import os
from dotenv import load_dotenv
load_dotenv()
from projectdavid import Entity
from src.my_app.constants import JSON_GENERATION_ERROR
from src.my_app.tools.utils import convert_to_list


VECTOR_STORE_SEARCH = {
    "function": {
        "name": "vector_store_search",
        "description": (
            "Returns the IDs of the top 10 items whose description matches the given textual "
            "query. The search is performed on the entire item catalog unless some item IDs are"
            "given."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query to perform the vector store search."
                },
                "items": {
                    "oneOf": [
                        {
                          "type": "array",
                          "items": {"type": "integer"},
                          "description": "A list of item IDs."
                        },
                        {
                          "type": "string",
                          "description": "Path to a JSON file containing the item IDs."
                        }
                    ],
                    "description": "Item ID(s) that have to be included in the vector store "
                                   "search, either directly as a list or as a path to a JSON file."
                }
            }
        },
        "required": ["query"]
    }
}


def perform_vector_store_search(query, filters=None, topk=11):
    """
    It performs a search on the vector store and returns the IDs of the retrieved items.

    :param query: query for the vector store search
    :param filters: Qdrant filters for the vector store search
    :param topk: number of items to be returned by the vector store search
    :return: IDs of retrieved items
    """
    client = Entity(
        base_url=os.getenv("BASE_URL", "http://localhost:9000"),
        api_key=os.getenv("ADMIN_API_KEY"),
    )
    store = os.getenv("ENTITIES_VECTOR_STORE_ID")

    embedder = client.vectors.file_processor.embedding_model
    qvec = embedder.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
        truncate="model_max_length",
    )[0].tolist()

    hits = client.vectors.vector_manager.query_store(
        store_name=store,
        query_vector=qvec,
        top_k=topk,
        filters=filters
    )

    item_ids = [
        str(h['metadata']['item_id'])
        for i, h in enumerate(hits)
    ]

    item_metadata = {
        str(h['metadata']['item_id']): {"item_id": str(h['metadata']['item_id']),
                                        # "title": h['metadata']['title'],
                                        # "genres": h['metadata']['genres'],
                                        # "director": h['metadata']['director'],
                                        "description": h['metadata']['description']}
        for i, h in enumerate(hits)
    }

    return item_ids, item_metadata


def vector_store_search(params):
    """
    This function is used by the assistant to perform vector store searches.

    :param params: dictionary containing all the arguments to process the vector store search

    :return: a prompt for the LLM that the LLM will use as additional context to prepare the final
    answer
    """
    print("\nvector_store_search has been triggered!!!\n")
    if 'query' in params:
        query = params.get('query')
        if 'items' in params:
            # if some item IDs are given, the vector store search has to be executed only on those
            # items
            items = params.get('items')
            try:
                items = convert_to_list(items)
            except Exception:
                return json.dumps({
                    "status": "failure",
                    "message": "There are issues with the temporary file containing the item IDs.",
                })
            items = [int(item) for item in items]
            qdrant_filters = {"filter": {"must": [{"key": "item_id", "match": {"any": items}}]}}
            item_ids, item_metadata = perform_vector_store_search(query, filters=qdrant_filters)
        else:
            item_ids, item_metadata = perform_vector_store_search(query)
        # remove item from list if its description in item_metadata is exactly the same as the
        # query
        # this happens when looking for an item description
        # in such case, the first hit will be the item itself. We need to remove this item from
        # the list
        item_metadata = {k: v for k, v in item_metadata.items() if v['description'] != query}
        # update the list of item ids too
        item_ids = [i for i in item_ids if i in item_metadata]

        return json.dumps({
            "status": "success",
            "message": f"These are the IDs of the best matching items produced by the vector "
                       f"store search: {item_ids}"
        })
    else:
        return json.dumps(JSON_GENERATION_ERROR)
