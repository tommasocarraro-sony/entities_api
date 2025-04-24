import os
from recbole.quick_start import load_data_and_model
import torch
from recbole.utils.case_study import full_sort_scores, full_sort_topk
import json
from src.my_app.utils import define_sql_query, execute_sql_query


def create_recbole_environment(model_path):
    """
    This function creates a global RecBole environment that can be accessed by the functions that
    process recommendation requests.

    :param model_path: path to pre-trained recsys model
    """
    global config, model, dataset, train_data, valid_data, test_data
    config, model, dataset, train_data, valid_data, test_data = load_data_and_model(
        model_file=model_path
    )


def get_top_k_recommendations(params, db_name):
    """
    This is the function that is invoked by the LLM when some recommendations are requested by the
    user.

    If conditions for constrained recommendation are given, it creates a SQL query to retrieve
    satisfying items.

    It then invokes the pre-trained recommender system to generate a ranking of recommended items
    for the given user.

    :param params: dictionary containing all the arguments to process standard and constrained
    recommendations
    :param db_name: name of the database where the queries have to be executed

    :return: a prompt for the LLM that the LLM will use as additional context to prepare the final
    answer
    """
    if 'user' in params and 'k' in params:
        user = params.get('user')
        k = params.get('k')
        # create RecBole environment if it is not already created
        if 'config' not in globals():
            create_recbole_environment(os.getenv("RECSYS_MODEL_PATH"))
        uid_series = dataset.token2id(dataset.uid_field, [str(user)])
        matched = None
        # check if it is a constrained recommendation
        if 'filters' in params:
            matched = False
            filters = params.get('filters')
            # execute sql query based on the filters to get items that satisfy the filters
            try:
                sql_query = define_sql_query("items", filters)
                result = execute_sql_query(db_name, sql_query)
                # invoke the recommender system to get rating of all items satisfying the given conditions
                item_ids = [str(row[0]) for row in result]
                all_scores = full_sort_scores(uid_series, model, test_data, device=config['device'])
                satisfying_item_scores = all_scores[
                    0, dataset.token2id(dataset.iid_field, item_ids)]
                _, sorted_indices = torch.sort(satisfying_item_scores, descending=True)
                external_item_list = [item_ids[i] for i in sorted_indices[:k].cpu().numpy()]
                matched = True
            except ValueError as e:
                print(e)
                # if no filters worked, then we perform a standard recommendation and we
                # can directly generate the ranking for the given user
                topk_score, topk_iid_list = full_sort_topk(uid_series, model, test_data, k=k,
                                                           device=config['device'])
                external_item_list = dataset.id2token(dataset.iid_field, topk_iid_list.cpu())[0]
        else:
            # if no filters are given, then it is a standard recommendation and we can directly
            # generate the ranking for the given user
            topk_score, topk_iid_list = full_sort_topk(uid_series, model, test_data, k=k,
                                                       device=config['device'])
            external_item_list = dataset.id2token(dataset.iid_field, topk_iid_list.cpu())[0]

        print(external_item_list)
        response_dict = get_item_metadata(params={'items': external_item_list,
                                                  'specification': ["item_id", "title", "genres", "director", "producer", "actors", "release_date", "duration", "imdb_rating", "description"]},
                                          db_name=db_name, return_dict=True)

        # get items interacted by user ID
        item_ids = get_interacted_items(params={'user': int(user)}, db_name=db_name, return_list=True)
        # get metadata of interacted items
        interaction_dict = get_item_metadata(params={'items': item_ids,
                                                     'specification': ["item_id", "title", "genres", "director", "producer", "actors", "release_date", "duration", "imdb_rating", "description"]},
                                             db_name=db_name, return_dict=True)

        print("\n" + str(interaction_dict) + "\n")
        print("\n" + str(response_dict) + "\n")
        return json.dumps({
            "status": "success",
            "message": f"{f'The given conditions did not match any item in the database. Hence, standard recommendations (without filters) for user {user} have been generated. ' if matched is not None and not matched else ''}Suggested recommendations for user {user}: {response_dict}. Please, include the movie ID when listing the recommended items. Please, use all the information included in the generated dictionary when listing recommendations. After listing the recommended items, ask the user if she/he would like to have an explanation for the recommendations. If the answer is positive, try to provide an explanation for the recommendations based on the similarities between the recommended items and the items the user interacted in the past, that are: {interaction_dict}. To explain recommendations, you could also use additional information that you might know in your pre-trained knowledge."
        })
    else:
        return json.dumps({
            "status": "failure",
            "message": f"Something went wrong in the function calling. The generated JSON "
                       f"is invalid.",
        })


def get_item_metadata(params, db_name, return_dict=False):
    """
    This function is used by the assistant to retrieve the metadata of items based on user requests.

    :param params: dictionary containing all the arguments to process the metadata request
    :param db_name: name of database on which the SQL query is to be executed
    :param return_dict: whether to return the output as a dictionary or stream
    :return: stream or dictionary with the requested information
    """
    if 'items' in params and 'specification' in params:
        items = params.get('items')
        specification = params.get('specification')
        sql_query = define_sql_query("items", {"items": items, "specification": specification})
        result = execute_sql_query(db_name, sql_query)

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
                r_dict[result[j][0]] = {}
                for i, spec in enumerate(specification):
                    r_dict[result[j][0]][spec] = result[j][i] if result[j][i] is not None else "unknown"
            return r_dict
        else:
            if not return_dict:
                return json.dumps({
                    "status": "failure",
                    "message": f"No information found for the given items.",
                })
            else:
                return None
    else:
        return json.dumps({
            "status": "failure",
            "message": f"Something went wrong in the function calling. The generated JSON "
                       f"is invalid.",
        })


def get_interacted_items(params, db_name, return_list=False):
    """
    This function is invoked by the LLM when the user requests for historical interactions of
    a specific user of the platform.

    :param params: dictionary containing all the arguments to process the request
    :param db_name: name of the database on which the SQL query is to be executed
    :param return_list: whether to return the output as a list or stream
    :return: stream or list with the requested information
    """
    if 'user' in params:
        user = params.get('user')
        sql_query = define_sql_query("interactions", params)
        result = execute_sql_query(db_name, sql_query)[0][0].split(",")

        if len(result) > 10:
            # if there are more than 10 interacted items, we take the most recent ones
            result = result[-10:]
            mess = (f"Since user {user} interacted with more than 10 items in the past, for simplicity "
                    "and to avoid verbosity, "
                    "these are his/her most recent 10 interactions: ")
        else:
            mess = (f"These are all the items user {user} interacted in the past: ")

        if result and not return_list:
            response_dict = get_item_metadata(params={'items': result,
                                                      'specification': ["item_id", "title", "genres", "director", "producer", "actors", "release_date", "duration", "imdb_rating", "description"]},
                                              db_name=db_name, return_dict=True)

            return json.dumps({
                "status": "success",
                "message": f"{mess}: {response_dict}. "
                           f"Please, includes the item ID when listing "
                           f"the interactions.",
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
        return json.dumps({
            "status": "failure",
            "message": f"Something went wrong in the function calling. The generated JSON "
                       f"is invalid.",
        })
