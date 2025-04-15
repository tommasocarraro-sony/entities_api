from chainlit import on_message
from projectdavid import Entity
from dotenv import load_dotenv
import os
load_dotenv()
os.environ.pop("DATABASE_URL", None)
import chainlit as cl
from data.my_functions.functions import RECOMMENDATION_QUERY, METADATA_QUERY, INTERACTION_QUERY
from projectdavid_common.schemas.tools import ToolFunction
import json
from recbole.quick_start import load_data_and_model
from recbole.utils.case_study import full_sort_topk, full_sort_scores
import sqlite3
import torch

# todo look for item metadata with multiple IDs instead of doing multiple searches in the table
# todo create a summary of a user based on its past interactions, depict the user based on his/her past interactions

config, model, dataset, train_data, valid_data, test_data = load_data_and_model(
    model_file='./data/recsys/ml-100k/model.pth',
)

def create_db():
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS movie_metadata (item_id INTEGER PRIMARY KEY, title TEXT, release_date INTEGER, genres TEXT)''')

    # load data
    with open('./data/recsys/ml-100k/ml-100k.item', 'r', encoding='utf-8') as f:
        first_line = True
        for line in f:
            if first_line:
                first_line = False
                continue
            parts = line.strip().split('\t')
            if len(parts) < 4:
                continue  # skip lines with missing data

            item_id = int(parts[0])
            movie_title = parts[1]
            release_year = int(parts[2]) if parts[2].isdigit() else None
            movie_class = parts[3]

            # Insert into the table
            cursor.execute('INSERT OR IGNORE INTO movie_metadata VALUES (?, ?, ?, ?)',
                           (item_id, movie_title, release_year, movie_class))

    cursor.execute('''CREATE TABLE IF NOT EXISTS interactions (user_id INTEGER PRIMARY KEY, items TEXT)''')

    # Read the file and build the dictionary
    user_interactions = {}
    with open('./data/recsys/ml-100k/ml-100k.inter', 'r') as f:
        first_line = True
        for line in f:
            if first_line:
                first_line = False
                continue
            user_id, item_id, rating, timestamp = line.strip().split('\t')
            user_id = int(user_id)
            item_id = int(item_id)

            if user_id not in user_interactions:
                user_interactions[user_id] = []
            user_interactions[user_id].append(item_id)

    # Insert data into the table
    for user_id, items in user_interactions.items():
        items_str = ','.join(map(str, items))
        cursor.execute('INSERT OR REPLACE INTO interactions (user_id, items) VALUES (?, ?)',
                       (user_id, items_str))

    conn.commit()
    conn.close()

def associate_tool_to_assistant(assistant_id, tool):
    # check if tool is already associated
    tools = client.tools.list_tools(assistant_id)
    if tool['function']['name'] in [t['name'] for t in tools]:
        print("Tool already associated!")
    else:
        try:
            print("Associating tool to assistant")
            tool_func_obj = ToolFunction(function=tool['function'])

            tool_ = client.tools.create_tool(
                name=tool['function']['name'],
                type="function",
                function=tool_func_obj
            )

            client.tools.associate_tool_with_assistant(tool_id=tool_.id,
                                                       assistant_id=assistant_id, )

        except ValueError as e:
            print(f"ERROR: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


def get_interacted_items(params, get_directly=False):
    if 'query' in params:
        sql_query = params.get('query')
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchone()
        conn.close()

        if result and get_directly:
            return result[0]
        elif result and not get_directly:
            return json.dumps({
                "status": "success",
                "message": f"The list of item IDs user {user} interacted is: {result[0]}",
            })
        else:
            return None
    else:
        return json.dumps({
            "status": "failure",
            "message": f"Something went wrong in the function calling. The generated JSON is invalid.",
        })


def get_top_k_recommendations(params):
    if 'user' in params and 'k' in params:
        user = params.get('user')
        k = params.get('k')
        uid_series = dataset.token2id(dataset.uid_field, [str(user)])
        # satisfy filters
        if 'filter_query' in params:
            sql_query = params.get('filter_query')
            # execute sql query based on the filters to get items that satisfy the filters
            conn = sqlite3.connect('movies.db')
            cursor = conn.cursor()
            cursor.execute(sql_query)
            result = cursor.fetchall()
            conn.close()
            # invoke the recommender system to get rating of all items satisfying the given conditions
            item_ids = [str(row[0]) for row in result]
            all_scores = full_sort_scores(uid_series, model, test_data, device=config['device'])
            satisfying_item_scores = all_scores[0, dataset.token2id(dataset.iid_field, item_ids)]
            _, sorted_indices = torch.sort(satisfying_item_scores, descending=True)
            external_item_list = [item_ids[i] for i in sorted_indices[:k].cpu().numpy()]
        else:
            topk_score, topk_iid_list = full_sort_topk(uid_series, model, test_data, k=k,
                                                       device=config['device'])
            external_item_list = dataset.id2token(dataset.iid_field, topk_iid_list.cpu())[0]

        print(external_item_list)
        response_dict = get_item_metadata(params={'filter_query': f"SELECT title, release_date, genres FROM movie_metadata WHERE item_id IN ({', '.join([i for i in external_item_list])})"}, return_dict=True)

        # get items interacted by user ID
        item_ids = get_interacted_items(params={'query': f"SELECT items FROM interactions WHERE user_id = {user}"}, get_directly=True)
        # get metadata of interacted items
        interaction_dict = get_item_metadata(params={'filter_query': f"SELECT title, release_date, genres FROM movie_metadata WHERE item_id IN ({item_ids})"}, return_dict=True)

        print("\n" + str(interaction_dict) + "\n")
        print("\n" + str(response_dict) + "\n")
        return json.dumps({
            "status": "success",
            "message": f"Suggested recommendations for user {user}: {response_dict}. Please, include the movie ID when listing the recommended items. After listing the recommended items, if the user asks for an explanation in a subsequent prompt, please try to provide an explanation for the recommendations based on the similarities between recommended items and the items the user interacted in the past, that are: {interaction_dict}. To explain recommendations, you could also use additional information that you might know. Please, ask the user if he/she would like an explanation to be provided. If the answer is yes, explain the recommendations."
        })
    else:
        return json.dumps({
            "status": "failure",
            "message": f"Something went wrong in the function calling. The generated JSON is invalid.",
        })


def get_item_metadata(params, return_dict=False):
    if 'filter_query' in params:
        conn = sqlite3.connect('movies.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        sql_query = params.get('filter_query')
        cursor.execute(sql_query)
        result = cursor.fetchone()

        conn.close()

        if result and not return_dict:
            return json.dumps({
                "status": "success",
                "message": f"This is the requested metadata for item {result['item_id']}:\n{result}",
            })
        elif result and return_dict:
            return result
        else:
            if not return_dict:
                return json.dumps({
                    "status": "failure",
                    "message": f"No information found for the given item.",
                })
            else:
                return None
    else:
        return json.dumps({
            "status": "failure",
            "message": f"Something went wrong in the function calling. The generated JSON is invalid.",
        })


def function_call_handler(tool_name, arguments):
    if tool_name == "get_top_k_recommendations":
        return get_top_k_recommendations(arguments)
    if tool_name == "get_item_metadata":
        return get_item_metadata(arguments)
    if tool_name == "get_past_interactions":
        return get_interacted_items(arguments)

    return json.dumps({
        "status": "success",
        "message": f"Executed tool '{tool_name}' successfully."
    })


create_db()
client = Entity(base_url="http://localhost:9000", api_key=os.getenv("API_KEY"))
user = client.users.retrieve_user('user_HkTZCaqKmvEOKFzQRfjtLR')
thread = client.threads.create_thread(participant_ids=[user.id])
assistant = client.assistants.retrieve_assistant("default")
associate_tool_to_assistant(assistant.id, tool=RECOMMENDATION_QUERY)
associate_tool_to_assistant(assistant.id, tool=METADATA_QUERY)
associate_tool_to_assistant(assistant.id, tool=INTERACTION_QUERY)


@on_message
async def handle_message(message):
    client.messages.create_message(
        thread_id=thread.id,
        role='user',
        content=message.content,
        assistant_id=assistant.id
    )

    run = client.runs.create_run(
        assistant_id=assistant.id,
        thread_id=thread.id
    )

    msg = cl.Message(content="")

    sync_stream = client.synchronous_inference_stream

    sync_stream.setup(
        user_id=user.id,
        thread_id=thread.id,
        assistant_id=assistant.id,
        message_id=message.id,
        run_id=run.id,
        api_key=os.getenv("HYPERBOLIC_API_KEY"),
    )

    for chunk in sync_stream.stream_chunks(
        provider="Hyperbolic",
        model="hyperbolic/deepseek-ai/DeepSeek-V3",
        timeout_per_chunk=15.0,
        api_key=os.getenv("HYPERBOLIC_API_KEY"),
    ):
        token = chunk.get("content", "")
        await msg.stream_token(token)

    try:
        action_was_handled = client.runs.poll_and_execute_action(
            run_id=run.id,
            thread_id=thread.id,
            assistant_id=assistant.id,
            tool_executor=function_call_handler,
            actions_client=client.actions,
            messages_client=client.messages,
            timeout=45.0,
            interval=1.5,
        )

        if action_was_handled:
            print("\n[Tool executed. Generating final response...]\n")
            sync_stream.setup(
                user_id=user.id,
                thread_id=thread.id,
                assistant_id=assistant.id,
                message_id="regenerated",
                run_id=run.id,
                api_key=os.getenv("HYPERBOLIC_API_KEY"),
            )
            for final_chunk in sync_stream.stream_chunks(
                provider="Hyperbolic",
                model="hyperbolic/deepseek-ai/DeepSeek-V3",
                timeout_per_chunk=15.0,
                api_key=os.getenv("HYPERBOLIC_API_KEY"),
            ):
                token = final_chunk.get("content", "")
                await msg.stream_token(token)
    except Exception as e:
        print(f"\n[Error during tool execution or final stream]: {str(e)}")

    await msg.update()
