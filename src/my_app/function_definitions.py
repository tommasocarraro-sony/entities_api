RECOMMENDATION = {
    "function": {
        "name": "get_top_k_recommendations",
        "description": (
            "Returns a ranking of recommended item IDs for the specified user ID. "
            "If some conditions are given in the user request, the returned items must satisfy "
            "these conditions."
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
                        # "country": {
                        #     "type": "string",
                        #     "description": "The country of origin for the movie (e.g., 'USA')."
                        # },
                        # "avg_rating": {
                        #     "type": "object",
                        #     "properties": {
                        #         "request": {
                        #             "type": "string",
                        #             "enum": ["higher", "lower"],
                        #             "description": "Whether to search for movies with high or low average ratings."
                        #         },
                        #         "threshold": {
                        #             "type": "number",
                        #             "description": "Threshold for average rating (between 1 and 5). "
                        #                            "If not explicitly provided in the request, try to infer it."
                        #                            "For example, if the user asks for highly rated movies, "
                        #                            "the threshold must be 4."
                        #         }
                        #     },
                        #     "required": ["request", "threshold"]
                        # },
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
                        },
                        "popularity_by_age_category": {
                            "type": "string",
                            "enum": ["popular_kid", "popular_teenager", "popular_young_adult",
                                     "popular_adult", "popular_senior"],
                            "description": "Whether to filter for popular or unpopular movies on a "
                                           "specific age group."
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
                        # "Filters for movies with a bad average rating in the platform": {
                        #     "filters": {
                        #         "avg_rating": {
                        #             "request": "lower",
                        #             "threshold": 2
                        #         }
                        #     }
                        # },
                        # "Filters for movies from France": {
                        #     "filters": {
                        #         "country": "France"
                        #     }
                        # },
                        # "Filters for movies starring Leonardo DiCaprio, belonging to sci-fi and thriller genres, and with a high average rating on the platform": {
                        #     "filters": {
                        #         "actors": ["Leonardo DiCaprio"],
                        #         "genres": ["sci-fi", "thriller"],
                        #         "director": ["Christopher Nolan"],
                        #         "avg_rating": {
                        #             "request": "higher",
                        #             "threshold": 4
                        #         }
                        #     }
                        # },
                        # "Filters for romantic short old movies from France": {
                        #     "filters": {
                        #         "genres": ["romance"],
                        #         "country": "France",
                        #         "duration": {
                        #             "request": "lower",
                        #             "threshold": 30
                        #         },
                        #         "release_date": {
                        #             "request": "lower",
                        #             "threshold": 1980
                        #         }
                        #     }
                        # },
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
                        # "Filters for italian action movies with a low average rating on the platform": {
                        #     "filters": {
                        #         "genres": ["action"],
                        #         "country": "Italy",
                        #         "avg_rating": {
                        #             "request": "lower",
                        #             "threshold": 2
                        #         }
                        #     }
                        # },
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
                        # "Filters for old historical and drama movies with a high average rating on the platform but an IMDb rating lower than 6": {
                        #     "filters": {
                        #         "genres": ["history", "drama"],
                        #         "avg_rating": {
                        #             "request": "higher",
                        #             "threshold": 4
                        #         },
                        #         "imdb_rating": {
                        #             "request": "lower",
                        #             "threshold": 6
                        #         },
                        #         "release_date": {
                        #             "request": "lower",
                        #             "threshold": 1980
                        #         }
                        #     }
                        # },
                        "Filters for movies released in 1994": {
                            "filters": {
                                "genres": ["action"],
                                "release_date": 1994
                            }
                        },
                        "Filters for movies with Tom Cruise popular among young adults": {
                            "filters": {
                                "actors": ["Tom Cruise"],
                                "popularity_by_age_category": "popular_young_adult"
                            }
                        },
                        "Filters for movies released prior to 1996 popular among kids": {
                            "filters": {
                                "release_date": {
                                    "request": "lower",
                                    "threshold": 1996
                                },
                                "popularity_by_age_category": "popular_kid"
                            }
                        },
                        "Filters for drama movies popular among teenagers": {
                            "filters": {
                                "genres": ["drama"],
                                "popularity_by_age_category": "popular_teenager"
                            }
                        },
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
                },
                "Recommend some movies with Tom Cruise that are popular among teenagers for user 45": {
                    "name": "get_top_k_recommendations",
                    "arguments": {
                        "user": 45,
                        "k": 5,
                        "filters": {
                            "actors": ["Tom Cruise"],
                            "popularity_by_age_category": "popular_teenager"
                        }
                    }
                }
            }
        }
    }
}

