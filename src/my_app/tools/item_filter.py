import json
from src.my_app.tools.utils import execute_sql_query, define_sql_query
from src.my_app.constants import JSON_GENERATION_ERROR
import hashlib
import os


ITEM_FILTER = {
    "function": {
        "name": "item_filter",
        "description": (
            "Returns the path to a temporary file containing the IDs of the items that satisfy the "
            "given conditions."
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
            # Create a hash from the item IDs to generate a unique filename
            hash_input = ','.join(item_ids).encode('utf-8')
            filename_hash = hashlib.md5(hash_input).hexdigest()
            file_path = f"./temp/{filename_hash}.json"

            # Create the JSON content
            data = {"items": item_ids}
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Save the file
            with open(file_path, "w") as f:
                json.dump(data, f)

            print(f"Saved item IDs to {file_path}")
            mess = f"The IDs of the items satisfying the given conditions have been saved to this file path: {file_path}. You can now proceed to the next step. It is enough you pass this path to the \"items\" parameter of the next tool call."
            matched = True

        failed_corr_text = f"Note that corrections for these fields have been tried but failed: {failed_corrections}, so the final recommendation output will not take the failed filters into consideration."
        void_str = ''
        return json.dumps({
            "status": "success",
            "message": f"{f'Note that the following corrections have been made to retrieve the items: {corrections}. Please, remember to explain the user these corrections. {failed_corr_text if failed_corrections else void_str}' if corrections else ''}{f'Unfortunately, the given conditions did not match any item in the database, so it is not possible to proceed with the next step. You do not have to perform other tool calls.' if not matched else mess}"
        })
    else:
        return json.dumps(JSON_GENERATION_ERROR)
