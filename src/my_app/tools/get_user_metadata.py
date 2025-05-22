import json
from src.my_app.tools.utils import execute_sql_query, define_sql_query
from src.my_app.constants import JSON_GENERATION_ERROR, DATABASE_NAME


GET_USER_METADATA = {
    "function": {
        "name": "get_user_metadata",
        "description": (
            "Returns the requested metadata for the given user."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user": {
                    "type": "int",
                    "description": "User ID."
                },
                "get": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user metadata features to be retrieved. Available "
                                   "features are: \"age_category\", \"gender\".",
                }
            }
        },
        "required": ["user", "get"],
    }
}


def get_user_metadata(params):
    """
    This function is used by the assistant to retrieve the metadata of a user based on user
    requests.

    :param params: dictionary containing all the arguments to process the metadata request
    :return: requested metadata
    """
    print("\nget_user_metadata has been triggered!!!\n")
    if 'user' in params and 'get' in params:
        user = params.get('user')
        specification = params.get('get')
        sql_query, _, _ = define_sql_query("users", {"user": user, "specification": specification})
        result = execute_sql_query(sql_query)

        if result:
            return_str = ""
            for j in range(len(result)):
                return_str += f"User {result[j][0]}:"
                for i, spec in enumerate(specification):
                    return_str += f"\n\n{spec}: {result[j][i] if result[j][i] is not None else 'unknown'}\n"
            return json.dumps({
                "status": "success",
                "message": f"This is the requested metadata for user {user}:\n{return_str}.",
            })
        else:
            return json.dumps({
                "status": "failure",
                "message": f"No information found for user {user}.",
            })
    else:
        return json.dumps(JSON_GENERATION_ERROR)
