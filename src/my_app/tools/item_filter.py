import json
from src.my_app.tools.utils import execute_sql_query, define_sql_query
from src.my_app.constants import JSON_GENERATION_ERROR
import random


ITEM_FILTER = {
    "function": {
        "name": "item_filter",
        "description": (
            "Returns the IDs of the items that satisfy the given conditions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "description": "Filters that specify the conditions the items must satisfy.",
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
                            "description": "List of director names to filter by."
                        },
                        "producer": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of producer names to filter by."
                        },
                        "imdb_rating": {
                            "type": "object",
                            "properties": {
                                "request": {
                                    "type": "string",
                                    "enum": ["higher", "lower", "exact"],
                                    "description": "Whether to filter for movies with an exact "
                                                   "IMDb rating, or IMDb ratings "
                                                   "higher or lower than a certain threshold."
                                },
                                "threshold": {
                                    "type": "integer",
                                    "description": "IMDb rating (between 1 and 10)."
                                }
                            },
                            "required": ["request", "threshold"]
                        },
                        "duration": {
                            "type": "object",
                            "properties": {
                                "request": {
                                    "type": "string",
                                    "enum": ["higher", "lower", "exact"],
                                    "description": "Whether to filter for movies with an exact "
                                                   "duration, or movies that last longer or lower "
                                                   "than a certain duration."
                                },
                                "threshold": {
                                    "type": "integer",
                                    "description": "Duration in minutes (e.g., 90 for 1h30min)."
                                }
                            },
                            "required": ["request", "threshold"]
                        },
                        "release_date": {
                            "type": "object",
                            "properties": {
                                "request": {
                                    "type": "string",
                                    "enum": ["higher", "lower", "exact"],
                                    "description": "Whether to search for movies released on an "
                                                   "exact year, or for movies released prior to "
                                                   "or after a certain year."
                                },
                                "threshold": {
                                    "type": "integer",
                                    "description": "Release year (e.g., 2000)."
                                }
                            },
                            "required": ["request", "threshold"]
                        },
                        "release_month": {
                            "type": "integer",
                            "description": "Release month in MM format."
                        },
                        "country": {
                            "type": "string",
                            "description": "Country of origin."
                        }
                    },
                }
            },
            "required": ["filters"],
        }
    }
}


def item_filter(params):
    """
    This is the function that is invoked by the LLM when some filters have to be applied to the item
    catalog before doing a vector store search or invoking the recommender system.

    :param params: dictionary containing all the arguments to process standard and constrained
    recommendations

    :return: a prompt for the LLM that the LLM will use as additional context to prepare the final
    answer
    """
    print("\nitem_filter has been triggered!!!\n")
    if 'filters' in params:
        matched = False
        filters = params.get('filters')
        # execute sql query based on the filters to get items that satisfy the filters
        sql_query, corrections, failed_corrections = define_sql_query("items", filters)
        mess = ""
        if sql_query is not None:
            result = execute_sql_query(sql_query)
            item_ids = [str(row[0]) for row in result]
            # todo understand how to return only the most popular movies when no recommendations are requested -> I could call get_popular_items
            # todo there is the problem that a random sampling is done out of a huge number of movies. This random sampling make it difficult to find the real best performing genre or duration
            # todo it is probably better to do the filtering and the popularity all together
            if len(item_ids) > 20:
                # if there are more than 20 items satisfying the conditions, we sample 20 items
                item_ids = random.sample(item_ids, 20)
                mess = f"These are the IDs of 20 items satisfying the given conditions: {item_ids}. Explain the user that since more than 20 items were satisfying the given conditions, a uniform sampling has been done to retrieve a small set of items. If the user originally asked for recommendations, explain that this sampling is good to promote diversity and serendipity, and to reduce the popularity bias when performing recommendations. Instead, if the user originally asked to just retrieve some item IDs, explain him/her that this sampling is helpful to avoid streaming a vast amount of tokens. 20 items IDs should be enough to explore the item space. You can then proceed with the next reasoning step, if there is one."
            else:
                mess = f"These are the IDs of the items satisfying the given conditions: {item_ids}. You can now proceed to the next step."
            matched = True

        failed_corr_text = f"Note that corrections for these fields have been tried but failed: {failed_corrections}, so the final recommendation output will not take the failed filters into consideration."
        void_str = ''
        return json.dumps({
            "status": "success",
            "message": f"{f'Note that the following corrections have been made to retrieve the items: {corrections}. Please, remember to explain the user these corrections. {failed_corr_text if failed_corrections else void_str}' if corrections else ''}{f'Unfortunately, the given conditions did not match any item in the database, so it is not possible to proceed with the next step. You do not have to perform other tool calls.' if not matched else mess}"
        })
    else:
        return json.dumps(JSON_GENERATION_ERROR)
