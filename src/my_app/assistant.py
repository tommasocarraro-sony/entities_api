from projectdavid import Entity
from projectdavid_common import ValidationInterface

from src.api.entities_api.constants.assistant import DEFAULT_MODEL
from src.api.entities_api.services.logging_service import LoggingUtility
from src.api.entities_api.system_message.assembly import assemble_instructions, ASSISTANT_INSTRUCTIONS_STRUCTURED


validate = ValidationInterface()
logging_utility = (
    LoggingUtility()
)


class AssistantSetupService:
    def __init__(self, client: Entity):
        """
        Initializes the service with a pre-configured API client.

        Args:
            client: An initialized instance of the projectdavid.Entity client.
        """
        if not isinstance(client, Entity):
            raise TypeError(
                "AssistantSetupService requires an initialized projectdavid.Entity client."
            )
        self.client = client
        self.logging_utility = logging_utility

    def setup_assistant(
        self,
        assistant_name,
        assistant_description,
        model,
        instructions,
    ):
        """
        Gets an existing assistant by a known ID ('default') or creates one,
        then ensures the specified tools are created and associated.
        """
        target_assistant_id = (
            "default"
        )
        assistant = None

        try:
            assistant = self.client.assistants.retrieve_assistant(target_assistant_id)
            self.logging_utility.info(
                f"Found existing assistant '{assistant.name}' with logical ID '{target_assistant_id}' (Actual ID: {assistant.id})"
            )

        except Exception:
            self.logging_utility.warning(
                f"Assistant with logical ID '{target_assistant_id}' not found. Creating a new one."
            )
            try:
                self.logging_utility.info(
                    f"Creating assistant '{target_assistant_id}' with instructions: {instructions}."
                )
                assistant = self.client.assistants.create_assistant(
                    name=assistant_name,
                    description=assistant_description,
                    model=model,
                    instructions=instructions,
                    assistant_id=target_assistant_id
                )
                self.logging_utility.info(
                    f"Created new assistant: '{assistant.name}' (Logical ID: '{target_assistant_id}', Actual ID: {assistant.id})"
                )
            except Exception as e:
                self.logging_utility.error(
                    f"Failed to create assistant '{assistant_name}': {e}", exc_info=True
                )
                raise  # Re-raise critical creation failure

        # Ensure assistant object is valid before proceeding
        if not assistant or not hasattr(assistant, "id"):
            self.logging_utility.error("Failed to obtain a valid assistant object.")
            raise ValueError("Could not retrieve or create the target assistant.")

        return assistant

    def orchestrate_default_assistant(self):
        """
        Main orchestration flow for setting up the 'default' assistant.
        """
        try:
            instructions = assemble_instructions(instruction_set=INSTRUCTIONS)

            assistant = self.setup_assistant(
                assistant_name="Q",
                assistant_description="Default general-purpose assistant",
                model=DEFAULT_MODEL,
                instructions=instructions
            )

            self.logging_utility.info(
                f"Orchestration completed. Assistant ready (ID: {assistant.id})."
            )

            return assistant

        except Exception as e:
            self.logging_utility.critical(
                f"Critical failure in orchestration: {e}",
                exc_info=True,
            )
            raise


