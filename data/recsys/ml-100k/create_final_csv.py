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

ordered_columns = ['item_id', 'title', 'genres', 'director', 'producer', 'actors', 'release_date', 'duration', 'age_rating', 'imdb_rating', 'imdb_num_reviews', 'description', 'genres_list', 'directors_list', 'producers_list', 'actors_list']

# fill remaining NaN values with unknown
df.fillna("unknown", inplace=True)

# Save the final CSV
df.to_csv('final_ml-100k.csv', index=False, sep='\t', columns=ordered_columns)

print("Final CSV saved as 'final_movies.csv'")


# todo if it does not work with numerical features, we can implement filters
