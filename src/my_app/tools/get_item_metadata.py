import json
from src.my_app.tools.utils import execute_sql_query, define_sql_query
from src.my_app.constants import JSON_GENERATION_ERROR


GET_ITEM_METADATA = {
    "function": {
        "name": "get_item_metadata",
        "description": (
            "Returns the requested metadata for the given items."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "int"},
                    "description": "Item ID(s) for which the metadata has to be retrieved."
                },
                "get": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of item metadata features to be retrieved. Available "
                                   "features are: \"title\", \"description\", \"genres\", "
                                   "\"director\", \"producer\", \"duration\", \"release_date\", "
                                   "\"release_month\", \"country\", \"actors\", \"imdb_rating\".",
                }
            }
        }
    },
    "required": ["items", "get"],
}


def get_item_metadata(params, return_dict=False):
    """
    This function is used by the assistant to retrieve the metadata of items based on user requests.

    :param params: dictionary containing all the arguments to process the metadata request
    :param db_name: name of database on which the SQL query is to be executed
    :param return_dict: whether to return the output as a dictionary or stream
    :return: stream or dictionary with the requested information
    """
    print("\nget_item_metadata has been triggered!!!\n")
    if 'items' in params and 'get' in params:
        items = params.get('items')
        specification = params.get('get')
        sql_query, _, _ = define_sql_query("items", {"items": items, "specification": specification})
        result = execute_sql_query(sql_query)

        if result and not return_dict:
            return_str = ""
            for j in range(len(result)):
                return_str += f"Item {result[j][0]}:"
                for i, spec in enumerate(specification):
                    return_str += f"\n\n{spec}: {result[j][i] if result[j][i] is not None else 'unknown'}\n"
            return json.dumps({
                "status": "success",
                "message": f"This is the requested metadata for items {items}:\n{return_str}",
            })
        elif result and return_dict:
            r_dict = {}
            for j in range(len(result)):
                r_dict[result[j][0]] = {} # in 0-position there is the item ID of the retrieved item
                for i, spec in enumerate(specification):
                    r_dict[result[j][0]][spec] = result[j][i] if result[j][i] is not None else "unknown"
            return r_dict
        else:
            if not return_dict:
                return json.dumps({
                    "status": "failure",
                    "message": f"No information found for the given items: {items}.",
                })
            else:
                return None
    else:
        return json.dumps(JSON_GENERATION_ERROR)
