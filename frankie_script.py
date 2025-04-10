import os
from dotenv import load_dotenv
load_dotenv()
from projectdavid import Entity

client = Entity(base_url="http://localhost:9000", api_key=os.getenv("API_KEY"))

user = client.users.create_user(name='test_user2')


assistant = client.assistants.create_assistant(name='test_assistant',
                                               instructions='You are a helpful AI assistant')


# step 1 - Create a thread

thread = client.threads.create_thread(participant_ids=[user.id])


# step 2 - Create a message

message = client.messages.create_message(
    thread_id=thread.id,
    role="user",
    content="Hello, assistant!",
    assistant_id=assistant.id
)

# step 3 - Create a run

run = client.runs.create_run(assistant_id=assistant.id, thread_id=thread.id)


# Instantiate the syncronous streaming helper

sync_stream = client.synchronous_inference_stream


# step 4 - Set up the stream

sync_stream.setup(
    user_id=user.id,
    thread_id=thread.id,
    assistant_id=assistant.id,
    message_id=message.id,
    run_id=run.id,
    api_key=os.getenv("HYPERBOLIC_API_KEY"),
)

# step 5 - Stream the response

import logging
import json

logging.basicConfig(level=logging.INFO)

# Stream completions synchronously
logging.info("Beginning sync stream...")
for chunk in sync_stream.stream_chunks(
    provider="Hyperbolic",
    model="hyperbolic/deepseek-ai/DeepSeek-V3",
    timeout_per_chunk=15.0
):
    logging.info(json.dumps(chunk, indent=2))

logging.info("Stream finished.")
