from chainlit import on_message
from projectdavid import Entity, EventsInterface
import os
import httpx
from dotenv import load_dotenv
load_dotenv()
os.environ.pop("DATABASE_URL", None)
import time
import chainlit as cl
import json
from data.my_functions.functions import RECOMMENDATION
from projectdavid_common import UtilsInterface
from flask import jsonify, request, Response, stream_with_context

logging_utility = UtilsInterface.LoggingUtility()

client = Entity(base_url="http://localhost:9000", api_key=os.getenv("API_KEY"))
user = client.users.create_user(name='chainlit_user')
thread = client.threads.create_thread(participant_ids=[user.id])
assistant = client.assistants.create_assistant(instructions="You are a helpful AI assistant, connected to a movie database.")

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


def get_top_k_recommendations(tool_name, arguments):
    if tool_name == "get_top_k_recommendations":
        return json.dumps(
            {
                "status": "success",
                "message": f"Items 34, 45, and 67."
            }
        )
    return json.dumps(
        {"status": "success", "message": f"Executed tool '{tool_name}' successfully."}
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

    def generate_chunks():
        action_was_handled = False
        logging_utility.info(f"[{run.id}] Starting stream")

        # -------------------------------------------
        # Initial LLM response stream
        # -------------------------------------------
        sync_stream = None
        try:
            if not hasattr(client, "synchronous_inference_stream"):
                raise AttributeError("Missing stream client")

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
                timeout_per_chunk=15.0
            ):
                try:
                    yield json.dumps(chunk) + "\n"
                except TypeError as te:
                    yield json.dumps(
                        {
                            "type": "error",
                            "error": "Non-serializable chunk",
                            "chunk_repr": repr(chunk),
                        }
                    ) + "\n"
        except Exception as e:
            logging_utility.error(
                f"[{run.id}] Stream error: {repr(e)}", exc_info=True
            )
            yield json.dumps(
                {"type": "error", "error": str(e), "run_id": run.id}
            ) + "\n"
            return
        finally:
            if sync_stream and hasattr(sync_stream, "close"):
                try:
                    sync_stream.close()
                except Exception as close_err:
                    logging_utility.error(
                        f"[{run.id}] Close error: {repr(close_err)}"
                    )

        # -------------------------------------------
        # If a function call is triggered, it will
        # be handled here
        # -------------------------------------------
        try:
            action_was_handled = client.runs.poll_and_execute_action(
                run_id=run.id,
                thread_id=thread.id,
                assistant_id=assistant.id,
                tool_executor=get_top_k_recommendations,
                actions_client=client.actions,
                messages_client=client.messages,
                timeout=45.0,
                interval=1.5,
            )

            if action_was_handled:
                yield json.dumps(
                    {"type": "status", "status": "tool_execution_complete"}
                ) + "\n"
        except Exception as err:
            logging_utility.error(f"[{run.id}] Action error: {err}", exc_info=True)
            yield json.dumps(
                {"type": "error", "error": str(err), "run_id": run.id}
            ) + "\n"

        # -------------------------------------------
        # If a tool was used, stream final response
        # -------------------------------------------
        if action_was_handled:
            yield json.dumps(
                {"type": "status", "status": "generating_final_response"}
            ) + "\n"

            final_stream = None
            try:
                final_stream = client.synchronous_inference_stream
                final_stream.setup(
                    user_id=user.id,
                    thread_id=thread.id,
                    assistant_id=assistant.id,
                    message_id="So, what next?",
                    run_id=run.id,
                    api_key=os.getenv("HYPERBOLIC_API_KEY")
                )
                for final_chunk in final_stream.stream_chunks(
                    provider="Hyperbolic",
                    model="hyperbolic/deepseek-ai/DeepSeek-V3",
                    timeout_per_chunk=15.0
                ):
                    try:
                        yield json.dumps(final_chunk) + "\n"
                    except TypeError as te:
                        yield json.dumps(
                            {
                                "type": "error",
                                "error": "Non-serializable final chunk",
                                "chunk_repr": repr(final_chunk),
                            }
                        ) + "\n"
            except Exception as e:
                logging_utility.error(
                    f"[{run.id}] Final stream error: {repr(e)}", exc_info=True
                )
                yield json.dumps(
                    {"type": "error", "error": str(e), "run_id": run.id}
                ) + "\n"
            finally:
                if final_stream and hasattr(final_stream, "close"):
                    try:
                        final_stream.close()
                    except Exception as close_err:
                        logging_utility.error(
                            f"[{run.id}] Final close error: {repr(close_err)}"
                        )

        # -------------------------------------------
        # Final status signal
        # -------------------------------------------
        final_status = (
            "tool_completed" if action_was_handled else "inference_complete"
        )
        yield json.dumps(
            {"type": "status", "status": final_status, "run_id": run.id}
        ) + "\n"

    msg = cl.Message(content="")

    for chunk in generate_chunks():
        token = json.loads(chunk).get("content", "")
        await msg.stream_token(token)

    await msg.update()



