from chainlit import on_message
from dotenv import load_dotenv
import os
load_dotenv()
os.environ.pop("DATABASE_URL", None)
import chainlit as cl
from projectdavid import Entity
from src.my_app.utils import create_lists_for_fuzzy_matching
from src.my_app.functions import get_item_metadata, get_interacted_items, get_top_k_recommendations, get_recommendations_by_similar_item, get_recommendations_by_description, get_user_metadata
import asyncio

db_name = "movielens-100k"

client = Entity(base_url="http://localhost:9000", api_key=os.getenv("ADMIN_API_KEY"))
user = client.users.retrieve_user(user_id=os.getenv("ENTITIES_USER_ID"))
thread = client.threads.create_thread(participant_ids=[user.id])
assistant = client.assistants.retrieve_assistant(assistant_id="default")

# this is necessary for the working of fuzzy matching to correct typos (for actors, directors,
# producers. and genres) in the user prompts
create_lists_for_fuzzy_matching()


def function_call_handler(tool_name, arguments):
    print(f"Calling tool: {tool_name}")
    if tool_name == "get_top_k_recommendations":
        return get_top_k_recommendations(arguments, db_name)
    if tool_name == "get_item_metadata":
        return get_item_metadata(arguments, db_name)
    if tool_name == "get_interacted_items":
        return get_interacted_items(arguments, db_name)
    if tool_name == "get_recommendations_by_description":
        return get_recommendations_by_description(arguments)
    # if tool_name == "get_recommendations_by_similar_item":
    #     return get_recommendations_by_similar_item(arguments, db_name)
    if tool_name == "get_user_metadata":
        return get_user_metadata(arguments, db_name)


sync_stream = client.synchronous_inference_stream


async def standard_stream(run, message_id, msg, stream=True):
    sync_stream.setup(
        user_id=user.id,
        thread_id=thread.id,
        assistant_id=assistant.id,
        message_id=message_id,
        run_id=run.id,
        api_key=os.getenv("HYPERBOLIC_API_KEY"),
    )

    for chunk in sync_stream.stream_chunks(
        provider="Hyperbolic",
        model="hyperbolic/deepseek-ai/DeepSeek-V3",
        timeout_per_chunk=30.0,
        api_key=os.getenv("HYPERBOLIC_API_KEY"),
    ):
        token = chunk.get("content", "")
        if stream:
            await msg.stream_token(token)


