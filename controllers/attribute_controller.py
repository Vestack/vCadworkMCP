"""
Attribute controller for attribute operations
"""
from typing import Dict, Any, List, Optional
from .base_controller import BaseController

class AttributeController(BaseController):
    """Controller for attribute operations"""
    
    def __init__(self) -> None:
        super().__init__("AttributeController")
    
    async def get_standard_attributes(self, element_ids: List[int]) -> Dict[str, Any]:
        """Get standard attributes for elements"""
        if not isinstance(element_ids, list):
            raise ValueError("element_ids must be a list")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        return self.send_command("get_standard_attributes", {"element_ids": validated_ids})
    
    async def get_user_attributes(self, element_ids: List[int], 
                                 attribute_numbers: List[int]) -> Dict[str, Any]:
        """Get user attributes for elements"""
        if not isinstance(element_ids, list):
            raise ValueError("element_ids must be a list")
        if not isinstance(attribute_numbers, list):
            raise ValueError("attribute_numbers must be a list")
        
        # Validate element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        # Validate attribute numbers
        validated_attrs = []
        for num in attribute_numbers:
            try:
                attr_num = int(num)
                if attr_num <= 0:
                    raise ValueError(f"Attribute number must be positive: {attr_num}")
                validated_attrs.append(attr_num)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid attribute number: {num}")
        
        return self.send_command("get_user_attributes", {
            "element_ids": validated_ids,
            "attribute_numbers": validated_attrs
        })
    
    async def list_defined_user_attributes(self) -> Dict[str, Any]:
        """List all defined user attributes"""
        return self.send_command("list_defined_user_attributes")
    
    # --- ATTRIBUTE SETTERS ---
    
    async def set_name(self, element_ids: List[int], name: str) -> Dict[str, Any]:
        """Set name for elements"""
        if not isinstance(element_ids, list):
            raise ValueError("element_ids must be a list")
        if not isinstance(name, str):
            raise ValueError("name must be a string")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        return self.send_command("set_name", {
            "element_ids": validated_ids,
            "name": str(name)
        })
    
    async def set_material(self, element_ids: List[int], material: str) -> Dict[str, Any]:
        """Set material for elements"""
        if not isinstance(element_ids, list):
            raise ValueError("element_ids must be a list")
        if not isinstance(material, str):
            raise ValueError("material must be a string")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        return self.send_command("set_material", {
            "element_ids": validated_ids,
            "material": str(material)
        })
    
    async def set_group(self, aElementIds: list, aGroup: str) -> dict:
        """
        Sets the group for a list of elements
        
        Args:
            aElementIds: list of element IDs
            aGroup: Gruppen-Name (String)
        
        Returns:
            dict: status of the operation
        """
        try:
            # Validierung
            if not isinstance(aElementIds, list) or not aElementIds:
                return {"status": "error", "message": "element_ids must be a non-empty list"}
            
            lValidatedIds = [self.validate_element_id(lId) for lId in aElementIds]
            
            if not isinstance(aGroup, str):
                return {"status": "error", "message": "group must be a string"}
            
            # Command senden
            return self.send_command("set_group", {
                "element_ids": lValidatedIds,
                "group": aGroup
            })
            
        except Exception as e:
            return {"status": "error", "message": f"set_group failed: {e}"}
    
    async def set_comment(self, aElementIds: list, aComment: str) -> dict:
        """
        Sets the comment for a list of elements
        
        Args:
            aElementIds: list of element IDs
            aComment: Kommentar-Text (String)
        
        Returns:
            dict: status of the operation
        """
        try:
            # Validierung
            if not isinstance(aElementIds, list) or not aElementIds:
                return {"status": "error", "message": "element_ids must be a non-empty list"}
            
            lValidatedIds = [self.validate_element_id(lId) for lId in aElementIds]
            
            if not isinstance(aComment, str):
                return {"status": "error", "message": "comment must be a string"}
            
            # Command senden
            return self.send_command("set_comment", {
                "element_ids": lValidatedIds,
                "comment": aComment
            })
            
        except Exception as e:
            return {"status": "error", "message": f"set_comment failed: {e}"}
    
    async def set_subgroup(self, aElementIds: list, aSubgroup: str) -> dict:
        """
        Sets the subgroup for a list of elements
        
        Args:
            aElementIds: list of element IDs
            aSubgroup: Untergruppen-Name (String)
        
        Returns:
            dict: status of the operation
        """
        try:
            # Validierung
            if not isinstance(aElementIds, list) or not aElementIds:
                return {"status": "error", "message": "element_ids must be a non-empty list"}
            
            lValidatedIds = [self.validate_element_id(lId) for lId in aElementIds]
            
            if not isinstance(aSubgroup, str):
                return {"status": "error", "message": "subgroup must be a string"}
            
            # Command senden
            return self.send_command("set_subgroup", {
                "element_ids": lValidatedIds,
                "subgroup": aSubgroup
            })
            
        except Exception as e:
            return {"status": "error", "message": f"set_subgroup failed: {e}"}
    
    async def set_user_attribute(self, element_ids: List[int], attribute_number: int, attribute_value: str) -> Dict[str, Any]:
        """Set user-defined attribute for elements"""
        if not isinstance(element_ids, list) or not element_ids:
            raise ValueError("element_ids must be a non-empty list")
        
        if not isinstance(attribute_value, str):
            raise ValueError("attribute_value must be a string")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        # Validate attribute number
        try:
            attr_num = int(attribute_number)
            if attr_num <= 0:
                raise ValueError(f"Attribute number must be positive: {attr_num}")
        except (ValueError, TypeError):
            raise ValueError(f"Invalid attribute number: {attribute_number}")
        
        args: Dict[str, Any] = {
            "element_ids": validated_ids,
            "attribute_number": attr_num,
            "attribute_value": str(attribute_value)
        }
        
        return self.send_command("set_user_attribute", args)
    
    async def get_element_attribute_display_name(self, attribute_number: int) -> Dict[str, Any]:
        """Get display name for a user-defined attribute number"""
        # Validate attribute number
        try:
            attr_num = int(attribute_number)
            if attr_num <= 0:
                raise ValueError(f"Attribute number must be positive: {attr_num}")
        except (ValueError, TypeError):
            raise ValueError(f"Invalid attribute number: {attribute_number}")
        
        args: Dict[str, Any] = {
            "attribute_number": attr_num
        }
        
        return self.send_command("get_element_attribute_display_name", args)
    
    async def clear_user_attribute(self, element_ids: List[int], attribute_number: int) -> Dict[str, Any]:
        """Clear/delete user-defined attribute for elements"""
        if not isinstance(element_ids, list) or not element_ids:
            raise ValueError("element_ids must be a non-empty list")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        # Validate attribute number
        try:
            attr_num = int(attribute_number)
            if attr_num <= 0:
                raise ValueError(f"Attribute number must be positive: {attr_num}")
        except (ValueError, TypeError):
            raise ValueError(f"Invalid attribute number: {attribute_number}")
        
        args: Dict[str, Any] = {
            "element_ids": validated_ids,
            "attribute_number": attr_num
        }
        
        return self.send_command("clear_user_attribute", args)
    
    async def copy_attributes(self, source_element_id: int, target_element_ids: List[int], 
                            copy_user_attributes: bool = True, copy_standard_attributes: bool = True) -> Dict[str, Any]:
        """Copy attributes from source element to target elements"""
        # Validate source element ID
        validated_source = self.validate_element_id(source_element_id)
        
        if not isinstance(target_element_ids, list) or not target_element_ids:
            raise ValueError("target_element_ids must be a non-empty list")
        
        # Validate all target element IDs
        validated_targets = [self.validate_element_id(eid) for eid in target_element_ids]
        
        # Validate boolean flags
        if not isinstance(copy_user_attributes, bool):
            raise ValueError("copy_user_attributes must be a boolean")
        if not isinstance(copy_standard_attributes, bool):
            raise ValueError("copy_standard_attributes must be a boolean")
        
        # At least one type of attributes must be copied
        if not copy_user_attributes and not copy_standard_attributes:
            raise ValueError("At least one of copy_user_attributes or copy_standard_attributes must be True")
        
        args: Dict[str, Any] = {
            "source_element_id": validated_source,
            "target_element_ids": validated_targets,
            "copy_user_attributes": copy_user_attributes,
            "copy_standard_attributes": copy_standard_attributes
        }
        
        return self.send_command("copy_attributes", args)
    
    async def batch_set_user_attributes(self, element_ids: List[int], 
                                      attribute_mappings: Dict[int, str]) -> Dict[str, Any]:
        """Set multiple user-defined attributes for elements in a single operation"""
        if not isinstance(element_ids, list) or not element_ids:
            raise ValueError("element_ids must be a non-empty list")
        
        if not isinstance(attribute_mappings, dict) or not attribute_mappings:
            raise ValueError("attribute_mappings must be a non-empty dictionary")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        # Validate attribute mappings
        validated_mappings: Dict[int, str] = {}
        for attr_num, attr_value in attribute_mappings.items():
            # Validate attribute number
            try:
                validated_attr_num = int(attr_num)
                if validated_attr_num <= 0:
                    raise ValueError(f"Attribute number must be positive: {validated_attr_num}")
            except (ValueError, TypeError):
                raise ValueError(f"Invalid attribute number: {attr_num}")
            
            # Validate attribute value
            if not isinstance(attr_value, str):
                raise ValueError(f"Attribute value must be a string, got: {type(attr_value)} for attribute {attr_num}")
            
            validated_mappings[validated_attr_num] = str(attr_value)
        
        args: Dict[str, Any] = {
            "element_ids": validated_ids,
            "attribute_mappings": validated_mappings
        }
        
        return self.send_command("batch_set_user_attributes", args)
    
    async def validate_attribute_consistency(self, element_ids: List[int], 
                                           attribute_numbers: List[int],
                                           check_completeness: bool = True,
                                           check_uniqueness: bool = False) -> Dict[str, Any]:
        """Validate attribute consistency across multiple elements"""
        if not isinstance(element_ids, list) or not element_ids:
            raise ValueError("element_ids must be a non-empty list")
        
        if not isinstance(attribute_numbers, list) or not attribute_numbers:
            raise ValueError("attribute_numbers must be a non-empty list")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        # Validate attribute numbers
        validated_attrs = []
        for num in attribute_numbers:
            try:
                attr_num = int(num)
                if attr_num <= 0:
                    raise ValueError(f"Attribute number must be positive: {attr_num}")
                validated_attrs.append(attr_num)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid attribute number: {num}")
        
        # Validate boolean flags
        if not isinstance(check_completeness, bool):
            raise ValueError("check_completeness must be a boolean")
        if not isinstance(check_uniqueness, bool):
            raise ValueError("check_uniqueness must be a boolean")
        
        # At least one check must be enabled
        if not check_completeness and not check_uniqueness:
            raise ValueError("At least one of check_completeness or check_uniqueness must be True")
        
        args: Dict[str, Any] = {
            "element_ids": validated_ids,
            "attribute_numbers": validated_attrs,
            "check_completeness": check_completeness,
            "check_uniqueness": check_uniqueness
        }
        
        return self.send_command("validate_attribute_consistency", args)
    
    async def search_elements_by_attributes(self, search_criteria: Dict[str, Any], 
                                          search_mode: str = "AND") -> Dict[str, Any]:
        """Search elements by attribute criteria with flexible matching"""
        if not isinstance(search_criteria, dict) or not search_criteria:
            raise ValueError("search_criteria must be a non-empty dictionary")
        
        # Validate search mode
        valid_modes = ["AND", "OR", "EXACT", "CONTAINS", "STARTS_WITH", "ENDS_WITH"]
        if search_mode.upper() not in valid_modes:
            raise ValueError(f"Invalid search_mode. Must be one of: {valid_modes}")
        
        # Validate and process search criteria
        validated_criteria: Dict[str, Any] = {}
        
        for key, value in search_criteria.items():
            # Handle different types of search criteria
            if key.startswith("user_attr_"):
                # User attribute search: user_attr_101 = "value"
                try:
                    attr_num_str = key.replace("user_attr_", "")
                    attr_num = int(attr_num_str)
                    if attr_num <= 0:
                        raise ValueError(f"Invalid user attribute number: {attr_num}")
                    validated_criteria[key] = {"type": "user_attribute", "number": attr_num, "value": str(value)}
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid user attribute key format: {key}")
                    
            elif key in ["name", "material", "group", "comment", "subgroup"]:
                # Standard attribute search
                validated_criteria[key] = {"type": "standard_attribute", "value": str(value)}
                
            elif key.startswith("dimension_"):
                # Dimension-based search: dimension_width, dimension_height, etc.
                dimension_type = key.replace("dimension_", "")
                if dimension_type not in ["width", "height", "length", "volume", "weight"]:
                    raise ValueError(f"Invalid dimension type: {dimension_type}")
                
                # Value can be single number, range, or comparison
                if isinstance(value, (int, float)):
                    validated_criteria[key] = {"type": "dimension", "dimension": dimension_type, "value": float(value), "operator": "equals"}
                elif isinstance(value, dict):
                    # Range or comparison: {"min": 100, "max": 200} or {"operator": ">=", "value": 150}
                    validated_criteria[key] = {"type": "dimension", "dimension": dimension_type, **value}
                else:
                    raise ValueError(f"Invalid dimension value format for {key}: {value}")
                    
            else:
                raise ValueError(f"Unknown search criteria key: {key}")
        
        args: Dict[str, Any] = {
            "search_criteria": validated_criteria,
            "search_mode": search_mode.upper()
        }
        
        return self.send_command("search_elements_by_attributes", args)
    
    async def export_attribute_report(self, element_ids: List[int], 
                                    report_format: str = "JSON",
                                    include_standard_attributes: bool = True,
                                    include_user_attributes: bool = True,
                                    user_attribute_numbers: Optional[List[int]] = None,
                                    include_dimensions: bool = False,
                                    group_by: Optional[str] = None) -> Dict[str, Any]:
        """Export comprehensive attribute report for elements"""
        if not isinstance(element_ids, list) or not element_ids:
            raise ValueError("element_ids must be a non-empty list")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        # Validate report format
        valid_formats = ["JSON", "CSV", "XML", "HTML", "PDF"]
        if report_format.upper() not in valid_formats:
            raise ValueError(f"Invalid report_format. Must be one of: {valid_formats}")
        
        # Validate boolean flags
        if not isinstance(include_standard_attributes, bool):
            raise ValueError("include_standard_attributes must be a boolean")
        if not isinstance(include_user_attributes, bool):
            raise ValueError("include_user_attributes must be a boolean")
        if not isinstance(include_dimensions, bool):
            raise ValueError("include_dimensions must be a boolean")
        
        # At least one type of data must be included
        if not include_standard_attributes and not include_user_attributes and not include_dimensions:
            raise ValueError("At least one of include_standard_attributes, include_user_attributes, or include_dimensions must be True")
        
        # Validate user attribute numbers if provided
        validated_user_attrs = None
        if user_attribute_numbers is not None:
            if not isinstance(user_attribute_numbers, list):
                raise ValueError("user_attribute_numbers must be a list if provided")
            validated_user_attrs = []
            for num in user_attribute_numbers:
                try:
                    attr_num = int(num)
                    if attr_num <= 0:
                        raise ValueError(f"User attribute number must be positive: {attr_num}")
                    validated_user_attrs.append(attr_num)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid user attribute number: {num}")
        
        # Validate group_by option
        valid_group_by = [None, "material", "group", "subgroup", "element_type"]
        if group_by not in valid_group_by:
            raise ValueError(f"Invalid group_by option. Must be one of: {valid_group_by}")
        
        args: Dict[str, Any] = {
            "element_ids": validated_ids,
            "report_format": report_format.upper(),
            "include_standard_attributes": include_standard_attributes,
            "include_user_attributes": include_user_attributes,
            "include_dimensions": include_dimensions
        }
        
        if validated_user_attrs is not None:
            args["user_attribute_numbers"] = validated_user_attrs
            
        if group_by is not None:
            args["group_by"] = group_by
        
        return self.send_command("export_attribute_report", args)
