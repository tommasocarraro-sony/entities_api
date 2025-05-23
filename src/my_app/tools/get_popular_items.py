import json
from src.my_app.tools.utils import execute_sql_query, define_sql_query
from src.my_app.constants import JSON_GENERATION_ERROR
import numpy as np


GET_POPULAR_ITEMS = {
    "function": {
        "name": "get_popular_items",
        "description": (
            "Returns the IDs of the popular items from a set of given item IDs. If no IDs are given,"
            "it computes the popularity of the entire item set."
            "It can optionally return popular items in a given user group (e.g., kids, "
            "females, etc.)."
            "If requested, it can return the top 3 popular items."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "oneOf": [
                        {
                          "type": "array",
                          "items": {"type": "integer"},
                          "description": "A list of item IDs."
                        },
                        {
                          "type": "string",
                          "description": "Path to a JSON file containing the item IDs."
                        }
                    ],
                    "description": "Item ID(s) for which the popularity has to be computed, either "
                                   "directly as a list or as a path to a JSON file."
                },
                "popularity": {
                    "type": "string",
                    "enum": ["standard", "by_user_group"],
                    "description": "Whether to compute standard popularity or by user group."
                },
                "user_group": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The user groups on which the item popularity has to be "
                                   "computed."
                                   "Available user groups are: \"kid\", \"teenager\", "
                                   "\"young_adult\", \"adult\", \"senior\", \"male\", \"female\"."
                },
                "get": {
                    "type": "string",
                    "enum": ["all", "top3"],
                    "description": "Whether to return all the popular items or just the top "
                                   "3 popular items."
                }
            },
            "required": ["popularity", "get"]
        }
    }
}


def get_popular_items(params):
    """
    This is the function that is invoked by the LLM when it has to compute item popularity.

    :param params: dictionary containing all the arguments to compute item popularity

    :return: a prompt for the LLM that the LLM will use as additional context to prepare the final
    answer
    """
    print("\nget_popular_items has been triggered!!!\n")
    if 'popularity' in params and 'get' in params:
        popularity = params.get('popularity')
        # prepare sql query to get item rating count
        if popularity == "standard":
            if 'items' in params:
                items = params.get('items')
                items = [int(i) for i in items]
                sql_query, _, _ = define_sql_query("items", {"select": ["item_id", "n_ratings"], "items": items})
            else:
                sql_query, _, _ = define_sql_query("items", {"select": ["item_id", "n_ratings"]})
        else:
            if 'user_group' in params:
                user_group = params.get('user_group')
                user_group = [f"n_ratings_{group}" for group in user_group]
                if 'items' in params:
                    items = params.get('items')
                    items = [int(i) for i in items]
                    sql_query, _, _ = define_sql_query("items",
                                                       {"select": ["item_id"] + user_group, "items": items})
                else:
                    sql_query, _, _ = define_sql_query("items", {"select": ["item_id"] + user_group})
            else:
                return json.dumps(JSON_GENERATION_ERROR)

        if sql_query is not None:
            # execute the query
            result = execute_sql_query(sql_query)
            # row[0] is the item id while the rest are the counts, that are summed
            ids_with_count = [(str(row[0]), sum(row[1:])) for row in result]
            # order in descending order of count
            ids_with_count_sorted = sorted(ids_with_count, key=lambda x: x[1], reverse=True)
            # compute the .75 quantile
            q75 = np.quantile([item[1] for item in ids_with_count_sorted], 0.75)
            # filter IDs with count above the 0.75 quantile
            item_ids = [item_id for item_id, count in ids_with_count_sorted if count > q75]
            filtered = False
            if 'get' in params:
                get = params.get('get')
                if get == "top3":
                    item_ids = item_ids[:3]
                else:
                    if len(item_ids) > 10:
                        item_ids = item_ids[:10]
                        filtered = True
            n_pop_items = len(item_ids)
        else:
            return json.dumps({
                "status": "failure",
                "message": "The SQL query did not produce any result"
            })

        return json.dumps({
            "status": "success",
            "message": f"These are the IDs of the {n_pop_items} most popular items: {item_ids}. {'Explain the user that more than 10 popular items were retrieved by the tool. However, to avoid verbosity and for efficient use of tokens, the IDs of the 10 most popular items are generated.' if filtered else ''}"
        })
    else:
        return json.dumps(JSON_GENERATION_ERROR)
