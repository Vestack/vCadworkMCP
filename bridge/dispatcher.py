"""Command dispatcher for the Cadwork MCP bridge.

Single entry point for everything arriving on the bridge socket. Operations are
discovered by convention: any `handle_<operation>(args) -> dict` in a registered
handler module becomes the operation `<operation>`. Adding a handler is therefore
enough to expose it; there is no second list to keep in sync.

Handler modules are imported defensively, one by one. Some of them import
`cadwork` at module level and so only exist inside Cadwork; a module that cannot
be imported is recorded in `unavailable_modules` and the rest keep working.
"""
import importlib
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

HANDLER_PREFIX = "handle_"

Handler = Callable[[Dict[str, Any]], Any]

# Generic Cadwork handlers. Order matters only if two modules were to define the
# same operation; the first registration wins and the loser is recorded.
HANDLER_MODULES: Tuple[str, ...] = (
    "bridge.handlers.element_handlers",
    "bridge.handlers.geometry_handlers",
    "bridge.handlers.attribute_handlers",
    "bridge.handlers.visualization_handlers",
    "bridge.handlers.utility_handlers",
    "bridge.handlers.list_handlers",
    "bridge.handlers.optimization_handlers",
    "bridge.handlers.export_handlers",
    "bridge.handlers.import_handlers",
    "bridge.handlers.machine_handlers",
    "bridge.handlers.roof_handlers",
    "bridge.handlers.shop_drawing_handlers",
)

# Domain-specific extensions, kept out of the generic bridge. Drop the entry and
# delete the package to return to a purely generic Cadwork bridge.
EXTENSION_MODULES: Tuple[str, ...] = (
    "vestack.bridge_handler",
)


def _normalise(result: Any) -> Dict[str, Any]:
    """Coerce a handler result into the response contract the MCP side expects.

    `core.connection` and `controllers.base_controller` treat only "ok" as
    success, while handlers variously return "ok", "success" or no status at all.
    """
    if not isinstance(result, dict):
        return {"status": "ok", "data": result}

    response: Dict[str, Any] = dict(result)
    if response.get("status") in (None, "success"):
        response["status"] = "ok"
    return response


class CommandDispatcher:
    """Maps operation names to handler functions."""

    def __init__(self, module_names: Optional[Sequence[str]] = None) -> None:
        self.operations: Dict[str, Handler] = {}
        self.unavailable_modules: Dict[str, str] = {}
        self.collisions: List[str] = []

        if module_names is None:
            module_names = HANDLER_MODULES + EXTENSION_MODULES
        for module_name in module_names:
            self._register(module_name)

    def _register(self, module_name: str) -> None:
        """Discover the handlers of one module, tolerating an unusable module."""
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            self.unavailable_modules[module_name] = f"{type(exc).__name__}: {exc}"
            return

        for member_name in dir(module):
            if not member_name.startswith(HANDLER_PREFIX):
                continue
            handler = getattr(module, member_name)
            if not callable(handler):
                continue

            operation = member_name[len(HANDLER_PREFIX):]
            if operation in self.operations:
                self.collisions.append(f"{operation} (ignored in {module_name})")
                continue
            self.operations[operation] = handler

    def dispatch(self, operation: str, args: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Run one operation and return its response."""
        handler = self.operations.get(operation)
        if handler is None:
            return {
                "status": "error",
                "message": f"Unknown operation: {operation}",
                "available_operations": sorted(self.operations),
            }

        try:
            result = handler(args or {})
        except Exception as exc:
            return {
                "status": "error",
                "message": f"{operation} failed: {type(exc).__name__}: {exc}",
            }

        return _normalise(result)

    def diagnostics(self) -> Dict[str, Any]:
        """What was discovered, and what could not be."""
        return {
            "status": "ok",
            "operation_count": len(self.operations),
            "operations": sorted(self.operations),
            "unavailable_modules": self.unavailable_modules,
            "collisions": self.collisions,
        }


_dispatcher: Optional[CommandDispatcher] = None


def get_dispatcher() -> CommandDispatcher:
    """The process-wide dispatcher, built on first use."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = CommandDispatcher()
    return _dispatcher


def dispatch_command(operation: str, args: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Main entry point for all bridge commands."""
    return get_dispatcher().dispatch(operation, args)
