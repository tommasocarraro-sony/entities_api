RECOMMENDATION = {
    "type": "function",
    "function": {
        "name": "get_top_k_recommendations",
        "description": (
            "Returns a ranking of recommended item IDs for the specified user ID. "
            "If some conditions are given in the user request, the returned items must satisfy these conditions."
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
                    "description": "Number of items IDs that have to be included in the generated ranking. "
                                   "Default value is 5."
                },
                "filters": {
                    "type": "object",
                    "description": "Optional filters that specify the conditions the recommended items must satisfy.",
                    "properties": {
                        "actors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of actor names to filter by."
                        },
                        "genres": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of movie genres to filter by."
                        },
                        "director": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of directors to filter by."
                        },
                        "producer": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of producers to filter by."
                        },
                        "country": {
                            "type": "string",
                            "description": "The country of origin for the movie (e.g., 'USA')."
                        },
                        "avg_rating": {
                            "type": "object",
                            "properties": {
                                "request": {
                                    "type": "string",
                                    "enum": ["higher", "lower"],
                                    "description": "Whether to search for movies with high or low average ratings."
                                },
                                "threshold": {
                                    "type": "number",
                                    "description": "Threshold for average rating (between 1 and 5). "
                                                   "If not explicitly provided in the request, try to infer it."
                                                   "For example, if the user asks for highly rated movies, "
                                                   "the threshold might be 4."
                                }
                            },
                            "required": ["request", "threshold"]
                        },
                        "imdb_rating": {
                            "type": "object",
                            "properties": {
                                "request": {
                                    "type": "string",
                                    "enum": ["higher", "lower"],
                                    "description": "Whether to search for movies with high or low IMDb ratings. "
                                                   "If not explicitly provided in the request, try to infer it."
                                                   "For example, if the user asks for highly IMDb rated movies, "
                                                   "the threshold might be 7."
                                },
                                "threshold": {
                                    "type": "number",
                                    "description": "Threshold for IMDb rating (between 1 and 10)."
                                }
                            },
                            "required": ["request", "threshold"]
                        },
                        "duration": {
                            "type": "object",
                            "properties": {
                                "request": {
                                    "type": "string",
                                    "enum": ["higher", "lower"],
                                    "description": "Whether to search for longer or shorter movie durations."
                                },
                                "threshold": {
                                    "type": "integer",
                                    "description": "Duration in minutes (e.g., 90 for 1h30min)."
                                                   "If not explicitly provided in the request, try to infer it."
                                                   "For example, if the user asks for long movies, "
                                                   "the threshold might be 120 (e.g., for 2h movies). Instead, if the "
                                                   "user asks for short movies, the threshold might be 30."
                                }
                            },
                            "required": ["request", "threshold"]
                        },
                        "release_date": {
                            "oneOf": [
                                {
                                    "type": "integer",
                                    "description": "Exact release year (e.g., 1994)."
                                },
                                {
                                    "type": "object",
                                    "properties": {
                                        "request": {
                                            "type": "string",
                                            "enum": ["higher", "lower"],
                                            "description": "Whether to search for more recent or older releases."
                                        },
                                        "threshold": {
                                            "type": "integer",
                                            "description": "Year threshold (e.g., 2000)."
                                                           "If not explicitly provided in the request, try to infer it."
                                                           "For example, if the user asks for recent movies, "
                                                           "the threshold might be 2000. If the user asks for old "
                                                           "movies, the threshold might be 1980."
                                        }
                                    },
                                    "required": ["request", "threshold"]
                                }
                            ]
                        },
                        "popularity": {
                            "type": "string",
                            "enum": ["popular", "unpopular"],
                            "description": "Whether to filter for popular or unpopular movies."
                        }
                    },
                    "examples": {
                        "highly_imdb_rated_sci_fi_movies_with_tom_cruise": {
                            "actors": ["Tom Cruise"],
                            "genres": ["sci-fi"],
                            "imdb_rating": {
                                "request": "higher",
                                "threshold": 8
                            }
                        },
                        "higher_than_7_imdb_rated_action_and_sci-fi_movies_with_tom_cruise_and_emily_blunt": {
                            "actors": ["Tom Cruise", "Emily Blunt"],
                            "genres": ["sci-fi", "action"],
                            "imdb_rating": {
                                "request": "higher",
                                "threshold": 7
                            }
                        },
                        "short_comedies": {
                            "genres": ["comedy"],
                            "duration": {
                                "request": "lower",
                                "threshold": 30
                            }
                        },
                        "action_movies_longer_than_1_hour_and_30_minutes": {
                            "genres": ["action"],
                            "duration": {
                                "request": "higher",
                                "threshold": 90
                            }
                        },
                        "old_popular_movies": {
                            "release_date": {
                                "request": "lower",
                                "threshold": 1980
                            },
                            "popularity": "popular"
                        },
                        "long_recent_movies_by_director": {
                            "director": ["Christopher Nolan"],
                            "duration": {
                                "request": "higher",
                                "threshold": 120
                            },
                            "release_date": {
                                "request": "higher",
                                "threshold": 2000
                            }
                        },
                        "badly_rated_avg": {
                            "avg_rating": {
                                "request": "lower",
                                "threshold": 2
                            }
                        },
                        "country_specific": {
                            "country": "France"
                        },
                        "highly_rated_sci_fi_thrillers_with_di_caprio_and_nolan": {
                            "actors": ["Leonardo DiCaprio"],
                            "genres": ["sci-fi", "thriller"],
                            "director": ["Christopher Nolan"],
                            "avg_rating": {
                                "request": "higher",
                                "threshold": 4
                            },
                        },
                        "short_old_french_romance_movies": {
                            "genres": ["romance"],
                            "country": "France",
                            "duration": {
                                "request": "lower",
                                "threshold": 30
                            },
                            "release_date": {
                                "request": "lower",
                                "threshold": 1980
                            },
                        },
                        "recent_animated_movies_produced_by_pixar": {
                            "genres": ["animation"],
                            "producer": ["Pixar"],
                            "release_date": {
                                "request": "higher",
                                "threshold": 2000
                            },
                        },
                        "long_badly_rated_action_movies_from_india": {
                            "genres": ["action"],
                            "country": "India",
                            "avg_rating": {
                                "request": "lower",
                                "threshold": 2.5
                            },
                        },
                        "older_thrillers_by_david_fincher": {
                            "genres": ["thriller"],
                            "director": ["David Fincher"],
                            "release_date": {
                                "request": "lower",
                                "threshold": 1980
                            },
                        },
                        "comedies_by_producers_judd_apatow_and_will_ferrell": {
                            "genres": ["comedy"],
                            "producer": ["Judd Apatow", "Will Ferrell"],
                        },
                        "historical_dramas_with_low_imdb_but_high_avg_rating": {
                            "genres": ["history", "drama"],
                            "avg_rating": {
                                "request": "higher",
                                "threshold": 4
                            },
                            "imdb_rating": {
                                "request": "lower",
                                "threshold": 6
                            },
                            "release_date": {
                                "request": "lower",
                                "threshold": 1980
                            }
                        },
                        "exact_year_release_action_movie_1994": {
                            "genres": ["action"],
                            "release_date": 1994
                        }
                    }
                }
            },
            "required": ["user", "k"],
            "examples": {
                "recommendation_of_6_movies_for_user_14": {
                    "user": 14,
                    "k": 6
                },
                "recommendation_for_user_85": {
                    "user": 85,
                    "k": 5
                },
                "recommendation_of_3_recent_action_movies_with_high_IMDb_score_for_user_10": {
                    "user": 10,
                    "k": 3,
                    "filters": {
                        "genres": ["action"],
                        "release_date": {
                            "request": "higher",
                            "threshold": 2000
                        },
                        "imdb_rating": {
                            "request": "higher",
                            "threshold": 8
                        }
                    }
                },
                "recommendation_of_sci-fi_movies_for_user_45": {
                    "user": 45,
                    "k": 5,
                    "filters": {
                        "genres": ["sci-fi"]
                    }
                }
            }
        }
    }
}

METADATA = {
    "type": "function",
    "function": {
        "name": "get_item_metadata",
        "description": (
            "Returns metadata for the given item ID. Specific metadata might be requested. If no specification is given"
            "all the metadata available for the item is returned."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "item": {
                    "type": "integer",
                    "description": "Item ID for which the metadata has to be retrieved."
                },
                "specification": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of item metadata features to be included in the response. Available features"
                                   "are: [\"title\", \"avg_rating\", \"description\", \"genres\", \"director\", "
                                   "\"producer\", \"duration\", \"release_date\", \"actors\", \"country\", "
                                   "\"imdb_rating\", \"popularity\"]."
                }
            }
        },
        "required": ["item"],
        "examples": {
            "all_metadata_for_item_47": {
                "item": 47
            },
            "actors_of_item_54": {
                "item": 54,
                "specification": ["actors"]
            },
            "country_genres_director_for_item_98": {
                "item": 98,
                "specification": ["director", "genres", "country"]
            }
        }
    }
}

# todo explanation function and interaction function??
