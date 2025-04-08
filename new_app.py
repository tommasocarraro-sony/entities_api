from chainlit import on_message
from projectdavid import Entity, EventsInterface
import os
import httpx
os.environ.pop("DATABASE_URL", None)
import time
import chainlit as cl
from data.my_functions.functions import RECOMMENDATION

client = Entity()
user = client.users.create_user(name='chainlit_user')
thread = client.threads.create_thread(participant_ids=[user.id])
assistant = client.assistants.create_assistant(instructions="You are a helpful AI assistant, connected to a movie database. This database will allow you to provide recommendations or item metadata when requested by the user. If the user does not request this information, you can just reply normally.")

# attaching tools to the assistant
recommendation_tool = client.tools.create_tool(
    name="get_top_k_recommendations",
    type="function",
    function=RECOMMENDATION,
    assistant_id=assistant.id
)

client.tools.associate_tool_with_assistant(
    tool_id=recommendation_tool.id,
    assistant_id=assistant.id
)

def custom_tool_handler(run_id, run_data, pending_actions):
    print("trial!!!")
    for action in pending_actions:
        tool_name = action.get("tool_name")
        args = action.get("function_args", {})
        print(f"Handling tool '{tool_name}' with args {args}")
        # TODO: Add tool logic and optionally submit results:


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

    # Start monitoring tool invocation events
    monitor = EventsInterface.MonitorLauncher(
        client=client,
        actions_client=client.actions,
        run_id=run.id,
        on_action_required=custom_tool_handler,
        events=EventsInterface
    )
    monitor.start()

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
