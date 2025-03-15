from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
import json
from sandbox_api.services.logging_service import LoggingUtility
from sandbox_api.services.web_socket_shell_service import WebSocketShellService

logging_utility = LoggingUtility()
v1_router = APIRouter()  # No prefix here

shell_service = WebSocketShellService()  # Global singleton instance

@v1_router.websocket("/shell")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    current_room = None
    try:
        while True:
            data = await websocket.receive_text()
            shell_service.logging_utility.debug(f"Received data: {data}")
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                shell_service.logging_utility.error("Failed to decode JSON")
                continue

            action = payload.get("action")
            if action == "join_room":
                room = payload.get("room")
                if room:
                    if current_room:
                        shell_service.remove_from_room(websocket)
                    current_room = room
                    shell_service.add_to_room(room, websocket)
                    await shell_service.create_client_session(websocket)
            elif action == "leave_room":
                room = payload.get("room")
                if room:
                    shell_service.remove_from_room(websocket)
                    if current_room == room:
                        current_room = None
            elif action == "shell_command":
                command = payload.get("command", "").strip()
                if command:
                    await shell_service.process_command(websocket, command)
            elif action == "message":
                message = payload.get("message")
                if current_room and message:
                    broadcast_payload = {
                        "room": current_room,
                        "message": message,
                        "sender": payload.get("sender")
                    }
                    await shell_service.broadcast_to_room(current_room, broadcast_payload)
            else:
                shell_service.logging_utility.info("Unknown action received")
    except WebSocketDisconnect:
        shell_service.logging_utility.info("Client disconnected gracefully")
    except Exception as e:
        shell_service.logging_utility.error(f"Error: {e}")
    finally:
        if current_room:
            shell_service.remove_from_room(websocket)
        await shell_service.cleanup_session(websocket)
        shell_service.logging_utility.info("Cleaned up session")