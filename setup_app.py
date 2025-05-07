from src.my_app.function_definitions import (RECOMMENDATION, METADATA, INTERACTION,
                                             RECOMMENDATION_VECTOR, RECOMMENDATION_SIMILAR_ITEM,
                                             USER_METADATA)
import os
from src.my_app.utils import create_app_environment
from dotenv import load_dotenv
import subprocess


load_dotenv()


entities_setup = {
    "api_key": os.getenv("ADMIN_API_KEY"),
    "user_id": os.getenv("ENTITIES_USER_ID"),
    "assistant_tools": [RECOMMENDATION, METADATA, INTERACTION, RECOMMENDATION_VECTOR,
                        RECOMMENDATION_SIMILAR_ITEM, USER_METADATA],
    "vector_store_name": "ml-100k_metadata_vector_store"
}

db_name = "movielens-100k"

create_app_environment(
    database_name=db_name,
    entities_setup=entities_setup
)

# # remove docker containers and restart them
# subprocess.run(["docker", "rm", "-f", "my_mysql_cosmic_catalyst"], check=True)
# subprocess.run(["docker", "rm", "-f", "samba_server"], check=True)
# subprocess.run(["docker", "rm", "-f", "sandbox_api"], check=True)
# subprocess.run(["docker", "rm", "-f", "qdrant_server"], check=True)
# subprocess.run(["docker", "rm", "-f", "fastapi_cosmic_catalyst"], check=True)
#
# # restart containers by calling start.py
# subprocess.run(["python", "start.py"], check=True)
