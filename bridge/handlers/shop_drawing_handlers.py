"""
Shop drawing handler for the Cadwork bridge
Handles shop-drawing-specific operations
"""

def handle_add_wall_section_x(aParams: dict) -> dict:
    """Adds a wall section in the X direction"""
    try:
        import shop_drawing_controller as sdc
        
        lWallId = aParams.get("wall_id")
        lSectionParams = aParams.get("section_params")
        
        if lWallId is None:
            return {"status": "error", "message": "No wall ID provided"}
        
        # Cadwork API aufrufen - section_params optional
        lSectionId = sdc.add_wall_section_x(lWallId, lSectionParams)
        
        return {
            "status": "success",
            "section_id": lSectionId,
            "wall_id": lWallId,
            "section_direction": "x",
            "section_params": lSectionParams,
            "operation": "add_wall_section_x"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"add_wall_section_x failed: {e}"}

def handle_add_wall_section_y(aParams: dict) -> dict:
    """Adds a wall section in the Y direction"""
    try:
        import shop_drawing_controller as sdc
        
        lWallId = aParams.get("wall_id")
        lSectionParams = aParams.get("section_params")
        
        if lWallId is None:
            return {"status": "error", "message": "No wall ID provided"}
        
        # Cadwork API aufrufen - section_params optional
        lSectionId = sdc.add_wall_section_y(lWallId, lSectionParams)
        
        return {
            "status": "success",
            "section_id": lSectionId,
            "wall_id": lWallId,
            "section_direction": "y",
            "section_params": lSectionParams,
            "operation": "add_wall_section_y"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"add_wall_section_y failed: {e}"}

def handle_add_wall_section_vertical(aParams: dict) -> dict:
    """Adds a vertical wall section"""
    try:
        import shop_drawing_controller as sdc
        
        lWallId = aParams.get("wall_id")
        lPositionVector = aParams.get("position_vector")
        lSectionParams = aParams.get("section_params")
        
        if lWallId is None:
            return {"status": "error", "message": "No wall ID provided"}
        
        # Call the cadwork API - position_vector and section_params are optional
        # The API positions the section automatically when position_vector=None
        lSectionId = sdc.add_wall_section_vertical(lWallId, lPositionVector, lSectionParams)
        
        return {
            "status": "success",
            "section_id": lSectionId,
            "wall_id": lWallId,
            "position_vector": lPositionVector,
            "section_direction": "vertical",
            "section_params": lSectionParams,
            "operation": "add_wall_section_vertical"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"add_wall_section_vertical failed: {e}"}

def handle_export_2d_wireframe(aParams: dict) -> dict:
    """Exports a 2D wireframe from the clipboard"""
    try:
        import shop_drawing_controller as sdc
        
        lClipboardNumber = aParams.get("clipboard_number", 3)
        lWithLayout = aParams.get("with_layout", False)
        lExportFormat = aParams.get("export_format", "dxf")
        lFilePath = aParams.get("file_path")
        lScale = aParams.get("scale", 1.0)
        lLineWeights = aParams.get("line_weights", True)
        
        # Call the cadwork API - pass ALL parameters
        result = sdc.export_2d_wireframe(
            lClipboardNumber,
            lWithLayout,
            lExportFormat,
            lFilePath,
            lScale,
            lLineWeights
        )
        
        # Erweiterte Export-Informationen
        lExportInfo = {
            "clipboard_number": lClipboardNumber,
            "with_layout": lWithLayout,
            "export_format": lExportFormat,
            "scale": lScale,
            "line_weights": lLineWeights
        }
        
        if lFilePath:
            lExportInfo["file_path"] = lFilePath
            lExportInfo["export_location"] = "file"
        else:
            lExportInfo["export_location"] = "clipboard"
        
        return {
            "status": "success",
            "message": "2D wireframe export completed successfully",
            "export_info": lExportInfo,
            "operation": "export_2d_wireframe",
            "api_result": result
        }
        
    except Exception as e:
        return {"status": "error", "message": f"export_2d_wireframe failed: {e}"}
