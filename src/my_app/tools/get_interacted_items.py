import json
from src.my_app.tools.utils import execute_sql_query, define_sql_query
from src.my_app.constants import JSON_GENERATION_ERROR
from src.my_app.tools.get_item_metadata import get_item_metadata


GET_INTERACTED_ITEMS = {
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
                    "description": "User ID."
                }
            }
        },
        "required": ["user"],
    }
}


def get_interacted_items(params, return_list=False):
    """
    This function is invoked by the LLM when the user requests for historical interactions of
    a specific user of the platform.

    :param params: dictionary containing all the arguments to process the request
    :param return_list: whether to return the output as a list or stream
    :return: stream or list with the requested information
    """
    print("\nget_interacted_items has been triggered!!!\n")
    if 'user' in params:
        user = params.get('user')
        sql_query, _, _ = define_sql_query("interactions", params)
        result = execute_sql_query(sql_query)[0][0].split(",")

        if len(result) > 20:
            # if there are more than 20 interacted items, we take the most recent ones
            result = result[-20:]
            mess = (f"Since user {user} interacted with more than 20 items in the past, we only "
                    f"list his/her most recent 20 interactions: ")
        else:
            mess = f"These are all the items user {user} interacted in the past: "

        if result and not return_list:
            response_dict = get_item_metadata(params={'items': result,
                                                      'get': ["item_id", "title", "genres", "director", "producer", "actors", "release_date", "release_month", "country", "duration", "imdb_rating", "description"]},
                                              return_dict=True)

            return json.dumps({
                "status": "success",
                "message": f"{mess}: {response_dict}."
            })
        elif result and return_list:
            return result
        else:
            if not return_list:
                return json.dumps({
                    "status": "failure",
                    "message": f"No information found for the given user.",
                })
            else:
                return None
    else:
        return json.dumps(JSON_GENERATION_ERROR)
