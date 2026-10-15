"""Receiving the bridge's answer: the bridge sends one JSON document, then closes.

A bridge-like sender runs on an ephemeral port: it reads the command, sends the
payload with sendall and closes the connection, as cadwork_bridge.py does.
"""
import json
import socket
import threading
import time
import unittest

from core.connection import CadworkConnection


class OneShotBridge:
    """Answers a single connection with `payload`, then closes it."""

    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("127.0.0.1", 0))
        self.server.listen(1)
        self.port = self.server.getsockname()[1]
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self) -> None:
        conn, _ = self.server.accept()
        try:
            conn.settimeout(20.0)
            conn.recv(65536)
            conn.sendall(self.payload)
        finally:
            conn.close()

    def close(self) -> None:
        self.thread.join(5.0)
        self.server.close()


def big_payload() -> bytes:
    """About 5 MB of inventory-shaped JSON."""
    elements = [{"element_id": i, "name": "Montant", "material": "C24",
                 "origin": [1234, 5678, 90], "size": [45, 200, 2645]}
                for i in range(50000)]
    return json.dumps({"status": "ok", "modules": [{"module_id": "M1",
                                                    "elements": elements}]}).encode("utf-8")


class Receive(unittest.TestCase):
    def answer(self, payload: bytes) -> CadworkConnection:
        bridge = OneShotBridge(payload)
        self.addCleanup(bridge.close)
        return CadworkConnection("127.0.0.1", bridge.port)

    def test_a_large_response_is_received_in_linear_time(self) -> None:
        payload = big_payload()
        self.assertGreater(len(payload), 4_500_000)
        connection = self.answer(payload)
        started = time.monotonic()
        response = connection.send_command("get_object_inventory", {}, timeout=30.0)
        self.assertLess(time.monotonic() - started, 5.0)
        self.assertEqual(len(response["modules"][0]["elements"]), 50000)

    def test_a_small_response_is_returned(self) -> None:
        connection = self.answer(b'{"status": "ok", "message": "pong"}')
        self.assertEqual(connection.send_command("ping"), {"status": "ok", "message": "pong"})

    def test_test_connection_reads_the_ping(self) -> None:
        self.assertTrue(self.answer(b'{"status": "ok"}').test_connection())

    def test_an_empty_response_is_a_connection_error(self) -> None:
        with self.assertRaises(ConnectionError):
            self.answer(b"").send_command("ping")

    def test_an_invalid_response_is_a_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.answer(b'{"status": "ok"').send_command("ping")


if __name__ == "__main__":
    unittest.main()
