from chainlit import on_message, run_sync, Message
from projectdavid import Entity
import os
import httpx
os.environ.pop("DATABASE_URL", None)
import time
import chainlit as cl
from data.my_functions.functions import RECOMMENDATION, METADATA

client = Entity()
user = client.users.create_user(name='chainlit_user')
thread = client.threads.create_thread(participant_ids=[user.id])
assistant = client.assistants.create_assistant(instructions="You are a helpful AI assistant, connected to a movie database. This database will allow you to provide recommendations or item metadata when requested by the user. If the user does not request this information, you can just reply normally.")

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

# metadata_tool = client.tools.create_tool(
#     name="metadata_tool",
#     type="function",
#     function=METADATA,
#     assistant_id=assistant.id
# )
#
# client.tools.associate_tool_with_assistant(
#     tool_id=metadata_tool.id,
#     assistant_id=assistant.id
# )

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

    # while True:
    #     try:
    #         response = client.inference.create_completion_sync(
    #             provider="Hyperbolic",
    #             model="hyperbolic/meta-llama/llama-3.3-70b-instruct",
    #             # model="hyperbolic/deepseek-ai/deepseek-v3",
    #             thread_id=thread.id,
    #             message_id=message.id,
    #             run_id=run.id,
    #             assistant_id=assistant.id
    #         )
    #         reply_text = response['choices'][0]['message']['content']
    #         break
    #     except httpx.ReadTimeout:
    #         time.sleep(2)
    #
    # await Message(content=reply_text).send()

    msg = cl.Message(content="")
    while True:
        try:
            async for chunk in client.inference.stream_inference_response(
                provider="Hyperbolic",
                model="hyperbolic/meta-llama/llama-3.3-70b-instruct",
                thread_id=thread.id,
                message_id=message.id,
                run_id=run.id,
                assistant_id=assistant.id
            ):
                token = chunk.get("content", "")
                await msg.stream_token(token)
            break
        except httpx.TimeoutException as e:
            time.sleep(10)

    await msg.update()

