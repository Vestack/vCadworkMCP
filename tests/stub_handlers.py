"""Handler stubs for the dispatcher tests.

Deliberately follows the real bridge convention: handle_<operation>(args) -> dict.
"""
from typing import Any, Dict, List


def handle_stub_ok(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "ok", "echo": args.get("value")}


def handle_stub_success(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "success", "data": 42}


def handle_stub_error(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "error", "message": "handler said no"}


def handle_stub_raises(args: Dict[str, Any]) -> Dict[str, Any]:
    raise RuntimeError("boom")


def handle_stub_plain_result(args: Dict[str, Any]) -> List[int]:
    return [1, 2, 3]


def handle_stub_without_status(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"element_ids": [7]}


not_a_handler = "a module member the dispatcher must ignore"
