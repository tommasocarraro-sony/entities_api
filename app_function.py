from chainlit import on_message
from dotenv import load_dotenv
import os
load_dotenv()
os.environ.pop("DATABASE_URL", None)
import chainlit as cl
from src.my_app.function_definitions import RECOMMENDATION, METADATA, INTERACTION, RECOMMENDATION_VECTOR, RECOMMENDATION_SIMILAR_ITEM, USER_METADATA
from src.my_app.utils import create_app_environment
from src.my_app.functions import get_item_metadata, get_interacted_items, get_top_k_recommendations, get_recommendations_by_similar_item, get_recommendations_by_description, get_user_metadata


entities_setup = {
    "api_key": os.getenv("ENTITIES_API_KEY"),
    "user_id": os.getenv("ENTITIES_USER_ID"),
    "assistant_tools": [RECOMMENDATION, METADATA, INTERACTION, RECOMMENDATION_VECTOR,
                        RECOMMENDATION_SIMILAR_ITEM, USER_METADATA],
    "vector_store_name": "ml-100k_metadata_vector_store"
}

db_name = "movielens-100k"

client, user, thread, assistant = create_app_environment(
    database_name=db_name,
    entities_setup=entities_setup
)


def function_call_handler(tool_name, arguments):
    print(f"Calling tool: {tool_name}")
    if tool_name == "get_top_k_recommendations":
        return get_top_k_recommendations(arguments, db_name)
    if tool_name == "get_item_metadata":
        return get_item_metadata(arguments, db_name)
    if tool_name == "get_interacted_items":
        return get_interacted_items(arguments, db_name)
    if tool_name == "get_recommendations_by_description":
        return get_recommendations_by_description(arguments, db_name)
    if tool_name == "get_recommendations_by_similar_item":
        return get_recommendations_by_similar_item(arguments, db_name)
    if tool_name == "get_user_metadata":
        return get_user_metadata(arguments, db_name)


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
        timeout_per_chunk=20.0,
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
                timeout_per_chunk=20.0,
                api_key=os.getenv("HYPERBOLIC_API_KEY"),
            ):
                token = final_chunk.get("content", "")
                await msg.stream_token(token)
    except Exception as e:
        print(f"\n[Error during tool execution or final stream]: {str(e)}")

    await msg.update()


# todo get user age category to then recommend
# todo remove unassary tools from default assistant
