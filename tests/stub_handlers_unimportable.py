"""A handler module that cannot be imported outside Cadwork.

Mirrors export_handlers.py and import_handlers.py, which do `import cadwork` at
module level. Discovery must skip these without losing the other modules.
"""
from typing import Any, Dict

import a_module_that_does_not_exist  # noqa: F401


def handle_stub_never_reachable(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "ok"}
