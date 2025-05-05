import os
from recbole.quick_start import load_data_and_model
import torch
from recbole.utils.case_study import full_sort_scores, full_sort_topk
import json
from src.my_app.utils import define_sql_query, execute_sql_query, define_qdrant_filters
from projectdavid import Entity


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
        corrections = []
        failed_corrections = []
        # check if it is a constrained recommendation
        if 'filters' in params:
            matched = False
            filters = params.get('filters')
            # execute sql query based on the filters to get items that satisfy the filters
            sql_query, corrections, failed_corrections = define_sql_query("items", filters)
            if sql_query is not None:
                result = execute_sql_query(db_name, sql_query)
                if result is not None:
                    # invoke the recommender system to get ratings of all items satisfying
                    # the given conditions
                    item_ids = [str(row[0]) for row in result]
                    recommended_items = recommend_given_items(uid_series, item_ids, k=k)
                    matched = True
                else:
                    recommended_items = recommend_full_catalog(uid_series, k=k)
            else:
                recommended_items = recommend_full_catalog(uid_series, k=k)
        else:
            # if no filters are given, we can directly generate the ranking for the given user
            recommended_items = recommend_full_catalog(uid_series, k=k)

        print(recommended_items)
        response_dict = get_item_metadata(params={'items': recommended_items,
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
        failed_corr_text = f"Note that corrections for these fields have been tried but failed: {failed_corrections}, so the recommendation output will not take these filters into condideration."
        void_str = ''
        return json.dumps({
            "status": "success",
            "message": f"{f'The given conditions did not match any item in the database. Hence, standard recommendations (without filters) for user {user} have been generated. ' if matched is not None and not matched else ''}{f'Note that the following corrections have been made to retrieve recommendations: {corrections}. Please, explain the user that you have been able to provide recommendations only thanks to these adjustments. {failed_corr_text if failed_corrections else void_str}' if corrections else ''}Suggested recommendations for user {user}: {response_dict}. Please, include the movie ID when listing the recommended items. Please, use just item_id, title, genres, director, and description in the generated dictionary when listing recommendations. After listing the recommended items, ask the user if she/he would like to have an explanation for the recommendations. If the answer is positive, try to provide an explanation for the recommendations based on the similarities between metadata (genres, director, duration, description, and so on) of the recommended items and the items the user interacted in the past, that are: {interaction_dict}. To explain recommendations, you could also use additional information that you might know in your pre-trained knowledge."
        })
    else:
        return json.dumps({
            "status": "failure",
            "message": f"Something went wrong in the function calling. The generated JSON "
                       f"is invalid.",
        })


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
    satisfying_item_scores = all_scores[
        0, dataset.token2id(dataset.iid_field, item_ids)]
    _, sorted_indices = torch.sort(satisfying_item_scores, descending=True)
    return [item_ids[i] for i in sorted_indices[:k].cpu().numpy()]


def vector_store_search(query, filters=None, topk=5):
    """
    It performs a search on the vector store and returns the IDs of the retrieved items.

    :param query: query for the vector store search
    :param filters: Qdrant filters for the vector store search
    :param topk: number of items to be returned by the vector store search
    :return: IDs of retrieved items
    """
    client = Entity(
        base_url=os.getenv("BASE_URL", "http://localhost:9000"),
        api_key=os.getenv("ADMIN_API_KEY"),
    )
    store = os.getenv("ENTITIES_VECTOR_STORE_ID")

    embedder = client.vectors.file_processor.embedding_model
    qvec = embedder.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
        truncate="model_max_length",
    )[0].tolist()

    hits = client.vectors.vector_manager.query_store(
        store_name=store,
        query_vector=qvec,
        top_k=topk,
        filters=filters
    )

    results = [
        str(h['metadata']['item_id'])
        for i, h in enumerate(hits)
    ]

    return results


def get_recommendations_by_description(params, db_name):
    """
    This function is used by the assistant to perform recommendations of items that match a given
    textual description.

    :param params: dictionary containing all the arguments to process the description-based
    recommendations
    :param db_name: name of the database where SQL queries of get_item_metadata have to be performed

    :return: a prompt for the LLM that the LLM will use as additional context to prepare the final
    answer
    """
    if 'user' in params and 'query' in params:
        user = params.get('user')
        query = params.get('query')
        # create RecBole environment if it is not already created
        if 'config' not in globals():
            create_recbole_environment(os.getenv("RECSYS_MODEL_PATH"))
        uid_series = dataset.token2id(dataset.uid_field, [str(user)])
        matched = None
        corrections = []
        failed_corrections = []
        # check if it is a constrained recommendation
        if 'filters' in params:
            matched = False
            filters = params.get('filters')
            # execute sql query based on the filters to get items that satisfy the filters
            qdrant_filters_dict, corrections, failed_corrections = define_qdrant_filters(filters)
            if qdrant_filters_dict:
                item_ids = vector_store_search(query, filters=qdrant_filters_dict)
                recommended_items = recommend_given_items(uid_series, item_ids)
                matched = True
            else:
                item_ids = vector_store_search(query)
                recommended_items = recommend_given_items(uid_series, item_ids)
        else:
            # if no filters are given, we can directly perform the vector store search with the
            # LLM generated query
            item_ids = vector_store_search(query)
            recommended_items = recommend_given_items(uid_series, item_ids)

        print(recommended_items)
        response_dict = get_item_metadata(params={'items': recommended_items,
                                                  'specification': ["item_id", "title", "genres", "director", "description"]},
                                          db_name=db_name, return_dict=True)

        # get items interacted by user ID
        # item_ids = get_interacted_items(params={'user': int(user)}, db_name=db_name, return_list=True)
        # # get metadata of interacted items
        # interaction_dict = get_item_metadata(params={'items': item_ids,
        #                                              'specification': ["item_id", "title", "genres", "director", "producer", "actors", "release_date", "duration", "imdb_rating", "description"]},
        #                                      db_name=db_name, return_dict=True)
        #
        # print("\n" + str(interaction_dict) + "\n")
        print("\n" + str(response_dict) + "\n")
        failed_corr_text = f"Note that corrections for these fields have been tried but failed: {failed_corrections}, so the recommendation output will not take these filters into condideration."
        void_str = ''
        return json.dumps({
            "status": "success",
            "message": f"{f'The given conditions did not match any item in the database. Hence, standard vector store search (without filters) has been performed. ' if matched is not None and not matched else ''}{f'Note that the following corrections have been made to retrieve items through vector store search: {corrections}. Please, explain the user that you have been able to perform the search only thanks to these adjustments. {failed_corr_text if failed_corrections else void_str}' if corrections else ''}Suggested recommendations for user {user}: {response_dict}. Please, include the movie ID when listing the recommended items. Please, use all the information included in the generated dictionary when listing recommendations. Please, explain the users that the recommended items are items that match the description the user gave in the prompt."
        })
    else:
        return json.dumps({
            "status": "failure",
            "message": f"Something went wrong in the function calling. The generated JSON "
                       f"is invalid.",
        })


def get_recommendations_by_similar_item(params, db_name):
    """
    This function is used by the assistant to perform recommendations of items that are similar
    to a given item.

    :param params: dictionary containing all the arguments to process the recommendations
    :param db_name: name of the database where SQL queries of get_item_metadata have to be performed

    :return: a prompt for the LLM that the LLM will use as additional context to prepare the final
    answer
    """
    if 'user' in params and 'item' in params:
        user = params.get('user')
        item = params.get('item')
        # create RecBole environment if it is not already created
        if 'config' not in globals():
            create_recbole_environment(os.getenv("RECSYS_MODEL_PATH"))
        uid_series = dataset.token2id(dataset.uid_field, [str(user)])
        # get item description
        item_desc = get_item_metadata(params={'items': [item],
                                              'specification': ["item_id", "description"]},
                                          db_name=db_name, return_dict=True)
        if item_desc[item]["description"] != "unknown":
            item_ids = vector_store_search(item_desc[item]["description"], topk=11)
            # remove the first item -> it is the item we are using for finding similar items
            # it is the first in the ranking of the vector store search because the description
            # matches perfectly. We are interested in the other 29 items
            item_ids = item_ids[1:]
            print("Vector store search results: " + str(item_ids))
            # 10 items are retrieved through vector store search, 5 of them will be recommended to
            # the user based on what the recommender system predict
            recommended_items = recommend_given_items(uid_series, item_ids)

            print(recommended_items)
            response_dict = get_item_metadata(params={'items': recommended_items,
                                                      'specification': ["item_id", "title", "genres", "director", "description"]},
                                              db_name=db_name, return_dict=True)

            print("\n" + str(response_dict) + "\n")
            return json.dumps({
                "status": "success",
                "message": f"Suggested recommendations for user {user}: {response_dict}. Please, include the movie ID when listing the recommended items. Please, use all the information included in the generated dictionary when listing recommendations. Please, explain the users that the recommended items are items that are similar to the item provided in the user prompt (i.e., item {item}). The similarity is based on the description of the item, that is: {item_desc}. Please, explain this important aspect."
            })
        else:
            return json.dumps({
                "status": "failure",
                "message": f"Something went wrong in the function calling. The provided item ID does not have a description in the database, so it is impossible to determine similar items.",
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
        sql_query, _, _ = define_sql_query("items", {"items": items, "specification": specification})
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
                r_dict[result[j][0]] = {}  # in 0-position there is the item ID of the retrieved item
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
        sql_query, _, _ = define_sql_query("interactions", params)
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


def get_user_metadata(params, db_name, return_dict=False):
    """
    This function is used by the assistant to retrieve the metadata of a user based on user
    requests.

    :param params: dictionary containing all the arguments to process the metadata request
    :param db_name: name of database on which the SQL query is to be executed
    :param return_dict: whether to return the output as a dictionary or stream
    :return: stream or dictionary with the requested information
    """
    if 'user' in params and 'specification' in params:
        user = params.get('user')
        specification = params.get('specification')
        sql_query, _, _ = define_sql_query("users", {"user": user, "specification": specification})
        result = execute_sql_query(db_name, sql_query)

        if result and not return_dict:
            return_str = ""
            for j in range(len(result)):
                return_str += f"User {result[j][0]}:"
                for i, spec in enumerate(specification):
                    return_str += f"\n\n{spec}: {result[j][i] if result[j][i] is not None else 'unknown'}\n"
            return json.dumps({
                "status": "success",
                "message": f"This is the requested metadata for user {user}:\n{return_str}",
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
