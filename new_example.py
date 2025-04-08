from dotenv import load_dotenv
import os
import pprint
from entities import Entities

load_dotenv()
client = Entities()  # this is used to access the API

user = client.users.create_user(name='test_user')  # creates a new user in the system
thread = client.threads.create_thread(participant_ids=[user.id])  # this is like a chatroom that will contain conversation context
assistant = client.assistants.create_assistant()  # LLM chatbot creation

message = client.messages.create_message(  # this is a user message in the previously created thread and associated with the specified assistant (more than one assistant can partecipate in the chat)
    thread_id=thread.id,
    role='user',
    content='Hello, This is a test message.',
    assistant_id=assistant.id
)

# every interaction between the user and the assistant is a run in a thread -> the assistant will add messages to the thread based on the request and tools it had to use
# failed	You can view the reason for the failure by looking at the last_error object in the Run. The timestamp for the failure will be recorded under failed_at.
# incomplete	Run ended due to max_prompt_tokens or max_completion_tokens being reached. You can view the specific reason by looking at the incomplete_details object in the Run.
# cancelling -> when the user presses on the stop button the run should be cancelled
run = client.runs.create_run(  # this is a session where the assistant processes the request and generate the answer -> this session includes 9 states
    assistant_id=assistant.id,
    thread_id=thread.id
)

completion = client.inference.create_completion_sync(  # the run is executed by using a specified provider for the assistant, the answer is a stream of chunks of text
    provider="Hyperbolic",
    model="hyperbolic/meta-llama/llama-3.3-70b-instruct",
    # model="hyperbolic/deepseek-ai/deepseek-v3",
    thread_id=thread.id,
    message_id=message.id,
    run_id=run.id,
    assistant_id=assistant.id
)

pprint.pprint(completion)

