import pandas as pd
import ast
from src.my_app.utils import convert_age_to_string

# Genre mapping
genre_map = {
    0: "Action", 1: "Adventure", 2: "Animation", 3: "Children's",
    4: "Comedy", 5: "Crime", 6: "Documentary", 7: "Drama",
    8: "Fantasy", 9: "Film-Noir", 10: "Horror", 12: "Musical",
    13: "Mystery", 14: "Romance", 15: "Sci-Fi", 16: "Thriller", 17: "unknown",
    18: "War", 19: "Western"
}

# Read your original CSV
df = pd.read_csv('movielens100k_details.csv')

# Rename columns
df = df.rename(columns={
    'movie_genres': 'genres',
    'writer': 'producer',
    'cast': 'actors',
    'movie_length': 'duration',
    'rating': 'imdb_rating',
    'num_review': 'imdb_num_reviews',
    'year': 'release_date',
    'movie_id': 'item_id',
    'movie_title': 'title'
})

# Drop unwanted columns
df = df.drop(columns=['poster_url', 'movie_url', 'genre'])


# Convert genre IDs to names
def map_genre_ids(genre_id_string, as_list=False):
    try:
        ids = ast.literal_eval(genre_id_string)
        genres = [genre_map.get(int(i), f"Unknown({i})") for i in ids]
        if as_list:
            return genres
        else:
            if len(genres) == 1:
                return genres[0]
            elif len(genres) == 2:
                return f"{genres[0]} and {genres[1]}"
            else:
                return ", ".join(genres[:-1]) + ", and " + genres[-1]
    except (ValueError, SyntaxError):
        return "unknown"


def format_names(name_list):
    name_list = ast.literal_eval(name_list)
    if not name_list:
        return "unknown"
    elif len(name_list) == 1:
        return name_list[0]
    elif len(name_list) == 2:
        return f"{name_list[0]} and {name_list[1]}"
    else:
        return ", ".join(name_list[:-1]) + ", and " + name_list[-1]


def analyze_item_popularity(csv_path, quantiles=(0.25, 0.9)):
    """
    Loads a ratings CSV, counts the number of ratings per item, and computes quantiles.

    Args:
        csv_path (str): Path to the CSV file.
        quantiles (list): List of quantiles to compute, e.g., [0.25, 0.5, 0.75, 0.9].

    Returns:
        quantile_values (pd.Series): Quantile thresholds for rating counts.
    """
    # Load CSV
    df = pd.read_csv(csv_path, sep='\t')

    # Count number of ratings per item
    item_rating_counts = df['item_id:token'].value_counts().sort_values(ascending=False)

    # Compute quantiles
    quantile_values = list(item_rating_counts.quantile(quantiles))

    return item_rating_counts, quantile_values[0], quantile_values[1]


def get_popularity_label(count, low_q, high_q):
    """
    It computes whether an item is popular based on the number of ratings and quantiles of the
    rating distribution.

    :param count: number of ratings of the item
    :param low_q: low quantile
    :param high_q: high quantile
    :return: popularity value
    """
    if count >= high_q:
        return 'popular'
    elif count < low_q:
        return 'unpopular'
    else:
        return 'average'


def add_popularity_columns_by_age_group(ratings_path, users_path, items_df):
    """
    Adds binary columns to ratings_df indicating whether each item is popular within each age group.

    Args:
        ratings_path (str): Path to the ratings CSV file.
        users_path (str): Path to the users CSV file.
        items_df (pd.DataFrame): Items DataFrame.
    """
    users_df = pd.read_csv(users_path, sep="\t")
    ratings_df = pd.read_csv(ratings_path, sep="\t")
    # Convert age to age category
    users_df['age_category'] = users_df['age:token'].astype(int).apply(convert_age_to_string)

    # Merge ratings with user info
    merged_df = ratings_df.merge(users_df[['user_id:token', 'age_category']], on='user_id:token')

    # Identify all age groups
    age_groups = ["kid", "teenager", "young adult", "adult", "senior"]

    for age_group in age_groups:
        # Filter to the current group
        group_df = merged_df[merged_df['age_category'] == age_group]

        # Count ratings per item in this group
        item_counts = group_df['item_id:token'].value_counts()

        # Compute 0.9 quantile
        threshold = item_counts.quantile(0.9)

        # Get popular items in this group
        popular_items = set(item_counts[item_counts >= threshold].index)

        # Create binary column for this group
        column_name = f'popular_{age_group.replace(" ", "_")}'
        items_df[column_name] = items_df['item_id'].apply(lambda x: 1 if x in popular_items else 0)


df['genres_list'] = df['genres'].apply(map_genre_ids, args=(True, ))
df['genres'] = df['genres'].apply(map_genre_ids)
df['release_date'] = df['release_date'].str.extract(r'(\d{4})')
# df['release_date'] = pd.to_numeric(df['release_date'], errors='coerce').astype('Int64')
df['directors_list'] = df['director']
df['director'] = df['director'].apply(format_names)
df['actors_list'] = df['actors']
df['actors'] = df['actors'].apply(format_names)
df['producers_list'] = df['producer']
df['producer'] = df['producer'].apply(format_names)
item_rating_counts, low_q, high_q = analyze_item_popularity("./ml-100k.inter")
df['item_rating_count'] = df['item_id'].map(item_rating_counts)
df['popularity'] = df['item_rating_count'].apply(get_popularity_label, args=(low_q, high_q))

ordered_columns = ['item_id', 'title', 'genres', 'director', 'producer', 'actors', 'release_date', 'duration', 'age_rating', 'imdb_rating', 'imdb_num_reviews', 'item_rating_count', 'popularity', 'description', 'genres_list', 'directors_list', 'producers_list', 'actors_list', 'popular_kid', 'popular_teenager', 'popular_young_adult', 'popular_adult', 'popular_senior']

# fill remaining NaN values with unknown
df.fillna("unknown", inplace=True)

# compute popularity based on age category
add_popularity_columns_by_age_group("./ml-100k.inter", "./ml-100k.user", df)

# Save the final CSV
df.to_csv('final_ml-100k.csv', index=False, sep='\t', columns=ordered_columns)

print("Final CSV saved as 'final_movies.csv'")
