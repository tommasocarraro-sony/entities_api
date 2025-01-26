import json
import time
from dotenv import load_dotenv
from ollama import Client
from entities_api.clients.inference.base_inference import BaseInference
from entities_api.services.logging_service import LoggingUtility

load_dotenv()
logging_utility = LoggingUtility()


class LlamaLocal(BaseInference):
    def setup_services(self):
        self.ollama_client = Client()
        logging_utility.info("LlamaLocal inference setup completed.")

    def create_tool_filtering_messages(self, messages):
        logging_utility.debug("Filtering messages for tools")
        system_message = next((msg for msg in messages if msg['role'] == 'system'), None)
        last_user_message = next((msg for msg in reversed(messages) if msg['role'] == 'user'), None)
        return [system_message, last_user_message] if system_message and last_user_message else messages

    def process_tool_calls(self, run_id, tool_calls, message_id, thread_id):
        tool_results = []
        try:
            for tool in tool_calls:
                func_name = tool['function']['name']
                func_args = json.loads(tool['function']['arguments'])

                logging_utility.info(f"Processing tool call: {func_name}")
                tool_record = self.tool_service.get_tool_by_name(func_name)

                if not tool_record or func_name not in self.available_functions:
                    raise ValueError(f"Tool {func_name} not found")

                # Execute tool function
                func_response = self.available_functions[func_name](**func_args)
                parsed_response = json.loads(func_response)

                self.message_service.add_tool_message(message_id, func_response)
                tool_results.append(parsed_response)

        except Exception as e:
            logging_utility.error(f"Tool processing error: {str(e)}", exc_info=True)

        return tool_results

    def generate_final_response(self, thread_id, message_id, run_id, tool_results, messages, model):
        logging_utility.info(f"Generating final response for {run_id}")

        if tool_results:
            messages.extend({'role': 'tool', 'content': json.dumps(r)} for r in tool_results)

        try:
            stream = self.ollama_client.chat(
                model=model,
                messages=messages,
                options={'num_ctx': 4096},
                stream=True
            )

            full_response = ""
            for chunk in stream:
                if not chunk.get('message') or not chunk['message'].get('content'):
                    continue

                content = chunk['message']['content']
                full_response += content

                # Standardized streaming format
                yield json.dumps({
                    'type': 'content',
                    'content': content
                })

                # Check for cancellation
                if self.run_service.retrieve_run(run_id).status in ["cancelling", "cancelled"]:
                    logging_utility.warning(f"Run {run_id} cancelled during streaming")
                    break

                time.sleep(0.01)  # Prevent chunk merging

            # Save final message state
            self.message_service.save_assistant_message_chunk(thread_id, full_response, True)
            self.run_service.update_run_status(run_id, "completed")

        except Exception as e:
            logging_utility.error(f"Streaming error: {str(e)}", exc_info=True)
            yield json.dumps({
                'type': 'error',
                'content': f"LLM streaming error: {str(e)}"
            })

    def process_conversation(self, thread_id, message_id, run_id, assistant_id, model='llama3.1'):
        logging_utility.info(f"Processing conversation: thread={thread_id}, run={run_id}")

        assistant = self.assistant_service.retrieve_assistant(assistant_id)
        messages = self.message_service.get_formatted_messages(thread_id, assistant.instructions)

        # Tool processing workflow
        filtered_messages = self.create_tool_filtering_messages(messages)
        initial_response = self.ollama_client.chat(
            model=model,
            messages=filtered_messages,
            options={'num_ctx': 8000}
        )

        tool_results = []
        if initial_response['message'].get('tool_calls'):
            tool_results = self.process_tool_calls(
                run_id,
                initial_response['message']['tool_calls'],
                message_id,
                thread_id
            )

        return self.generate_final_response(
            thread_id, message_id, run_id, tool_results, messages, model
        )