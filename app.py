from chainlit import on_message, run_sync, Message
from entities import Entities
import os
import httpx
os.environ.pop("DATABASE_URL", None)
import time
import chainlit as cl

client = Entities()
user = client.users.create_user(name='chainlit_user')
thread = client.threads.create_thread(participant_ids=[user.id])
assistant = client.assistants.create_assistant()

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
    except httpx.ReadTimeout:
        time.sleep(2)

    await msg.update()

