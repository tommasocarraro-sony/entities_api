import json
import logging
from entities import Entities
from entities import EventsInterface
from entities.clients.actions import ActionsClient
from data.my_functions.functions import RECOMMENDATION, METADATA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inference")

client = Entities()
actions_client = ActionsClient()

# Step 1: Create a user
user = client.users.create_user(name="platform_owner")

# Step 2: Create an assistant
assistant = client.assistants.create_assistant(
    name="Recommendation Agent",
    instructions="You are a helpful AI assistant, connected to a movie database."
)

# Step 3: Register the SQL query tool
# todo this has to be done for each tool I have, each tool is a function
# todo problems when the passed arguments do not entirely or completely match data contained in the database (for example. misspelled movie genre)
# todo test it to understand structure and then see what could be the system prompt
#
explanation_function = {
    "type": "function",
    "function": {
        "name": "get_explanation_data",
        "description": (
            "It retrieves metadata useful to provide a personalized explanation to the user. The function retrieves metadata of the recommended items"
            "and items the user interacted with in the past. Similarities between the metadata of recommended and interacted items can be then used to provide personalized explanations for the user."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user": {
                    "type": "integer",
                    "description": "User for which the explanation has to be generated."
                },
                "recommended_items": {
                    "type": "list",
                    "description": "List of items that have been recommended to the user and for which an explanation has to be generated."
                }
            },
            "required": ["user", "recommended_items"]
        }
    }
}

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

# Step 4: Start a conversation
thread = client.threads.create_thread(participant_ids=[user.id])

message = client.messages.create_message(
    thread_id=thread.id,
    assistant_id=assistant.id,
    content="Can you recommend some horror movies starring Tom Cruise released after 2010 with an IMDb rating above 6 for user 45?",
    role="user"
)

# Step 5: Create a run
run = client.runs.create_run(
    thread_id=thread.id,
    assistant_id=assistant.id
)

# ------------------------------
# Function Call handler Class
# Can be scaled to handle and manage additional calls
# ------------------------------

class FunctionCallService:
    def __init__(self):
        self.function_handlers = {
            "get_top_k_recommendations": self.handle_get_top_k_recommendations,
            "get_item_metadata": self.handle_get_item_metadata
        }

    def call_function(self, function_name, arguments):
        return self.function_handlers[function_name](arguments)

    @staticmethod
    def handle_get_top_k_recommendations(arguments):
        parsed_args = json.loads(arguments) if isinstance(arguments, str) else arguments
        # query = parsed_args.get("query")
        # logger.info(f"Executing SQL: {query}")
        print("Generating recommendations")
        # return {"rows": [{"title": "Oblivion", "year": 2013, "rating": 7.1}]}
        return {"recs": []}

    @staticmethod
    def handle_get_item_metadata(arguments):
        parsed_args = json.loads(arguments) if isinstance(arguments, str) else arguments
        print("Retrieving metadata")
        return {"metadata": []}

# ------------------------------
# ✅ NEW: Asynchronous Monitor using MonitorLauncher
# ------------------------------

def my_custom_tool_handler(run_id, run_data, pending_actions):
    logger.info(f"[ACTION_REQUIRED] run {run_id} has {len(pending_actions)} pending action(s)")
    for action in pending_actions:
        action_id = action.get("id")
        tool_name = action.get("tool_name")
        args = action.get("function_args")

        logger.info(f"[ACTION] Tool: {tool_name}, Args: {args}")

        handler = FunctionCallService()
        result = handler.call_function(tool_name, args)

        client.message_service.submit_tool_output(
            thread_id=run_data["thread_id"],
            assistant_id=run_data["assistant_id"],
            tool_id=action.get("tool_id"),
            role="tool",
            content=json.dumps(result)
        )

        client.actions.update_action(
            action_id=action_id,
            status="completed"
        )

        logger.info("✅ Tool output submitted and action marked complete.")

# 🔄 Launch the monitor in the background
monitor = EventsInterface.MonitorLauncher(
    client=client,
    actions_client=actions_client,
    run_id=run.id,
    on_action_required=my_custom_tool_handler,
    events=EventsInterface
)
monitor.start()

# ------------------------------
# Step 6: Stream the assistant response
# ------------------------------
stream = client.synchronous_inference_stream
stream.setup(
    user_id=user.id,
    thread_id=thread.id,
    assistant_id=assistant.id,
    message_id=message.id,
    run_id=run.id
)

try:
    print("📡 Streaming assistant response...\n")
    print_str = ""
    for chunk in stream.stream_chunks(provider="Hyperbolic", model="hyperbolic/meta-llama/llama-3.3-70b-instruct"):
        if "content" in chunk:
            print_str += chunk["content"]
    print(print_str)
    print("\n✅ Stream complete.")
except Exception as e:
    logger.error("❌ Stream failed: %s", str(e))
finally:
    try:
        stream.close()
    except Exception as e:
        logger.warning("⚠️ Stream cleanup failed: %s", str(e))
