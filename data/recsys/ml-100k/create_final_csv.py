import pandas as pd
import ast

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

ordered_columns = ['item_id', 'title', 'genres', 'director', 'producer', 'actors', 'release_date', 'duration', 'age_rating', 'imdb_rating', 'imdb_num_reviews', 'item_rating_count', 'popularity', 'description', 'genres_list', 'directors_list', 'producers_list', 'actors_list']

# fill remaining NaN values with unknown
df.fillna("unknown", inplace=True)

# Save the final CSV
df.to_csv('final_ml-100k.csv', index=False, sep='\t', columns=ordered_columns)

print("Final CSV saved as 'final_movies.csv'")
