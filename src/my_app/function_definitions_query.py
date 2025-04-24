INTERACTION_QUERY = {
    "function": {
        "name": "get_past_interactions",
        "description": (
            "Returns previously interacted item IDs for the given user ID. "
            "This function uses a SQL query to extract the user interactions. Note that"
            "when generating JSON files for this function, you always has to follow the template"
            "given in the examples."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to retrieve historical interactions for given user."
                }
            }
        },
        "required": ["query"],
        "examples": {
            "Provide me the historical interactions of user 45.": {
                "name": "get_past_interactions",
                "arguments": {
                    "query": "SELECT items FROM interactions WHERE user_id = 45"
                }
            },
            "What are the items user 14 interacted in the past?": {
                "name": "get_past_interactions",
                "arguments": {
                    "query": "SELECT items FROM interactions WHERE user_id = 14"
                }
            },
            "List all previously interacted items for user 88.": {
                "name": "get_past_interactions",
                "arguments": {
                    "query": "SELECT items FROM interactions WHERE user_id = 88"
                }
            },
            "Show me the past interaction history of user 32.": {
                "name": "get_past_interactions",
                "arguments": {
                    "query": "SELECT items FROM interactions WHERE user_id = 32"
                }
            },
            "Retrieve interaction records for user 101.": {
                "name": "get_past_interactions",
                "arguments": {
                    "query": "SELECT items FROM interactions WHERE user_id = 101"
                }
            },
            "Which items has user 67 interacted with before?": {
                "name": "get_past_interactions",
                "arguments": {
                    "query": "SELECT items FROM interactions WHERE user_id = 67"
                }
            }
        }
    }
}

METADATA_QUERY = {
    "function": {
        "name": "get_item_metadata",
        "description": (
            "Returns metadata for the given item ID(s). Specific metadata might be "
            "requested. If no specification is given all the metadata available for the item(s) is "
            "returned. Available metadata features are: \"actors\", \"genres\", \"release_date\", "
            "\"imdb_rating\", \"director\", \"producer\", \"country\", \"avg_rating\", \"duration\""
            ", \"popularity\", \"description\". This function uses a SQL query to extract the "
            "requested metadata. Note that"
            "when generating JSON files for this function, you always has to follow the template"
            "given in the examples."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filter_query": {
                    "type": "string",
                    "description": "SQL query to retrieve requested metadata for given item(s)."
                }
            }
        },
        "required": ["filter_query"],
        "examples": {
            "Provide me actors and director of item 45.": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, actors, director FROM movie_metadata WHERE item_id = 45"
                }
            },
            "Provide all the information you know about item 47": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, title, avg_rating, description, genres, director, producer, duration, release_date, actors, country, imdb_rating, popularity FROM movie_metadata WHERE item_id = 47"
                }
            },
            "What are the actors of item 54?": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, actors FROM movie_metadata WHERE item_id = 54"
                }
            },
            "What are the director, genres and country of item 98?": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, director, genres, country FROM movie_metadata WHERE item_id = 98"
                }
            },
            "Give me the release date and duration for item 12": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, release_date, duration FROM movie_metadata WHERE item_id = 12"
                }
            },
            "Show the IMDb rating and popularity of item 200": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, imdb_rating, popularity FROM movie_metadata WHERE item_id = 200"
                }
            },
            "Provide the title and average rating of item 77": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, title, avg_rating FROM movie_metadata WHERE item_id = 77"
                }
            },
            "Tell me about the genres and producer of item 150": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, genres, producer FROM movie_metadata WHERE item_id = 150"
                }
            },
            "What is the description of item 33?": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, description FROM movie_metadata WHERE item_id = 33"
                }
            },
            "Provide information for item 205, including actors and director": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, actors, director FROM movie_metadata WHERE item_id = 205"
                }
            },
            "What are the genres and country for item 82?": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, genres, country FROM movie_metadata WHERE item_id = 82"
                }
            },
            "Show me the title, director, and popularity of item 120": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, title, director, popularity FROM movie_metadata WHERE item_id = 120"
                }
            },
            "Give me the average rating and duration for item 50": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, avg_rating, duration FROM movie_metadata WHERE item_id = 50"
                }
            },
            "Tell me the country and release date for item 199": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, country, release_date FROM movie_metadata WHERE item_id = 199"
                }
            },
            "What is the producer and description of item 105?": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, producer, description FROM movie_metadata WHERE item_id = 105"
                }
            },
            "Provide the title and genres for item 60": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, title, genres FROM movie_metadata WHERE item_id = 60"
                }
            },
            "Give me the actors and IMDb rating of item 45": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, actors, imdb_rating FROM movie_metadata WHERE item_id = 45"
                }
            },
            "What is the release date of item 111?": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, release_date FROM movie_metadata WHERE item_id = 111"
                }
            },
            "Show me the title, director, and popularity of items 120, 121, and 122": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, title, director, popularity FROM movie_metadata WHERE item_id IN (120, 121, 122)"
                }
            },
            "Give me the average rating and duration for items 50, 51, and 52": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, avg_rating, duration FROM movie_metadata WHERE item_id IN (50, 51, 52)"
                }
            },
            "Tell me the country and release date for items 199, 200, and 201": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, country, release_date FROM movie_metadata WHERE item_id IN (199, 200, 201)"
                }
            },
            "What is the producer and description of items 105, 106, and 107?": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, producer, description FROM movie_metadata WHERE item_id IN (105, 106, 107)"
                }
            },
            "Provide the title and genres for items 60, 61, and 62": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, title, genres FROM movie_metadata WHERE item_id IN (60, 61, 62)"
                }
            },
            "Give me the actors and IMDb rating of items 45, 46, and 47": {
                "name": "get_item_metadata",
                "arguments": {
                    "filter_query": "SELECT item_id, actors, imdb_rating FROM movie_metadata WHERE item_id IN (45, 46, 47)"
                }
            }
        }
    }
}

