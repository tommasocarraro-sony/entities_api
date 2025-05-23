import os
from recbole.quick_start import load_data_and_model
import torch
from recbole.utils.case_study import full_sort_scores, full_sort_topk
import json
from src.my_app.constants import JSON_GENERATION_ERROR
from src.my_app.tools.get_item_metadata import get_item_metadata
from src.my_app.tools.get_interacted_items import get_interacted_items
from src.my_app.tools.utils import convert_to_list


GET_TOP_K_RECOMMENDATIONS = {
    "function": {
        "name": "get_top_k_recommendations",
        "description": (
            "Returns the top k recommended items for the given user."
            "It computes recommendations over the entire item catalog unless a list of items "
            "is given."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user": {
                    "type": "integer",
                    "description": "User ID."
                },
                "k": {
                    "type": "integer",
                    "description": "Number of recommended items."
                },
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
                    "description": "Item ID(s) for which the recommendation has to be computed, "
                                   "either directly as a list or as a path to a JSON file."
                },
            },
            "required": ["user", "k"],
        }
    }
}


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


def get_top_k_recommendations(params):
    """
    This is the function that is invoked by the LLM when some recommendations are requested by the
    user.

    If conditions for constrained recommendation are given, it creates a SQL query to retrieve
    satisfying items.

    It then invokes the pre-trained recommender system to generate a ranking of recommended items
    for the given user.

    :param params: dictionary containing all the arguments to process standard and constrained
    recommendations

    :return: a prompt for the LLM that the LLM will use as additional context to prepare the final
    answer
    """
    print("\nget_top_k_recommendations has been triggered!!!\n")
    if 'user' in params and 'k' in params:
        user = params.get('user')
        k = params.get('k')
        # create RecBole environment if it is not already created
        if 'config' not in globals():
            create_recbole_environment(os.getenv("RECSYS_MODEL_PATH"))
        uid_series = dataset.token2id(dataset.uid_field, [str(user)])
        # check if it is a constrained recommendation
        if 'items' in params:
            items = params.get('items')
            try:
                items = convert_to_list(items)
            except Exception:
                return json.dumps({
                    "status": "failure",
                    "message": "There are issues with the temporary file containing the item IDs.",
                })
            recommended_items = recommend_given_items(uid_series, items, k=k)
        else:
            recommended_items = recommend_full_catalog(uid_series, k=k)

        print(recommended_items)
        response_dict = get_item_metadata(params={'items': recommended_items,
                                                  'get': ["item_id", "title", "genres", "director", "producer", "actors", "release_date", "country", "duration", "imdb_rating", "description"]},
                                          return_dict=True)

        # get items interacted by user ID
        item_ids = get_interacted_items(params={'user': int(user)}, return_list=True)
        # get metadata of interacted items
        interaction_dict = get_item_metadata(params={'items': item_ids,
                                                     'get': ["item_id", "title", "genres", "director", "producer", "actors", "release_date", "country", "duration", "imdb_rating", "description"]},
                                             return_dict=True)

        print("\n" + str(interaction_dict) + "\n")
        print("\n" + str(response_dict) + "\n")

        return json.dumps({
            "status": "success",
            "message": f"Suggested recommendations for user {user}: {response_dict}. After listing the recommended items, ask the user if she/he would like to have an explanation for the recommendations. If the answer is positive, try to provide an explanation for the recommendations based on the similarities between metadata (genres, director, duration, description, and so on) of the recommended items and the items the user interacted in the past, that are: {interaction_dict}. To explain recommendations, you could also use additional information that you might know in your pre-trained knowledge."
        })
    else:
        return json.dumps(JSON_GENERATION_ERROR)


def recommend_full_catalog(user, k=5):
    """
    It generates a ranking for the given user on the entire item catalog using the loaded
    pre-trained model.

    :param user: user ID for which the recommendation has to be generated
    :param k: number of items to be returned (first k positions in the ranking)
    :return: ranking (of item IDs) for the given user ID
    """
    topk_score, topk_iid_list = full_sort_topk(user, model, test_data, k=k,
                                               device=config['device'])
    return dataset.id2token(dataset.iid_field, topk_iid_list.cpu())[0]


def recommend_given_items(user, item_ids, k=5):
    """
    Generates recommendations for the given user and item IDs using the pre-trained model.

    :param user: user ID for which the recommendation has to be generated
    :param item_ids: item IDs for which the recommendation has to be generated
    :param k: number of items to be returned (first k positions in the ranking)
    :return: ranking (of item IDs) for the given user ID
    """
    all_scores = full_sort_scores(user, model, test_data, device=config['device'])
    item_ids = [str(i) for i in item_ids]
    satisfying_item_scores = all_scores[
        0, dataset.token2id(dataset.iid_field, item_ids)]
    _, sorted_indices = torch.sort(satisfying_item_scores, descending=True)
    return [item_ids[i] for i in sorted_indices[:k].cpu().numpy()]
