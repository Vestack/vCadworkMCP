"""
Shop Drawing Controller for the vCadworkMCP server
Manages shop drawing-specific functions for production planning
"""
from typing import Dict, Any, Optional
from .base_controller import BaseController

class ShopDrawingController(BaseController):
    """Controller for shop drawing operations"""
    
    def __init__(self) -> None:
        super().__init__("ShopDrawingController")
    
    async def add_wall_section_x(self, wall_id: int, section_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add wall section in X-direction
        
        Creates technical section views for shop drawings.
        X-direction means section parallel to X-axis.
        
        Args:
            wall_id: ID of wall element for section
            section_params: Optional parameters for section configuration
                          (position, depth, display options, etc.)
        
        Returns:
            dict: Information about created wall section
        """
        try:
            # Validate wall ID
            validated_id = self.validate_element_id(wall_id)
            
            # Standardize section parameters
            final_section_params = section_params if section_params is not None else {}
            
            # Send command
            return self.send_command("add_wall_section_x", {
                "wall_id": validated_id,
                "section_params": final_section_params
            })
            
        except Exception as e:
            return {"status": "error", "message": f"add_wall_section_x failed: {e}"}
    
    async def add_wall_section_y(self, wall_id: int, section_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add wall section in Y-direction
        
        Creates technical section views for shop drawings.
        Y-direction means section parallel to Y-axis.
        
        Args:
            wall_id: ID of wall element for section
            section_params: Optional parameters for section configuration
                          (position, depth, display options, etc.)
        
        Returns:
            dict: Information about created wall section
        """
        try:
            # Validate wall ID
            validated_id = self.validate_element_id(wall_id)
            
            # Standardize section parameters
            final_section_params = section_params if section_params is not None else {}
            
            # Send command
            return self.send_command("add_wall_section_y", {
                "wall_id": validated_id,
                "section_params": final_section_params
            })
            
        except Exception as e:
            return {"status": "error", "message": f"add_wall_section_y failed: {e}"}

    async def add_wall_section_vertical(self, wall_id: int, position_vector: Optional[list] = None, 
                                       section_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add vertical wall section for shop drawings
        
        Creates vertical section cuts through wall elements for technical drawings.
        This is essential for piece-by-piece shop drawing generation.
        
        Args:
            wall_id: ID of wall element for section
            position_vector: Position vector [x,y,z] for section placement (optional)
            section_params: Optional parameters for section configuration
                          (depth, display options, scale, etc.)
        
        Returns:
            dict: Information about created vertical wall section
        """
        try:
            # Validate wall ID
            validated_id = self.validate_element_id(wall_id)
            
            # Validate position vector if provided
            if position_vector is not None:
                if not isinstance(position_vector, list) or len(position_vector) != 3:
                    return {"status": "error", "message": "position_vector must be a list of 3 numbers [x,y,z]"}
                
                # Ensure all values are numbers
                try:
                    position_vector = [float(x) for x in position_vector]
                except (ValueError, TypeError):
                    return {"status": "error", "message": "position_vector must contain valid numbers"}
            
            # Standardize section parameters
            final_section_params = section_params if section_params is not None else {}
            
            # Send command
            return self.send_command("add_wall_section_vertical", {
                "wall_id": validated_id,
                "position_vector": position_vector,
                "section_params": final_section_params
            })
            
        except Exception as e:
            return {"status": "error", "message": f"add_wall_section_vertical failed: {e}"}

    async def export_2d_wireframe(self, clipboard_number: int = 3, with_layout: bool = False,
                                 export_format: str = "dxf", file_path: Optional[str] = None,
                                 scale: float = 1.0, line_weights: bool = True) -> Dict[str, Any]:
        """
        Export 2D wireframe drawings for shop drawings
        
        Exports technical 2D wireframe drawings from the clipboard to various formats.
        Essential for creating shop drawings and technical documentation.
        
        Args:
            clipboard_number: Clipboard number (1-10) containing the drawing
            with_layout: Whether to export with layout/template
            export_format: Export format ("dxf", "dwg", "pdf", "png")
            file_path: Output file path (optional)
            scale: Drawing scale factor
            line_weights: Whether to include line weights
        
        Returns:
            dict: Export status and file information
        """
        try:
            # Validate clipboard number
            if not isinstance(clipboard_number, int) or clipboard_number < 1 or clipboard_number > 10:
                return {"status": "error", "message": "clipboard_number must be an integer between 1 and 10"}
            
            # Validate export format
            valid_formats = ["dxf", "dwg", "pdf", "png", "jpg", "svg"]
            if export_format not in valid_formats:
                return {"status": "error", "message": f"export_format must be one of: {', '.join(valid_formats)}"}
            
            # Validate scale
            if not isinstance(scale, (int, float)) or scale <= 0:
                return {"status": "error", "message": "scale must be a positive number"}
            
            # Validate file path if provided
            if file_path is not None:
                if not isinstance(file_path, str) or not file_path.strip():
                    return {"status": "error", "message": "file_path must be a non-empty string when provided"}
                
                # Ensure correct extension
                file_path = file_path.strip()
                expected_ext = f'.{export_format}'
                if not file_path.lower().endswith(expected_ext):
                    file_path += expected_ext
            
            # Send command
            return self.send_command("export_2d_wireframe", {
                "clipboard_number": clipboard_number,
                "with_layout": bool(with_layout),
                "export_format": export_format,
                "file_path": file_path,
                "scale": float(scale),
                "line_weights": bool(line_weights)
            })
            
        except Exception as e:
            return {"status": "error", "message": f"export_2d_wireframe failed: {e}"}
