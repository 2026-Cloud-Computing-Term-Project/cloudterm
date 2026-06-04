import sys
import unittest
from pathlib import Path
from types import ModuleType

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.modules.setdefault("asyncpg", ModuleType("asyncpg"))

from app.api.routes.ws import _handle_heartbeat_message


class FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_json(self, payload: dict) -> None:
        self.messages.append(payload)


class WebSocketHeartbeatTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_ping_message_gets_pong_response(self) -> None:
        websocket = FakeWebSocket()

        handled = await _handle_heartbeat_message(websocket=websocket, message="ping")

        self.assertTrue(handled)
        self.assertEqual(websocket.messages, [{"type": "pong"}])

    async def test_pong_message_is_accepted(self) -> None:
        websocket = FakeWebSocket()

        handled = await _handle_heartbeat_message(websocket=websocket, message="pong")

        self.assertTrue(handled)
        self.assertEqual(websocket.messages, [])

    async def test_non_heartbeat_message_is_ignored_by_helper(self) -> None:
        websocket = FakeWebSocket()

        handled = await _handle_heartbeat_message(websocket=websocket, message="hello")

        self.assertFalse(handled)
        self.assertEqual(websocket.messages, [])
