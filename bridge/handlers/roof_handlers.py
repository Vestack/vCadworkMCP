"""
Roof handler for the Cadwork bridge
Handles roof-specific CAD operations
"""
import math

def handle_get_roof_surfaces(aParams: dict) -> dict:
    """Retrieves roof surface information"""
    try:
        import roof_controller as rc
        
        lElementIds = aParams.get("element_ids", [])
        
        if not lElementIds:
            return {"status": "error", "message": "No element IDs provided"}
        
        # Cadwork API aufrufen
        lRoofSurfaces = rc.get_roof_surfaces(lElementIds)
        
        # Structure the roof surface information
        lSurfaceDetails = []
        
        for lElementId in lElementIds:
            try:
                # Collect element-specific roof surface data
                lElementInfo = rc.get_element_info(lElementId)
                
                # Extract roof-surface-specific properties
                lSurfaceInfo = {
                    "element_id": lElementId,
                    "element_type": lElementInfo.get("type", "unknown"),
                    "roof_surface_area": 0,  # Filled in by the API
                    "roof_slope": 0,         # Filled in by the API
                    "roof_orientation": 0,   # Filled in by the API
                    "is_roof_element": True
                }
                
                lSurfaceDetails.append(lSurfaceInfo)
                
            except Exception as e:
                # Fallback for elements without roof properties
                lSurfaceDetails.append({
                    "element_id": lElementId,
                    "element_type": "unknown",
                    "error": f"Could not analyze roof properties: {e}",
                    "is_roof_element": False
                })
        
        return {
            "status": "success",
            "analyzed_elements": len(lElementIds),
            "roof_surfaces": lRoofSurfaces if lRoofSurfaces else lSurfaceDetails,
            "surface_details": lSurfaceDetails,
            "operation": "get_roof_surfaces"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"get_roof_surfaces failed: {e}"}

def handle_calculate_roof_area(aParams: dict) -> dict:
    """Calculates roof surface areas"""
    try:
        import roof_controller as rc
        
        lRoofElementIds = aParams.get("roof_element_ids", [])
        
        if not lRoofElementIds:
            return {"status": "error", "message": "No roof element IDs provided"}
        
        # Cadwork API aufrufen
        lRoofAreaData = rc.calculate_roof_area(lRoofElementIds)
        
        # Additional roof surface calculations
        lTotalGroundArea = 0
        lTotalSlopedArea = 0
        lElementAreas = []
        
        for lElementId in lRoofElementIds:
            try:
                # Element-specific area calculations
                lElementInfo = rc.get_element_info(lElementId)
                lElementArea = rc.get_element_reference_face_area(lElementId)
                
                lElementAreaInfo = {
                    "element_id": lElementId,
                    "element_type": lElementInfo.get("type", "unknown"),
                    "area_m2": lElementArea / 1000000 if lElementArea else 0,  # mm² zu m²
                    "area_mm2": lElementArea if lElementArea else 0
                }
                
                lElementAreas.append(lElementAreaInfo)
                
                if lElementArea:
                    lTotalSlopedArea += lElementArea
                    
            except Exception as e:
                lElementAreas.append({
                    "element_id": lElementId,
                    "error": f"Could not calculate area: {e}",
                    "area_m2": 0,
                    "area_mm2": 0
                })
        
        # Roof-surface-specific calculations
        lRoofAreaResults = {
            "total_sloped_area_mm2": lTotalSlopedArea,
            "total_sloped_area_m2": lTotalSlopedArea / 1000000,
            "element_count": len(lRoofElementIds),
            "average_area_per_element_m2": (lTotalSlopedArea / 1000000) / len(lRoofElementIds) if lRoofElementIds else 0
        }
        
        return {
            "status": "success",
            "roof_area_calculations": lRoofAreaData if lRoofAreaData else lRoofAreaResults,
            "detailed_calculations": lRoofAreaResults,
            "element_areas": lElementAreas,
            "operation": "calculate_roof_area"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"calculate_roof_area failed: {e}"}