RECOMMENDATION_VECTOR = {
    "function": {
        "name": "get_recommendations_by_description",
        "description": (
            "This function recommends items that match the given textual description."
            "It returns a ranking of recommended item IDs for the specified user ID."
            "If some conditions are given in the user request, the returned items must satisfy "
            "these conditions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user": {
                    "type": "integer",
                    "description": "User ID for which the recommendations have to be retrieved."
                },
                "query": {
                    "type": "string",
                    "description": "Query to be performed on a vector store to find items that match the user description. This has to be generated by the LLM based on the user prompt."
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
                        # "country": {
                        #     "type": "string",
                        #     "description": "The country of origin for the movie (e.g., 'USA')."
                        # },
                        # "avg_rating": {
                        #     "type": "object",
                        #     "properties": {
                        #         "request": {
                        #             "type": "string",
                        #             "enum": ["higher", "lower"],
                        #             "description": "Whether to search for movies with high or low average ratings."
                        #         },
                        #         "threshold": {
                        #             "type": "number",
                        #             "description": "Threshold for average rating (between 1 and 5). "
                        #                            "If not explicitly provided in the request, try to infer it."
                        #                            "For example, if the user asks for highly rated movies, "
                        #                            "the threshold must be 4."
                        #         }
                        #     },
                        #     "required": ["request", "threshold"]
                        # },
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
                        },
                        "popularity_by_age_category": {
                            "type": "string",
                            "enum": ["popular_kid", "popular_teenager", "popular_young_adult",
                                     "popular_adult", "popular_senior"],
                            "description": "Whether to filter for popular or unpopular movies on a "
                                           "specific age group."
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
                        # "Filters for movies with a bad average rating in the platform": {
                        #     "filters": {
                        #         "avg_rating": {
                        #             "request": "lower",
                        #             "threshold": 2
                        #         }
                        #     }
                        # },
                        # "Filters for movies from France": {
                        #     "filters": {
                        #         "country": "France"
                        #     }
                        # },
                        # "Filters for movies starring Leonardo DiCaprio, belonging to sci-fi and thriller genres, and with a high average rating on the platform": {
                        #     "filters": {
                        #         "actors": ["Leonardo DiCaprio"],
                        #         "genres": ["sci-fi", "thriller"],
                        #         "director": ["Christopher Nolan"],
                        #         "avg_rating": {
                        #             "request": "higher",
                        #             "threshold": 4
                        #         }
                        #     }
                        # },
                        # "Filters for romantic short old movies from France": {
                        #     "filters": {
                        #         "genres": ["romance"],
                        #         "country": "France",
                        #         "duration": {
                        #             "request": "lower",
                        #             "threshold": 30
                        #         },
                        #         "release_date": {
                        #             "request": "lower",
                        #             "threshold": 1980
                        #         }
                        #     }
                        # },
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
                        # "Filters for italian action movies with a low average rating on the platform": {
                        #     "filters": {
                        #         "genres": ["action"],
                        #         "country": "Italy",
                        #         "avg_rating": {
                        #             "request": "lower",
                        #             "threshold": 2
                        #         }
                        #     }
                        # },
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
                        # "Filters for old historical and drama movies with a high average rating on the platform but an IMDb rating lower than 6": {
                        #     "filters": {
                        #         "genres": ["history", "drama"],
                        #         "avg_rating": {
                        #             "request": "higher",
                        #             "threshold": 4
                        #         },
                        #         "imdb_rating": {
                        #             "request": "lower",
                        #             "threshold": 6
                        #         },
                        #         "release_date": {
                        #             "request": "lower",
                        #             "threshold": 1980
                        #         }
                        #     }
                        # },
                        "Filters for movies released in 1994": {
                            "filters": {
                                "genres": ["action"],
                                "release_date": 1994
                            }
                        },
                        "Filters for movies with Tom Cruise popular among young adults": {
                            "filters": {
                                "actors": ["Tom Cruise"],
                                "popularity_by_age_category": "popular_young_adult"
                            }
                        },
                        "Filters for movies released prior to 1996 popular among kids": {
                            "filters": {
                                "release_date": {
                                    "request": "lower",
                                    "threshold": 1996
                                },
                                "popularity_by_age_category": "popular_kid"
                            }
                        },
                        "Filters for drama movies popular among teenagers": {
                            "filters": {
                                "genres": ["drama"],
                                "popularity_by_age_category": "popular_teenager"
                            }
                        },
                    }
                }
            },
            "required": ["user", "query"],
            "examples": {
                "Provide recommendations for user 14 for films with a whimsical tone but dark undertones, likely animated and aimed at children but emotionally traumatic for adults.": {
                    "name": "get_recommendations_by_description",
                    "arguments": {
                        "user": 14,
                        "query": "whimsical tone, dark undertones, animated, for children, emotionally traumatic for adults.",
                    }
                },
                "Provide recommendations for user 10 for ensemble comedy movies where at least one character wears a trench coat and the score uses saxophones.": {
                    "name": "get_recommendations_by_description",
                    "arguments": {
                        "user": 10,
                        "query": "comedy movie, wears a trench coat, score uses saxophones.",
                        "filters": {
                            "genres": ["comedy"]
                        }
                    }
                },
                "Provide recommendations for user 45 for sci-fi movies made before the year 2000 that are clearly inspired by Blade Runner but take place underwater": {
                    "name": "get_recommendations_by_description",
                    "arguments": {
                        "user": 45,
                        "query": "sci-fi movie, blade runner, underwater",
                        "filters": {
                            "genres": ["sci-fi"],
                            "release_date": {
                                "request": "lower",
                                "threshold": 2000
                            }
                        }
                    }
                },
                "Provide recommendations for user 104 given the fact she/he is happy": {
                    "name": "get_recommendations_by_description",
                    "arguments": {
                        "user": 104,
                        "query": "comedy, light-hearted and funny, romantic, humor, adventure, fantasy, fun escapism, upbeat energy, musical. energetic, colorful, emotionally uplifting, stories of triumph, connection, personal growth.",
                        "filters": {
                            "genres": ["comedy", "romance", "fantasy", "adventure", "musical"],
                        }
                    }
                },
                "Provide recommendations for user 23 given the fact she/he is depressed": {
                    "name": "get_recommendations_by_description",
                    "arguments": {
                        "user": 23,
                        "query": "sad drama, melancholic films, indie films, introspective, emotionally raw, comfort films, nostalgic, comedy, mood booster, inspirational story.",
                        "filters": {
                            "genres": ["drama", "comedy"],
                        }
                    }
                },
                "Recommend some movies for user 45 that are popular among teenagers and where the main character is kidnapped": {
                    "name": "get_recommendations_by_description",
                    "arguments": {
                        "user": 45,
                        "query": "main character is kidnapped",
                        "filters": {
                            "actors": ["Tom Cruise"],
                            "popularity_by_age_category": "popular_teenager"
                        }
                    }
                }
            }
        }
    }
}

