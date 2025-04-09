from projectdavid import Entity, EventsInterface
import time
import chainlit as cl
from data.my_functions.functions import RECOMMENDATION
from pprint import pprint

client = Entity()
user = client.users.create_user(name='chainlit_user')
thread = client.threads.create_thread(participant_ids=[user.id])
assistant = client.assistants.create_assistant(instructions="You are a helpful AI assistant, connected to a movie database. This database will allow you to provide recommendations or item metadata when requested by the user. If the user does not request this information, you can just reply normally."
                                                            "When generating JSONs, please use \"arguments\" in place of \"parameters\". If you fail to satisfy this requirement, the database will be destroyed.")

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



user_msg = client.messages.create_message(
    thread_id=thread.id,
    role='user',
    content="Please, recommend some horror movies directed by Tom Cruise for user 45. Please, use \"arguments\" in place of \"parameters\" when generating JSONs.",
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

while True:
    try:
        response = client.inference.create_completion_sync(
                    provider="Hyperbolic",
                    model="hyperbolic/meta-llama/llama-3.3-70b-instruct",
                    thread_id=thread.id,
                    message_id=user_msg.id,
                    run_id=run.id,
                    assistant_id=assistant.id
                )
        break
    except Exception as e:
        time.sleep(5)

pprint(response)
