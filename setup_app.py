from src.my_app.function_definitions import (RECOMMENDATION, METADATA, INTERACTION,
                                             RECOMMENDATION_VECTOR, RECOMMENDATION_SIMILAR_ITEM,
                                             USER_METADATA)
import os
from src.my_app.utils import create_app_environment
from dotenv import load_dotenv
import subprocess
import time
import pymysql


def wait_for_mysql(host='localhost', port=3306, user='root', password='yourpass', db='entities_db', timeout=60):
    print("Waiting for MySQL to be ready...")
    start_time = time.time()
    while True:
        try:
            conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db)
            conn.close()
            print("MySQL is ready.")
            break
        except pymysql.MySQLError:
            if time.time() - start_time > timeout:
                raise RuntimeError("Timed out waiting for MySQL to be ready.")
            time.sleep(1)


load_dotenv()

# start docker containers
subprocess.run(["python", "start.py"], check=True)
wait_for_mysql(host="localhost", port=3307, user=os.getenv("MYSQL_USER"),
               password=os.getenv("MYSQL_PASSWORD"), db=os.getenv("MYSQL_DATABASE"))

print("Waiting 30 seconds for the database to be ready...")
time.sleep(30)

# creating admin user
subprocess.run(["python", "scripts/bootstrap_admin.py"], check=True)

load_dotenv(override=True)

# creating standard user
subprocess.run(["python", "scripts/create_user.py"], check=True)

load_dotenv(override=True)


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

# remove docker containers and restart them
subprocess.run(["docker", "rm", "-f", "my_mysql_cosmic_catalyst"], check=True)
subprocess.run(["docker", "rm", "-f", "samba_server"], check=True)
subprocess.run(["docker", "rm", "-f", "sandbox_api"], check=True)
subprocess.run(["docker", "rm", "-f", "qdrant_server"], check=True)
subprocess.run(["docker", "rm", "-f", "fastapi_cosmic_catalyst"], check=True)

# restart containers by calling start.py
subprocess.run(["python", "start.py"], check=True)
