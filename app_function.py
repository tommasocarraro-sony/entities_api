from chainlit import on_message
from projectdavid import Entity
from dotenv import load_dotenv
import os
load_dotenv()
os.environ.pop("DATABASE_URL", None)
import chainlit as cl
from data.my_functions.functions import RECOMMENDATION, METADATA
from projectdavid_common.schemas.tools import ToolFunction
import json

client = Entity(base_url="http://localhost:9000", api_key=os.getenv("API_KEY"))
user = client.users.create_user(name='chainlit_user')
thread = client.threads.create_thread(participant_ids=[user.id])
assistant = client.assistants.create_assistant(instructions="You are a helpful AI assistant, connected to a movie database. This database will allow you to provide recommendations (for example top k movies for a specific user of the platform) or item metadata (for example title, director, and/or description) when requested by the user. If you detect the user asks for this kind of information, you will use function calling to retrieve that, otherwise (if the user does not specifically ask for recommendations or item metadata) you can reply normally. When generating JSONs, just generate them without additional contextual text.")  # , connected to a movie database. This database will allow you to provide recommendations or item metadata when requested by the user. If the user does not request this information, you can just reply normally.")

try:
    tool_func_obj_rec = ToolFunction(function=RECOMMENDATION['function'])

    tool_rec = client.tools.create_tool(
        name=RECOMMENDATION['function']['name'],
        type="function",
        function=tool_func_obj_rec
    )

    client.tools.associate_tool_with_assistant(tool_id=tool_rec.id, assistant_id=assistant.id)

    tool_func_obj_meta = ToolFunction(function=METADATA['function'])

    tool_meta = client.tools.create_tool(
        name=RECOMMENDATION['function']['name'],
        type="function",
        function=tool_func_obj_rec
    )

    client.tools.associate_tool_with_assistant(tool_id=tool_meta.id, assistant_id=assistant.id)

except ValueError as e:
     print(f"ERROR: {e}")
except Exception as e:
     print(f"An unexpected error occurred: {e}")

def function_call_handler(tool_name, arguments):
    if tool_name == "get_top_k_recommendations":
        return json.dumps({
            "status": "success",
            "message": f"Suggested recommendations for user {arguments.get('user')}: 45, 65, 43"
        })
    elif tool_name == "get_item_metadata":
        return json.dumps({
            "status": "success",
            "message": f"Here's the requested metadata ({arguments.get('specification')}) for item {arguments.get('item')}: Oblivion"
        })
    raise ValueError("Wrong tool name passed!!")

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
                api_key=os.getenv("HYPERBOLIC_API_KEY")
            )
            for final_chunk in sync_stream.stream_chunks(
                provider="Hyperbolic",
                model="hyperbolic/deepseek-ai/DeepSeek-V3",
                timeout_per_chunk=15.0,
                api_key=os.getenv("HYPERBOLIC_API_KEY"),
            ):
                token = final_chunk.get("content", "")
                await msg.stream_token(token)

            await msg.update()
    except Exception as e:
        print(f"\n[Error during tool execution or final stream]: {str(e)}")
