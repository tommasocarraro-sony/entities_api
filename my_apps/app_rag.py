from chainlit import on_message
from dotenv import load_dotenv
import os
load_dotenv()
os.environ.pop("DATABASE_URL", None)
import chainlit as cl
from src.my_app.utils import create_app_environment


entities_setup = {
    "api_key": "ea_zzCWjSYSRZFCXjh_jhqRn3HExNoXkZI8xn0Sbq5XYHw",
    "user_id": "user_K55QgQVJEu0pmiGrExxuLc",
    "assistant_tools": []
}

db_name = "movielens-100k"

client, user, thread, assistant = create_app_environment(
    database_name=db_name,
    entities_setup=entities_setup
)

# todo create the vector store similarly for the tools. We pass to create_app_environment that creates the store only if this does not exist and add files to the store only if they do not exist
# create a vector store
store = client.vectors.create_vector_store(
    name='Movie metadata',
    user_id=user.id,
)

attach = client.vectors.attach_vector_store_to_assistant(
    vector_store_id=store.id,
    assistant_id=assistant.id
)

save_file_to_store = client.vectors.add_file_to_vector_store(
    vector_store_id=store.id,
    file_path='../data/recsys/ml-100k/ml-100k.md'
)

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

    await msg.update()
