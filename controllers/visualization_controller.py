"""
Visualization Controller for the vCadworkMCP server
Manages colors, transparency and visibility of elements
"""
from typing import Dict, Any, List, Optional
from .base_controller import BaseController

class VisualizationController(BaseController):
    """Controller for visualization operations"""
    
    def __init__(self) -> None:
        super().__init__("VisualizationController")
    
    async def set_color(self, element_ids: List[int], color_id: int) -> Dict[str, Any]:
        """
        Set color for a list of elements
        
        Args:
            element_ids: List of element IDs
            color_id: Color ID (1-255, see Cadwork color palette)
        
        Returns:
            dict: Status of operation
        """
        try:
            # Validation
            if not isinstance(element_ids, list) or not element_ids:
                return {"status": "error", "message": "element_ids must be a non-empty list"}
            
            validated_ids = [self.validate_element_id(eid) for eid in element_ids]
            
            if not isinstance(color_id, int) or color_id < 1 or color_id > 255:
                return {"status": "error", "message": "color_id must be an integer between 1 and 255"}
            
            # Send command
            return self.send_command("set_color", {
                "element_ids": validated_ids,
                "color_id": color_id
            })
            
        except Exception as e:
            return {"status": "error", "message": f"set_color failed: {e}"}
    
    async def set_visibility(self, element_ids: List[int], visible: bool) -> Dict[str, Any]:
        """
        Set visibility for a list of elements
        
        Args:
            element_ids: List of element IDs  
            visible: True = visible, False = hidden
        
        Returns:
            dict: Status of operation
        """
        try:
            # Validation
            if not isinstance(element_ids, list) or not element_ids:
                return {"status": "error", "message": "element_ids must be a non-empty list"}
            
            validated_ids = [self.validate_element_id(eid) for eid in element_ids]
            
            if not isinstance(visible, bool):
                return {"status": "error", "message": "visible must be a boolean (True/False)"}
            
            # Send command
            return self.send_command("set_visibility", {
                "element_ids": validated_ids,
                "visible": visible
            })
            
        except Exception as e:
            return {"status": "error", "message": f"set_visibility failed: {e}"}
    
    async def set_transparency(self, element_ids: List[int], transparency: int) -> Dict[str, Any]:
        """
        Set transparency for a list of elements
        
        Args:
            element_ids: List of element IDs
            transparency: Transparency value (0-100, 0=opaque, 100=fully transparent)
        
        Returns:
            dict: Status of operation
        """
        try:
            # Validation
            if not isinstance(element_ids, list) or not element_ids:
                return {"status": "error", "message": "element_ids must be a non-empty list"}
            
            validated_ids = [self.validate_element_id(eid) for eid in element_ids]
            
            if not isinstance(transparency, int) or transparency < 0 or transparency > 100:
                return {"status": "error", "message": "transparency must be an integer between 0 and 100"}
            
            # Send command
            return self.send_command("set_transparency", {
                "element_ids": validated_ids,
                "transparency": transparency
            })
            
        except Exception as e:
            return {"status": "error", "message": f"set_transparency failed: {e}"}
    
    async def get_color(self, element_id: int) -> Dict[str, Any]:
        """
        Get color of an element
        
        Args:
            element_id: Element ID
        
        Returns:
            dict: Color ID and color information
        """
        try:
            # Validation
            validated_id = self.validate_element_id(element_id)
            
            # Send command
            return self.send_command("get_color", {
                "element_id": validated_id
            })
            
        except Exception as e:
            return {"status": "error", "message": f"get_color failed: {e}"}
    
    async def get_transparency(self, element_id: int) -> Dict[str, Any]:
        """
        Get transparency of an element
        
        Args:
            element_id: Element ID
        
        Returns:
            dict: Transparency value (0-100)
        """
        try:
            # Validation
            validated_id = self.validate_element_id(element_id)
            
            # Send command
            return self.send_command("get_transparency", {
                "element_id": validated_id
            })
            
        except Exception as e:
            return {"status": "error", "message": f"get_transparency failed: {e}"}
    
    async def show_all_elements(self) -> Dict[str, Any]:
        """
        Make all elements in the model visible
        
        Returns:
            dict: Status of operation with count of affected elements
        """
        try:
            # Send command
            return self.send_command("show_all_elements", {})
            
        except Exception as e:
            return {"status": "error", "message": f"show_all_elements failed: {e}"}
    
    async def hide_all_elements(self) -> Dict[str, Any]:
        """
        Hide all elements in the model
        
        Returns:
            dict: Status of operation with count of affected elements
        """
        try:
            # Send command
            return self.send_command("hide_all_elements", {})
            
        except Exception as e:
            return {"status": "error", "message": f"hide_all_elements failed: {e}"}
    
    async def refresh_display(self) -> Dict[str, Any]:
        """
        Refresh display/viewport after changes
        
        Returns:
            dict: Status of display refresh
        """
        try:
            # Send command
            return self.send_command("refresh_display", {})
            
        except Exception as e:
            return {"status": "error", "message": f"refresh_display failed: {e}"}
    
    async def get_visible_element_count(self) -> Dict[str, Any]:
        """
        Get count of currently visible elements
        
        Returns:
            dict: Count of visible elements + statistics
        """
        try:
            # Send command
            return self.send_command("get_visible_element_count", {})
            
        except Exception as e:
            return {"status": "error", "message": f"get_visible_element_count failed: {e}"}
    
    async def create_visual_filter(self, filter_name: str, filter_criteria: Dict[str, Any], 
                                 visual_properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create and apply visual filter based on element attributes
        
        Args:
            filter_name: Name for the visual filter
            filter_criteria: Criteria to select elements (like search_elements_by_attributes)
            visual_properties: Visual properties to apply (color, transparency, visibility)
        
        Returns:
            dict: Status of filter creation and application
        """
        try:
            # Validate filter name
            if not isinstance(filter_name, str) or not filter_name.strip():
                return {"status": "error", "message": "filter_name must be a non-empty string"}
            
            # Validate filter criteria
            if not isinstance(filter_criteria, dict) or not filter_criteria:
                return {"status": "error", "message": "filter_criteria must be a non-empty dictionary"}
            
            # Validate visual properties
            if not isinstance(visual_properties, dict) or not visual_properties:
                return {"status": "error", "message": "visual_properties must be a non-empty dictionary"}
            
            # Validate visual properties content
            valid_visual_keys = ["color_id", "transparency", "visibility"]
            validated_visuals: Dict[str, Any] = {}
            
            for key, value in visual_properties.items():
                if key not in valid_visual_keys:
                    return {"status": "error", "message": f"Invalid visual property: {key}. Must be one of: {valid_visual_keys}"}
                
                if key == "color_id":
                    if not isinstance(value, int) or value < 1 or value > 255:
                        return {"status": "error", "message": "color_id must be an integer between 1 and 255"}
                    validated_visuals[key] = value
                    
                elif key == "transparency":
                    if not isinstance(value, int) or value < 0 or value > 100:
                        return {"status": "error", "message": "transparency must be an integer between 0 and 100"}
                    validated_visuals[key] = value
                    
                elif key == "visibility":
                    if not isinstance(value, bool):
                        return {"status": "error", "message": "visibility must be a boolean"}
                    validated_visuals[key] = value
            
            # Validate filter criteria structure (similar to search_elements_by_attributes)
            validated_criteria: Dict[str, Any] = {}
            for key, val in filter_criteria.items():
                if key.startswith("user_attr_"):
                    try:
                        attr_num_str = key.replace("user_attr_", "")
                        attr_num = int(attr_num_str)
                        if attr_num <= 0:
                            return {"status": "error", "message": f"Invalid user attribute number: {attr_num}"}
                        validated_criteria[key] = {"type": "user_attribute", "number": attr_num, "value": str(val)}
                    except (ValueError, TypeError):
                        return {"status": "error", "message": f"Invalid user attribute key format: {key}"}
                        
                elif key in ["name", "material", "group", "comment", "subgroup"]:
                    validated_criteria[key] = {"type": "standard_attribute", "value": str(val)}
                    
                elif key.startswith("dimension_"):
                    dimension_type = key.replace("dimension_", "")
                    if dimension_type not in ["width", "height", "length", "volume", "weight"]:
                        return {"status": "error", "message": f"Invalid dimension type: {dimension_type}"}
                    validated_criteria[key] = {"type": "dimension", "dimension": dimension_type, "value": val}
                    
                else:
                    return {"status": "error", "message": f"Unknown filter criteria key: {key}"}
            
            # Send command
            return self.send_command("create_visual_filter", {
                "filter_name": filter_name.strip(),
                "filter_criteria": validated_criteria,
                "visual_properties": validated_visuals
            })
            
        except Exception as e:
            return {"status": "error", "message": f"create_visual_filter failed: {e}"}
    
    async def apply_color_scheme(self, scheme_name: str, element_ids: Optional[List[int]] = None, 
                               scheme_basis: str = "material") -> Dict[str, Any]:
        """
        Apply predefined color scheme to elements
        
        Args:
            scheme_name: Name of color scheme ('material_based', 'status_based', 'priority_based', 'custom')
            element_ids: Optional list of element IDs (if None, applies to all visible elements)
            scheme_basis: Basis for coloring ('material', 'group', 'element_type', 'user_attribute')
        
        Returns:
            dict: Status of color scheme application
        """
        try:
            # Validate scheme name
            valid_schemes = ["material_based", "status_based", "priority_based", "element_type_based", 
                           "group_based", "dimension_based", "custom"]
            if scheme_name not in valid_schemes:
                return {"status": "error", "message": f"Invalid scheme_name. Must be one of: {valid_schemes}"}
            
            # Validate element IDs if provided
            validated_ids = None
            if element_ids is not None:
                if not isinstance(element_ids, list):
                    return {"status": "error", "message": "element_ids must be a list if provided"}
                if element_ids:  # Only validate if not empty
                    validated_ids = [self.validate_element_id(eid) for eid in element_ids]
            
            # Validate scheme basis
            valid_basis = ["material", "group", "element_type", "user_attribute", "dimension", "status"]
            if scheme_basis not in valid_basis:
                return {"status": "error", "message": f"Invalid scheme_basis. Must be one of: {valid_basis}"}
            
            # Build command arguments
            args: Dict[str, Any] = {
                "scheme_name": scheme_name,
                "scheme_basis": scheme_basis
            }
            
            if validated_ids is not None:
                args["element_ids"] = validated_ids
            
            # Send command
            return self.send_command("apply_color_scheme", args)
            
        except Exception as e:
            return {"status": "error", "message": f"apply_color_scheme failed: {e}"}
    
    async def create_assembly_animation(self, 
                                      element_ids: List[int],
                                      animation_type: str = "sequential",
                                      duration: float = 10.0,
                                      start_delay: float = 0.0,
                                      element_delay: float = 0.5,
                                      fade_in: bool = True,
                                      movement_path: str = "gravity") -> Dict[str, Any]:
        """
        Create assembly animation showing construction sequence
        
        Args:
            element_ids: List of elements to animate
            animation_type: Type of animation (sequential, parallel, grouped)
            duration: Total animation duration in seconds
            start_delay: Delay before animation starts
            element_delay: Delay between individual elements (for sequential)
            fade_in: Use fade-in effect
            movement_path: Movement path (gravity, linear, custom)
        
        Returns:
            dict: Animation creation status and details
        """
        try:
            # Validate element IDs
            if not isinstance(element_ids, list) or not element_ids:
                return {"status": "error", "message": "element_ids must be a non-empty list"}
            
            validated_ids = [self.validate_element_id(eid) for eid in element_ids]
            
            # Validate animation_type
            valid_animation_types = ["sequential", "parallel", "grouped", "reverse_sequential"]
            if animation_type not in valid_animation_types:
                return {"status": "error", "message": f"Invalid animation_type. Must be one of: {valid_animation_types}"}
            
            # Validate duration and timing
            if not isinstance(duration, (int, float)) or duration <= 0:
                return {"status": "error", "message": "duration must be a positive number"}
            
            if not isinstance(start_delay, (int, float)) or start_delay < 0:
                return {"status": "error", "message": "start_delay must be non-negative"}
            
            if not isinstance(element_delay, (int, float)) or element_delay < 0:
                return {"status": "error", "message": "element_delay must be non-negative"}
            
            # Validate movement_path
            valid_paths = ["gravity", "linear", "custom", "arc", "spiral"]
            if movement_path not in valid_paths:
                return {"status": "error", "message": f"Invalid movement_path. Must be one of: {valid_paths}"}
            
            return self.send_command("create_assembly_animation", {
                "element_ids": validated_ids,
                "animation_type": animation_type,
                "duration": float(duration),
                "start_delay": float(start_delay),
                "element_delay": float(element_delay),
                "fade_in": bool(fade_in),
                "movement_path": movement_path
            })
            
        except ValueError as e:
            return {"status": "error", "message": f"Invalid input: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"create_assembly_animation failed: {e}"}
    
    async def set_camera_position(self, 
                                position: List[float],
                                target: List[float],
                                up_vector: List[float] = [0.0, 0.0, 1.0],
                                fov: float = 45.0,
                                animate_transition: bool = True,
                                transition_duration: float = 2.0,
                                camera_name: str = "default") -> Dict[str, Any]:
        """
        Set camera position and orientation for optimal viewing
        
        Args:
            position: Camera position [x, y, z]
            target: Target point to look at [x, y, z]
            up_vector: Camera up vector [x, y, z]
            fov: Field of view in degrees
            animate_transition: Animate camera movement
            transition_duration: Animation duration in seconds
            camera_name: Name for camera preset
        
        Returns:
            dict: Camera positioning status
        """
        try:
            # Validate and convert position
            position = self.validate_point_3d(position, "position")
            if position is None:
                return {"status": "error", "message": "position is required and must be [x, y, z]"}
            
            # Validate and convert target
            target = self.validate_point_3d(target, "target")
            if target is None:
                return {"status": "error", "message": "target is required and must be [x, y, z]"}
            
            # Validate and convert up_vector
            up_vector = self.validate_point_3d(up_vector, "up_vector")
            if up_vector is None:
                return {"status": "error", "message": "up_vector must be [x, y, z]"}
            
            # Validate FOV
            if not isinstance(fov, (int, float)) or fov <= 0 or fov >= 180:
                return {"status": "error", "message": "fov must be between 0 and 180 degrees"}
            
            # Validate transition duration
            if not isinstance(transition_duration, (int, float)) or transition_duration < 0:
                return {"status": "error", "message": "transition_duration must be non-negative"}
            
            # Validate camera name
            if not isinstance(camera_name, str) or not camera_name.strip():
                return {"status": "error", "message": "camera_name must be a non-empty string"}
            
            return self.send_command("set_camera_position", {
                "position": position,
                "target": target,
                "up_vector": up_vector,
                "fov": float(fov),
                "animate_transition": bool(animate_transition),
                "transition_duration": float(transition_duration),
                "camera_name": camera_name.strip()
            })
            
        except ValueError as e:
            return {"status": "error", "message": f"Invalid input: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"set_camera_position failed: {e}"}
    
    async def create_walkthrough(self,
                               waypoints: List[List[float]],
                               duration: float = 30.0,
                               camera_height: float = 1700.0,
                               movement_speed: str = "smooth",
                               focus_elements: Optional[List[int]] = None,
                               include_audio: bool = False,
                               output_format: str = "mp4",
                               resolution: str = "1920x1080") -> Dict[str, Any]:
        """
        Create interactive 3D walkthrough for VR and presentations
        
        Args:
            waypoints: List of waypoint positions [[x,y,z], [x,y,z], ...]
            duration: Total walkthrough duration in seconds
            camera_height: Camera height above ground in mm
            movement_speed: Movement style (smooth, linear, accelerated, custom)
            focus_elements: Optional element IDs to highlight during walkthrough
            include_audio: Include ambient audio tracks
            output_format: Output format (mp4, webm, vr, interactive)
            resolution: Video resolution (1920x1080, 2560x1440, 3840x2160)
        
        Returns:
            dict: Walkthrough creation status and export details
        """
        try:
            # Validate waypoints
            if not isinstance(waypoints, list) or len(waypoints) < 2:
                return {"status": "error", "message": "At least 2 waypoints required for walkthrough"}
            
            validated_waypoints = []
            for i, waypoint in enumerate(waypoints):
                validated_point = self.validate_point_3d(waypoint, f"waypoint_{i}")
                if validated_point is None:
                    return {"status": "error", "message": f"waypoint_{i} must be [x, y, z] coordinates"}
                validated_waypoints.append(validated_point)
            
            # Validate duration
            if not isinstance(duration, (int, float)) or duration <= 0:
                return {"status": "error", "message": "duration must be a positive number"}
            
            # Validate camera_height
            if not isinstance(camera_height, (int, float)) or camera_height < 0:
                return {"status": "error", "message": "camera_height must be non-negative"}
            
            # Validate movement_speed
            valid_movement_speeds = ["smooth", "linear", "accelerated", "decelerated", "custom"]
            if movement_speed not in valid_movement_speeds:
                return {"status": "error", "message": f"Invalid movement_speed. Must be one of: {valid_movement_speeds}"}
            
            # Validate focus_elements if provided
            validated_focus_elements = None
            if focus_elements is not None:
                if not isinstance(focus_elements, list):
                    return {"status": "error", "message": "focus_elements must be a list if provided"}
                if focus_elements:  # Only validate if not empty
                    validated_focus_elements = [self.validate_element_id(eid) for eid in focus_elements]
            
            # Validate output_format
            valid_output_formats = ["mp4", "webm", "avi", "mov", "vr", "interactive", "frames"]
            if output_format not in valid_output_formats:
                return {"status": "error", "message": f"Invalid output_format. Must be one of: {valid_output_formats}"}
            
            # Validate resolution
            valid_resolutions = ["1280x720", "1920x1080", "2560x1440", "3840x2160", "4096x2160"]
            if resolution not in valid_resolutions:
                return {"status": "error", "message": f"Invalid resolution. Must be one of: {valid_resolutions}"}
            
            return self.send_command("create_walkthrough", {
                "waypoints": validated_waypoints,
                "duration": float(duration),
                "camera_height": float(camera_height),
                "movement_speed": movement_speed,
                "focus_elements": validated_focus_elements,
                "include_audio": bool(include_audio),
                "output_format": output_format,
                "resolution": resolution
            })
            
        except ValueError as e:
            return {"status": "error", "message": f"Invalid input: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"create_walkthrough failed: {e}"}
