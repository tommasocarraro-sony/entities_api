RECOMMENDATION = {
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
                                                   "the threshold must be 4."
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
                                                   "the threshold must be 8."
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
                                                   "the threshold must be 120 (e.g., for 2h movies). Instead, if the "
                                                   "user asks for short movies, the threshold must be 30."
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
                                                           "the threshold must be 2000. If the user asks for old "
                                                           "movies, the threshold must be 1980."
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
                        "Filters for highly IMDb rated sci-fi movies starring Tom Cruise": {
                            "filters": {
                                "actors": ["Tom Cruise"],
                                "genres": ["sci-fi"],
                                "imdb_rating": {
                                    "request": "higher",
                                    "threshold": 8
                                }
                            }
                        },
                        "Filters for movies starring Tom Cruise and Emily Blunt, belonging to sci-fi and action genres, and with an IMDb rating higher than 7": {
                            "filters": {
                                "actors": ["Tom Cruise", "Emily Blunt"],
                                "genres": ["sci-fi", "action"],
                                "imdb_rating": {
                                    "request": "higher",
                                    "threshold": 7
                                }
                            }
                        },
                        "Filters for short comedy movies": {
                            "filters": {
                                "genres": ["comedy"],
                                "duration": {
                                    "request": "lower",
                                    "threshold": 30
                                }
                            }
                        },
                        "Filters for action movies lasting more than 1 hour and 30 minutes. This is the content of the \"filters\" field for this kind of request": {
                            "genres": ["action"],
                            "duration": {
                                "request": "higher",
                                "threshold": 90
                            }
                        },
                        "Filters for old but popular movies": {
                            "filters": {
                                "release_date": {
                                    "request": "lower",
                                    "threshold": 1980
                                },
                                "popularity": "popular"
                            }
                        },
                        "Filters for long movies directed by Christopher Nolan and recently released": {
                            "filters": {
                                "director": ["Christopher Nolan"],
                                "duration": {
                                    "request": "higher",
                                    "threshold": 120
                                },
                                "release_date": {
                                    "request": "higher",
                                    "threshold": 2000
                                }
                            }
                        },
                        "Filters for movies with a bad average rating in the platform": {
                            "filters": {
                                "avg_rating": {
                                    "request": "lower",
                                    "threshold": 2
                                }
                            }
                        },
                        "Filters for movies from France": {
                            "filters": {
                                "country": "France"
                            }
                        },
                        "Filters for movies starring Leonardo DiCaprio, belonging to sci-fi and thriller genres, and with a high average rating on the platform": {
                            "filters": {
                                "actors": ["Leonardo DiCaprio"],
                                "genres": ["sci-fi", "thriller"],
                                "director": ["Christopher Nolan"],
                                "avg_rating": {
                                    "request": "higher",
                                    "threshold": 4
                                }
                            }
                        },
                        "Filters for romantic short old movies from France": {
                            "filters": {
                                "genres": ["romance"],
                                "country": "France",
                                "duration": {
                                    "request": "lower",
                                    "threshold": 30
                                },
                                "release_date": {
                                    "request": "lower",
                                    "threshold": 1980
                                }
                            }
                        },
                        "Filters for recent animation movies produced by Pixar": {
                            "filters": {
                                "genres": ["animation"],
                                "producer": ["Pixar"],
                                "release_date": {
                                    "request": "higher",
                                    "threshold": 2000
                                }
                            }
                        },
                        "Filters for italian action movies with a low average rating on the platform": {
                            "filters": {
                                "genres": ["action"],
                                "country": "Italy",
                                "avg_rating": {
                                    "request": "lower",
                                    "threshold": 2
                                }
                            }
                        },
                        "Filters for old thriller movies directed by David Fincher": {
                            "filters": {
                                "genres": ["thriller"],
                                "director": ["David Fincher"],
                                "release_date": {
                                    "request": "lower",
                                    "threshold": 1980
                                }
                            }
                        },
                        "Filters for comedy movies produced by Judd Apatow and Will Ferrell": {
                            "filters": {
                                "genres": ["comedy"],
                                "producer": ["Judd Apatow", "Will Ferrell"]
                            }
                        },
                        "Filters for old historical and drama movies with a high average rating on the platform but an IMDb rating lower than 6": {
                            "filters": {
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
                            }
                        },
                        "Filters for movies released in 1994": {
                            "filters": {
                                "genres": ["action"],
                                "release_date": 1994
                            }
                        }
                    }
                }
            },
            "required": ["user", "k"],
            "examples": {
                "Provide 6 recommendations for user 14": {
                    "name": "get_top_k_recommendations",
                    "arguments": {
                        "user": 14,
                        "k": 6
                    }
                },
                "Provide some recommendations for user 85": {
                    "name": "get_top_k_recommendations",
                    "arguments": {
                        "user": 85,
                        "k": 5
                    }
                },
                "Recommend 3 recent action movies with a high IMDb rating for user 10": {
                    "name": "get_top_k_recommendations",
                    "arguments": {
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
                    }
                },
                "Recommend some sci-fi movies for user 45": {
                    "name": "get_top_k_recommendations",
                    "arguments": {
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
}

METADATA = {
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
                                   "\"imdb_rating\", \"popularity\"].",
                    "examples": {
                        "Specification for when actors and director are the requested features": {
                            "specification": ["actors", "director"]
                        },
                        "Specification for when title and description are the requested features": {
                            "specification": ["title", "description"]
                        },
                        "Specification for when full metadata is requested": {
                            "specification": ["title", "avg_rating", "description", "genres", "director", "producer", "duration", "release_date", "actors", "country", "imdb_rating", "popularity"]
                        },
                        "Specification for when the average rating, the IMDb rating, and the popularity are the requested features": {
                            "specification": ["avg_rating", "imdb_rating", "popularity"]
                        },
                        "Specification for when director, producer, and release date are the requested features": {
                            "specification": ["director", "producer", "release_date"]
                        },
                        "Specification for the genres and country are the requested features": {
                            "specification": ["genres", "country"]
                        },
                        "Specification for when title and duration are the requested features": {
                            "specification": ["title", "duration"]
                        },
                        "Specification for when title and director are the requested features": {
                            "specification": ["title", "director"]
                        }
                    }
                }
            }
        },
        "required": ["item", "specification"],
        "examples": {
            "Provide all the information you know about item 47": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 47,
                    "specification": ["title", "avg_rating", "description", "genres", "director", "producer", "duration", "release_date", "actors", "country", "imdb_rating", "popularity"]
                }
            },
            "What are the actors of item 54?": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 54,
                    "specification": ["actors"]
                }
            },
            "What are the director, genres and country of item 98?": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 98,
                    "specification": ["director", "genres", "country"]
                }
            },
            "Give me the release date and duration for item 12": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 12,
                    "specification": ["release_date", "duration"]
                }
            },
            "Show the IMDb rating and popularity of item 200": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 200,
                    "specification": ["imdb_rating", "popularity"]
                }
            },
            "Provide the title and average rating of item 77": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 77,
                    "specification": ["title", "avg_rating"]
                }
            },
            "Tell me about the genres and producer of item 150": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 150,
                    "specification": ["genres", "producer"]
                }
            },
            "What is the description of item 33?": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 33,
                    "specification": ["description"]
                }
            },
            "Provide information for item 205, including actors and director": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 205,
                    "specification": ["actors", "director"]
                }
            },
            "What are the genres and country for item 82?": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 82,
                    "specification": ["genres", "country"]
                }
            },
            "Show me the title, director, and popularity of item 120": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 120,
                    "specification": ["title", "director", "popularity"]
                }
            },
            "Give me the average rating and duration for item 50": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 50,
                    "specification": ["avg_rating", "duration"]
                }
            },
            "Tell me the country and release date for item 199": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 199,
                    "specification": ["country", "release_date"]
                }
            },
            "What is the producer and description of item 105?": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 105,
                    "specification": ["producer", "description"]
                }
            },
            "Provide the title and genres for item 60": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 60,
                    "specification": ["title", "genres"]
                }
            },
            "Give me the actors and IMDb rating of item 45": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 45,
                    "specification": ["actors", "imdb_rating"]
                }
            },
            "What is the release date of item 111?": {
                "name": "get_item_metadata",
                "arguments": {
                    "item": 111,
                    "specification": ["release_date"]
                }
            }
        }
    }
}

# todo explanation function and interaction function??
