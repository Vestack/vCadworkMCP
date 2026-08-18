"""Router to the Cadwork API modules.

Inside Cadwork, `import attribute_controller` gives the Cadwork API. This repo
also has a `controllers/attribute_controller.py`, which is something else
entirely: an async proxy that sends a socket command to this very bridge. That
name collision is what broke the bridge before, so the resolution here is
explicit and one-way: a function name maps to exactly one Cadwork API module,
imported by its bare name at call time.

The map covers the functions the handlers actually call. Add an entry when a
handler needs a new one; there is deliberately no fallback that hunts through
modules looking for a matching name.
"""
import importlib
from typing import Any, Dict


class UnknownCadworkFunction(AttributeError):
    """Raised when a function is not mapped, or absent from its Cadwork module."""


CADWORK_FUNCTION_MODULES: Dict[str, str] = {
    # --- attribute_controller ---
    "get_name": "attribute_controller",
    "get_group": "attribute_controller",
    "get_subgroup": "attribute_controller",
    "get_comment": "attribute_controller",
    "get_element_material_name": "attribute_controller",
    "get_user_attribute": "attribute_controller",
    "get_user_attribute_name": "attribute_controller",
    "get_user_attribute_count": "attribute_controller",
    "set_name": "attribute_controller",
    "set_material": "attribute_controller",
    "set_group": "attribute_controller",
    "set_comment": "attribute_controller",
    "set_subgroup": "attribute_controller",
    "set_user_attribute": "attribute_controller",
    # --- visualization_controller ---
    "set_color": "visualization_controller",
    "get_color": "visualization_controller",
    "set_transparency": "visualization_controller",
    "get_transparency": "visualization_controller",
    "show_elements": "visualization_controller",
    "hide_elements": "visualization_controller",
    "show_all_elements": "visualization_controller",
    "hide_all_elements": "visualization_controller",
    "refresh_display": "visualization_controller",
    "get_visible_element_count": "visualization_controller",
}


def call_cadwork_function(function_name: str, *args: Any, **kwargs: Any) -> Any:
    """Call one Cadwork API function by name.

    Raises:
        UnknownCadworkFunction: the name is unmapped, or the Cadwork module in
            this version does not provide it.
        ImportError: the Cadwork module is unavailable, i.e. this is not running
            inside Cadwork.
    """
    module_name = CADWORK_FUNCTION_MODULES.get(function_name)
    if module_name is None:
        raise UnknownCadworkFunction(
            f"'{function_name}' is not mapped to a Cadwork API module. "
            f"Add it to CADWORK_FUNCTION_MODULES in bridge/cadwork_api.py."
        )

    module = importlib.import_module(module_name)
    function = getattr(module, function_name, None)
    if function is None:
        raise UnknownCadworkFunction(
            f"Cadwork module '{module_name}' has no '{function_name}' in this "
            f"version. Check https://docs.cadwork.com/projects/cwapi3dpython/."
        )

    return function(*args, **kwargs)
