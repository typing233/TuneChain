import logging
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

ws_router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._global_connections: set[WebSocket] = set()

    async def connect(self, task_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[task_id].add(ws)

    async def connect_global(self, ws: WebSocket):
        await ws.accept()
        self._global_connections.add(ws)

    def disconnect(self, task_id: str, ws: WebSocket):
        self._connections[task_id].discard(ws)
        if not self._connections[task_id]:
            del self._connections[task_id]

    def disconnect_global(self, ws: WebSocket):
        self._global_connections.discard(ws)

    async def broadcast(self, task_id: str, message: dict):
        dead: list[tuple[str, WebSocket]] = []

        for ws in list(self._connections.get(task_id, set())):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append((task_id, ws))

        for ws in list(self._global_connections):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(("__global__", ws))

        for tid, ws in dead:
            if tid == "__global__":
                self._global_connections.discard(ws)
            else:
                self._connections[tid].discard(ws)


manager = ConnectionManager()


# IMPORTANT: The global route MUST be defined before the parameterized route,
# otherwise FastAPI matches "all" as a {task_id} path parameter.
@ws_router.websocket("/ws/progress")
async def ws_all_progress(websocket: WebSocket):
    await manager.connect_global(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_global(websocket)


@ws_router.websocket("/ws/progress/{task_id}")
async def ws_task_progress(websocket: WebSocket, task_id: str):
    await manager.connect(task_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(task_id, websocket)
