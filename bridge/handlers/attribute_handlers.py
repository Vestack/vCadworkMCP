"""
Repaired attribute handler using ControllerManager
"""
from typing import Dict, Any, List
from .base_handler import BaseHandler, validate_element_ids
from ..cadwork_api import call_cadwork_function

def handle_get_standard_attributes(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get standard attributes command"""
    try:
        element_ids = validate_element_ids(args.get("element_ids", []))
        
        results = {}
        
        # Define the standard attributes
        standard_attrs = ["name", "group", "subgroup", "comment"]
        
        for eid in element_ids:
            elem_attrs = {}
            
            # Retrieve the standard attributes
            for attr_key in standard_attrs:
                try:
                    value = call_cadwork_function(f'get_{attr_key}', eid)
                    elem_attrs[attr_key] = value
                except Exception:
                    elem_attrs[attr_key] = None
            
            # Retrieve the material
            try:
                material_name = call_cadwork_function('get_element_material_name', eid)
                elem_attrs['material'] = material_name if material_name else None
            except Exception:
                elem_attrs['material'] = None
            
            results[eid] = elem_attrs
        
        return {"status": "ok", "attributes_by_id": results}
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_user_attributes(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get user attributes command"""
    try:
        element_ids = validate_element_ids(args.get("element_ids", []))
        attr_numbers = args.get("attribute_numbers", [])
        
        if not isinstance(attr_numbers, list):
            raise ValueError("attribute_numbers must be a list")
        
        # Validate the attribute numbers
        attr_numbers = [int(num) for num in attr_numbers]
        if not all(num > 0 for num in attr_numbers):
            raise ValueError("Attribute numbers must be positive integers")
        
        if not element_ids or not attr_numbers:
            return {"status": "ok", "user_attributes_by_id": {}}
        
        results = {}
        
        for eid in element_ids:
            user_attrs = {}
            for num in attr_numbers:
                try:
                    value = call_cadwork_function('get_user_attribute', eid, num)
                    user_attrs[num] = value
                except Exception:
                    user_attrs[num] = None
            
            results[eid] = user_attrs
        
        return {"status": "ok", "user_attributes_by_id": results}
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_list_defined_user_attributes(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle list defined user attributes command"""
    try:
        defined_attributes = {}
        
        # Check attributes 1-100
        for i in range(1, 101):
            try:
                name = call_cadwork_function('get_user_attribute_name', i)
                if name:
                    defined_attributes[i] = name
            except AttributeError:
                return {
                    "status": "error", 
                    "message": "Function get_user_attribute_name not available"
                }
            except Exception:
                continue  # Skip this attribute number
        
        return {"status": "ok", "defined_attributes": defined_attributes}
        
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

# --- ATTRIBUTE SETTER FUNCTIONS ---

def handle_set_name(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle set name command"""
    try:
        element_ids = validate_element_ids(args.get("element_ids", []))
        name = args.get("name", "")
        
        if not isinstance(name, str):
            raise ValueError("name must be a string")
        
        # Verwende Controller Manager
        call_cadwork_function('set_name', element_ids, name)
        
        return {
            "status": "ok", 
            "message": f"Name '{name}' set for {len(element_ids)} elements",
            "element_ids": element_ids
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_set_material(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle set material command"""
    try:
        element_ids = validate_element_ids(args.get("element_ids", []))
        material = args.get("material", "")
        
        if not isinstance(material, str):
            raise ValueError("material must be a string")
        
        # Verwende Controller Manager
        call_cadwork_function('set_material', element_ids, material)
        
        return {
            "status": "ok", 
            "message": f"Material '{material}' set for {len(element_ids)} elements",
            "element_ids": element_ids
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_set_group(aParams: dict) -> dict:
    """Sets the group for elements"""
    try:
        lElementIds = validate_element_ids(aParams.get("element_ids", []))
        lGroup = aParams.get("group")
        
        if lGroup is None:
            return {"status": "error", "message": "No group name provided"}
        
        # Verwende Controller Manager
        call_cadwork_function('set_group', lElementIds, lGroup)
        
        return {
            "status": "success",
            "message": f"Group '{lGroup}' set for {len(lElementIds)} elements",
            "element_ids": lElementIds,
            "group": lGroup
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"set_group failed: {e}"}

def handle_set_comment(aParams: dict) -> dict:
    """Sets the comment for elements"""
    try:
        lElementIds = validate_element_ids(aParams.get("element_ids", []))
        lComment = aParams.get("comment")
        
        if lComment is None:
            return {"status": "error", "message": "No comment text provided"}
        
        # Verwende Controller Manager
        call_cadwork_function('set_comment', lElementIds, lComment)
        
        return {
            "status": "success",
            "message": f"Comment '{lComment}' set for {len(lElementIds)} elements",
            "element_ids": lElementIds,
            "comment": lComment
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"set_comment failed: {e}"}

def handle_set_subgroup(aParams: dict) -> dict:
    """Sets the subgroup for elements"""
    try:
        lElementIds = validate_element_ids(aParams.get("element_ids", []))
        lSubgroup = aParams.get("subgroup")
        
        if lSubgroup is None:
            return {"status": "error", "message": "No subgroup name provided"}
        
        # Verwende Controller Manager
        call_cadwork_function('set_subgroup', lElementIds, lSubgroup)
        
        return {
            "status": "success",
            "message": f"Subgroup '{lSubgroup}' set for {len(lElementIds)} elements",
            "element_ids": lElementIds,
            "subgroup": lSubgroup
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"set_subgroup failed: {e}"}

def handle_set_user_attribute(args: Dict[str, Any]) -> Dict[str, Any]:
    """Sets a user-defined attribute for elements"""
    try:
        element_ids = validate_element_ids(args.get("element_ids", []))
        attribute_number = args.get("attribute_number")
        attribute_value = args.get("attribute_value", "")
        
        if attribute_number is None:
            return {"status": "error", "message": "No attribute number provided"}
        
        attribute_number = int(attribute_number)
        if attribute_number <= 0:
            return {"status": "error", "message": "Attribute number must be positive"}
        
        # Verwende Controller Manager
        for eid in element_ids:
            call_cadwork_function('set_user_attribute', eid, attribute_number, str(attribute_value))
        
        return {
            "status": "success",
            "message": f"User attribute {attribute_number} set to '{attribute_value}' for {len(element_ids)} elements",
            "element_ids": element_ids,
            "attribute_number": attribute_number,
            "attribute_value": attribute_value
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"set_user_attribute failed: {e}"}

# Further attribute handlers can be added here...
def handle_get_element_attribute_display_name(args: Dict[str, Any]) -> Dict[str, Any]:
    """Gets display name for user attribute"""
    try:
        attribute_number = int(args.get("attribute_number"))
        
        name = call_cadwork_function('get_user_attribute_name', attribute_number)
        
        return {
            "status": "success",
            "attribute_number": attribute_number,
            "display_name": name or f"Attribute_{attribute_number}"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"get_element_attribute_display_name failed: {e}"}

def handle_clear_user_attribute(args: Dict[str, Any]) -> Dict[str, Any]:
    """Clears user attribute for elements"""
    try:
        element_ids = validate_element_ids(args.get("element_ids", []))
        attribute_number = int(args.get("attribute_number"))
        
        # Clear the attribute for all elements
        for eid in element_ids:
            call_cadwork_function('set_user_attribute', eid, attribute_number, "")
        
        return {
            "status": "success",
            "message": f"User attribute {attribute_number} cleared for {len(element_ids)} elements",
            "element_ids": element_ids,
            "attribute_number": attribute_number
        }
        
    except Exception as e:
        return {"status": "error", "message": f"clear_user_attribute failed: {e}"}

def handle_copy_attributes(args: Dict[str, Any]) -> Dict[str, Any]:
    """Copies attributes between elements - Placeholder"""
    return {
        "status": "success",
        "message": "Attributes copied (placeholder)",
        "operation": "copy_attributes"
    }

def handle_batch_set_user_attributes(args: Dict[str, Any]) -> Dict[str, Any]:
    """Batch sets user attributes - Placeholder"""
    return {
        "status": "success",
        "message": "User attributes batch set (placeholder)",
        "operation": "batch_set_user_attributes"
    }

def handle_validate_attribute_consistency(args: Dict[str, Any]) -> Dict[str, Any]:
    """Validates attribute consistency - Placeholder"""
    return {
        "status": "success",
        "message": "Attribute consistency validated (placeholder)",
        "operation": "validate_attribute_consistency"
    }

def handle_search_elements_by_attributes(args: Dict[str, Any]) -> Dict[str, Any]:
    """Searches elements by attributes - Placeholder"""
    return {
        "status": "success",
        "message": "Elements searched by attributes (placeholder)",
        "operation": "search_elements_by_attributes"
    }

def handle_export_attribute_report(args: Dict[str, Any]) -> Dict[str, Any]:
    """Exports attribute report - Placeholder"""
    return {
        "status": "success",
        "message": "Attribute report exported (placeholder)",
        "operation": "export_attribute_report"
    }
