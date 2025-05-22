import sqlite3
from projectdavid import Entity
from projectdavid_common.schemas.tools import ToolFunction
import os
import re
import pandas as pd
from dotenv import load_dotenv, set_key
from src.my_app.assistant import AssistantSetupService
from src.my_app.constants import DATABASE_NAME


def create_entities_environment(api_key, user_id, assistant_tools, vector_store_name):
    """
    This function creates the Entities API environment (middleware layer between user and LLM)

    :param api_key: api_key to access Entities API
    :param user_id: user_id of the user that interacts with the assistant (i.e., LLM)
    :param assistant_tools: tools (for function calling) that have to be associated with the
    assistant
    :param vector_store_name: name of the vector store that has to be created
    """
    client = Entity(base_url="http://localhost:9000",
                    api_key=api_key)
    user = client.users.retrieve_user(user_id=user_id)
    service = AssistantSetupService(client)
    assistant = service.orchestrate_default_assistant()

    for tool in assistant_tools:
        associate_tool_to_assistant(client, assistant.id, tool=tool)

    vector_store_setup_movielens(client=client, user_id=user.id,
                                 vector_store_name=vector_store_name)


def create_app_environment(entities_setup):
    """
    This function creates the entire app environment. The components of the app are:
    1. a database containing data accessible to the assistant through function calling;
    2. a pre-trained recommender system accessible to the assistant through function calling;
    3. the Entities API environment (middleware layer between user and LLM)

    :param entities_setup: dictionary containing parameters for Entities API environment creation
    :return: client, user, thread, and assistant of Entities API environment
    """
    create_ml100k_db(DATABASE_NAME)
    return create_entities_environment(
        api_key=entities_setup["api_key"],
        user_id=entities_setup["user_id"],
        assistant_tools=entities_setup["assistant_tools"],
        vector_store_name=entities_setup["vector_store_name"]
    )


def create_ml100k_db(db_name):
    """
    This function creates the database and tables needed for MovieLens-100k dataset. The metadata
    table contains item metadata (title, release date, and genres). The name of the table is 'items'.
    The interaction table contains user historical interactions (list of item IDs for each user
    of the dataset). The name of the table is 'interactions'. These tables are both used in the app.

    :param db_name: name of the database
    """
    conn = sqlite3.connect(f'{db_name}.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
                    item_id INTEGER PRIMARY KEY,
                    title TEXT,
                    genres TEXT,
                    director TEXT,
                    producer TEXT,
                    actors TEXT,
                    release_date INTEGER,
                    release_month INTEGER,
                    country TEXT,
                    duration INTEGER,
                    age_rating TEXT,
                    imdb_rating FLOAT,
                    imdb_num_reviews INTEGER,
                    n_ratings INTEGER,
                    n_ratings_kid INTEGER,
                    n_ratings_teenager INTEGER,
                    n_ratings_young_adult INTEGER,
                    n_ratings_adult INTEGER,
                    n_ratings_senior INTEGER,
                    n_ratings_male INTEGER,
                    n_ratings_female INTEGER,
                    description TEXT)''')

    # load data
    with open('./data/recsys/ml-100k/final_ml-100k.csv', 'r', encoding='utf-8') as f:
        first_line = True
        for line in f:
            if first_line:
                first_line = False
                continue
            parts = line.strip().split('\t')
            if len(parts) < 16:
                continue  # skip lines with missing data

            item_id = int(parts[0])
            movie_title = parts[1] if parts[1] != 'unknown' else None
            genres = parts[2] if parts[2] != 'unknown' else None
            director = parts[3] if parts[3] != 'unknown' else None
            producer = parts[4] if parts[4] != 'unknown' else None
            actors = parts[5] if parts[5] != 'unknown' else None
            release_date = int(parts[6]) if parts[6] != 'unknown' and parts[6].isdigit() else None
            release_month = int(parts[7]) if parts[7] != 'unknown' else None
            country = parts[8] if parts[8] != 'unknown' else None
            duration = convert_duration(parts[9]) if parts[9] != 'unknown' else None
            age_rating = parts[10] if parts[10] != 'unknown' else None
            imdb_rating = float(parts[11]) if parts[11] != 'unknown' else None
            imdb_num_reviews = convert_num_reviews(parts[12]) if parts[12] != 'unknown' else None
            n_ratings = int(parts[13])
            description = parts[14] if parts[14] != 'unknown' else None
            n_ratings_kid = int(parts[15])
            n_ratings_teenager = int(parts[16])
            n_ratings_young_adult = int(parts[17])
            n_ratings_adult = int(parts[18])
            n_ratings_senior = int(parts[19])
            n_ratings_male = int(parts[20])
            n_ratings_female = int(parts[21])

            # Insert into the table
            cursor.execute('INSERT OR IGNORE INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           (item_id, movie_title, genres, director, producer, actors,
                            release_date, release_month, country, duration, age_rating, imdb_rating,
                            imdb_num_reviews,
                            n_ratings, n_ratings_kid, n_ratings_teenager, n_ratings_young_adult,
                            n_ratings_adult, n_ratings_senior, n_ratings_male, n_ratings_female,
                            description))

    cursor.execute('''CREATE TABLE IF NOT EXISTS interactions (user_id INTEGER PRIMARY KEY, items TEXT)''')

    # Read the file and build the dictionary
    user_interactions = read_ml100k_ratings()

    # Sort by timestamp
    user_interactions.sort(key=lambda x: x[2])

    # Build dictionary with timestamp-ordered items
    user_interactions_dict = {}
    for user_id, item_id, _ in user_interactions:
        if user_id not in user_interactions_dict:
            user_interactions_dict[user_id] = []
        user_interactions_dict[user_id].append(item_id)

    # Insert data into the table
    for user_id, items in user_interactions_dict.items():
        items_str = ','.join(map(str, items))
        cursor.execute('INSERT OR REPLACE INTO interactions (user_id, items) VALUES (?, ?)',
                       (user_id, items_str))

    # create user table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, age_category TEXT, gender TEXT)''')

    with open('./data/recsys/ml-100k/ml-100k.user', 'r') as f:
        first_line = True
        for line in f:
            if first_line:
                first_line = False
                continue
            user_id, age, gender, occupation, location = line.strip().split('\t')
            cursor.execute('INSERT OR REPLACE INTO users (user_id, age_category, gender) VALUES (?, ?, ?)',
                           (user_id, convert_age_to_string(int(age)), gender))


    conn.commit()
    conn.close()


