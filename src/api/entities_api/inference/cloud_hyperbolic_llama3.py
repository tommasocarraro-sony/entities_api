from dotenv import load_dotenv
from openai import OpenAI
import os
import json
import time

from entities_api.inference.base_inference import BaseInference
from entities_api.services.logging_service import LoggingUtility

from entities_api.constants.assistant import PLATFORM_TOOLS

load_dotenv()
logging_utility = LoggingUtility()


class HyperbolicLlama3Inference(BaseInference):

    def setup_services(self):
        """
        Initialize the DeepSeek client and other services.
        """
        self.hyperbolic_client = OpenAI(
            api_key=os.getenv("HYPERBOLIC_API_KEY"), base_url="https://api.hyperbolic.xyz/v1"
        )
        logging_utility.info("HyperbolicLlama3Cloud specific setup completed.")

    def get_tool_response_state(self):
        return self.tool_response

    def get_function_call_state(self):
        return self.function_call

    def handle_code_interpreter_action(
        self, thread_id, run_id, assistant_id, arguments_dict
    ):
        return super().handle_code_interpreter_action(
            thread_id, run_id, assistant_id, arguments_dict
        )

    def stream_function_call_output(
        self, thread_id, run_id, assistant_id, model, stream_reasoning=False
    ):
        logging_utility.info(
            "Processing conversation for thread_id: %s, run_id: %s, assistant_id: %s",
            thread_id,
            run_id,
            assistant_id,
        )

        try:
            stream_response = self.hyperbolic_client.chat.completions.create(
                model=model,
                messages=self._set_up_context_window(
                    assistant_id, thread_id, trunk=True
                ),
                stream=True,
                temperature=0.6,
            )

            assistant_reply = ""
            accumulated_content = ""
            reasoning_content = ""

            for chunk in stream_response:
                logging_utility.debug("Raw chunk received: %s", chunk)
                reasoning_chunk = getattr(
                    chunk.choices[0].delta, "reasoning_content", ""
                )

                if reasoning_chunk:
                    reasoning_content += reasoning_chunk
                    yield json.dumps({"type": "reasoning", "content": reasoning_chunk})

                content_chunk = getattr(chunk.choices[0].delta, "content", "")
                if content_chunk:
                    assistant_reply += content_chunk
                    accumulated_content += content_chunk
                    yield json.dumps(
                        {"type": "content", "content": content_chunk}
                    ) + "\n"

                time.sleep(0.01)

        except Exception as e:
            error_msg = "[ERROR] Hyperbolic API streaming error"
            logging_utility.error(f"{error_msg}: {str(e)}", exc_info=True)
            yield json.dumps({"type": "error", "content": error_msg})
            return

        if assistant_reply:
            assistant_message = self.finalize_conversation(
                assistant_reply=assistant_reply,
                thread_id=thread_id,
                assistant_id=assistant_id,
                run_id=run_id,
            )
            logging_utility.info("Assistant response stored successfully.")

        self.run_service.update_run_status(run_id, "completed")
        if reasoning_content:
            logging_utility.info("Final reasoning content: %s", reasoning_content)

    def stream_response(
        self, thread_id, message_id, run_id, assistant_id, model, stream_reasoning=True
    ):
        return super().stream_response_hyperbolic_llama3(
            thread_id, message_id, run_id, assistant_id, model, stream_reasoning=True
        )

    def process_function_calls(self, thread_id, run_id, assistant_id, model=None):
        return super().process_function_calls(
            thread_id, run_id, assistant_id, model=None
        )

    def process_conversation(
        self, thread_id, message_id, run_id, assistant_id, model, stream_reasoning=False
    ):

        if self._get_model_map(value=model):
            model = self._get_model_map(value=model)

        # Stream the response and yield each chunk.
        for chunk in self.stream_response(
            thread_id, message_id, run_id, assistant_id, model, stream_reasoning
        ):
            yield chunk

        if self.get_function_call_state():
            if self.get_function_call_state():
                if self.get_function_call_state().get("name") in PLATFORM_TOOLS:

                    self._process_platform_tool_calls(
                        thread_id=thread_id,
                        assistant_id=assistant_id,
                        content=self.get_function_call_state(),
                        run_id=run_id,
                    )

                    # Stream the output to the response:
                    for chunk in self.stream_function_call_output(
                        thread_id=thread_id,
                        run_id=run_id,
                        model=model,
                        assistant_id=assistant_id,
                    ):
                        yield chunk

        # Deal with user side function calls
        if self.get_function_call_state():
            if self.get_function_call_state():
                if self.get_function_call_state().get("name") not in PLATFORM_TOOLS:
                    self._process_tool_calls(
                        thread_id=thread_id,
                        assistant_id=assistant_id,
                        content=self.get_function_call_state(),
                        run_id=run_id,
                    )
                    # Stream the output to the response:
                    for chunk in self.stream_function_call_output(
                        thread_id=thread_id, run_id=run_id, model="meta-llama/Meta-Llama-3.1-70B-Instruct", assistant_id=assistant_id
                    ):
                        yield chunk

    def __del__(self):
        """Cleanup resources."""
        super().__del__()

    def _process_tool_calls(self, thread_id, assistant_id, content, run_id):
        return super()._process_tool_calls(thread_id, assistant_id, content, run_id)
