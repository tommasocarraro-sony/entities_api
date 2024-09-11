import httpx
from typing import List, Optional
from fastapi import HTTPException
from pydantic import ValidationError
from requests import Session
from sqlalchemy.orm import joinedload
from entities_api.schemas import ToolCreate, ToolRead, ToolUpdate
from entities_api.services.logging_service import LoggingUtility
from models.models import Assistant, Tool

logging_utility = LoggingUtility()


class ToolService:
    def __init__(self, db: Session):
        self.db = db
        self.client = httpx.Client()  # Initialize the httpx client
        logging_utility.info("ToolService initialized with database session.")

    def create_tool(self, **tool_data) -> ToolRead:
        logging_utility.info("Creating new tool")
        try:
            tool = ToolCreate(**tool_data)
            response = self.client.post("/v1/tools", json=tool.model_dump())
            response.raise_for_status()
            created_tool = response.json()
            validated_tool = ToolRead.model_validate(created_tool)
            logging_utility.info("Tool created successfully with id: %s", validated_tool.id)
            return validated_tool
        except ValidationError as e:
            logging_utility.error("Validation error during tool creation: %s", e.json())
            raise ValueError(f"Validation error: {e}")
        except httpx.HTTPStatusError as e:
            logging_utility.error("HTTP error during tool creation: %s | Response: %s", str(e), e.response.text)
            raise
        except Exception as e:
            logging_utility.error("Unexpected error during tool creation: %s", str(e))
            raise

    def associate_tool_with_assistant(self, tool_id: str, assistant_id: str) -> None:
        logging_utility.info("Associating tool with ID %s to assistant with ID %s", tool_id, assistant_id)
        try:
            tool = self._get_tool_or_404(tool_id)
            assistant = self.db.query(Assistant).filter(Assistant.id == assistant_id).first()

            if not assistant:
                logging_utility.warning("Assistant with ID %s not found.", assistant_id)
                raise HTTPException(status_code=404, detail=f"Assistant with id {assistant_id} not found")

            assistant.tools.append(tool)
            self.db.commit()

            logging_utility.info("Successfully associated tool ID %s with assistant ID %s", tool_id, assistant_id)
        except HTTPException as e:
            logging_utility.error("HTTPException: %s", str(e))
            raise
        except Exception as e:
            self.db.rollback()
            logging_utility.error("Error associating tool with assistant: %s", str(e))
            raise HTTPException(status_code=500, detail="An error occurred while associating the tool with the assistant")

    def get_tool(self, tool_id: str) -> ToolRead:
        logging_utility.info("Retrieving tool with ID: %s", tool_id)
        try:
            db_tool = self._get_tool_or_404(tool_id)
            logging_utility.info("Tool retrieved successfully: %s", db_tool)
            return ToolRead.model_validate(db_tool)
        except HTTPException as e:
            logging_utility.error("HTTPException: %s", str(e))
            raise
        except Exception as e:
            logging_utility.error("Unexpected error retrieving tool: %s", str(e))
            raise HTTPException(status_code=500, detail="An error occurred while retrieving the tool")

    def update_tool(self, tool_id: str, tool_update: ToolUpdate) -> ToolRead:
        logging_utility.info("Updating tool with ID: %s, ToolUpdate: %s", tool_id, tool_update)
        try:
            db_tool = self._get_tool_or_404(tool_id)
            update_data = tool_update.model_dump(exclude_unset=True)
            logging_utility.debug("Updating tool with data: %s", update_data)

            for key, value in update_data.items():
                setattr(db_tool, key, value)

            self.db.commit()
            self.db.refresh(db_tool)

            logging_utility.info("Tool with ID %s updated successfully", tool_id)
            return ToolRead.model_validate(db_tool)
        except HTTPException as e:
            logging_utility.error("HTTPException: %s", str(e))
            raise
        except Exception as e:
            self.db.rollback()
            logging_utility.error("Error updating tool: %s", str(e))
            raise HTTPException(status_code=500, detail="An error occurred while updating the tool")

    def delete_tool(self, tool_id: str) -> None:
        logging_utility.info("Deleting tool with ID: %s", tool_id)
        try:
            db_tool = self._get_tool_or_404(tool_id)
            self.db.delete(db_tool)
            self.db.commit()

            logging_utility.info("Tool with ID %s deleted successfully", tool_id)
        except HTTPException as e:
            logging_utility.error("HTTPException: %s", str(e))
            raise
        except Exception as e:
            self.db.rollback()
            logging_utility.error("Error deleting tool: %s", str(e))
            raise HTTPException(status_code=500, detail="An error occurred while deleting the tool")

    def list_tools(self, assistant_id: Optional[str] = None, restructure: bool = False) -> List[dict]:
        logging_utility.info("Listing tools for assistant ID: %s", assistant_id)
        try:
            if assistant_id:
                assistant = self.db.query(Assistant).options(joinedload(Assistant.tools)).filter(Assistant.id == assistant_id).first()
                logging_utility.debug("Assistant found: %s", assistant)

                if not assistant:
                    logging_utility.warning("Assistant with ID %s not found", assistant_id)
                    raise HTTPException(status_code=404, detail=f"Assistant with id {assistant_id} not found")

                tools = assistant.tools
            else:
                tools = self.db.query(Tool).all()

            logging_utility.info("Found %d tools", len(tools))

            # Convert ORM objects to dictionaries manually
            tool_list = [self._tool_to_dict(tool) for tool in tools]

            # Optionally restructure tools
            if restructure:
                tool_list = self.restructure_tools({'tools': tool_list})

            return tool_list
        except Exception as e:
            logging_utility.error("Error listing tools: %s", str(e))
            raise HTTPException(status_code=500, detail="An error occurred while listing the tools")

    def restructure_tools(self, assistant_tools):
        """Restructure the tools to handle dynamic function structures."""

        def parse_parameters(parameters):
            """Recursively parse parameters and handle different structures."""
            if isinstance(parameters, dict):
                parsed = {}
                for key, value in parameters.items():
                    if isinstance(value, dict):
                        parsed[key] = parse_parameters(value)
                    else:
                        parsed[key] = value
                return parsed
            return parameters

        restructured_tools = []

        for tool in assistant_tools['tools']:
            function_info = tool['function']

            # Check if the 'function' key is nested and extract accordingly
            if 'function' in function_info:
                function_info = function_info['function']

            restructured_tool = {
                'type': tool['type'],
                'name': function_info.get('name', 'Unnamed tool'),
                'description': function_info.get('description', 'No description provided'),
                'parameters': parse_parameters(function_info.get('parameters', {})),
            }

            restructured_tools.append(restructured_tool)

        return restructured_tools

    def _tool_to_dict(self, tool: Tool) -> dict:
        return {
            "id": tool.id,
            "type": tool.type,
            "function": tool.function  # Assuming function is stored as a dictionary or JSON-like structure
        }

    def _get_tool_or_404(self, tool_id: str) -> Tool:
        logging_utility.debug("Fetching tool with ID: %s", tool_id)
        db_tool = self.db.query(Tool).filter(Tool.id == tool_id).first()
        if not db_tool:
            logging_utility.warning("Tool not found with ID: %s", tool_id)
            raise HTTPException(status_code=404, detail="Tool not found")
        logging_utility.debug("Tool with ID %s found", tool_id)
        return db_tool