RECOMMENDATION_SIMILAR_ITEM = {
    "function": {
        "name": "get_recommendations_by_similar_item",
        "description": (
            "This function recommends items that are similar to the given item."
            "It returns a ranking of recommended item IDs for the specified user ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user": {
                    "type": "integer",
                    "description": "User ID for which the recommendations have to be retrieved."
                },
                "item": {
                    "type": "integer",
                    "description": "Item ID of the item used to find similar items."
                },
            },
            "required": ["user", "item"],
            "examples": {
                "Provide recommendations for user 14 for films that are similar to item 4.": {
                    "name": "get_recommendations_by_similar_item",
                    "arguments": {
                        "user": 14,
                        "item": 4,
                    }
                },
                "Provide recommendations for user 10 for movies that are similar to item 2.": {
                    "name": "get_recommendations_by_similar_item",
                    "arguments": {
                        "user": 10,
                        "item": 2
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
            "Returns metadata for the given item ID(s). Specific metadata might be requested. "
            "If no specification is given"
            "all the metadata available for the item(s) is returned."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "int"},
                    "description": "Item ID(s) for which the metadata has to be retrieved."
                },
                "specification": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of item metadata features to be included in the response. Available features"
                                   "are: [\"title\", \"description\", \"genres\", \"director\", "
                                   "\"producer\", \"duration\", \"release_date\", \"actors\", "
                                   "\"imdb_rating\"], \"popularity\".",  # \"avg_rating\", \"country\", \"popularity\"
                    "examples": {
                        "Specification for when actors and director are the requested features": {
                            "specification": ["actors", "director"]
                        },
                        "Specification for when title and description are the requested features": {
                            "specification": ["title", "description"]
                        },
                        "Specification for when full metadata is requested": {
                            "specification": ["title", "description", "genres", "director", "producer", "duration", "release_date", "actors", "imdb_rating"]  # "avg_rating", "country", "popularity"
                        },
                        "Specification for when the IMDb rating and the popularity are the requested features": {
                            "specification": ["imdb_rating", "popularity"]
                        },
                        "Specification for when director, producer, and release date are the requested features": {
                            "specification": ["director", "producer", "release_date"]
                        },
                        # "Specification for the genres and country are the requested features": {
                        #     "specification": ["genres", "country"]
                        # },
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
                    "item ": [47],
                    "specification": ["title", "description", "genres", "director", "producer", "duration", "release_date", "actors", "imdb_rating", "popularity"]  # "avg_rating", "country"
                }
            },
            "What are the actors of item 54 and 65?": {
                "name": "get_item_metadata",
                "arguments": {
                    "items": [54, 65],
                    "specification": ["actors"]
                }
            },
            # "What are the director, genres and country of item 98?": {
            #     "name": "get_item_metadata",
            #     "arguments": {
            #         "items": [98],
            #         "specification": ["director", "genres", "country"]
            #     }
            # },
            "Give me the release date and duration for item 12 and 4": {
                "name": "get_item_metadata",
                "arguments": {
                    "items": [12, 4],
                    "specification": ["release_date", "duration"]
                }
            },
            "Show the IMDb rating and popularity of item 200, 123, and 45": {
                "name": "get_item_metadata",
                "arguments": {
                    "items": [200, 123, 45],
                    "specification": ["imdb_rating", "popularity"]
                }
            },
            # "Provide the title and average rating of item 77": {
            #     "name": "get_item_metadata",
            #     "arguments": {
            #         "items": [77],
            #         "specification": ["title", "avg_rating"]
            #     }
            # },
            "Tell me about the genres and producer of item 150 and 56": {
                "name": "get_item_metadata",
                "arguments": {
                    "items": [150, 56],
                    "specification": ["genres", "producer"]
                }
            },
            "What is the description of item 33, 4, and 89?": {
                "name": "get_item_metadata",
                "arguments": {
                    "items": [33, 4, 89],
                    "specification": ["description"]
                }
            },
            "Provide information for item 205, including actors and director": {
                "name": "get_item_metadata",
                "arguments": {
                    "items": [205],
                    "specification": ["actors", "director"]
                }
            },
            # "What are the genres and country for item 82?": {
            #     "name": "get_item_metadata",
            #     "arguments": {
            #         "items": [82],
            #         "specification": ["genres", "country"]
            #     }
            # },
            "Show me the title, director, and popularity of item 120 and 90": {
                "name": "get_item_metadata",
                "arguments": {
                    "items": [120, 90],
                    "specification": ["title", "director", "popularity"]
                }
            },
            # "Give me the average rating and duration for item 50, 34, 56, and 78": {
            #     "name": "get_item_metadata",
            #     "arguments": {
            #         "items": [50, 34, 56, 78],
            #         "specification": ["avg_rating", "duration"]
            #     }
            # },
            # "Tell me the country and release date for item 199": {
            #     "name": "get_item_metadata",
            #     "arguments": {
            #         "items": [199],
            #         "specification": ["country", "release_date"]
            #     }
            # },
            "What is the producer and description of item 105?": {
                "name": "get_item_metadata",
                "arguments": {
                    "items": [105],
                    "specification": ["producer", "description"]
                }
            },
            "Provide the title and genres for item 60 and 34": {
                "name": "get_item_metadata",
                "arguments": {
                    "items": [60, 34],
                    "specification": ["title", "genres"]
                }
            },
            "Give me the actors and IMDb rating of item 45": {
                "name": "get_item_metadata",
                "arguments": {
                    "items": [45],
                    "specification": ["actors", "imdb_rating"]
                }
            },
            "What is the release date of item 111?": {
                "name": "get_item_metadata",
                "arguments": {
                    "items": [111],
                    "specification": ["release_date"]
                }
            },
            "What do you know about item 11?": {
                "name": "get_item_metadata",
                "arguments": {
                    "items": [11],
                    "specification": ["title", "description", "genres", "director", "producer", "duration", "release_date", "actors", "imdb_rating"]  # "avg_rating", "country", , "popularity"
                }
            },
        }
    }
}

