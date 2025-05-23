import json
from src.my_app.constants import JSON_GENERATION_ERROR
from src.my_app.utils import read_ml100k_ratings
from src.my_app.tools.utils import convert_to_list


GET_LIKE_PERCENTAGE = {
    "function": {
        "name": "get_like_percentage",
        "description": (
            "Returns the percentage of users that like the given item IDs."
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
                    "description": "Item ID(s) for which the percentage has to be computed, either "
                                   "directly as a list or as a path to a JSON file."
                },
            },
            "required": ["items"]
        }
    }
}


def get_like_percentage(params):
    """
    This is the function that is invoked by the LLM when it has to compute the percentage of users
    that like the given item IDs.

    :param params: dictionary containing all the arguments to compute user percentage

    :return: a prompt for the LLM that the LLM will use as additional context to prepare the final
    answer
    """
    print("\nget_like_percentage has been triggered!!!\n")
    if 'items' in params:
        items = params.get('items')
        try:
            items = convert_to_list(items)
        except Exception:
            return json.dumps({
                "status": "failure",
                "message": "There are issues with the temporary file containing the item IDs.",
            })
        items = [int(i) for i in items]
        # load rating file to compute percentage
        user_interactions = read_ml100k_ratings()
        # compute number of users
        n_users = len(set(int(inter[0]) for inter in user_interactions))
        # get number of users that interacted with the given items
        n_users_by_items = len(set(int(inter[0]) for inter in user_interactions if inter[1] in items))
        # compute percentage
        perc = n_users_by_items / n_users * 100

        return json.dumps({
            "status": "success",
            "message": f"This is the percentage of users that might like the given items: {perc}%"
        })
    else:
        return json.dumps(JSON_GENERATION_ERROR)