async def stream_after_action(run, msg):
    action_was_handled = client.runs.poll_and_execute_action(
        run_id=run.id,
        thread_id=thread.id,
        assistant_id=assistant.id,
        tool_executor=function_call_handler,
        actions_client=client.actions,
        messages_client=client.messages,
        timeout=60.0,
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
        answer = ""
        for final_chunk in sync_stream.stream_chunks(
            provider="Hyperbolic",
            model="hyperbolic/deepseek-ai/DeepSeek-V3",
            timeout_per_chunk=30.0,
            api_key=os.getenv("HYPERBOLIC_API_KEY"),
        ):
            token = final_chunk.get("content", "")
            answer += token
            await msg.stream_token(token)

        # check if the answer contains a JSON
        if "{" in answer and "}" in answer:
            # we mark the run status as completed and create e new run to request the new information
            print("Detected JSON so other tool call has to be executed...")
            # print(f"This is the content of the answer that will be sent to the LLM: {answer}")
            # # in this case, we have to call entire_conversation again
            # await entire_conversation(message=answer, msg=msg)
            # return True
            # todo I should create a new run here as the other one is completed after the generation by the tool
            # todo difficult because I need a message but it has to be internal
            return True
        else:
            return False


async def entire_conversation(message, msg):
    message = client.messages.create_message(
        thread_id=thread.id,
        role='user',
        content=message,
        assistant_id=assistant.id
    )

    run = client.runs.create_run(
        assistant_id=assistant.id,
        thread_id=thread.id
    )

    await standard_stream(run, message.id, msg)
    await msg.stream_token("\n\n")
    answer_containing_json = await stream_after_action(run, msg)
    await msg.stream_token("\n\n")

    if answer_containing_json:
        print("YES! The answer contains indeed a JSON!!")
        message = client.messages.create_message(
            thread_id=thread.id,
            role='user',
            content="Please, use the generated JSON to call the tool. It should be enough that you regenerate the same JSON for the tool call to be effective.",
            assistant_id=assistant.id
        )

        run = client.runs.create_run(
            assistant_id=assistant.id,
            thread_id=thread.id
        )

        await standard_stream(run, message.id, msg, stream=False)
        await stream_after_action(run, msg)

    # close the stream at the end of everything
    await msg.update()


@on_message
async def handle_message(message):
    msg = cl.Message(content="")

    # async def retry_conversation():
    #     while True:
    #         try:
    #             await entire_conversation()
    #             print("Conversation finished smoothly.")
    #             break  # Exit the loop if everything runs successfully
    #         except Exception as e:
    #             print(f"There has been an error: {e}. Trying to recover the conversation...")
    #             print("Printing message till now for debugging")
    #             print(msg.content)
    #             # await msg.update()  # Optionally update the message here to reflect the retry
    #             await asyncio.sleep(5)  # Wait for 10 seconds before retrying

    # Start the retry loop
    await entire_conversation(message.content, msg)


@cl.on_chat_start
async def on_chat_start():
    msg = cl.Message(content="")
    system_message = ("Hello, I am your Recommendation Assistant! I am here to help you investigating how is your streaming platform working. Specifically, this is a brief list of my skills:"
                      "\n\n1. **Standard recommendations**: you can ask for recommendations for a specific user ID. I will call a recommender system and display the top k (by default, k = 5, but you can potentially ask for a specific number of recommendations) recommended items along with useful metadata to differentiate them (e.g., title and description)."
                      "\n\n2. **Constrained recommendations**: you can ask for recommendations for a specific user ID and that have to satisfy some given conditions, for example, you can ask for movies starring a specific actor, directed by specific producers, released in a specific date and so on. Before calling the recommender system, a MySQL database will be queried to get all the items satisfying the given conditions. Note that once the filters have been applied, it might be that less than k items satisfy all the conditions. In this case, the final ranking might contain a number of items that does not match the provided k (i.e., the desired number of recommended items). This is a list of the available features on which you can build conditions:"
                      "\n   - Actors: you can provide an actor name or a list of actor names. Fuzzy matching is also used internally to correct mispelled names or to find the most similar names w.r.t. the given names. If I had to correct some names, I will excplicity tell you what have been the corrections I made to perform the query;"
                      "\n   - Directors: same as actors but for directors;"
                      "\n   - Movie genres: same as actors but for movie genres;"
                      "\n   - Producers: same as actors but for producers;"
                      "\n   - IMDb rating: you can ask for movies with an IMDb rating higher or lower than a given threshold;"
                      "\n   - Duration: you can ask for short or long movies, and for movies that last more or less than a certain threshold;"
                      "\n   - Release date: you can ask for movies released on a specific date or movies that have been released prior to or after a specific date. Please, use the year when referring to dates;"
                      "\n   - Popularity: you can ask for popular or unpopular movies;"
                      "\n   - Popularity by age group: you can ask for movies popular in a specific age category: teenagers, kids, young adults, adults, seniors."
                      "\n\n3. **Explanations for recommendations**: every time I provide you with a list of recommended items, I will ask you whether you would like a personalized explanation for them. If you reply yes, I will provide you explanations based on content-based (e.g., similar genres, actors, and so on) similarities between the recommended items and the 10 most recent items the user interacted with."
                      "\n\n4. **User's mood-based recommendations**: you can ask for recommendations based on the mood of the provided user ID. It is enough you describe the mood of the user and I will try to provide recommendations that match the described mood. To do so, I will perform a vector store search to look for movie plots that match the provided user's mood. The top 10 matching items will be retrieved and the recommender system will be called on them to create a personalized ranking. Only the top 5 items will be displayed in this case."
                      "\n\n5. **Description-based recommendations**: you can ask for recommendations for a specific user ID and that match a given description. To generate the result, similarly to the previous item, I will perform a vector store search to find the top 10 items that match the given description. Then, I will call the recommender system to generate a ranking of them. Finally, the top 5 items will be displayed."
                      "\n\n6. **Similar item-based recommendations**: you can ask for recommendations for a specific user ID and that are similar to a given item ID. To generate the result, I will first query a MySQL database to get the description of the given item. Then, I will perform a vector store search to find the top 10 items that match the given description. Finally, I will call the recommender system to generate a ranking over them, personalized for the given user. The top 5 items will be displayed."
                      "\n\n7. **Get item metadata**: you can ask for specific metadata of an item or list of item IDs. Specifically, you can ask for the following metadata: "
                      "\n   - Title;"
                      "\n   - Description; "
                      "\n   - Actors;"
                      "\n   - Movie genres; "
                      "\n   - Directors;"
                      "\n   - Producers;"
                      "\n   - Duration;"
                      "\n   - Release date;"
                      "\n   - IMDb rating; "
                      "\n   - Popularity."
                      "\n\n8. **Get user metadata**: you can ask for specific metadata regarding a user ID. Specifically, you can ask for the gender and age category."
                      "\n\n9. **Get user historical interactions**: you can ask for the historical interactions of a user ID. I will query a database to retrieve the item IDs of the previously interacted items. Then, I will query another database to get some metadata of these items to provide you a comprehensive description of them. Note that I will display to you the 10 most recent items. **Extra**: after I finished displaying the interacted items, you could ask me to analyze the user interests based on the metadata of the interacted items."
                      "\n\n\nAs carefully explained in the previous items, to prepare your answers, I will interact with external tools using sophisticated Tool Calling and Retrieval Agumented Genration techniques. I will tell you about each step of the process to build your answer to provide maximum transparency. I will use a Chain of Thoughts prompting technique to provide the step-by-step process behing each answer preparation."
                      "\n\n Feel free to start with your first query!")
    for token in system_message:
        # await msg.stream_token("The application is loading, please wait for my first message, thank you!\n\n")
        await msg.stream_token(token)

    # message = client.messages.create_message(
    #     thread_id=thread.id,
    #     role='user',
    #     content="This is a system message that the user does not see, so, avoid to start with 'certainly' or something similar!!! Instead, say hello and present yourself as the recommendation assistant. Then, explain to the user what are your skills and what you can do regarding the tools you can call. Provide a small description of the tools but do not provide examples of JSONs. Remember that the user is the owner of a streaming platform, so the recommendations you provide are always based on the user ID the platform owner prompts to you.",
    #     assistant_id=assistant.id
    # )
    #
    # run = client.runs.create_run(
    #     assistant_id=assistant.id,
    #     thread_id=thread.id
    # )
    #
    # await standard_stream(run, message.id, msg)
    await msg.update()

# todo fixing the stop of the service with a retry mechanism -> I need to get the exception in some way to implement a retry mechanism
# todo fixing the waiting time for the tool to execute
# todo conversation is correctly recovered but there is always an error
# todo idea, if there is False and the run arrived at terminal state, it is okay. In all the other cases, we need to re-run
# todo now that the exceptions are handled, we can reduce the timeout -> this will allow a better and more fluid stream when the run stays in queued status for long times
# todo I got this run does not require tool call even if the tool has been called correctly
# todo improve the user mood-based recommendations. Tell the LLM that it has to be able to determine what are the correct features based on the request. Internally, if the request is for sad mood, it has to do a query to understand what is usually suggested to user with a sad mood, or better if it both suggest something sad, to maintain the mood, or something happy, to make the user thinks less about problems
# todo once we fixed, refactor all the handles
# todo only put a lot of GB where necessary
# todo add a prompt at the beginning that explain what the assistant can do
# todo improve CoT prompting in the app by putting more rules in the system prompts
# todo if the tool are known, maybe it is not useful to waste tokens
# todo it seems like my implementation is not working. It hallucinates
# todo put some enters between the various CoT so that everything is clearer
# todo still do not understand what is not working, probably I need to create another run instead of relying on the same one
# todo explain that these are the tools that can be internally used by the LLM, maybe we should not mention them
# todo the parser does not work when there are filters




#     if "Hyperbolic SDK error" in msg.content:
    #         print("The tool has been executed but the provider returned a malformed answer, "
    #               "so not output is showed to the user. We need to retry!")
    #         return False
    #
    #     if msg.content.endswith("}"):
    #         # todo for the moment, we just retry. We should understand how to send an hidden
    #         #  message to the assistant to tell him it is doing wrong, namely that it should
    #         #  pay more attention to generate the JSON files
    #         print("The assistant generated the JSON file but a problem occurred and no "
    #               "tool has been called. Problems could be server disconnect or peer close"
    #               "connection.")
    #         return False
    #
    #     print("Tool call has been executed correctly!!!")
    #     return True
    #
    # else:
    #     if client.runs.retrieve_run(run_id=run.id).status == "completed" and msg.content.endswith("}"):
    #         # todo for the moment, we just retry. We should understand how to send an hidden
    #         #  message to the assistant to tell him it is doing wrong, namely that it should
    #         #  pay more attention to generate the JSON files
    #         print("The assistant generated the JSON file, but the file is not well "
    #               "formated. There is an extra } at the end. For this reason, the tool "
    #               "is not called properly. We need to retry in this case.")
    #         return False
    #     elif client.runs.retrieve_run(run_id=run.id).status == "completed":
    #         print("This run does not require calling any tool!!!")
    #         return True
    #     else:
    #         print("The tool call did not complete successfully!!! We need to retry!!")
    #         return False
