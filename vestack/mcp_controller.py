"""MCP-side proxy for the Vestack tools.

Mirrors the generic controllers in controllers/: validate the arguments, then send
one command over the socket to the bridge. The dependency runs one way only —
Vestack builds on the generic core, the core knows nothing about Vestack.
"""
import json
import os
import tempfile
from typing import Any, Collection, Dict, List, Optional

from controllers.base_controller import BaseController
from vestack.naming import parse_module_id

# Reading attributes alone takes about 48 s on a 50 940-element model under
# Cadwork 2026, beyond the default socket timeout; a full export takes minutes.
OBJECT_INVENTORY_TIMEOUT_S: float = 900.0

ELEMENT_DETAIL_LEVELS = ("none", "envelope", "vertices")


def write_inventory_file(inventory: Dict[str, Any], output_path: str) -> str:
    """Write the inventory as JSON, atomically: no partial file on failure.

    Returns the absolute path written. Raises OSError when it cannot be written.
    """
    target = os.path.abspath(output_path)
    directory = os.path.dirname(target)
    handle, temporary = tempfile.mkstemp(prefix=".object_inventory_", suffix=".json",
                                         dir=directory)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(inventory, stream, ensure_ascii=False, indent=1)
        os.replace(temporary, target)
    except BaseException:
        if os.path.exists(temporary):
            os.remove(temporary)
        raise
    return target


def summarise(inventory: Dict[str, Any], keep: Collection[str]) -> Dict[str, Any]:
    """Copy of a fully detailed inventory keeping objects only for `keep` modules."""
    modules = []
    for entry in inventory.get("modules", []):
        if entry["module_id"] in keep:
            modules.append(entry)
        else:
            modules.append({k: v for k, v in entry.items() if k != "objects"})
    return {**inventory, "modules": modules}


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

    async def get_object_inventory(self,
                                   element_ids: Optional[List[int]] = None,
                                   active_only: bool = False,
                                   module_ids: Optional[List[str]] = None,
                                   element_detail: str = "none",
                                   output_path: Optional[str] = None) -> Dict[str, Any]:
        """Objects per module in module frames; optionally the full JSON export."""
        if element_detail not in ELEMENT_DETAIL_LEVELS:
            return {"status": "error",
                    "message": f"element_detail must be one of {ELEMENT_DETAIL_LEVELS}"}

        args: Dict[str, Any] = {"element_detail": element_detail}
        if element_ids:
            args["element_ids"] = [self.validate_element_id(e) for e in element_ids]
        if active_only:
            args["active_only"] = True
        if module_ids:
            args["module_ids"] = [str(m) for m in module_ids]
        if output_path:
            args["detail_all"] = True

        response = self.send_command("get_object_inventory", args,
                                     timeout=OBJECT_INVENTORY_TIMEOUT_S)
        if response.get("status") != "ok" or not output_path:
            return response

        try:
            written = write_inventory_file(response, output_path)
        except OSError as exc:
            return {"status": "error",
                    "message": f"could not write the inventory to {output_path}: {exc}"}

        keep = {parse_module_id(m) or m for m in (module_ids or [])}
        return {**summarise(response, keep), "output_path": written}