RECOMMENDATION_QUERY = {
    "function": {
        "name": "get_top_k_recommendations",
        "description": (
            "Returns a ranking of recommended item IDs for the specified user ID. "
            "If some conditions are given in the user request (e.g., recommendations for movies "
            "with specific genres, actors, and so on), the returned items must satisfy "
            "these conditions. An SQL query is used to retrieve item IDs of items satisfying "
            "the conditions. Then, a pre-trained recommender system is called on them. Note that"
            "when generating JSON files for this function, you always has to follow the template"
            "given in the examples."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user": {
                    "type": "integer",
                    "description": "User ID for which the recommendations have to be retrieved."
                },
                "k": {
                    "type": "integer",
                    "description": "Number of items IDs that have to be included in the generated "
                                   "ranking. Default value is 5."
                },
                "filter_query": {
                    "type": "string",
                    "description": "Optional SQL query used to filter items before the recommender "
                                   "system is called. The features available for filtering are: "
                                   "\"actors\", \"genres\", \"release_date\", \"imdb_rating\", "
                                   "\"director\", \"producer\", \"country\", \"avg_rating\", "
                                   "\"duration\", \"popularity\"."
                }
            }
        },
        "required": ["user", "k"],
        "examples": {
            "Recommend some highly IMDb rated sci-fi movies starring Tom Cruise for user 14": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 14,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER(%Sci-Fi%) AND LOWER(actors) LIKE LOWER(%tom cruise%) AND imdb_rating >= 8"
                }
            },
            "Provide some movies starring Tom Cruise and Emily Blunt, belonging to sci-fi and action genres, and with an IMDb rating higher than 7 for user 128": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 128,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(actors) LIKE LOWER(%Tom Cruise%) AND LOWER(actors) LIKE LOWER(%Emily Blunt%) AND LOWER(genres) LIKE LOWER(%Sci-Fi%) AND LOWER(genres) LIKE LOWER(%Action%) AND imdb_rating > 7"
                }
            },
            "Recommend some short comedy movies for user 23": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 23,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER(%Comedy%) AND duration <= 30"
                }
            },
            "Suggest 3 horror movies directed by Jordan Peele, released after 2015 for user 45": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 45,
                    "k": 3,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Horror%') AND LOWER(director) LIKE LOWER('%Jordan Peele%') AND release_date > 2015"
                }
            },
            "List 8 drama movies produced by Warner Bros with average user ratings above 4.0 for user 87": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 87,
                    "k": 8,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Drama%') AND LOWER(producer) LIKE LOWER('%Warner Bros%') AND avg_rating > 4.0"
                }
            },
            "Recommend 10 French romantic films with an IMDb rating above 8.2 for user 12": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 12,
                    "k": 10,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Romance%') AND LOWER(country) LIKE LOWER('%France%') AND imdb_rating > 8.2"
                }
            },
            "Give me popular action movies shorter than 90 minutes for user 99": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 99,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Action%') AND duration < 90 AND popularity = 'popular'"
                }
            },
            "Suggest documentaries produced by BBC with an IMDb rating above 7.5 for user 60": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 60,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Documentary%') AND LOWER(producer) LIKE LOWER('%BBC%') AND imdb_rating > 7.5"
                }
            },
            "Recommend American thrillers directed by Christopher Nolan with an average rating above 4.5 for user 200": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 200,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Thriller%') AND LOWER(director) LIKE LOWER('%Christopher Nolan%') AND LOWER(country) LIKE LOWER('%USA%') AND avg_rating > 4.5"
                }
            },
            "Give me romantic comedies starring Ryan Reynolds and produced by 20th Century Fox for user 5": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 5,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Romantic%') AND LOWER(genres) LIKE LOWER('%Comedy%') AND LOWER(actors) LIKE LOWER('%Ryan Reynolds%') AND LOWER(producer) LIKE LOWER('%20th Century Fox%')"
                }
            },
            "Show me action movies longer than 90 minutes for user 34": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 34,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Action%') AND duration > 90"
                }
            },
            "Recommend some old but still popular movies for user 7": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 7,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE release_date < 1980 AND popularity = 'popular'"
                }
            },
            "Suggest 15 long and recently released movies directed by Christopher Nolan for user 88": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 88,
                    "k": 15,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(director) LIKE LOWER('%Christopher Nolan%') AND duration > 120 AND release_date > 2000"
                }
            },
            "Find movies with a very low average rating for user 102": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 102,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE avg_rating < 2"
                }
            },
            "Give me 2 movies from France for user 50": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 50,
                    "k": 2,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(country) LIKE LOWER('%France%')"
                }
            },
            "Find 23 sci-fi thriller movies starring Leonardo DiCaprio, directed by Christopher Nolan, with a high average rating for user 11": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 11,
                    "k": 23,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(actors) LIKE LOWER('%Leonardo DiCaprio%') AND LOWER(genres) LIKE LOWER('%Sci-Fi%') AND LOWER(genres) LIKE LOWER('%Thriller%') AND LOWER(director) LIKE LOWER('%Christopher Nolan%') AND avg_rating > 4"
                }
            },
            "Show me short old French romantic movies for user 63": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 63,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Romance%') AND LOWER(country) LIKE LOWER('%France%') AND duration < 30 AND release_date < 1980"
                }
            },
            "List recent animated movies produced by Pixar for user 78": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 78,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Animation%') AND LOWER(producer) LIKE LOWER('%Pixar%') AND release_date > 2000"
                }
            },
            "Show me Italian action movies with a low average rating for user 44": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 44,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Action%') AND LOWER(country) LIKE LOWER('%Italy%') AND avg_rating < 2"
                }
            },
            "Find old thriller movies directed by David Fincher for user 90": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 90,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Thriller%') AND LOWER(director) LIKE LOWER('%David Fincher%') AND release_date < 1980"
                }
            },
            "Suggest comedy movies produced by Judd Apatow or Will Ferrell for user 18": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 18,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Comedy%') AND (LOWER(producer) LIKE LOWER('%Judd Apatow%') OR LOWER(producer) LIKE LOWER('%Will Ferrell%'))"
                }
            },
            "Find old historical drama movies with a high platform rating but a low IMDb score for user 120": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 120,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%History%') AND LOWER(genres) LIKE LOWER('%Drama%') AND avg_rating > 4 AND imdb_rating < 6 AND release_date < 1980"
                }
            },
            "Give me action movies released in 1994 for user 77": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 77,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%Action%') AND release_date = 1994"
                }
            },
            "Suggest 8 movies for user 32": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 32,
                    "k": 8
                }
            },
            "Generate 4 recommendations for user 57": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 57,
                    "k": 4
                }
            },
            "Recommend 5 IMDb top-rated recent action films for user 22": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 22,
                    "k": 5,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%action%') AND release_date > 2000 AND imdb_rating > 8"
                }
            },
            "Show 6 sci-fi movie suggestions for user 73": {
                "name": "get_top_k_recommendations",
                "arguments": {
                    "user": 73,
                    "k": 6,
                    "filter_query": "SELECT item_id FROM movie_metadata WHERE LOWER(genres) LIKE LOWER('%sci-fi%')"
                }
            }
        }
    }
}