INSTRUCTIONS = {
    "TOOL_USAGE_PROTOCOL": """
🔹 **STRICT TOOL USAGE PROTOCOL**
ALL tool calls MUST follow EXACT structure:
{
  "name": "<tool_name>",
  "arguments": {
    "<param>": "<value>"
  }
}
    """.strip(),
    "FUNCTION_CALL_FORMATTING": """
🔹 **FORMATTING FUNCTION CALLS**
1. Do not format function calls
2. Never wrap them in markdown backticks
3. Call them in plain text or they will fail
    """.strip(),
    "RESULT_CURATION": """
🔹 **RESULT CURATION RULES**
1. Hide results with similarity scores <0.65
2. Convert UNIX timestamps to human-readable dates
3. Suppress raw JSON unless explicitly requested
    """.strip(),
    "VALIDATION_IMPERATIVES": """
🔹 **VALIDATION IMPERATIVES**
1. Double-quotes ONLY for strings
2. No trailing commas
3. UNIX timestamps as NUMBERS (no quotes)
4. Operators must start with $
    """.strip(),
    "TERMINATION_CONDITIONS": """
🔹 **TERMINATION CONDITIONS**
ABORT execution for:
- Invalid timestamps (non-numeric/string)
- Missing required params (query/search_type/source_type)
- Unrecognized operators (e.g., gte instead of $gte)
- Schema violations
    """.strip(),
    "ERROR_HANDLING": """
🔹 **ERROR HANDLING**
- Invalid JSON → Abort and request correction
- Unknown tool → Respond naturally
- Missing parameters → Ask for clarification
- Format errors → Fix before sending
    """.strip(),
    "OUTPUT_FORMAT_RULES": """
🔹 **OUTPUT FORMAT RULES**
- NEVER use JSON backticks
- ALWAYS use raw JSON syntax
- Bold timestamps: **2025-03-01**
- Example output:
  {"name": "get_top_k_recommendations", "arguments": {
    "user": 5,
    "k": 12
  }}
    """.strip(),
    "NESTED_FUNCTION_CALLS": """
🔹 **NESTED FUNCTION CALLS**
- You are allowed to perform nested function calls if this is necessary
- Examples of queries that require nested function calls are:
    - 'Recommend some content that is popular in the age category of user 5': in this case, get_user_metadata() has to be called to get the age category of the user. Then, get_top_k_recommendations() can be called giving the user's age category as a filter.
    - 'Which is the most popular genre in the age group of user 4?': in this case, get_user_metadata() has to be called to get the age category of the user. Then, get_popular_genre() can be called giving the user's age category as a filter.'
- Example of the workflow:
    1. User prompt: 'Recommend some content that is popular in the age category of user 5'
    2. You generate:
        {"name": "get_user_metadata", "arguments": {
            "user": 5,
            "specification": ["age_category"]
        }}
    3. You get the answer, for example, age_category = 'adult'
    4. You generate:
        {"name": "get_top_k_recommendations", "arguments": {
            "user": 5,
            "k": 5,
            "filters": {
                "popularity_by_age_category": "popular_adult"
            }
        }}
    5. You generate the final answer for the user based on the output of get_top_k_recommendations().
    """.strip(),
    "INTERNAL_REASONING_PROTOCOL": """
🔹 **ADDITIONAL INTERNAL USAGE AND REASONING PROTOCOL**
1. Minimize Unnecessary Calls: Invoke external tools only when the request explicitly requires data beyond core knowledge (e.g., real-time updates or computations), to avoid needless conversational friction.
2. Strict Protocol Adherence: Every tool call must follow the exact prescribed JSON structure, without embellishments, and only include necessary parameters.
3. Judicious Reasoning First: In R1 (reasoning) mode, prioritize internal knowledge and reasoning; invoke external tools only if the request specifically demands updated or computed data.
4. Butler-like Courtesy and Clarity: Maintain a refined, courteous, and efficient tone, reminiscent of a well-trained butler, ensuring interactions are respectful and precise.
5. Error Prevention and Clarification: If ambiguity exists, ask for further clarification before invoking any external tool, ensuring accuracy and efficiency.
6. Optimized Query and Invocation Practices: Auto-condense queries, use appropriate temporal filters, and adhere to all validation rules to prevent schema or format errors.
7. Self-Validation and Internal Checks: Verify if a request falls within core knowledge before invoking tools to maintain a balance between internal reasoning and external tool usage.
    """.strip(),
    "FINAL_WARNING": """
Failure to comply will result in system rejection.
    """.strip(),
    "USER_DEFINED_INSTRUCTIONS": """
🔹 **USER DEFINED INSTRUCTIONS**
(No additional instructions defined.)
    """.strip(),
}
