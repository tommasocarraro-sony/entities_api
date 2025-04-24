import sqlite3
from projectdavid import Entity
from projectdavid_common.schemas.tools import ToolFunction
import os
import re
import pandas as pd
from dotenv import load_dotenv
import ast


def create_entities_environment(api_key, user_id, assistant_tools):
    """
    This function creates the Entities API environment (middleware layer between user and LLM)

    :param api_key: api_key to access Entities API
    :param user_id: user_id of the user that interacts with the assistant (i.e., LLM)
    :param assistant_tools: tools (for function calling) that have to be associated with the
    assistant
    :return: client, user, thread, and assistant of Entities API environment
    """
    client = Entity(base_url="http://localhost:9000",
                    api_key=api_key)
    user = client.users.retrieve_user(user_id=user_id)
    thread = client.threads.create_thread(participant_ids=[user.id])
    assistant = client.assistants.retrieve_assistant("default")
    for tool in assistant_tools:
        associate_tool_to_assistant(assistant.id, tool=tool, api_key=api_key)

    return client, user, thread, assistant


def create_app_environment(database_name, entities_setup):
    """
    This function creates the entire app environment. The components of the app are:
    1. a database containing data accessible to the assistant through function calling;
    2. a pre-trained recommender system accessible to the assistant through function calling;
    3. the Entities API environment (middleware layer between user and LLM)

    :param database_name: name of the database that has to be created
    :param entities_setup: dictionary containing parameters for Entities API environment creation
    :return: client, user, thread, and assistant of Entities API environment
    """
    create_ml100k_db(database_name)
    return create_entities_environment(
        api_key=entities_setup["api_key"],
        user_id=entities_setup["user_id"],
        assistant_tools=entities_setup["assistant_tools"]
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

    cursor.execute('''CREATE TABLE IF NOT EXISTS items (item_id INTEGER PRIMARY KEY, title TEXT, release_date INTEGER, genres TEXT)''')

    # load data
    with open('./data/recsys/ml-100k/ml-100k.item', 'r', encoding='utf-8') as f:
        first_line = True
        for line in f:
            if first_line:
                first_line = False
                continue
            parts = line.strip().split('\t')
            if len(parts) < 4:
                continue  # skip lines with missing data

            item_id = int(parts[0])
            movie_title = parts[1]
            release_year = int(parts[2]) if parts[2].isdigit() else None
            movie_class = parts[3]

            # Insert into the table
            cursor.execute('INSERT OR IGNORE INTO items VALUES (?, ?, ?, ?)',
                           (item_id, movie_title, release_year, movie_class))

    cursor.execute('''CREATE TABLE IF NOT EXISTS interactions (user_id INTEGER PRIMARY KEY, items TEXT)''')

    # Read the file and build the dictionary
    user_interactions = []

    # Read and parse the file
    with open('./data/recsys/ml-100k/ml-100k.inter', 'r') as f:
        first_line = True
        for line in f:
            if first_line:
                first_line = False
                continue
            user_id, item_id, rating, timestamp = line.strip().split('\t')
            user_interactions.append((int(user_id), int(item_id), int(timestamp)))

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

    conn.commit()
    conn.close()


def associate_tool_to_assistant(assistant_id, tool, api_key):
    """
    This function associates the passed tool to the passed assistant. Tools are the function that
    could be called by the assistant. See my_app/functions.py for reference.

    :param assistant_id: ID of the assistant to which the tool is associated
    :param tool: tool to be associated
    :param api_key: api_key for Entities API
    """
    # create Entities API client
    client = Entity(base_url="http://localhost:9000",
                    api_key=api_key)
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


def execute_sql_query(db_name, sql_query):
    """
    This function executes the given SQL query and returns the result.

    :param db_name: database name
    :param sql_query: SQL query string
    :return: result of the query
    """
    conn = sqlite3.connect(f'{db_name}.db')
    cursor = conn.cursor()
    cursor.execute(sql_query)
    result = cursor.fetchall()
    conn.close()
    print("\n" + str(result) + "\n")
    return result


def define_sql_query(table, conditions):
    """
    This function defines a SQL query given the passed conditions (filter argument in the
    LLM-generated JSON for function calling)
    :param table: database table name
    :param conditions: filters to create SQL query
    :return: SQL query string ready to be executed
    """
    query_parts = []
    requested_field = ""
    if table == "interactions":
        if 'user' in conditions:
            user_id = conditions['user']
            query_parts.append(f'user_id = {user_id}')
            requested_field = "items"
        else:
            return None
    elif table == "items" and ('genres' in conditions or 'release_date' in conditions):
        if 'genres' in conditions:
            genres = conditions['genres']
            for genre in genres:
                query_parts.append(f"LOWER(genres) LIKE '%{genre.lower()}%'")

        if 'release_date' in conditions:
            release_date = conditions['release_date']
            request = None
            if isinstance(release_date, dict):
                request = release_date['request']
                release_date = release_date['threshold']
            if request is not None:
                query_parts.append(
                    f"release_date > {release_date}") if request == "higher" else query_parts.append(
                    f"release_date < {release_date}")
            else:
                query_parts.append(f"release_date = {release_date}")

        requested_field = "item_id"
    elif table == "items" and 'specification' in conditions and 'items' in conditions:
        specification = conditions['specification']
        items = conditions['items']
        requested_field = ", ".join(specification)
        query_parts.append(f"item_id IN ({', '.join([str(i) for i in items])})")
    else:
        return None

    sql_query = f"SELECT {requested_field} FROM {table} WHERE {'AND '.join(query_parts)}"
    print("\n" + sql_query + "\n")
    return sql_query


def create_md_from_item(item_file):
    output_file = f'{item_file[:-5]}.md'

    # Create a dictionary to store item metadata
    item_info = {}

    # Read the metadata file
    with open(item_file, 'r', encoding='utf-8') as meta:
        next(meta)  # Skip header
        for line in meta:
            parts = line.strip().split('\t')
            item_id = parts[0]
            title = parts[1]
            release_year = parts[2]
            genres = parts[3]
            item_info[item_id] = (title, release_year, genres)

    # Write to a markdown file
    with open(output_file, 'w', encoding='utf-8') as md:
        for item_id, (title, release_year, genres) in item_info.items():
            md.write(f"## Item ID: {item_id}\n\n")
            md.write(f"- Title: {title}\n")
            md.write(f"- Release Year: {release_year}\n")
            md.write(f"- Genres: {genres}\n\n")

    print("Markdown file created!")


def vector_store_setup_movielens():
    """
    Ingest MovieLens metadata into a vector store,
    embedding all known descriptive attributes into vectorized text.
    """
    load_dotenv()
    client = Entity(
        base_url=os.getenv("BASE_URL", "http://localhost:9000"),
        api_key=os.getenv("ENTITIES_API_KEY"),
    )
    user_id = os.getenv("ENTITIES_USER_ID")

    movies = pd.read_csv(
        "./data/recsys/ml-100k/final_ml-100k.csv",
        sep="\t",
        encoding="latin-1"
    )

    def build_embedding_text(mv: pd.Series) -> str:
        fields = [f"Title: {mv['title']}"]

        if mv["genres"] != "unknown":
            fields.append(f"Genres: {mv['genres']}")

        if mv['director'] != "unknown":
            fields.append(f"Director: {mv['director']}")

        if mv['producer'] != "unknown":
            fields.append(f"Producer: {mv['producer']}")

        if mv['actors'] != "unknown":
            fields.append(f"Actors: {mv['actors']}")

        if mv['release_date'] != "unknown":
            fields.append(f"Release date: {mv['release_date']}")

        if mv['duration'] == "unknown":
            fields.append(f"Duration: {mv['duration']}")

        if mv['age_rating'] != "unknown":
            fields.append(f"Age rating: {mv['age_rating']}")

        if mv['imdb_rating'] != "unknown":
            fields.append(f"IMDb rating: {mv['imdb_rating']}")

        if mv['imdb_num_reviews'] != "unknown":
            fields.append(f"IMDb review count: {mv['imdb_num_reviews']}")

        if mv['description'] != "unknown":
            fields.append(f"Description: {mv['description']}")

        return ". ".join(fields) + "."

    vs = client.vectors.create_vector_store(
        name="movielens-complete",
        user_id=user_id,
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
                "title": mv["title"] if mv["title"] != "unknown" else None,
                "genres": ast.literal_eval(mv["genres_list"]) if mv["genres_list"] != "unknown" else None,
                "director": ast.literal_eval(mv["director_list"]) if mv["director_list"] != "unknown" else None,
                "producer": ast.literal_eval(mv["producer_list"]) if mv["producer_list"] != "unknown" else None,
                "actors": ast.literal_eval(mv["actors_list"]) if mv["actors_list"] != "unknown" else None,
                "release_date": int(mv["release_date"]) if mv["release_date"] != "unknown" else None,
                "duration": convert_duration(mv["duration"]) if mv["duration"] != "unknown" else None,
                "age_rating": mv["age_rating"] if mv["age_rating"] != "unknown" else None,
                "imdb_rating": float(mv["imdb_rating"]) if mv["imdb_rating"] != "unknown" else None,
                "imdb_num_reviews": convert_num_reviews(mv["imdb_num_reviews"]) if mv["imdb_num_reviews"] != "unknown" else None,
                "description": mv["description"] if mv["description"] != "unknown" else None
            }

            client.vectors.vector_manager.add_to_store(
                store_name=collection,
                texts=[text],
                vectors=[vec],
                metadata=[meta],
            )

    print(f"✅ Ingested {len(movies)} fully enriched movies.")


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
