"""
Roof Controller for the vCadworkMCP server
Manages roof-specific CAD functions for carpentry and roof construction
"""
from typing import Dict, Any, List
from .base_controller import BaseController

class RoofController(BaseController):
    """Controller for roof operations"""
    
    def __init__(self) -> None:
        super().__init__("RoofController")
    
    async def get_roof_surfaces(self, element_ids: List[int]) -> Dict[str, Any]:
        """
        Get roof surface information for specified elements
        
        Analyzes roof elements and returns detailed information about
        roof surfaces, slopes, orientations and geometric properties.
        
        Args:
            element_ids: List of element IDs to analyze as roof elements
        
        Returns:
            dict: Detailed roof surface information (slopes, orientations, areas)
        """
        try:
            # Validate element IDs
            validated_ids = []
            for eid in element_ids:
                validated_ids.append(self.validate_element_id(eid))
            
            if not validated_ids:
                return {"status": "error", "message": "No valid element IDs provided"}
            
            # Send command
            return self.send_command("get_roof_surfaces", {
                "element_ids": validated_ids
            })
            
        except Exception as e:
            return {"status": "error", "message": f"get_roof_surfaces failed: {e}"}
    
    async def calculate_roof_area(self, roof_element_ids: List[int]) -> Dict[str, Any]:
        """
        Calculate total roof area for specified roof elements
        
        Performs specialized roof area calculations considering slopes,
        overhangs and complex roof geometries.
        
        Args:
            roof_element_ids: List of roof element IDs for area calculation
        
        Returns:
            dict: Roof area calculations (base area, sloped area, factors)
        """
        try:
            # Validate element IDs
            validated_ids = []
            for eid in roof_element_ids:
                validated_ids.append(self.validate_element_id(eid))
            
            if not validated_ids:
                return {"status": "error", "message": "No valid roof element IDs provided"}
            
            # Send command
            return self.send_command("calculate_roof_area", {
                "roof_element_ids": validated_ids
            })
            
        except Exception as e:
            return {"status": "error", "message": f"calculate_roof_area failed: {e}"}
