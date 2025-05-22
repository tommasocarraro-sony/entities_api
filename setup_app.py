from src.my_app.tools.get_item_metadata import GET_ITEM_METADATA
from src.my_app.tools.get_interacted_items import GET_INTERACTED_ITEMS
from src.my_app.tools.item_filter import ITEM_FILTER
from src.my_app.tools.get_user_metadata import GET_USER_METADATA
from src.my_app.tools.get_top_k_recommendations import GET_TOP_K_RECOMMENDATIONS
from src.my_app.tools.vector_store_search import VECTOR_STORE_SEARCH
from src.my_app.tools.get_popular_items import GET_POPULAR_ITEMS
from src.my_app.tools.get_like_percentage import GET_LIKE_PERCENTAGE
import os
from src.my_app.utils import create_app_environment
from dotenv import load_dotenv
import subprocess


load_dotenv()


entities_setup = {
    "api_key": os.getenv("ADMIN_API_KEY"),
    "user_id": os.getenv("ENTITIES_USER_ID"),
    "assistant_tools": [GET_ITEM_METADATA, GET_INTERACTED_ITEMS, GET_USER_METADATA,
                        GET_TOP_K_RECOMMENDATIONS, ITEM_FILTER, VECTOR_STORE_SEARCH,
                        GET_POPULAR_ITEMS, GET_LIKE_PERCENTAGE],
    "vector_store_name": "ml-100k_metadata_vector_store"
}

create_app_environment(
    entities_setup=entities_setup
)

# remove docker containers and restart them
subprocess.run(["docker", "rm", "-f", "my_mysql_cosmic_catalyst"], check=True)
subprocess.run(["docker", "rm", "-f", "qdrant_server"], check=True)
subprocess.run(["docker", "rm", "-f", "fastapi_cosmic_catalyst"], check=True)

# restart containers by calling start.py
subprocess.run(["python", "start.py"], check=True)