INTERACTION = {
"function": {
        "name": "get_interacted_items",
        "description": (
            "Returns a list of previously interacted item IDs for the given user ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user": {
                    "type": "integer",
                    "description": "User for which the historical interactions have to be "
                                   "retrieved."
                }
            }
        },
        "required": ["user"],
        "examples": {
            "Provide me the historical interactions of user 45.": {
                "name": "get_past_interactions",
                "arguments": {
                    "user": 45
                }
            },
            "What are the items user 14 interacted in the past?": {
                "name": "get_past_interactions",
                "arguments": {
                    "user": 14
                }
            },
            "List all previously interacted items for user 88.": {
                "name": "get_past_interactions",
                "arguments": {
                    "user": 88
                }
            },
            "Show me the past interaction history of user 32.": {
                "name": "get_past_interactions",
                "arguments": {
                    "user": 32
                }
            },
            "Retrieve interaction records for user 101.": {
                "name": "get_past_interactions",
                "arguments": {
                    "user": 101
                }
            },
            "Which items has user 67 interacted with before?": {
                "name": "get_past_interactions",
                "arguments": {
                    "user": 67
                }
            }
        }
    }
}

USER_METADATA = {
    "function": {
        "name": "get_user_metadata",
        "description": (
            "Returns metadata for the given user ID. Specific metadata might be requested. "
            "If no specification is given"
            "all the metadata available for the user is returned."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user": {
                    "type": "int",
                    "description": "User ID for which the metadata has to be retrieved."
                },
                "specification": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user metadata features to be included in the response. Available features"
                                   "are: [\"age_category\", \"gender\".",
                    "examples": {
                        "Specification for when age is the requested feature": {
                            "specification": ["age_category"]
                        },
                        "Specification for when age and gender are the requested features": {
                            "specification": ["age_category", "gender"]
                        },
                        "Specification for when full metadata is requested": {
                            "specification": ["age_category", "gender"]
                        }
                    }
                }
            }
        },
        "required": ["user", "specification"],
        "examples": {
            "Provide all the information you know about user 3": {
                "name": "get_user_metadata",
                "arguments": {
                    "user": 3,
                    "specification": ["age_category", "gender"]
                }
            },
            "What is the age category of user 65?": {
                "name": "get_user_metadata",
                "arguments": {
                    "items": 65,
                    "specification": ["age_category"]
                }
            },
            "What is the gender of user 90?": {
                "name": "get_user_metadata",
                "arguments": {
                    "items": 90,
                    "specification": ["gender"]
                }
            },
        }
    }
}
