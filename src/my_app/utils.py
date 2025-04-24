import sqlite3
from projectdavid import Entity
from projectdavid_common.schemas.tools import ToolFunction
import os
import re
import pandas as pd
from dotenv import load_dotenv
import ast
from rapidfuzz import process


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

    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
                    item_id INTEGER PRIMARY KEY,
                    title TEXT,
                    genres TEXT,
                    director TEXT,
                    producer TEXT,
                    actors TEXT,
                    release_date INTEGER,
                    duration INTEGER,
                    age_rating TEXT,
                    imdb_rating FLOAT,
                    imdb_num_reviews INTEGER,
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
            release_year = int(parts[6]) if parts[6].isdigit() and parts[6] != 'unknown' else None
            duration = int(parts[7]) if parts[7].isdigit() else None
            age_rating = parts[8] if parts[8] != 'unknown' else None
            imdb_rating = float(parts[9]) if parts[9] != 'unknown' else None
            imdb_num_reviews = int(parts[10]) if parts[10].isdigit() and parts[10] != 'unknown' else None
            description = parts[11] if parts[11] != 'unknown' else None

            # Insert into the table
            cursor.execute('INSERT OR IGNORE INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           (item_id, movie_title, genres, director, producer, actors,
                            release_year, duration, age_rating, imdb_rating, imdb_num_reviews,
                            description))

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

    # create the lists of actors, directors, producers, and genres for fuzzy matching
    global actors_list, producers_list, directors_list, genres_list
    actors_list = extract_unique_names("./data/recsys/ml-100k/final_ml-100k.csv", "actors_list")
    producers_list = extract_unique_names("./data/recsys/ml-100k/final_ml-100k.csv", "producers_list")
    directors_list = extract_unique_names("./data/recsys/ml-100k/final_ml-100k.csv", "directors_list")
    genres_list = extract_unique_names("./data/recsys/ml-100k/final_ml-100k.csv", "genres_list")


def extract_unique_names(csv_path, column):
    """
    This function extracts unique names from a column of the dataset CSV file. The returned list
    is used to implement fuzzy matching when performing SQL queries. Note fuzzy matching is only
    performed for textual features.

    :param csv_path: path to the CSV file
    :param column: column name
    :return: list of unique names
    """
    df = pd.read_csv(csv_path, sep='\t')

    all_names = set()

    for row in df[column].dropna():
        try:
            name_list = ast.literal_eval(row)
            all_names.update(name.strip() for name in name_list)
        except Exception as e:
            print(f"Error parsing row: {row}\n{e}")

    return sorted(all_names)


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
    elif table == "items" and ('genres' in conditions or 'actors' in conditions or
                               'director' in conditions or 'producer' in conditions or
                               'release_date' in conditions or 'duration' in conditions or
                               'imdb_rating' in conditions):
        # process textual features
        process_textual("genres", conditions, genres_list, query_parts)
        process_textual("actors", conditions, actors_list, query_parts)
        process_textual("director", conditions, directors_list, query_parts)
        process_textual("producer", conditions, producers_list, query_parts)

        # process numerical features
        process_numerical("release_date", conditions, query_parts)
        process_numerical("duration", conditions, query_parts)
        process_numerical("imdb_rating", conditions, query_parts)

        requested_field = "item_id"
    elif table == "items" and 'specification' in conditions and 'items' in conditions:
        specification = conditions['specification']
        items = conditions['items']
        requested_field = ", ".join(specification)
        query_parts.append(f"item_id IN ({', '.join([str(i) for i in items])})")
    else:
        return None
    if query_parts:
        sql_query = f"SELECT {requested_field} FROM {table} WHERE {'AND '.join(query_parts)}"
        print("\n" + sql_query + "\n")
        return sql_query
    else:
        raise ValueError("No matching conditions found in the database.")


def process_textual(feature, conditions, names_list, query_parts):
    """
    Process a textual feature for creating the SQL query.

    :param feature: name of the feature to be processed
    :param conditions: the filters provided by the user in the prompt
    :param names_list: list of valid names
    :param query_parts: str where to append the query part processed by this functions
    """
    if feature in conditions:
        f = conditions[feature]
        for f_ in f:
            # perform fuzzy matching
            f_corrected = correct_name(f_, names_list)
            if f_corrected is None:
                print(f"ERROR: {f_} is not a valid label for feature {feature}")
                continue  # if the name is not valid, we do not perform the query with that name
            query_parts.append(f"LOWER({feature}) LIKE '%{f_corrected.lower()}%'")


def correct_name(input_name, candidates, threshold=70):
    """
    Returns the best fuzzy match if above threshold; otherwise returns None.
    """
    print(f"Trying correcting name {input_name}")
    match, score, _ = process.extractOne(input_name, candidates)
    if score >= threshold:
        print(f"Corrected name {input_name} with name {match}")
        return match
    print(f"Failed to correct name {input_name}")
    return None


def process_numerical(feature, conditions, query_parts):
    """
    Process a numerical feature for creating the SQL query.

    :param feature: name of the feature to be processed
    :param conditions: conditions provided by the user in the prompt
    :param query_parts: str where to append the query part processed by this functions
    """
    if feature in conditions:
        f = conditions[feature]
        request = None
        if isinstance(f, dict):
            request = f['request']
            f = f['threshold']
        if request is not None:
            query_parts.append(
                f"{feature} > {f}") if request == "higher" else query_parts.append(
                f"{feature} < {f}")
        else:
            query_parts.append(f"{feature} = {f}")


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
