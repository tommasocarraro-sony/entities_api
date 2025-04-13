# from projectdavid import Entity
# from data.my_functions.functions import RECOMMENDATION
#
# client = Entity()
#
# user = client.users.create_user(name='test_user336')
# print(f"Created user {user.id}")
#
#
# assistant = client.assistants.create_assistant(name='test_assistant',
#                                                 instructions='You are a helpful assistant'
#                                                              'working at an airport.'
#                                                 )
# print(f"created assistant {assistant.id}")
#
# function_definition = {
#     "function": {
#         "name": "get_flight_times",
#         "description": "Get the flight times between two cities.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "departure": {"type": "string", "description": "The departure city (airport code)."},
#                 "arrival": {"type": "string", "description": "The arrival city (airport code)."}
#             },
#             "required": ["departure", "arrival"]
#         }
#     }
# }
#
# from projectdavid_common.schemas.tools import ToolFunction
#
# try:
#     print("Creating new tool...")
#
#     # 1. Create the ToolFunction object explicitly
#     tool_func_obj = ToolFunction(function=RECOMMENDATION['function'])
#
#     # 2. Call create_tool, passing the object
#     tool = client.tools.create_tool(
#         name=RECOMMENDATION['function']['name'],
#         type="function",
#         function=tool_func_obj
#     )
#     print(f"Created tool {tool.id}")
#
#     client.tools.associate_tool_with_assistant(tool_id=tool.id,
#                                                assistant_id=assistant.id)
#
#     client.tools.associate_tool_with_assistant(tool_id=tool.id,
#                                                assistant_id="default")
#
#     print(f"attached tool: {tool.id} to assistant: ")
#
# except ValueError as e:
#      print(f"ERROR: {e}")
# except Exception as e:
#      print(f"An unexpected error occurred: {e}")

import os
import json
import time
from projectdavid import Entity
from dotenv import load_dotenv

load_dotenv()

client = Entity()


# -----------------------------------------
# This is a basis mock handler returning
# static test data. Handling is a consumer
# side concern.
# ----------------------------------------
def get_flight_times(tool_name, arguments):
    if tool_name == "get_flight_times":
        return json.dumps({
            "status": "success",
            "message": f"Flight from {arguments.get('departure')} to {arguments.get('arrival')}: 4h 30m",
            "departure_time": "10:00 AM PST",
            "arrival_time": "06:30 PM EST",
        })
    return json.dumps({
        "status": "success",
        "message": f"Executed tool '{tool_name}' successfully."
    })

def function_call_handler(tool_name, arguments):
    if tool_name == "get_top_k_recommendations":
        return json.dumps({
            "status": "success",
            "message": f"Suggested recommendations for user {arguments.get('user')}: 45, 65, 43"
        })
    return json.dumps({
        "status": "success",
        "message": f"Executed tool '{tool_name}' successfully."
    })


# ------------------------------------------------------
# Please be aware:
# - user id needs to be a user id you have generated
# - We are using the default assistant since it is
# - already highly optimized for function calling.
# -------------------------------------------------------
user_id = "user_HjAjPGQLXPhqkppWQfGxZL"
assistant_id = "default"

# ----------------------------------------------------
# Create a thread
# ----------------------------------------------------

thread = client.threads.create_thread(participant_ids=[user_id])

# ----------------------------------------------------
# Create a message that should trigger the function call
# ----------------------------------------------------
message = client.messages.create_message(
    thread_id=thread.id,
    role="user",
    content="Please, recommend some horror movies for user 15.",
    assistant_id=assistant_id,
)

# ----------------------------------------------------
# Create a Run
# ----------------------------------------------------

run = client.runs.create_run(
    assistant_id=assistant_id,
    thread_id=thread.id
)

# ----------------------------------------------------
# Set up inference.
# - Note: that I am fetching the hyperbolic
# API key from .env
# ----------------------------------------------------


sync_stream = client.synchronous_inference_stream
sync_stream.setup(
    user_id=user_id,
    thread_id=thread.id,
    assistant_id=assistant_id,
    message_id=message.id,
    run_id=run.id,
    api_key=os.getenv("HYPERBOLIC_API_KEY"),
)

# --- Stream initial LLM response ---
for chunk in sync_stream.stream_chunks(
    provider="Hyperbolic",
    model="hyperbolic/deepseek-ai/DeepSeek-V3",
    timeout_per_chunk=15.0,
    api_key=os.getenv("HYPERBOLIC_API_KEY"),
):
    content = chunk.get("content", "")
    if content:
        print(content, end="", flush=True)

# --- Function call execution ---
try:

    # ----------------------------------------------------
    # This is the function call event handler
    # - Note: that you can tweak timeout & interval
    # - Alwauys place it here in the order of procedure
    # ----------------------------------------------------

    # ----------------------------------------------------
    #  This is a special case block.
    #  Some of the models need a follow-up message before
    #  they provide you with their synthesis on function call
    #  output. hyperbolic/deepseek-ai/DeepSeek-V3 is an
    #  example of a model we were able to make stable by
    #  using this method where there is no official
    #  work around from @DeepSeek
    # ----------------------------------------------------

    action_was_handled = client.runs.poll_and_execute_action(
        run_id=run.id,
        thread_id=thread.id,
        assistant_id=assistant_id,
        tool_executor=function_call_handler,
        actions_client=client.actions,
        messages_client=client.messages,
        timeout=45.0,
        interval=1.5,
    )

    if action_was_handled:
        print("\n[Tool executed. Generating final response...]\n")
        sync_stream.setup(
            user_id=user_id,
            thread_id=thread.id,
            assistant_id=assistant_id,
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
            content = final_chunk.get("content", "")
            if content:
                print(content, end="", flush=True)
except Exception as e:
    print(f"\n[Error during tool execution or final stream]: {str(e)}")