def read_ml100k_ratings():
    user_interactions = []
    with open('./data/recsys/ml-100k/ml-100k.inter', 'r') as f:
        first_line = True
        for line in f:
            if first_line:
                first_line = False
                continue
            user_id, item_id, rating, timestamp = line.strip().split('\t')
            user_interactions.append((int(user_id), int(item_id), int(timestamp)))
    return user_interactions


def convert_age_to_string(age):
    """
    This simply converts integer ages into age categories.

    :param age: age of the person
    :return: string indicating the age category of the person
    """
    if age <= 12:
        return "kid"
    if 12 < age < 20:
        return "teenager"
    if 20 <= age <= 30:
        return "young adult"
    if 30 < age <= 60:
        return "adult"
    if 60 < age <= 100:
        return "senior"


def associate_tool_to_assistant(client, assistant_id, tool):
    """
    This function associates the passed tool to the passed assistant. Tools are the function that
    could be called by the assistant. See my_app/functions.py for reference.

    :param client: Entities API client
    :param assistant_id: ID of the assistant to which the tool is associated
    :param tool: tool to be associated
    """
    # check if tool is already associated
    tools = client.tools.list_tools(assistant_id)
    if tool['function']['name'] in [t['name'] for t in tools]:
        print("Tool already associated!")
    else:
        try:
            tool_func_obj = ToolFunction(function=tool['function'])

            tool_ = client.tools.create_tool(
                name=tool['function']['name'],
                type="function",
                function=tool_func_obj
            )

            client.tools.associate_tool_with_assistant(tool_id=tool_.id,
                                                       assistant_id=assistant_id)

            print(f"Associated tool {tool_.id} to assistant {assistant_id}")

        except ValueError as e:
            print(f"ERROR: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


def vector_store_setup_movielens(client, user_id, vector_store_name):
    """
    Ingest MovieLens metadata into a vector store,
    embedding all known descriptive attributes into vectorized text.

    :param client: Entities API client
    :param user_id: ID of the user for creating the vector store
    :param vector_store_name: name of the vector store
    """
    load_dotenv()

    # check if the vector store already exists
    if os.getenv('ENTITIES_VECTOR_STORE_ID') is not None:
        try:
            client.vectors.retrieve_vector_store(os.getenv('ENTITIES_VECTOR_STORE_ID'))
            print("Store already exists!")
        except Exception as e:
            print(f"Failed to retrieve vector store: {e}")
            print(f"Creating vector store: {vector_store_name}")
            create_vector_store(client, user_id, vector_store_name)
    else:
        create_vector_store(client, user_id, vector_store_name)


def create_vector_store(client, user_id, vector_store_name):
    movies = pd.read_csv(
        "./data/recsys/ml-100k/final_ml-100k.csv",
        sep="\t",
        encoding="latin-1"
    )

    def build_embedding_text(mv: pd.Series) -> str:
        fields = [f"Title: {mv['title']}"]

        if mv["genres"] != "unknown":
            fields.append(f"Genres: {mv['genres']}")

        if mv['description'] != "unknown":
            fields.append(f"Description: {mv['description']}")

        return ". \n".join(fields) + "."

    vs = client.vectors.create_vector_store(
        name=vector_store_name,
        user_id=user_id
    )

    collection = vs.collection_name
    print(f"🆕 Created vector store {vs.id} → collection '{collection}'")

    embedder = client.vectors.file_processor.embedding_model

    for _, mv in movies.iterrows():
        if mv["title"] != "unknown":
            text = build_embedding_text(mv)
            vec = embedder.encode(
                [text],
                convert_to_numpy=True,
                normalize_embeddings=True,
                truncate="model_max_length",
                show_progress_bar=False,
            )[0].tolist()

            meta = {
                "item_id": int(mv["item_id"]),
                # "title": mv["title"] if mv["title"] != "unknown" else None,
                # "genres": ast.literal_eval(mv["genres_list"]) if mv["genres_list"] != "unknown" else None,
                # "director": ast.literal_eval(mv["directors_list"]) if mv["directors_list"] != "unknown" else None,
                # "producer": ast.literal_eval(mv["producers_list"]) if mv["producers_list"] != "unknown" else None,
                # "actors": ast.literal_eval(mv["actors_list"]) if mv["actors_list"] != "unknown" else None,
                # "release_date": int(mv["release_date"]) if mv["release_date"] != "unknown" else None,
                # "duration": convert_duration(mv["duration"]) if mv["duration"] != "unknown" else None,
                # "age_rating": mv["age_rating"] if mv["age_rating"] != "unknown" else None,
                # "imdb_rating": float(mv["imdb_rating"]) if mv["imdb_rating"] != "unknown" else None,
                # "imdb_num_reviews": convert_num_reviews(mv["imdb_num_reviews"]) if mv["imdb_num_reviews"] != "unknown" else None,
                # "item_rating_count": int(mv["item_rating_count"]),
                # "popularity": mv["popularity"],
                "description": mv["description"] if mv["description"] != "unknown" else None,
                # "popular_kid": mv["popular_kid"],
                # "popular_teenager": mv["popular_teenager"],
                # "popular_young_adult": mv["popular_young_adult"],
                # "popular_adult": mv["popular_adult"],
                # "popular_senior": mv["popular_senior"]
            }

            client.vectors.vector_manager.add_to_store(
                store_name=collection,
                texts=[text],
                vectors=[vec],
                metadata=[meta],
            )

    print(f"✅ Ingested {len(movies)} fully enriched movies.")
    print("Adding vector store ID to .env")

    set_key("./.env", "ENTITIES_VECTOR_STORE_ID", str(vs.id), quote_mode="always")


def convert_duration(duration_str):
    # Regular expressions to extract hours and minutes
    hours_match = re.search(r'(\d+)\s*h', duration_str)
    minutes_match = re.search(r'(\d+)\s*min', duration_str)

    # Convert found values to integers, default to 0 if not found
    hours = int(hours_match.group(1)) if hours_match else 0
    minutes = int(minutes_match.group(1)) if minutes_match else 0

    return hours * 60 + minutes


def convert_num_reviews(view_str):
    view_str = view_str.strip().upper()
    multipliers = {'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000}

    if view_str[-1] in multipliers:
        num = float(view_str[:-1])
        return int(num * multipliers[view_str[-1]])
    else:
        return int(view_str)
