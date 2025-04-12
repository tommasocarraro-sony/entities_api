from chainlit import on_message
from projectdavid import Entity
from dotenv import load_dotenv
import os
load_dotenv()
os.environ.pop("DATABASE_URL", None)
import chainlit as cl
from data.my_functions.functions import RECOMMENDATION, METADATA

client = Entity(base_url="http://localhost:9000", api_key=os.getenv("API_KEY"))
user = client.users.create_user(name='chainlit_user')
thread = client.threads.create_thread(participant_ids=[user.id])
assistant = client.assistants.create_assistant(instructions="You are a helpful AI assistant, connected to a movie database. This database will allow you to provide recommendations (for example top k movies for a specific user of the platform) or item metadata (for example title, director, and/or description) when requested by the user. If you detect the user asks for this kind of information, you will use function calling to retrieve that, otherwise (if the user does not specifically ask for recommendations or item metadata) you can reply normally. When generating JSONs, just generate them without additional contextual text.")  # , connected to a movie database. This database will allow you to provide recommendations or item metadata when requested by the user. If the user does not request this information, you can just reply normally.")

# attaching tools to the assistant
recommendation_tool = client.tools.create_tool(
    name="recommendation_tool",
    type="function",
    function=RECOMMENDATION,
    assistant_id=assistant.id
)

client.tools.associate_tool_with_assistant(
    tool_id=recommendation_tool.id,
    assistant_id=assistant.id
)

metadata_tool = client.tools.create_tool(
    name="metadata_tool",
    type="function",
    function=METADATA,
    assistant_id=assistant.id
)

client.tools.associate_tool_with_assistant(
    tool_id=metadata_tool.id,
    assistant_id=assistant.id
)

@on_message
async def handle_message(message):
    user_msg = client.messages.create_message(
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
        api_key=os.getenv("HYPERBOLIC_API_KEY")
    )

    for chunk in sync_stream.stream_chunks(
        provider="Hyperbolic",
        model="hyperbolic/deepseek-ai/DeepSeek-V3",
        timeout_per_chunk=15.0
    ):
        token = chunk.get("content", "")
        await msg.stream_token(token)

    await msg.update()
