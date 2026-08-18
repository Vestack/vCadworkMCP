"""
Geometry operation handlers
"""
from typing import Dict, Any
from ..helpers import validate_element_id, validate_element_ids

def handle_get_element_width(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element width command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        width = gc.get_width(element_id)
        
        if isinstance(width, (int, float)):
            return {"status": "ok", "width": float(width)}
        else:
            return {
                "status": "error", 
                "message": f"Invalid width value returned: {width}"
            }
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_element_height(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element height command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        height = gc.get_height(element_id)
        
        if isinstance(height, (int, float)):
            return {"status": "ok", "height": float(height)}
        else:
            return {
                "status": "error", 
                "message": f"Invalid height value returned: {height}"
            }
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_element_length(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element length command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        length = gc.get_length(element_id)
        
        if isinstance(length, (int, float)):
            return {"status": "ok", "length": float(length)}
        else:
            return {
                "status": "error", 
                "message": f"Invalid length value returned: {length}"
            }
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_element_volume(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element volume command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        volume = gc.get_volume(element_id)
        
        if isinstance(volume, (int, float)):
            return {"status": "ok", "volume": float(volume)}
        else:
            return {
                "status": "error", 
                "message": f"Invalid volume value returned: {volume}"
            }
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_element_weight(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element weight command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        weight = gc.get_weight(element_id)
        
        if isinstance(weight, (int, float)):
            return {"status": "ok", "weight": float(weight)}
        else:
            return {
                "status": "error", 
                "message": f"Invalid weight value returned: {weight}"
            }
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_element_xl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element xl vector command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        xl_vector = gc.get_xl(element_id)
        
        # Convert point_3d to list
        from ..helpers import point_3d_to_list
        xl_list = point_3d_to_list(xl_vector)
        
        return {"status": "ok", "xl_vector": xl_list}
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_element_yl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element yl vector command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        yl_vector = gc.get_yl(element_id)
        
        # Convert point_3d to list
        from ..helpers import point_3d_to_list
        yl_list = point_3d_to_list(yl_vector)
        
        return {"status": "ok", "yl_vector": yl_list}
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_element_zl(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element zl vector command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        zl_vector = gc.get_zl(element_id)
        
        # Convert point_3d to list
        from ..helpers import point_3d_to_list
        zl_list = point_3d_to_list(zl_vector)
        
        return {"status": "ok", "zl_vector": zl_list}
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_element_p1(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element p1 point command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        p1_point = gc.get_p1(element_id)
        
        # Convert point_3d to list
        from ..helpers import point_3d_to_list
        p1_list = point_3d_to_list(p1_point)
        
        return {"status": "ok", "p1_point": p1_list}
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_element_p2(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element p2 point command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        p2_point = gc.get_p2(element_id)
        
        # Convert point_3d to list
        from ..helpers import point_3d_to_list
        p2_list = point_3d_to_list(p2_point)
        
        return {"status": "ok", "p2_point": p2_list}
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_element_p3(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element p3 point command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        p3_point = gc.get_p3(element_id)
        
        # Convert point_3d to list
        from ..helpers import point_3d_to_list
        p3_list = point_3d_to_list(p3_point)
        
        return {"status": "ok", "p3_point": p3_list}
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_center_of_gravity(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get center of gravity command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        cog_point = gc.get_center_of_gravity(element_id)
        
        # Convert point_3d to list
        from ..helpers import point_3d_to_list
        cog_list = point_3d_to_list(cog_point)
        
        return {"status": "ok", "center_of_gravity": cog_list}
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_center_of_gravity_for_list(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get center of gravity for list command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_ids = validate_element_ids(args.get("element_ids", []))
        
        if not element_ids:
            return {"status": "error", "message": "No elements specified"}
        
        cog_point = gc.get_center_of_gravity_for_list(element_ids)
        
        # Convert point_3d to list
        from ..helpers import point_3d_to_list
        cog_list = point_3d_to_list(cog_point)
        
        return {
            "status": "ok", 
            "center_of_gravity": cog_list,
            "element_count": len(element_ids)
        }
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_element_vertices(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element vertices command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        vertices = gc.get_element_vertices(element_id)
        
        # Convert list of point_3d to list of lists
        from ..helpers import point_3d_to_list
        vertices_list = [point_3d_to_list(vertex) for vertex in vertices]
        
        return {
            "status": "ok", 
            "vertices": vertices_list,
            "vertex_count": len(vertices_list)
        }
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_minimum_distance_between_elements(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get minimum distance between elements command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        first_element_id_raw = args.get("first_element_id")
        if first_element_id_raw is None:
            raise ValueError("Missing required argument: first_element_id")
        first_element_id = validate_element_id(first_element_id_raw)
        
        second_element_id_raw = args.get("second_element_id")
        if second_element_id_raw is None:
            raise ValueError("Missing required argument: second_element_id")
        second_element_id = validate_element_id(second_element_id_raw)
        
        distance = gc.get_minimum_distance_between_elements(first_element_id, second_element_id)
        
        if isinstance(distance, (int, float)):
            return {
                "status": "ok", 
                "distance": float(distance),
                "first_element_id": first_element_id,
                "second_element_id": second_element_id
            }
        else:
            return {
                "status": "error", 
                "message": f"Invalid distance value returned: {distance}"
            }
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_element_facets(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element facets command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        facets = gc.get_element_facets(element_id)
        
        # Convert facet_list to appropriate format
        # Note: facet_list is a special Cadwork type, we need to extract data from it
        facets_data = []
        
        # Try to iterate through facets and convert each facet
        try:
            # Assuming facets is iterable and contains point_3d objects
            from ..helpers import point_3d_to_list
            
            for facet in facets:
                # Each facet should be a list of points forming a face
                if hasattr(facet, '__iter__'):
                    facet_points = [point_3d_to_list(point) for point in facet]
                    facets_data.append(facet_points)
                else:
                    # Single point facet (degenerate case)
                    facets_data.append([point_3d_to_list(facet)])
                    
        except Exception as facet_error:
            # If facet conversion fails, return basic info
            return {
                "status": "ok",
                "facet_count": len(facets) if hasattr(facets, '__len__') else 0,
                "message": "Facets available but format conversion not fully supported",
                "raw_type": str(type(facets))
            }
        
        return {
            "status": "ok", 
            "facets": facets_data,
            "facet_count": len(facets_data)
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_element_reference_face_area(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element reference face area command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        area = gc.get_element_reference_face_area(element_id)
        
        if isinstance(area, (int, float)):
            return {"status": "ok", "reference_face_area": float(area)}
        else:
            return {
                "status": "error", 
                "message": f"Invalid area value returned: {area}"
            }
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_get_total_area_of_all_faces(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get total area of all faces command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_id_raw = args.get("element_id")
        if element_id_raw is None:
            raise ValueError("Missing required argument: element_id")
        element_id = validate_element_id(element_id_raw)
        total_area = gc.get_total_area_of_all_faces(element_id)
        
        if isinstance(total_area, (int, float)):
            return {"status": "ok", "total_face_area": float(total_area)}
        else:
            return {
                "status": "error", 
                "message": f"Invalid area value returned: {total_area}"
            }
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"API error: {e}"}

def handle_rotate_elements(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle rotate elements command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_ids = validate_element_ids(args.get("element_ids", []))
        origin_raw = args.get("origin")
        rotation_axis_raw = args.get("rotation_axis")
        rotation_angle = args.get("rotation_angle")
        
        if not element_ids:
            return {"status": "error", "message": "No elements specified for rotation"}
        
        if origin_raw is None:
            raise ValueError("Missing required argument: origin")
        if rotation_axis_raw is None:
            raise ValueError("Missing required argument: rotation_axis")
        if rotation_angle is None:
            raise ValueError("Missing required argument: rotation_angle")
        
        # Convert arguments
        from ..helpers import to_point_3d
        origin = to_point_3d(origin_raw)
        rotation_axis = to_point_3d(rotation_axis_raw)
        angle = float(rotation_angle)
        
        # Rotate elements
        ec.rotate_elements(element_ids, origin, rotation_axis, angle)
        
        return {
            "status": "ok", 
            "rotated_count": len(element_ids),
            "rotation_angle": angle,
            "message": f"Successfully rotated {len(element_ids)} elements by {angle}° around axis"
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to rotate elements: {e}"}

def handle_apply_global_scale(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle apply global scale command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_ids = validate_element_ids(args.get("element_ids", []))
        scale = args.get("scale")
        origin_raw = args.get("origin")
        
        if not element_ids:
            return {"status": "error", "message": "No elements specified for scaling"}
        
        if scale is None:
            raise ValueError("Missing required argument: scale")
        if origin_raw is None:
            raise ValueError("Missing required argument: origin")
        
        # Convert arguments
        from ..helpers import to_point_3d
        scale_factor = float(scale)
        origin = to_point_3d(origin_raw)
        
        if scale_factor <= 0:
            raise ValueError(f"Scale factor must be positive, got: {scale_factor}")
        
        # Apply scaling
        gc.apply_global_scale(element_ids, scale_factor, origin)
        
        return {
            "status": "ok", 
            "scaled_count": len(element_ids),
            "scale_factor": scale_factor,
            "origin": origin_raw,
            "message": f"Successfully scaled {len(element_ids)} elements by factor {scale_factor}"
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to scale elements: {e}"}

def handle_invert_model(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle invert model command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_ids = validate_element_ids(args.get("element_ids", []))
        
        if not element_ids:
            return {"status": "error", "message": "No elements specified for inversion"}
        
        # Invert model
        gc.invert_model(element_ids)
        
        return {
            "status": "ok", 
            "inverted_count": len(element_ids),
            "message": f"Successfully inverted {len(element_ids)} elements"
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to invert elements: {e}"}

def handle_rotate_height_axis_90(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle rotate height axis 90 degrees command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_ids = validate_element_ids(args.get("element_ids", []))
        
        if not element_ids:
            return {"status": "error", "message": "No elements specified for rotation"}
        
        # Rotate height axis 90 degrees
        gc.rotate_height_axis_90(element_ids)
        
        return {
            "status": "ok", 
            "rotated_count": len(element_ids),
            "message": f"Successfully rotated height axis of {len(element_ids)} elements by 90°"
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to rotate height axis: {e}"}

def handle_rotate_length_axis_90(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle rotate length axis 90 degrees command"""
    try:
        # Import here to avoid import-time errors
        import element_controller as ec

        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_ids = validate_element_ids(args.get("element_ids", []))
        
        if not element_ids:
            return {"status": "error", "message": "No elements specified for rotation"}
        
        # Rotate length axis 90 degrees
        gc.rotate_length_axis_90(element_ids)
        
        return {
            "status": "ok", 
            "rotated_count": len(element_ids),
            "message": f"Successfully rotated length axis of {len(element_ids)} elements by 90°"
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to rotate length axis: {e}"}

def handle_get_element_type(aParams: dict) -> dict:
    """Retrieves the element type"""
    try:
        import element_controller as ec
        
        lElementId = aParams.get("element_id")
        
        if lElementId is None:
            return {"status": "error", "message": "No element ID provided"}
        
        # Cadwork API aufrufen
        lElementType = ec.get_element_type(lElementId)
        
        # Return the element type as a string
        lTypeNames = {
            0: "none",
            1: "beam", 
            2: "panel",
            3: "drilling",
            4: "node",
            5: "line",
            6: "surface",
            7: "volume",
            8: "container",
            9: "auxiliary",
            10: "text_object",
            11: "dimension",
            12: "architectural"
        }
        
        lTypeName = lTypeNames.get(lElementType, f"unknown_type_{lElementType}")
        
        return {
            "status": "success",
            "element_id": lElementId,
            "element_type": lTypeName,
            "type_id": lElementType
        }
        
    except Exception as e:
        return {"status": "error", "message": f"get_element_type failed: {e}"}

def handle_calculate_total_volume(aParams: dict) -> dict:
    """Calculates the total volume of a list of elements"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        
        if not lElementIds:
            return {"status": "error", "message": "No element IDs provided"}
        
        lTotalVolumeMm3 = 0.0
        lProcessedElements = []
        lFailedElements = []
        
        # Sum the volume of all elements
        for lElementId in lElementIds:
            try:
                lVolume = ec.get_element_volume(lElementId)
                if lVolume is not None and lVolume > 0:
                    lTotalVolumeMm3 += lVolume
                    lProcessedElements.append(lElementId)
                else:
                    lFailedElements.append(lElementId)
            except Exception as e:
                lFailedElements.append(lElementId)
        
        # Unit conversion
        lTotalVolumeCm3 = lTotalVolumeMm3 / 1000.0  # mm³ → cm³
        lTotalVolumeDm3 = lTotalVolumeMm3 / 1000000.0  # mm³ → dm³ (Liter)
        lTotalVolumeM3 = lTotalVolumeMm3 / 1000000000.0  # mm³ → m³
        
        return {
            "status": "success",
            "total_volume_mm3": lTotalVolumeMm3,
            "total_volume_cm3": lTotalVolumeCm3,
            "total_volume_dm3": lTotalVolumeDm3,
            "total_volume_m3": lTotalVolumeM3,
            "processed_elements": lProcessedElements,
            "failed_elements": lFailedElements,
            "processed_count": len(lProcessedElements),
            "failed_count": len(lFailedElements),
            "total_count": len(lElementIds)
        }
        
    except Exception as e:
        return {"status": "error", "message": f"calculate_total_volume failed: {e}"}

def handle_calculate_total_weight(aParams: dict) -> dict:
    """Calculates the total weight of a list of elements"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        
        if not lElementIds:
            return {"status": "error", "message": "No element IDs provided"}
        
        lTotalWeightKg = 0.0
        lProcessedElements = []
        lFailedElements = []
        
        # Sum the weight of all elements
        for lElementId in lElementIds:
            try:
                lWeight = ec.get_element_weight(lElementId)
                if lWeight is not None and lWeight > 0:
                    lTotalWeightKg += lWeight
                    lProcessedElements.append(lElementId)
                else:
                    lFailedElements.append(lElementId)
            except Exception as e:
                lFailedElements.append(lElementId)
        
        # Unit conversion
        lTotalWeightG = lTotalWeightKg * 1000.0      # kg → g
        lTotalWeightT = lTotalWeightKg / 1000.0      # kg → t (Tonnen)
        
        return {
            "status": "success",
            "total_weight_kg": lTotalWeightKg,
            "total_weight_g": lTotalWeightG,
            "total_weight_t": lTotalWeightT,
            "processed_elements": lProcessedElements,
            "failed_elements": lFailedElements,
            "processed_count": len(lProcessedElements),
            "failed_count": len(lFailedElements),
            "total_count": len(lElementIds)
        }
        
    except Exception as e:
        return {"status": "error", "message": f"calculate_total_weight failed: {e}"}


def handle_get_bounding_box(aParams: dict) -> dict:
    """Get bounding box (min/max coordinates) of a Cadwork element"""
    try:
        import geometry_controller as gc
        
        lElementId = aParams.get("element_id")
        
        if lElementId is None:
            return {"status": "error", "message": "No element ID provided"}
        
        if not isinstance(lElementId, int) or lElementId < 0:
            return {"status": "error", "message": "Invalid element ID"}
        
        # Get bounding box using Cadwork API
        # Try different possible function names
        lBoundingBox = None
        try:
            if hasattr(gc, 'get_bounding_box'):
                lBoundingBox = gc.get_bounding_box(lElementId)
            elif hasattr(gc, 'get_element_bounding_box'):
                lBoundingBox = gc.get_element_bounding_box(lElementId)
            elif hasattr(gc, 'get_envelope'):
                lBoundingBox = gc.get_envelope(lElementId)
            else:
                # Fallback: use element vertices to calculate bounding box
                if hasattr(gc, 'get_element_vertices'):
                    lVertices = gc.get_element_vertices(lElementId)
                    if lVertices:
                        lXCoords = [v[0] for v in lVertices]
                        lYCoords = [v[1] for v in lVertices]
                        lZCoords = [v[2] for v in lVertices]
                        lBoundingBox = [
                            min(lXCoords), min(lYCoords), min(lZCoords),
                            max(lXCoords), max(lYCoords), max(lZCoords)
                        ]
                    else:
                        return {"status": "error", "message": "Could not get element vertices for bounding box calculation"}
                else:
                    return {"status": "error", "message": "No bounding box function available in geometry_controller"}
        except Exception as e:
            return {"status": "error", "message": f"Error getting bounding box: {e}"}
        
        # Expected format: [min_x, min_y, min_z, max_x, max_y, max_z]
        if isinstance(lBoundingBox, (list, tuple)) and len(lBoundingBox) == 6:
            return {
                "status": "ok",
                "element_id": lElementId,
                "bounding_box": list(lBoundingBox),
                "min_x": lBoundingBox[0],
                "min_y": lBoundingBox[1], 
                "min_z": lBoundingBox[2],
                "max_x": lBoundingBox[3],
                "max_y": lBoundingBox[4],
                "max_z": lBoundingBox[5],
                "width": lBoundingBox[3] - lBoundingBox[0],
                "height": lBoundingBox[4] - lBoundingBox[1], 
                "depth": lBoundingBox[5] - lBoundingBox[2]
            }
        else:
            return {"status": "error", "message": f"Invalid bounding box format: {lBoundingBox}"}
            
    except Exception as e:
        return {"status": "error", "message": f"get_bounding_box failed: {e}"}

def handle_check_collisions(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle check collisions command"""
    try:
        # Import here to avoid import-time errors
        import geometry_controller as gc

        element_ids_raw = args.get("element_ids")
        if element_ids_raw is None:
            raise ValueError("Missing required argument: element_ids")
        
        element_ids = validate_element_ids(element_ids_raw)
        if len(element_ids) < 2:
            raise ValueError("At least 2 elements required for collision check")
        
        tolerance = args.get("tolerance", 0.1)
        if not isinstance(tolerance, (int, float)) or tolerance < 0:
            raise ValueError("Tolerance must be a non-negative number")
        
        # Check for collisions between all pairs of elements
        collision_results = []
        for i in range(len(element_ids)):
            for j in range(i + 1, len(element_ids)):
                # Use Cadwork API to check collision between elements
                # This is a placeholder - actual implementation depends on Cadwork API
                min_distance = gc.get_minimum_distance_between_elements(element_ids[i], element_ids[j])
                has_collision = min_distance <= tolerance
                
                collision_results.append({
                    "element_1": element_ids[i],
                    "element_2": element_ids[j],
                    "distance": min_distance,
                    "has_collision": has_collision
                })
        
        # Determine overall collision status
        total_collisions = sum(1 for result in collision_results if result["has_collision"])
        
        return {
            "status": "ok",
            "collision_count": total_collisions,
            "has_any_collision": total_collisions > 0,
            "details": collision_results,
            "tolerance": tolerance
        }
    
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"check_collisions failed: {e}"}

def handle_validate_joints(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle validate joints command"""
    try:
        # Import here to avoid import-time errors
        import geometry_controller as gc
        import attribute_controller as ac

        # Validate required arguments
        element_ids_raw = args.get("element_ids")
        if element_ids_raw is None:
            raise ValueError("Missing required argument: element_ids")
        
        element_ids = validate_element_ids(element_ids_raw)
        if len(element_ids) < 2:
            raise ValueError("At least 2 elements required for joint validation")
        
        # Get optional parameters with defaults
        joint_type = args.get("joint_type", "auto")
        load_conditions = args.get("load_conditions", {})
        safety_factor = args.get("safety_factor", 2.0)
        wood_grade = args.get("wood_grade", "C24")
        
        # Validate parameters
        valid_joint_types = ["auto", "mortise_tenon", "lap_joint", "dovetail", "scarf_joint", "custom"]
        if joint_type not in valid_joint_types:
            raise ValueError(f"Invalid joint_type. Must be one of: {valid_joint_types}")
        
        if not isinstance(safety_factor, (int, float)) or safety_factor <= 0:
            raise ValueError("safety_factor must be a positive number")
        
        valid_wood_grades = ["C16", "C20", "C24", "C27", "C30", "C35", "C40", "GL24h", "GL28h", "GL32h"]
        if wood_grade not in valid_wood_grades:
            raise ValueError(f"Invalid wood_grade. Must be one of: {valid_wood_grades}")
        
        # Material strength properties for different wood grades
        wood_properties = {
            "C24": {"fm_k": 24.0, "fv_k": 4.0, "fc_0_k": 21.0, "ft_0_k": 14.0, "E_mean": 11000.0},
            "C30": {"fm_k": 30.0, "fv_k": 4.0, "fc_0_k": 23.0, "ft_0_k": 18.0, "E_mean": 12000.0},
            "GL24h": {"fm_k": 24.0, "fv_k": 2.7, "fc_0_k": 24.0, "ft_0_k": 16.5, "E_mean": 11500.0}
        }
        
        # Get wood properties (default to C24 if not found)
        properties = wood_properties.get(wood_grade, wood_properties["C24"])
        
        # Analyze joints between element pairs
        joint_analyses = []
        for i in range(len(element_ids)):
            for j in range(i + 1, len(element_ids)):
                element_1 = element_ids[i]
                element_2 = element_ids[j]
                
                # Get element geometries
                try:
                    width_1 = gc.get_width(element_1)
                    height_1 = gc.get_height(element_1)
                    width_2 = gc.get_width(element_2)
                    height_2 = gc.get_height(element_2)
                    
                    # Calculate joint area (simplified)
                    joint_area = min(width_1 * height_1, width_2 * height_2)
                    
                    # Basic strength calculations
                    normal_force = load_conditions.get("normal_force", 0.0)
                    shear_force = load_conditions.get("shear_force", 0.0)
                    
                    # Calculate stresses
                    normal_stress = normal_force / joint_area if joint_area > 0 else 0
                    shear_stress = shear_force / joint_area if joint_area > 0 else 0
                    
                    # Check against allowable stresses with safety factor
                    allowable_normal = properties["fc_0_k"] / safety_factor
                    allowable_shear = properties["fv_k"] / safety_factor
                    
                    # Safety checks
                    normal_utilization = normal_stress / allowable_normal if allowable_normal > 0 else 0
                    shear_utilization = shear_stress / allowable_shear if allowable_shear > 0 else 0
                    
                    is_valid = normal_utilization <= 1.0 and shear_utilization <= 1.0
                    
                    joint_analyses.append({
                        "element_pair": [element_1, element_2],
                        "joint_type": joint_type,
                        "joint_area": joint_area,
                        "normal_stress": normal_stress,
                        "shear_stress": shear_stress,
                        "normal_utilization": normal_utilization,
                        "shear_utilization": shear_utilization,
                        "is_valid": is_valid,
                        "safety_factor": safety_factor
                    })
                    
                except Exception as e:
                    joint_analyses.append({
                        "element_pair": [element_1, element_2],
                        "error": f"Could not analyze joint: {e}",
                        "is_valid": False
                    })
        
        # Overall validation result
        all_valid = all(analysis.get("is_valid", False) for analysis in joint_analyses)
        
        return {
            "status": "ok",
            "overall_valid": all_valid,
            "joint_count": len(joint_analyses),
            "wood_grade": wood_grade,
            "safety_factor": safety_factor,
            "joint_analyses": joint_analyses,
            "wood_properties": properties,
            "message": f"Joint validation {'passed' if all_valid else 'failed'} for {len(joint_analyses)} joint(s)"
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"validate_joints failed: {e}"}
