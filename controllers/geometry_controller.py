"""
Geometry controller for geometry operations
"""
from typing import Dict, Any, List, Optional
from .base_controller import BaseController

class GeometryController(BaseController):
    """Controller for geometry operations"""
    
    def __init__(self) -> None:
        super().__init__("GeometryController")
    
    async def get_element_info(self, element_id: int) -> Dict[str, Any]:
        """Get detailed element information - proxy to ElementController"""
        from .element_controller import ElementController
        element_controller = ElementController()
        return await element_controller.get_element_info(element_id)
    
    async def get_element_width(self, element_id: int) -> Dict[str, Any]:
        """Get element width"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_width", {"element_id": element_id})
    
    async def get_element_height(self, element_id: int) -> Dict[str, Any]:
        """Get element height"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_height", {"element_id": element_id})
    
    async def get_element_length(self, element_id: int) -> Dict[str, Any]:
        """Get element length"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_length", {"element_id": element_id})
    
    async def get_element_volume(self, element_id: int) -> Dict[str, Any]:
        """Get element volume"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_volume", {"element_id": element_id})
    
    async def get_element_weight(self, element_id: int) -> Dict[str, Any]:
        """Get element weight"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_weight", {"element_id": element_id})
    
    async def get_element_xl(self, element_id: int) -> Dict[str, Any]:
        """Get element XL vector (length direction)"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_xl", {"element_id": element_id})
    
    async def get_element_yl(self, element_id: int) -> Dict[str, Any]:
        """Get element YL vector (width direction)"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_yl", {"element_id": element_id})
    
    async def get_element_zl(self, element_id: int) -> Dict[str, Any]:
        """Get element ZL vector (height direction)"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_zl", {"element_id": element_id})
    
    async def get_element_p1(self, element_id: int) -> Dict[str, Any]:
        """Get element P1 point (start point)"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_p1", {"element_id": element_id})
    
    async def get_element_p2(self, element_id: int) -> Dict[str, Any]:
        """Get element P2 point (end point)"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_p2", {"element_id": element_id})
    
    async def get_element_p3(self, element_id: int) -> Dict[str, Any]:
        """Get element P3 point (orientation point)"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_p3", {"element_id": element_id})
    
    async def get_center_of_gravity(self, element_id: int) -> Dict[str, Any]:
        """Get center of gravity for a single element"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_center_of_gravity", {"element_id": element_id})
    
    async def get_center_of_gravity_for_list(self, element_ids: list) -> Dict[str, Any]:
        """Get center of gravity for multiple elements combined"""
        if not isinstance(element_ids, list):
            raise ValueError("element_ids must be a list")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        return self.send_command("get_center_of_gravity_for_list", {"element_ids": validated_ids})
    
    async def get_element_vertices(self, element_id: int) -> Dict[str, Any]:
        """Get all vertices (corner points) of an element"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_vertices", {"element_id": element_id})
    
    async def get_minimum_distance_between_elements(self, first_element_id: int, second_element_id: int) -> Dict[str, Any]:
        """Get minimum distance between two elements"""
        first_element_id = self.validate_element_id(first_element_id)
        second_element_id = self.validate_element_id(second_element_id)
        
        return self.send_command("get_minimum_distance_between_elements", {
            "first_element_id": first_element_id,
            "second_element_id": second_element_id
        })

    async def get_closest_point_on_element(self, element_id: int, reference_point: List[float]) -> Dict[str, Any]:
        """Get the closest point on an element to a reference point"""
        try:
            element_id = self.validate_element_id(element_id)
            validated_point = self.validate_point_3d(reference_point, "reference_point")
            
            if validated_point is None:
                return {"status": "error", "message": "reference_point must be valid 3D coordinates"}
            
            return self.send_command("get_closest_point_on_element", {
                "element_id": element_id,
                "reference_point": validated_point
            })
            
        except ValueError as e:
            return {"status": "error", "message": f"Invalid input: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"get_closest_point_on_element failed: {e}"}
    
    async def get_element_facets(self, element_id: int) -> Dict[str, Any]:
        """Get all facets (faces) of an element"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_facets", {"element_id": element_id})
    
    async def get_element_reference_face_area(self, element_id: int) -> Dict[str, Any]:
        """Get reference face area of an element"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_element_reference_face_area", {"element_id": element_id})
    
    async def get_total_area_of_all_faces(self, element_id: int) -> Dict[str, Any]:
        """Get total surface area of all faces of an element"""
        element_id = self.validate_element_id(element_id)
        return self.send_command("get_total_area_of_all_faces", {"element_id": element_id})
    
    async def rotate_elements(self, element_ids: list, origin: list, rotation_axis: list, rotation_angle: float) -> Dict[str, Any]:
        """Rotate elements around an axis"""
        if not isinstance(element_ids, list):
            raise ValueError("element_ids must be a list")
        if not isinstance(origin, list) or len(origin) != 3:
            raise ValueError("origin must be a list of 3 numbers [x, y, z]")
        if not isinstance(rotation_axis, list) or len(rotation_axis) != 3:
            raise ValueError("rotation_axis must be a list of 3 numbers [x, y, z]")
        if not isinstance(rotation_angle, (int, float)):
            raise ValueError("rotation_angle must be a number")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        return self.send_command("rotate_elements", {
            "element_ids": validated_ids,
            "origin": origin,
            "rotation_axis": rotation_axis,
            "rotation_angle": float(rotation_angle)
        })
    
    async def apply_global_scale(self, element_ids: list, scale: float, origin: list) -> Dict[str, Any]:
        """Apply global scaling to elements"""
        if not isinstance(element_ids, list):
            raise ValueError("element_ids must be a list")
        if not isinstance(scale, (int, float)) or scale <= 0:
            raise ValueError("scale must be a positive number")
        if not isinstance(origin, list) or len(origin) != 3:
            raise ValueError("origin must be a list of 3 numbers [x, y, z]")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        return self.send_command("apply_global_scale", {
            "element_ids": validated_ids,
            "scale": float(scale),
            "origin": origin
        })
    
    async def invert_model(self, element_ids: list) -> Dict[str, Any]:
        """Invert/mirror elements"""
        if not isinstance(element_ids, list):
            raise ValueError("element_ids must be a list")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        return self.send_command("invert_model", {"element_ids": validated_ids})
    
    async def rotate_height_axis_90(self, element_ids: list) -> Dict[str, Any]:
        """Rotate element height axis by 90 degrees"""
        if not isinstance(element_ids, list):
            raise ValueError("element_ids must be a list")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        return self.send_command("rotate_height_axis_90", {"element_ids": validated_ids})
    
    async def rotate_length_axis_90(self, element_ids: list) -> Dict[str, Any]:
        """Rotate element length axis by 90 degrees"""
        if not isinstance(element_ids, list):
            raise ValueError("element_ids must be a list")
        
        # Validate all element IDs
        validated_ids = [self.validate_element_id(eid) for eid in element_ids]
        
        return self.send_command("rotate_length_axis_90", {"element_ids": validated_ids})
    
    async def get_element_type(self, aElementId: int) -> dict:
        """
        Retrieves the type of a cadwork element
        
        Args:
            aElementId: Element-ID
        
        Returns:
            dict: Element-Typ Information (beam, panel, drilling, etc.)
        """
        try:
            # Validierung
            lValidatedId = self.validate_element_id(aElementId)
            
            # Command senden
            return self.send_command("get_element_type", {
                "element_id": lValidatedId
            })
            
        except Exception as e:
            return {"status": "error", "message": f"get_element_type failed: {e}"}
    
    async def calculate_total_volume(self, aElementIds: list) -> dict:
        """
        Calculates the total volume of a list of elements
        
        Args:
            aElementIds: list of element IDs
        
        Returns:
            dict: total volume in mm³ and other units
        """
        try:
            # Validierung
            if not isinstance(aElementIds, list) or not aElementIds:
                return {"status": "error", "message": "element_ids must be a non-empty list"}
            
            lValidatedIds = [self.validate_element_id(lId) for lId in aElementIds]
            
            # Command senden
            return self.send_command("calculate_total_volume", {
                "element_ids": lValidatedIds
            })
            
        except Exception as e:
            return {"status": "error", "message": f"calculate_total_volume failed: {e}"}
    
    async def calculate_total_weight(self, aElementIds: list) -> dict:
        """
        Calculates the total weight of a list of elements
        
        Args:
            aElementIds: list of element IDs
        
        Returns:
            dict: total weight in kg and other units
        """
        try:
            # Validierung
            if not isinstance(aElementIds, list) or not aElementIds:
                return {"status": "error", "message": "element_ids must be a non-empty list"}
            
            lValidatedIds = [self.validate_element_id(lId) for lId in aElementIds]
            
            # Command senden
            return self.send_command("calculate_total_weight", {
                "element_ids": lValidatedIds
            })
            
        except Exception as e:
            return {"status": "error", "message": f"calculate_total_weight failed: {e}"}
    
    async def get_bounding_box(self, element_id: int) -> Dict[str, Any]:
        """Get the bounding box (min/max coordinates) of an element"""
        try:
            validated_id = self.validate_element_id(element_id)
            
            return self.send_command("get_bounding_box", {
                "element_id": validated_id
            })
            
        except Exception as e:
            return {"status": "error", "message": f"get_bounding_box failed: {e}"}
    
    async def get_element_outline(self, element_id: int) -> Dict[str, Any]:
        """Get the 2D outline/contour of an element projected to a plane"""
        try:
            validated_id = self.validate_element_id(element_id)
            
            return self.send_command("get_element_outline", {
                "element_id": validated_id
            })
            
        except Exception as e:
            return {"status": "error", "message": f"get_element_outline failed: {e}"}
    
    async def get_section_outline(self, element_id: int, section_plane_point: List[float], 
                                section_plane_normal: List[float]) -> Dict[str, Any]:
        """Get the outline of an element cut by a section plane"""
        try:
            validated_id = self.validate_element_id(element_id)
            
            if not isinstance(section_plane_point, list) or len(section_plane_point) != 3:
                return {"status": "error", "message": "section_plane_point must be a list of 3 coordinates [x,y,z]"}
            
            if not isinstance(section_plane_normal, list) or len(section_plane_normal) != 3:
                return {"status": "error", "message": "section_plane_normal must be a list of 3 coordinates [x,y,z]"}
            
            validated_point = [float(coord) for coord in section_plane_point]
            validated_normal = [float(coord) for coord in section_plane_normal]
            
            # Check if normal vector is not zero
            normal_length = sum(coord ** 2 for coord in validated_normal) ** 0.5
            if normal_length < 1e-10:
                return {"status": "error", "message": "section_plane_normal cannot be a zero vector"}
            
            args = {
                "element_id": validated_id,
                "section_plane_point": validated_point,
                "section_plane_normal": validated_normal
            }
            
            return self.send_command("get_section_outline", args)
            
        except Exception as e:
            return {"status": "error", "message": f"get_section_outline failed: {e}"}
    
    async def intersect_elements(self, element_ids: List[int], 
                               keep_originals: bool = True) -> Dict[str, Any]:
        """Intersect multiple elements to create new elements from their common volume"""
        try:
            if not isinstance(element_ids, list) or len(element_ids) < 2:
                return {"status": "error", "message": "element_ids must be a list with at least 2 element IDs"}
            
            if not isinstance(keep_originals, bool):
                return {"status": "error", "message": "keep_originals must be a boolean value"}
            
            validated_ids = [self.validate_element_id(eid) for eid in element_ids]
            
            args = {
                "element_ids": validated_ids,
                "keep_originals": keep_originals
            }
            
            return self.send_command("intersect_elements", args)
            
        except Exception as e:
            return {"status": "error", "message": f"intersect_elements failed: {e}"}
    
    async def subtract_elements(self, target_element_id: int, 
                              subtract_element_ids: List[int],
                              keep_originals: bool = False) -> Dict[str, Any]:
        """Subtract elements from a target element (Boolean difference operation)
        
        Args:
            target_element_id: ID of the element to subtract from
            subtract_element_ids: List of element IDs to subtract from the target
            keep_originals: Whether to keep the original elements after subtraction
        
        Returns:
            Dictionary with operation status and resulting element IDs if successful
        """
        try:
            if not isinstance(subtract_element_ids, list) or len(subtract_element_ids) < 1:
                return {"status": "error", "message": "subtract_element_ids must be a list with at least 1 element ID"}
            
            if not isinstance(keep_originals, bool):
                return {"status": "error", "message": "keep_originals must be a boolean value"}
            
            validated_target_id = self.validate_element_id(target_element_id)
            validated_subtract_ids = [self.validate_element_id(eid) for eid in subtract_element_ids]
            
            # Check that target is not in subtract list
            if validated_target_id in validated_subtract_ids:
                return {"status": "error", "message": "target_element_id cannot be in subtract_element_ids list"}
            
            args = {
                "target_element_id": validated_target_id,
                "subtract_element_ids": validated_subtract_ids,
                "keep_originals": keep_originals
            }
            
            return self.send_command("subtract_elements", args)
            
        except Exception as e:
            return {"status": "error", "message": f"subtract_elements failed: {e}"}
    
    async def unite_elements(self, element_ids: List[int], 
                           keep_originals: bool = False) -> Dict[str, Any]:
        """Unite/merge multiple elements into one (Boolean union operation)
        
        Args:
            element_ids: List of element IDs to unite (minimum 2 elements)
            keep_originals: Whether to keep the original elements after union
        
        Returns:
            Dictionary with operation status and resulting element ID if successful
        """
        try:
            if not isinstance(element_ids, list) or len(element_ids) < 2:
                return {"status": "error", "message": "element_ids must be a list with at least 2 element IDs"}
            
            if not isinstance(keep_originals, bool):
                return {"status": "error", "message": "keep_originals must be a boolean value"}
            
            validated_ids = [self.validate_element_id(eid) for eid in element_ids]
            
            # Check for duplicate IDs
            if len(set(validated_ids)) != len(validated_ids):
                return {"status": "error", "message": "Duplicate element IDs found in unite list"}
            
            args = {
                "element_ids": validated_ids,
                "keep_originals": keep_originals
            }
            
            return self.send_command("unite_elements", args)
            
        except Exception as e:
            return {"status": "error", "message": f"unite_elements failed: {e}"}
    
    async def project_point_to_element(self, point: List[float], element_id: int) -> Dict[str, Any]:
        """Project a 3D point onto an element surface and find closest point"""
        try:
            # Validate input parameters
            validated_point = self.validate_point_3d(point, "point")
            if validated_point is None:
                return {"status": "error", "message": "Point coordinates are required"}
                
            validated_element_id = self.validate_element_id(element_id)
            
            args = {
                "point": validated_point,
                "element_id": validated_element_id
            }
            
            return self.send_command("project_point_to_element", args)
            
        except Exception as e:
            return {"status": "error", "message": f"project_point_to_element failed: {e}"}

    async def calculate_center_of_mass(self, element_ids: List[int], include_material_properties: bool = True) -> Dict[str, Any]:
        """Calculate center of mass for a list of elements considering their material properties"""
        try:
            # Validate element IDs
            if not isinstance(element_ids, list) or len(element_ids) == 0:
                return {"status": "error", "message": "element_ids must be a non-empty list"}
            
            validated_ids = []
            for element_id in element_ids:
                validated_id = self.validate_element_id(element_id)
                validated_ids.append(validated_id)
            
            # Validate include_material_properties parameter
            if not isinstance(include_material_properties, bool):
                include_material_properties = True
            
            return self.send_command("calculate_center_of_mass", {
                "element_ids": validated_ids,
                "include_material_properties": include_material_properties
            })
            
        except ValueError as e:
            return {"status": "error", "message": f"Invalid input: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"calculate_center_of_mass failed: {e}"}
    
    async def check_collisions(self, element_ids: List[int], tolerance: float = 0.1) -> Dict[str, Any]:
        """Check for collisions between elements with specified tolerance"""
        try:
            # Validate element IDs
            validated_ids = [self.validate_element_id(eid) for eid in element_ids]
            
            if len(validated_ids) < 2:
                return {"status": "error", "message": "At least 2 elements required for collision check"}
            
            # Validate tolerance
            if tolerance < 0:
                return {"status": "error", "message": "Tolerance must be non-negative"}
            
            return self.send_command("check_collisions", {
                "element_ids": validated_ids,
                "tolerance": tolerance
            })
            
        except ValueError as e:
            return {"status": "error", "message": f"Invalid input: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"check_collisions failed: {e}"}
    
    async def validate_joints(self, 
                            element_ids: List[int],
                            joint_type: str = "auto",
                            load_conditions: Optional[Dict[str, Any]] = None,
                            safety_factor: float = 2.0,
                            wood_grade: str = "C24") -> Dict[str, Any]:
        """
        Validate joints between elements for structural integrity and feasibility
        
        Args:
            element_ids: List of element IDs to check joints between
            joint_type: Type of joint to validate (auto, mortise_tenon, lap_joint, dovetail, custom)
            load_conditions: Load conditions dict with forces and moments
            safety_factor: Safety factor for calculations (default 2.0)
            wood_grade: Wood grade for strength calculations (C24, C30, GL24h, etc.)
        
        Returns:
            dict: Joint validation results with strength analysis
        """
        try:
            # Validate element IDs
            if not isinstance(element_ids, list) or len(element_ids) < 2:
                return {"status": "error", "message": "At least 2 elements required for joint validation"}
            
            validated_ids = [self.validate_element_id(eid) for eid in element_ids]
            
            # Validate joint_type
            valid_joint_types = ["auto", "mortise_tenon", "lap_joint", "dovetail", "scarf_joint", "custom"]
            if joint_type not in valid_joint_types:
                return {"status": "error", "message": f"Invalid joint_type. Must be one of: {valid_joint_types}"}
            
            # Validate safety_factor
            if not isinstance(safety_factor, (int, float)) or safety_factor <= 0:
                return {"status": "error", "message": "safety_factor must be a positive number"}
            
            # Validate wood_grade
            valid_wood_grades = ["C16", "C20", "C24", "C27", "C30", "C35", "C40", "GL24h", "GL28h", "GL32h"]
            if wood_grade not in valid_wood_grades:
                return {"status": "error", "message": f"Invalid wood_grade. Must be one of: {valid_wood_grades}"}
            
            # Validate load_conditions if provided
            if load_conditions is not None:
                if not isinstance(load_conditions, dict):
                    return {"status": "error", "message": "load_conditions must be a dictionary"}
                
                # Check for required load condition keys
                valid_load_keys = ["normal_force", "shear_force", "moment", "torsion", "load_duration"]
                for key in load_conditions.keys():
                    if key not in valid_load_keys:
                        return {"status": "error", "message": f"Invalid load condition key '{key}'. Valid keys: {valid_load_keys}"}
            
            return self.send_command("validate_joints", {
                "element_ids": validated_ids,
                "joint_type": joint_type,
                "load_conditions": load_conditions or {},
                "safety_factor": float(safety_factor),
                "wood_grade": wood_grade
            })
            
        except ValueError as e:
            return {"status": "error", "message": f"Invalid input: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"validate_joints failed: {e}"}
