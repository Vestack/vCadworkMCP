"""MCP-side proxy for the Vestack tools.

Mirrors the generic controllers in controllers/: validate the arguments, then send
one command over the socket to the bridge. The dependency runs one way only —
Vestack builds on the generic core, the core knows nothing about Vestack.
"""
from typing import Any, Dict, List, Optional

from controllers.base_controller import BaseController


class VestackController(BaseController):
    """Controller for Vestack modular-construction operations."""

    def __init__(self) -> None:
        super().__init__("VestackController")

    async def get_module_inventory(self,
                                   element_ids: Optional[List[int]] = None,
                                   active_only: bool = False,
                                   id_source: Optional[str] = None) -> Dict[str, Any]:
        """List the modules of the model with their dimensions."""
        args: Dict[str, Any] = {}

        if element_ids:
            args["element_ids"] = [self.validate_element_id(e) for e in element_ids]
        if active_only:
            args["active_only"] = True
        if id_source:
            args["id_source"] = id_source

        return self.send_command("get_module_inventory", args)
