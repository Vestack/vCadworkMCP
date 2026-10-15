"""Per-call timeout on the bridge socket, against a bridge that never answers.

That is what Cadwork 2026 does while a Cadwork command is active: it accepts the
connection, then stays silent until the modeller presses Escape.
"""
import socket
import threading
import time
import unittest
from typing import List
from unittest.mock import patch

from controllers.base_controller import BaseController
from core.connection import CadworkConnection


class SilentBridge:
    """Accepts connections on an ephemeral port and never replies."""

    def __init__(self) -> None:
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("127.0.0.1", 0))
        self.server.listen(5)
        self.port = self.server.getsockname()[1]
        self.held: List[socket.socket] = []
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self) -> None:
        while True:
            try:
                conn, _ = self.server.accept()
            except OSError:
                return
            self.held.append(conn)

    def close(self) -> None:
        for conn in self.held:
            conn.close()
        self.server.close()


class PerCallTimeout(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge = SilentBridge()
        self.addCleanup(self.bridge.close)

    def test_the_connection_honours_a_per_call_timeout(self) -> None:
        connection = CadworkConnection("127.0.0.1", self.bridge.port)
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            connection.send_command("ping", {}, timeout=0.3)
        self.assertLess(time.monotonic() - started, 5.0)

    def test_the_controller_passes_the_timeout_and_suggests_escape(self) -> None:
        connection = CadworkConnection("127.0.0.1", self.bridge.port)
        with patch("controllers.base_controller.get_connection", return_value=connection):
            response = BaseController("Test").send_command("ping", {}, timeout=0.3)
        self.assertEqual(response["status"], "error")
        self.assertIn("press Escape", response["message"])


if __name__ == "__main__":
    unittest.main()
