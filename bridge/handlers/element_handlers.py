"""
Element operation handlers
"""
from typing import Dict, Any
from .base_handler import BaseHandler, validate_element_ids

# Helper functions for data conversion
def to_point_3d(point_data):
    """Convert point data to cadwork point_3d"""
    try:
        import cadwork
        if isinstance(point_data, (list, tuple)) and len(point_data) >= 3:
            return cadwork.point_3d(float(point_data[0]), float(point_data[1]), float(point_data[2]))
        else:
            raise ValueError("Point must be a list/tuple of at least 3 numbers")
    except ImportError:
        # Fallback when cadwork is not available
        return point_data

def point_3d_to_list(point):
    """Convert cadwork point_3d to list"""
    try:
        return [point.x, point.y, point.z]
    except:
        return point if isinstance(point, list) else [0, 0, 0]

def validate_positive_number(value, name):
    """Validate positive number"""
    try:
        num = float(value)
        if num <= 0:
            raise ValueError(f"{name} must be positive")
        return num
    except (ValueError, TypeError):
        raise ValueError(f"{name} must be a positive number")

def handle_create_beam(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle create beam command"""
    try:
        import cadwork
        import element_controller as ec
        
        # Validate required arguments
        required = ["p1", "p2", "width", "height"]
        for key in required:
            if key not in args:
                raise ValueError(f"Missing required argument: {key}")
        
        # Convert and validate arguments
        p1 = to_point_3d(args["p1"])
        p2 = to_point_3d(args["p2"])
        width = validate_positive_number(args["width"], "width")
        height = validate_positive_number(args["height"], "height")
        
        # Handle optional p3
        p3_raw = args.get("p3")
        if p3_raw is None:
            p3 = cadwork.point_3d(p1.x, p1.y, p1.z + 1.0)
        else:
            p3 = to_point_3d(p3_raw)
        
        # Create beam using element_controller
        beam_id = ec.create_rectangular_beam_points(width, height, p1, p2, p3)
        
        if isinstance(beam_id, int) and beam_id >= 0:
            return {"status": "ok", "id": beam_id}
        else:
            return {
                "status": "error", 
                "message": f"Beam creation failed, returned: {beam_id}"
            }
            
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Cadwork API error: {e}"}

def handle_create_panel(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle create panel command"""
    try:
        import cadwork
        import element_controller as ec

        # Validate required arguments
        required = ["p1", "p2", "width", "thickness"]
        for key in required:
            if key not in args:
                raise ValueError(f"Missing required argument: {key}")
        
        # Convert and validate arguments
        p1 = to_point_3d(args["p1"])
        p2 = to_point_3d(args["p2"])
        width = validate_positive_number(args["width"], "width")
        thickness = validate_positive_number(args["thickness"], "thickness")
        
        # Handle optional p3
        p3_raw = args.get("p3")
        if p3_raw is None:
            p3 = cadwork.point_3d(p1.x, p1.y, p1.z + 1.0)
        else:
            p3 = to_point_3d(p3_raw)
        
        # Create panel using element_controller
        panel_id = ec.create_rectangular_panel_points(width, thickness, p1, p2, p3)
        
        if isinstance(panel_id, int) and panel_id >= 0:
            return {"status": "ok", "id": panel_id}
        else:
            return {
                "status": "error", 
                "message": f"Panel creation failed, returned: {panel_id}"
            }
            
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Cadwork API error: {e}"}

def handle_get_active_element_ids(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get active element IDs command"""
    try:
        import element_controller as ec
        
        active_ids = ec.get_active_identifiable_element_ids()
        return {"status": "ok", "element_ids": active_ids}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get active elements: {e}"}

def handle_get_all_element_ids(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get all element IDs command"""
    try:
        import element_controller as ec
        
        all_ids = ec.get_all_identifiable_element_ids()
        return {"status": "ok", "element_ids": all_ids}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get all elements: {e}"}

def handle_delete_elements(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle delete elements command"""
    try:
        import element_controller as ec

        element_ids = validate_element_ids(args.get("element_ids", []))
        
        if not element_ids:
            return {"status": "ok", "message": "No elements to delete"}
        
        # Delete elements
        ec.delete_elements(element_ids)
        
        return {
            "status": "ok", 
            "message": f"Successfully deleted {len(element_ids)} elements",
            "deleted_count": len(element_ids)
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete elements: {e}"}

def handle_move_element(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle move element command"""
    try:
        import element_controller as ec

        element_ids = validate_element_ids(args.get("element_ids", []))
        move_vector_raw = args.get("move_vector")
        
        if not element_ids:
            return {"status": "error", "message": "No elements specified for moving"}
        
        if move_vector_raw is None:
            raise ValueError("Missing required argument: move_vector")
        
        # Convert move vector
        move_vector = to_point_3d(move_vector_raw)
        
        # Move elements
        ec.move_element(element_ids, move_vector)
        
        return {
            "status": "ok", 
            "moved_count": len(element_ids),
            "message": f"Successfully moved {len(element_ids)} elements"
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to move elements: {e}"}

def handle_get_user_element_ids(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get user element IDs command"""
    try:
        import element_controller as ec

        count = args.get("count")
        
        if count is not None:
            # Get specific number of user-selected elements
            try:
                count = int(count)
                if count <= 0:
                    raise ValueError("Count must be positive")
                user_ids = ec.get_user_element_ids_with_count(count)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid count value: {count}")
        else:
            # Get user-selected elements without count limit
            user_ids = ec.get_user_element_ids()
        
        return {
            "status": "ok", 
            "element_ids": user_ids,
            "selected_count": len(user_ids)
        }
        
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get user elements: {e}"}

def handle_copy_elements(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle copy elements command"""
    try:
        import element_controller as ec

        element_ids = validate_element_ids(args.get("element_ids", []))
        copy_vector_raw = args.get("copy_vector")
        
        if not element_ids:
            return {"status": "error", "message": "No elements specified for copying"}
        
        if copy_vector_raw is None:
            raise ValueError("Missing required argument: copy_vector")
        
        # Convert copy vector
        copy_vector = to_point_3d(copy_vector_raw)
        
        # Copy elements
        new_element_ids = ec.copy_elements(element_ids, copy_vector)
        
        if isinstance(new_element_ids, list):
            return {
                "status": "ok", 
                "new_element_ids": new_element_ids,
                "copied_count": len(new_element_ids),
                "message": f"Successfully copied {len(element_ids)} elements"
            }
        else:
            return {
                "status": "error", 
                "message": f"Copy operation failed, returned: {new_element_ids}"
            }
            
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to copy elements: {e}"}

def handle_get_visible_element_ids(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get visible element IDs command"""
    try:
        import element_controller as ec

        visible_ids = ec.get_visible_identifiable_element_ids()
        return {"status": "ok", "element_ids": visible_ids}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get visible elements: {e}"}

def handle_get_element_info(args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get element info command"""
    try:
        import element_controller as ec
        import geometry_controller as gc
        import attribute_controller as ac

        element_id = args.get("element_id")
        if element_id is None:
            raise ValueError("Missing required argument: element_id")
        
        element_id = int(element_id)
        
        # Get geometry
        p1 = gc.get_p1(element_id)
        p2 = gc.get_p2(element_id)
        p3 = gc.get_p3(element_id)
        vec_x = gc.get_xl(element_id)
        vec_y = gc.get_yl(element_id)
        vec_z = gc.get_zl(element_id)
        
        # Get basic attributes
        attributes = {}
        try:
            attributes["name"] = ac.get_name(element_id)
        except Exception:
            attributes["name"] = None
            
        try:
            attributes["group"] = ac.get_group(element_id)
        except Exception:
            attributes["group"] = None
            
        try:
            attributes["subgroup"] = ac.get_subgroup(element_id)
        except Exception:
            attributes["subgroup"] = None
            
        try:
            attributes["comment"] = ac.get_comment(element_id)
        except Exception:
            attributes["comment"] = None
        
        # Get material
        try:
            material_name = ac.get_element_material_name(element_id)
            attributes["material"] = material_name if material_name else None
        except Exception:
            attributes["material"] = None
        
        element_info = {
            "element_id": element_id,
            "geometry": {
                "p1": point_3d_to_list(p1),
                "p2": point_3d_to_list(p2),
                "p3": point_3d_to_list(p3),
                "vector_x": point_3d_to_list(vec_x),
                "vector_y": point_3d_to_list(vec_y),
                "vector_z": point_3d_to_list(vec_z),
            },
            "attributes": attributes
        }
        
        return {"status": "ok", "info": element_info}
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Element not found or API error: {e}"}

# --- EXTENDED ELEMENT CREATION HANDLERS ---

def handle_create_circular_beam_points(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle circular beam creation with points"""
    try:
        import element_controller as ec
        
        diameter = validate_positive_number(params["diameter"], "diameter")
        p1 = to_point_3d(params["p1"])
        p2 = to_point_3d(params["p2"])
        p3 = to_point_3d(params["p3"]) if params.get("p3") else None
        
        if p3:
            element_id = ec.create_circular_beam_points(diameter, p1, p2, p3)
        else:
            element_id = ec.create_circular_beam_points(diameter, p1, p2)
        
        if isinstance(element_id, int) and element_id >= 0:
            return {"status": "ok", "element_id": element_id}
        else:
            return {"status": "error", "message": f"Circular beam creation failed, returned: {element_id}"}
            
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except (ValueError, KeyError) as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create circular beam: {e}"}

def handle_create_square_beam_points(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle square beam creation with points"""
    try:
        import element_controller as ec
        
        width = validate_positive_number(params["width"], "width")
        p1 = to_point_3d(params["p1"])
        p2 = to_point_3d(params["p2"])
        p3 = to_point_3d(params["p3"]) if params.get("p3") else None
        
        if p3:
            element_id = ec.create_square_beam_points(width, p1, p2, p3)
        else:
            element_id = ec.create_square_beam_points(width, p1, p2)
        
        if isinstance(element_id, int) and element_id >= 0:
            return {"status": "ok", "element_id": element_id}
        else:
            return {"status": "error", "message": f"Square beam creation failed, returned: {element_id}"}
            
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except (ValueError, KeyError) as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create square beam: {e}"}

def handle_create_standard_beam_points(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle standard beam creation with points"""
    try:
        import element_controller as ec
        
        standard_element_name = params["standard_element_name"]
        if not standard_element_name or not isinstance(standard_element_name, str):
            raise ValueError("standard_element_name must be a non-empty string")
        p1 = to_point_3d(params["p1"])
        p2 = to_point_3d(params["p2"])
        p3 = to_point_3d(params["p3"]) if params.get("p3") else None
        
        if p3:
            element_id = ec.create_standard_beam_points(standard_element_name, p1, p2, p3)
        else:
            element_id = ec.create_standard_beam_points(standard_element_name, p1, p2)
        
        if isinstance(element_id, int) and element_id >= 0:
            return {"status": "ok", "element_id": element_id}
        else:
            return {"status": "error", "message": f"Standard beam creation failed, returned: {element_id}"}
            
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except (ValueError, KeyError) as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create standard beam: {e}"}

def handle_create_standard_panel_points(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle standard panel creation with points"""
    try:
        import element_controller as ec
        
        standard_element_name = params["standard_element_name"]
        if not standard_element_name or not isinstance(standard_element_name, str):
            raise ValueError("standard_element_name must be a non-empty string")
        p1 = to_point_3d(params["p1"])
        p2 = to_point_3d(params["p2"])
        p3 = to_point_3d(params["p3"]) if params.get("p3") else None
        
        if p3:
            element_id = ec.create_standard_panel_points(standard_element_name, p1, p2, p3)
        else:
            element_id = ec.create_standard_panel_points(standard_element_name, p1, p2)
        
        if isinstance(element_id, int) and element_id >= 0:
            return {"status": "ok", "element_id": element_id}
        else:
            return {"status": "error", "message": f"Standard panel creation failed, returned: {element_id}"}
            
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except (ValueError, KeyError) as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create standard panel: {e}"}

def handle_create_drilling_points(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle drilling creation with points"""
    try:
        import element_controller as ec
        
        diameter = validate_positive_number(params["diameter"], "diameter")
        p1 = to_point_3d(params["p1"])
        p2 = to_point_3d(params["p2"])
        
        element_id = ec.create_drilling_points(diameter, p1, p2)
        
        if isinstance(element_id, int) and element_id >= 0:
            return {"status": "ok", "element_id": element_id}
        else:
            return {"status": "error", "message": f"Drilling creation failed, returned: {element_id}"}
            
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except (ValueError, KeyError) as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create drilling: {e}"}

def handle_create_polygon_beam(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle polygon beam creation"""
    try:
        import element_controller as ec
        
        vertices = params["polygon_vertices"]
        if not isinstance(vertices, list) or len(vertices) < 3:
            raise ValueError("polygon_vertices must be a list with at least 3 points")
        
        polygon_vertices = [to_point_3d(vertex) for vertex in vertices]
        thickness = validate_positive_number(params["thickness"], "thickness")
        xl = to_point_3d(params["xl"])
        zl = to_point_3d(params["zl"])
        
        element_id = ec.create_polygon_beam(polygon_vertices, thickness, xl, zl)
        
        if isinstance(element_id, int) and element_id >= 0:
            return {"status": "ok", "element_id": element_id}
        else:
            return {"status": "error", "message": f"Polygon beam creation failed, returned: {element_id}"}
            
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except (ValueError, KeyError) as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create polygon beam: {e}"}

def handle_get_elements_by_type(aParams: dict) -> dict:
    """Finds all elements of a given type"""
    try:
        import element_controller as ec
        
        lElementType = aParams.get("element_type")
        
        if not lElementType or not isinstance(lElementType, str):
            return {"status": "error", "message": "element_type must be a non-empty string"}
        
        # Type mapping (string -> cadwork API number)
        lTypeMapping = {
            "beam": 1,
            "panel": 2, 
            "drilling": 3,
            "node": 4,
            "line": 5,
            "surface": 6,
            "volume": 7,
            "container": 8,
            "auxiliary": 9,
            "text_object": 10,
            "dimension": 11,
            "architectural": 12
        }
        
        if lElementType not in lTypeMapping:
            return {"status": "error", "message": f"Unknown element type: {lElementType}"}
        
        lTypeId = lTypeMapping[lElementType]
        
        # Find all elements of this type
        lAllElements = ec.get_all_identifiable_element_ids()
        lFilteredElements = []
        
        for lElementId in lAllElements:
            try:
                lCurrentType = ec.get_element_type(lElementId)
                if lCurrentType == lTypeId:
                    lFilteredElements.append(lElementId)
            except Exception:
                pass
        
        return {
            "status": "success",
            "element_type": lElementType,
            "type_id": lTypeId,
            "element_ids": lFilteredElements,
            "count": len(lFilteredElements)
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"get_elements_by_type failed: {e}"}

def handle_filter_elements_by_material(aParams: dict) -> dict:
    """Filters elements by material"""
    try:
        import element_controller as ec
        import attribute_controller as ac
        
        lMaterialName = aParams.get("material_name")
        
        if not lMaterialName or not isinstance(lMaterialName, str):
            return {"status": "error", "message": "material_name must be a non-empty string"}
        
        # Scan all elements in the model
        lAllElements = ec.get_all_identifiable_element_ids()
        lFilteredElements = []
        
        for lElementId in lAllElements:
            try:
                lCurrentMaterial = ac.get_element_material_name(lElementId)
                if lCurrentMaterial and lCurrentMaterial.strip().lower() == lMaterialName.strip().lower():
                    lFilteredElements.append(lElementId)
            except Exception:
                pass
        
        return {
            "status": "success",
            "material_name": lMaterialName,
            "element_ids": lFilteredElements,
            "count": len(lFilteredElements)
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"filter_elements_by_material failed: {e}"}

def handle_get_elements_in_group(aParams: dict) -> dict:
    """Finds all elements in a given group"""
    try:
        import element_controller as ec
        import attribute_controller as ac
        
        lGroupName = aParams.get("group_name")
        
        if not lGroupName or not isinstance(lGroupName, str):
            return {"status": "error", "message": "group_name must be a non-empty string"}
        
        # Scan all elements in the model
        lAllElements = ec.get_all_identifiable_element_ids()
        lFilteredElements = []
        
        for lElementId in lAllElements:
            try:
                lCurrentGroup = ac.get_group(lElementId)
                if lCurrentGroup and lCurrentGroup.strip().lower() == lGroupName.strip().lower():
                    lFilteredElements.append(lElementId)
            except Exception:
                pass
        
        return {
            "status": "success",
            "group_name": lGroupName,
            "element_ids": lFilteredElements,
            "count": len(lFilteredElements)
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"get_elements_in_group failed: {e}"}

def handle_get_element_count_by_type(aParams: dict) -> dict:
    """Counts the elements per type"""
    try:
        import element_controller as ec
        
        # Typ-Mapping
        lTypeMapping = {
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
        
        # All elements in the model
        lAllElements = ec.get_all_identifiable_element_ids()
        lTypeCounts = {}
        lTotalCount = 0
        
        # Count the elements by type
        for lElementId in lAllElements:
            try:
                lTypeId = ec.get_element_type(lElementId)
                lTypeName = lTypeMapping.get(lTypeId, f"unknown_type_{lTypeId}")
                
                if lTypeName not in lTypeCounts:
                    lTypeCounts[lTypeName] = 0
                lTypeCounts[lTypeName] += 1
                lTotalCount += 1
            except Exception:
                pass
        
        # Calculate the percentage distribution
        lTypePercentages = {}
        if lTotalCount > 0:
            for lTypeName, lCount in lTypeCounts.items():
                lTypePercentages[lTypeName] = (lCount / lTotalCount) * 100.0
        
        return {
            "status": "ok",
            "total_elements": lTotalCount,
            "type_counts": lTypeCounts,
            "type_percentages": lTypePercentages,
            "available_types": list(lTypeCounts.keys())
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"get_element_count_by_type failed: {e}"}

def handle_get_material_statistics(aParams: dict) -> dict:
    """Collects material statistics for the whole model"""
    try:
        import element_controller as ec
        import attribute_controller as ac
        
        # All elements in the model
        lAllElements = ec.get_all_identifiable_element_ids()
        lMaterialCounts = {}
        lTotalCount = 0
        lElementsWithoutMaterial = 0
        
        # Count the materials of all elements
        for lElementId in lAllElements:
            try:
                lMaterial = ac.get_element_material_name(lElementId)
                if lMaterial and lMaterial.strip():
                    lMaterialName = lMaterial.strip()
                    if lMaterialName not in lMaterialCounts:
                        lMaterialCounts[lMaterialName] = 0
                    lMaterialCounts[lMaterialName] += 1
                else:
                    lElementsWithoutMaterial += 1
                lTotalCount += 1
            except Exception:
                lElementsWithoutMaterial += 1
                lTotalCount += 1
        
        # Calculate the percentage distribution
        lMaterialPercentages = {}
        if lTotalCount > 0:
            for lMaterialName, lCount in lMaterialCounts.items():
                lMaterialPercentages[lMaterialName] = (lCount / lTotalCount) * 100.0
        
        # Top Materialien sortieren
        lSortedMaterials = sorted(lMaterialCounts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "status": "ok",
            "total_elements": lTotalCount,
            "elements_with_material": lTotalCount - lElementsWithoutMaterial,
            "elements_without_material": lElementsWithoutMaterial,
            "material_counts": lMaterialCounts,
            "material_percentages": lMaterialPercentages,
            "available_materials": list(lMaterialCounts.keys()),
            "top_materials": lSortedMaterials[:10],
            "unique_materials_count": len(lMaterialCounts)
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"get_material_statistics failed: {e}"}

def handle_get_group_statistics(aParams: dict) -> dict:
    """Collects group statistics for the whole model"""
    try:
        import element_controller as ec
        import attribute_controller as ac
        
        # All elements in the model
        lAllElements = ec.get_all_identifiable_element_ids()
        lGroupCounts = {}
        lTotalCount = 0
        lElementsWithoutGroup = 0
        
        # Count the groups of all elements
        for lElementId in lAllElements:
            try:
                lGroup = ac.get_group(lElementId)
                if lGroup and lGroup.strip():
                    lGroupName = lGroup.strip()
                    if lGroupName not in lGroupCounts:
                        lGroupCounts[lGroupName] = 0
                    lGroupCounts[lGroupName] += 1
                else:
                    lElementsWithoutGroup += 1
                lTotalCount += 1
            except Exception:
                lElementsWithoutGroup += 1
                lTotalCount += 1
        
        # Calculate the percentage distribution
        lGroupPercentages = {}
        if lTotalCount > 0:
            for lGroupName, lCount in lGroupCounts.items():
                lGroupPercentages[lGroupName] = (lCount / lTotalCount) * 100.0
        
        # Sort the top groups
        lSortedGroups = sorted(lGroupCounts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "status": "ok",
            "total_elements": lTotalCount,
            "elements_with_group": lTotalCount - lElementsWithoutGroup,
            "elements_without_group": lElementsWithoutGroup,
            "group_counts": lGroupCounts,
            "group_percentages": lGroupPercentages,
            "available_groups": list(lGroupCounts.keys()),
            "top_groups": lSortedGroups,
            "unique_groups_count": len(lGroupCounts)
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"get_group_statistics failed: {e}"}

def handle_duplicate_elements(aParams: dict) -> dict:
    """Duplicates elements in place"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        
        if not isinstance(lElementIds, list) or not lElementIds:
            return {"status": "error", "message": "element_ids must be a non-empty list"}
        
        # Validate element IDs
        try:
            lValidatedIds = validate_element_ids(lElementIds)
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        
        lNewElementIds = []
        lFailedElements = []
        
        # Convert zero vector to point_3d
        lZeroVector = to_point_3d([0.0, 0.0, 0.0])
        
        # Duplicate the elements one by one
        for lElementId in lValidatedIds:
            try:
                # Copy with a zero vector (no offset)
                lCopyResult = ec.copy_elements([lElementId], lZeroVector)
                if lCopyResult and len(lCopyResult) > 0:
                    lNewElementIds.extend(lCopyResult)
                else:
                    lFailedElements.append(lElementId)
            except Exception:
                lFailedElements.append(lElementId)
        
        return {
            "status": "ok",
            "message": f"Duplicated {len(lNewElementIds)} elements",
            "original_element_ids": lValidatedIds,
            "new_element_ids": lNewElementIds,
            "failed_elements": lFailedElements,
            "duplicated_count": len(lNewElementIds),
            "failed_count": len(lFailedElements),
            "total_count": len(lValidatedIds)
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"duplicate_elements failed: {e}"}


def handle_join_elements(aParams: dict) -> dict:
    """Joins elements together"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        
        if not isinstance(lElementIds, list) or len(lElementIds) < 2:
            return {"status": "error", "message": "element_ids must be a list with at least 2 element IDs"}
        
        # Validate element IDs
        try:
            lValidatedIds = validate_element_ids(lElementIds)
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        
        # Call the cadwork API - join all elements at once
        try:
            ec.join_elements(lValidatedIds)
            
            return {
                "status": "ok",
                "message": f"Successfully joined {len(lValidatedIds)} elements",
                "joined_elements": lValidatedIds,
                "joined_count": len(lValidatedIds)
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Join operation failed: {e}"}
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"join_elements failed: {e}"}

def handle_unjoin_elements(aParams: dict) -> dict:
    """Separates joined elements"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        
        if not isinstance(lElementIds, list) or not lElementIds:
            return {"status": "error", "message": "element_ids must be a non-empty list"}
        
        # Validate element IDs
        try:
            lValidatedIds = validate_element_ids(lElementIds)
        except ValueError as e:
            return {"status": "error", "message": str(e)}
        
        # Cadwork API aufrufen
        ec.unjoin_elements(lValidatedIds)
        
        return {
            "status": "ok",
            "message": f"Successfully unjoined {len(lValidatedIds)} elements",
            "processed_elements": lValidatedIds,
            "unjoined_count": len(lValidatedIds)
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"unjoin_elements failed: {e}"}


def handle_cut_corner_lap(aParams: dict) -> dict:
    """Creates a corner lap joint between elements"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        lCutParams = aParams.get("cut_params", {})
        
        if len(lElementIds) < 2:
            return {"status": "error", "message": "At least 2 element IDs required for corner lap cut"}
        
        # Cadwork API aufrufen - Eckblatt-Verbindung
        lProcessedElements = []
        lFailedElements = []
        
        try:
            # Perform the corner lap cut
            # Typically the first element is used as the "master"
            lMasterElement = lElementIds[0]
            lTargetElements = lElementIds[1:]
            
            for lTargetElement in lTargetElements:
                try:
                    # Run the cadwork cut operation
                    # The exact parameters depend on the cadwork API
                    if lCutParams:
                        ec.cut_corner_lap_with_params([lMasterElement, lTargetElement], lCutParams)
                    else:
                        ec.cut_corner_lap([lMasterElement, lTargetElement])
                    
                    lProcessedElements.extend([lMasterElement, lTargetElement])
                except Exception as e:
                    lFailedElements.append({"elements": [lMasterElement, lTargetElement], "error": str(e)})
            
        except Exception as e:
            return {"status": "error", "message": f"Corner lap cut operation failed: {e}"}
        
        return {
            "status": "ok",
            "message": f"Successfully created corner lap cuts for {len(lProcessedElements)} elements",
            "cut_type": "corner_lap",
            "master_element": lMasterElement,
            "target_elements": lTargetElements,
            "processed_elements": lProcessedElements,
            "failed_elements": lFailedElements,
            "cut_params": lCutParams
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"cut_corner_lap failed: {e}"}

def handle_cut_cross_lap(aParams: dict) -> dict:
    """Creates a cross lap joint between elements"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        lCutParams = aParams.get("cut_params", {})
        
        if len(lElementIds) < 2:
            return {"status": "error", "message": "At least 2 element IDs required for cross lap cut"}
        
        # Cadwork API aufrufen - Kreuzblatt-Verbindung
        lProcessedElements = []
        lFailedElements = []
        
        try:
            # Perform the cross lap cut  
            # A cross lap cuts both elements
            lElement1 = lElementIds[0]
            lElement2 = lElementIds[1]
            
            # For multiple elements: process them pairwise
            for i in range(0, len(lElementIds) - 1, 2):
                try:
                    lElem1 = lElementIds[i]
                    lElem2 = lElementIds[i + 1] if i + 1 < len(lElementIds) else lElementIds[0]
                    
                    # Run the cadwork cut operation
                    if lCutParams:
                        ec.cut_cross_lap_with_params([lElem1, lElem2], lCutParams)
                    else:
                        ec.cut_cross_lap([lElem1, lElem2])
                    
                    lProcessedElements.extend([lElem1, lElem2])
                except Exception as e:
                    lFailedElements.append({"elements": [lElem1, lElem2], "error": str(e)})
            
        except Exception as e:
            return {"status": "error", "message": f"Cross lap cut operation failed: {e}"}
        
        return {
            "status": "ok",
            "message": f"Successfully created cross lap cuts for {len(lProcessedElements)} elements",
            "cut_type": "cross_lap", 
            "processed_elements": lProcessedElements,
            "failed_elements": lFailedElements,
            "cut_params": lCutParams,
            "pairs_processed": len(lProcessedElements) // 2
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"cut_cross_lap failed: {e}"}


def handle_cut_half_lap(aParams: dict) -> dict:
    """Creates a half lap joint between elements"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        lCutParams = aParams.get("cut_params", {})
        
        if len(lElementIds) < 2:
            return {"status": "error", "message": "At least 2 element IDs required for half lap cut"}
        
        # Cadwork API aufrufen - Halbes Blatt-Verbindung
        lProcessedElements = []
        lFailedElements = []
        
        try:
            # Half Lap Cut Parameter extrahieren
            lMasterElement = lCutParams.get("master_element", lElementIds[0])
            lCutDepthRatio = lCutParams.get("cut_depth_ratio", 0.5)
            lCutPosition = lCutParams.get("cut_position", "end")
            
            # Perform the half lap cut
            # The master element is cut halfway, the other elements all the way
            for lTargetElement in lElementIds:
                if lTargetElement == lMasterElement:
                    continue
                    
                try:
                    # Cadwork Half Lap Cut-Operation
                    if "cut_depth_ratio" in lCutParams:
                        ec.cut_half_lap_with_ratio([lMasterElement, lTargetElement], 
                                                 lCutDepthRatio, lCutPosition)
                    else:
                        ec.cut_half_lap([lMasterElement, lTargetElement])
                    
                    lProcessedElements.extend([lMasterElement, lTargetElement])
                except Exception as e:
                    lFailedElements.append({
                        "master": lMasterElement, 
                        "target": lTargetElement, 
                        "error": str(e)
                    })
            
        except Exception as e:
            return {"status": "error", "message": f"Half lap cut operation failed: {e}"}
        
        return {
            "status": "ok",
            "message": f"Successfully created half lap cuts for {len(lProcessedElements)} elements",
            "cut_type": "half_lap",
            "master_element": lMasterElement,
            "cut_depth_ratio": lCutDepthRatio,
            "cut_position": lCutPosition,
            "processed_elements": lProcessedElements,
            "failed_elements": lFailedElements,
            "cut_params": lCutParams
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"cut_half_lap failed: {e}"}

def handle_cut_double_tenon(aParams: dict) -> dict:
    """Creates a double tenon joint between elements"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        lCutParams = aParams.get("cut_params", {})
        
        if len(lElementIds) != 2:
            return {"status": "error", "message": "Exactly 2 element IDs required for double tenon cut"}
        
        # Cadwork API aufrufen - Doppelzapfen-Verbindung
        try:
            # Double Tenon Parameter extrahieren
            lTenonElement = lCutParams.get("tenon_element", lElementIds[0])
            lMortiseElement = lCutParams.get("mortise_element", lElementIds[1])
            lTenonWidth = lCutParams.get("tenon_width", 40)
            lTenonHeight = lCutParams.get("tenon_height", 80)
            lTenonSpacing = lCutParams.get("tenon_spacing", 60)
            lTenonDepth = lCutParams.get("tenon_depth", 50)
            
            # Validate the parameters
            if lTenonElement not in lElementIds or lMortiseElement not in lElementIds:
                return {"status": "error", "message": "Tenon and mortise elements must be from provided element IDs"}
            
            # Run the cadwork double tenon cut operation
            lTenonParams = {
                "width": lTenonWidth,
                "height": lTenonHeight, 
                "spacing": lTenonSpacing,
                "depth": lTenonDepth
            }
            
            if all(param in lCutParams for param in ["tenon_width", "tenon_height", "tenon_spacing"]):
                ec.cut_double_tenon_with_params([lTenonElement, lMortiseElement], lTenonParams)
            else:
                ec.cut_double_tenon([lTenonElement, lMortiseElement])
            
        except Exception as e:
            return {"status": "error", "message": f"Double tenon cut operation failed: {e}"}
        
        return {
            "status": "ok",
            "message": f"Successfully created double tenon connection",
            "cut_type": "double_tenon",
            "tenon_element": lTenonElement,
            "mortise_element": lMortiseElement,
            "tenon_specifications": {
                "width": lTenonWidth,
                "height": lTenonHeight,
                "spacing": lTenonSpacing,
                "depth": lTenonDepth
            },
            "processed_elements": lElementIds,
            "cut_params": lCutParams
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"cut_double_tenon failed: {e}"}


def handle_cut_scarf_joint(aParams: dict) -> dict:
    """Creates a scarf joint between elements"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        lCutParams = aParams.get("cut_params", {})
        
        if len(lElementIds) != 2:
            return {"status": "error", "message": "Exactly 2 element IDs required for scarf joint"}
        
        # Call the cadwork API - scarf joint
        try:
            # Scarf Joint Parameter extrahieren
            lScarfType = lCutParams.get("scarf_type", "plain_scarf")
            lScarfLength = lCutParams.get("scarf_length", 400)
            lScarfAngle = lCutParams.get("scarf_angle", 30)
            lElement1 = lCutParams.get("element_1", lElementIds[0])
            lElement2 = lCutParams.get("element_2", lElementIds[1])
            lOverlapLength = lCutParams.get("overlap_length", 50)
            
            # Validate the parameters
            if lElement1 not in lElementIds or lElement2 not in lElementIds:
                return {"status": "error", "message": "Element references must be from provided element IDs"}
            
            # Parameter-Validierung
            if lScarfLength <= 0 or lScarfAngle <= 0 or lScarfAngle >= 90:
                return {"status": "error", "message": "Invalid scarf parameters: length > 0, angle between 0-90 degrees"}
            
            # Run the cadwork scarf joint cut operation
            lScarfParams = {
                "type": lScarfType,
                "length": lScarfLength,
                "angle": lScarfAngle,
                "overlap": lOverlapLength
            }
            
            if "scarf_length" in lCutParams and "scarf_angle" in lCutParams:
                ec.cut_scarf_joint_with_params([lElement1, lElement2], lScarfParams)
            else:
                ec.cut_scarf_joint([lElement1, lElement2])
            
        except Exception as e:
            return {"status": "error", "message": f"Scarf joint cut operation failed: {e}"}
        
        return {
            "status": "ok",
            "message": f"Successfully created scarf joint connection",
            "cut_type": "scarf_joint",
            "scarf_specifications": {
                "type": lScarfType,
                "length": lScarfLength,
                "angle": lScarfAngle,
                "overlap_length": lOverlapLength
            },
            "element_1": lElement1,
            "element_2": lElement2,
            "processed_elements": lElementIds,
            "cut_params": lCutParams
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"cut_scarf_joint failed: {e}"}

def handle_cut_shoulder(aParams: dict) -> dict:
    """Creates a shoulder cut between elements"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        lCutParams = aParams.get("cut_params", {})
        
        if len(lElementIds) < 2:
            return {"status": "error", "message": "At least 2 element IDs required for shoulder cut"}
        
        # Cadwork API aufrufen - Schulterschnitt
        lProcessedPairs = []
        lFailedPairs = []
        
        try:
            # Shoulder Cut Parameter extrahieren
            lSupportingElement = lCutParams.get("supporting_element", lElementIds[0])
            lShoulderDepth = lCutParams.get("shoulder_depth", 40)
            lShoulderWidth = lCutParams.get("shoulder_width", 120)
            lShoulderType = lCutParams.get("shoulder_type", "simple_shoulder")
            lContactAngle = lCutParams.get("contact_angle", 90)
            
            # Parameter-Validierung
            if lShoulderDepth <= 0 or lShoulderWidth <= 0:
                return {"status": "error", "message": "Shoulder depth and width must be positive values"}
            
            if lContactAngle <= 0 or lContactAngle > 180:
                return {"status": "error", "message": "Contact angle must be between 0 and 180 degrees"}
            
            # Run the shoulder cut on all elements (except the supporting element)
            for lSupportedElement in lElementIds:
                if lSupportedElement == lSupportingElement:
                    continue
                    
                try:
                    # Cadwork Shoulder Cut-Operation
                    lShoulderParams = {
                        "depth": lShoulderDepth,
                        "width": lShoulderWidth,
                        "type": lShoulderType,
                        "angle": lContactAngle
                    }
                    
                    if all(param in lCutParams for param in ["shoulder_depth", "shoulder_width"]):
                        ec.cut_shoulder_with_params([lSupportingElement, lSupportedElement], lShoulderParams)
                    else:
                        ec.cut_shoulder([lSupportingElement, lSupportedElement])
                    
                    lProcessedPairs.append({
                        "supporting": lSupportingElement,
                        "supported": lSupportedElement
                    })
                except Exception as e:
                    lFailedPairs.append({
                        "supporting": lSupportingElement,
                        "supported": lSupportedElement,
                        "error": str(e)
                    })
            
        except Exception as e:
            return {"status": "error", "message": f"Shoulder cut operation failed: {e}"}
        
        return {
            "status": "ok",
            "message": f"Successfully created shoulder cuts for {len(lProcessedPairs)} element pairs",
            "cut_type": "shoulder",
            "supporting_element": lSupportingElement,
            "shoulder_specifications": {
                "depth": lShoulderDepth,
                "width": lShoulderWidth,
                "type": lShoulderType,
                "contact_angle": lContactAngle
            },
            "processed_pairs": lProcessedPairs,
            "failed_pairs": lFailedPairs,
            "total_pairs": len(lProcessedPairs),
            "cut_params": lCutParams
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"cut_shoulder failed: {e}"}


def handle_create_auxiliary_beam_points(aParams: dict) -> dict:
    """Creates an auxiliary beam element from points"""
    try:
        import element_controller as ec
        
        # Parameter extrahieren
        lP1 = aParams.get("p1")
        lP2 = aParams.get("p2") 
        lP3 = aParams.get("p3")
        
        if not lP1 or not lP2:
            return {"status": "error", "message": "p1 and p2 points are required"}
        
        # Convert to a cadwork point_3d
        lCwP1 = to_point_3d(lP1)
        lCwP2 = to_point_3d(lP2)
        lCwP3 = to_point_3d(lP3) if lP3 else None
        
        # Cadwork API aufrufen
        if lCwP3:
            lElementId = ec.create_auxiliary_beam_points(lCwP1, lCwP2, lCwP3)
        else:
            lElementId = ec.create_auxiliary_beam_points(lCwP1, lCwP2)
        
        return {
            "status": "ok",
            "element_id": lElementId,
            "element_type": "auxiliary_beam",
            "p1": lP1,
            "p2": lP2,
            "p3": lP3,
            "operation": "create_auxiliary_beam_points"
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"create_auxiliary_beam_points failed: {e}"}

def handle_convert_beam_to_panel(aParams: dict) -> dict:
    """Converts beams into panels"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        
        if not lElementIds:
            return {"status": "error", "message": "No element IDs provided"}
        
        # Before conversion - collect element information  
        lBeforeInfo = []
        for lId in lElementIds:
            try:
                lInfo = ec.get_element_info(lId)
                lBeforeInfo.append({"id": lId, "type": lInfo.get("type", "unknown")})
            except:
                lBeforeInfo.append({"id": lId, "type": "unknown"})
        
        # Cadwork API aufrufen
        lNewElementIds = ec.convert_beam_to_panel(lElementIds)
        
        return {
            "status": "ok", 
            "converted_elements": len(lElementIds),
            "original_element_ids": lElementIds,
            "new_element_ids": lNewElementIds if isinstance(lNewElementIds, list) else [lNewElementIds],
            "before_conversion": lBeforeInfo,
            "operation": "convert_beam_to_panel"
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"convert_beam_to_panel failed: {e}"}


def handle_convert_panel_to_beam(aParams: dict) -> dict:
    """Converts panels into beams"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        
        if not lElementIds:
            return {"status": "error", "message": "No element IDs provided"}
        
        # Before conversion - collect element information  
        lBeforeInfo = []
        for lId in lElementIds:
            try:
                lInfo = ec.get_element_info(lId)
                lBeforeInfo.append({"id": lId, "type": lInfo.get("type", "unknown")})
            except:
                lBeforeInfo.append({"id": lId, "type": "unknown"})
        
        # Cadwork API aufrufen
        lNewElementIds = ec.convert_panel_to_beam(lElementIds)
        
        return {
            "status": "ok", 
            "converted_elements": len(lElementIds),
            "original_element_ids": lElementIds,
            "new_element_ids": lNewElementIds if isinstance(lNewElementIds, list) else [lNewElementIds],
            "before_conversion": lBeforeInfo,
            "conversion_type": "panel_to_beam",
            "operation": "convert_panel_to_beam"
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"convert_panel_to_beam failed: {e}"}

def handle_convert_auxiliary_to_beam(aParams: dict) -> dict:
    """Converts auxiliary elements into regular beams"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        
        if not lElementIds:
            return {"status": "error", "message": "No element IDs provided"}
        
        # Before conversion - collect element information  
        lBeforeInfo = []
        for lId in lElementIds:
            try:
                lInfo = ec.get_element_info(lId)
                lBeforeInfo.append({"id": lId, "type": lInfo.get("type", "unknown")})
            except:
                lBeforeInfo.append({"id": lId, "type": "auxiliary_unknown"})
        
        # Cadwork API aufrufen
        lNewElementIds = ec.convert_auxiliary_to_beam(lElementIds)
        
        return {
            "status": "ok", 
            "converted_elements": len(lElementIds),
            "original_element_ids": lElementIds,
            "new_element_ids": lNewElementIds if isinstance(lNewElementIds, list) else [lNewElementIds],
            "before_conversion": lBeforeInfo,
            "conversion_type": "auxiliary_to_beam",
            "operation": "convert_auxiliary_to_beam"
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"convert_auxiliary_to_beam failed: {e}"}


def handle_create_auto_container_from_standard(aParams: dict) -> dict:
    """Creates an automatic container from standard elements"""
    try:
        import element_controller as ec
        
        lElementIds = aParams.get("element_ids", [])
        lContainerName = aParams.get("container_name", "")
        
        if not lElementIds:
            return {"status": "error", "message": "No element IDs provided"}
        
        if not lContainerName:
            return {"status": "error", "message": "No container name provided"}
        
        # Before creating the container - collect element information
        lElementInfo = []
        for lId in lElementIds:
            try:
                lInfo = ec.get_element_info(lId)
                lElementInfo.append({
                    "id": lId, 
                    "type": lInfo.get("type", "unknown"),
                    "name": lInfo.get("name", "")
                })
            except:
                lElementInfo.append({"id": lId, "type": "unknown", "name": ""})
        
        # Cadwork API aufrufen
        lContainerId = ec.create_auto_container_from_standard(lElementIds, lContainerName)
        
        return {
            "status": "ok",
            "container_id": lContainerId,
            "container_name": lContainerName,
            "element_count": len(lElementIds),
            "contained_elements": lElementIds,
            "element_info": lElementInfo,
            "operation": "create_auto_container_from_standard"
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"create_auto_container_from_standard failed: {e}"}

def handle_get_container_content_elements(aParams: dict) -> dict:
    """Retrieves the container content"""
    try:
        import element_controller as ec
        
        lContainerId = aParams.get("container_id")
        
        if lContainerId is None:
            return {"status": "error", "message": "No container ID provided"}
        
        # Cadwork API aufrufen
        lContentElements = ec.get_container_content_elements(lContainerId)
        
        # Convert the element IDs to a list if needed
        if not isinstance(lContentElements, list):
            if lContentElements is None:
                lContentElements = []
            else:
                lContentElements = [lContentElements]
        
        # Collect additional information about the contained elements
        lElementDetails = []
        for lElementId in lContentElements:
            try:
                lInfo = ec.get_element_info(lElementId)
                lElementDetails.append({
                    "id": lElementId,
                    "type": lInfo.get("type", "unknown"),
                    "name": lInfo.get("name", ""),
                    "material": lInfo.get("material", "")
                })
            except:
                lElementDetails.append({
                    "id": lElementId, 
                    "type": "unknown", 
                    "name": "", 
                    "material": ""
                })
        
        return {
            "status": "ok",
            "container_id": lContainerId,
            "element_count": len(lContentElements),
            "content_element_ids": lContentElements,
            "element_details": lElementDetails,
            "operation": "get_container_content_elements"
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"get_container_content_elements failed: {e}"}


def handle_create_surface(aParams: dict) -> dict:
    """Create surface element from vertices"""
    try:
        import element_controller as ec
        
        # Validate required arguments
        lVertices = aParams.get("vertices", [])
        lSurfaceType = aParams.get("surface_type", "flat")
        
        if not lVertices or len(lVertices) < 3:
            return {"status": "error", "message": "At least 3 vertices required for surface"}
        
        # Convert vertices to point_3d objects
        lPoint3dVertices = []
        for lVertex in lVertices:
            try:
                lPoint = to_point_3d(lVertex)
                lPoint3dVertices.append(lPoint)
            except Exception as e:
                return {"status": "error", "message": f"Invalid vertex format: {e}"}
        
        # Create surface using Cadwork API
        lSurfaceId = ec.create_surface(lPoint3dVertices)
        
        if isinstance(lSurfaceId, int) and lSurfaceId >= 0:
            return {
                "status": "ok", 
                "id": lSurfaceId,
                "vertex_count": len(lVertices),
                "surface_type": lSurfaceType
            }
        else:
            return {"status": "error", "message": f"Surface creation failed, returned: {lSurfaceId}"}
            
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"create_surface failed: {e}"}


def handle_create_beam_from_points(aParams: dict) -> dict:
    """Create beam element from series of points defining centerline"""
    try:
        import element_controller as ec
        
        # Validate required arguments
        lPoints = aParams.get("points", [])
        lCrossSection = aParams.get("cross_section", {})
        lMaterial = aParams.get("material", "Wood")
        
        if not lPoints or len(lPoints) < 2:
            return {"status": "error", "message": "At least 2 points required for beam"}
        
        if not lCrossSection:
            return {"status": "error", "message": "Cross section parameters required"}
        
        # Convert points to point_3d objects
        lPoint3dList = []
        for lPoint in lPoints:
            try:
                lPoint3d = to_point_3d(lPoint)
                lPoint3dList.append(lPoint3d)
            except Exception as e:
                return {"status": "error", "message": f"Invalid point format: {e}"}
        
        # Extract cross section parameters
        lWidth = validate_positive_number(lCrossSection.get("width", 100), "width")
        lHeight = validate_positive_number(lCrossSection.get("height", 100), "height")
        
        # Use first two points to create beam, then extend if needed
        lP1 = lPoint3dList[0]
        lP2 = lPoint3dList[1]
        
        # Create optional P3 for orientation if not provided
        import cadwork
        lP3 = cadwork.point_3d(lP1.x, lP1.y, lP1.z + 1.0)
        
        # Create initial beam with proper point_3d objects
        lBeamId = ec.create_rectangular_beam_points(lWidth, lHeight, lP1, lP2, lP3)
        
        if isinstance(lBeamId, int) and lBeamId >= 0:
            return {
                "status": "ok", 
                "id": lBeamId,
                "point_count": len(lPoints),
                "material": lMaterial,
                "cross_section": lCrossSection
            }
        else:
            return {"status": "error", "message": f"Beam creation failed, returned: {lBeamId}"}
            
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except ValueError as e:
        return {"status": "error", "message": f"Invalid input: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"create_beam_from_points failed: {e}"}


def handle_create_auxiliary_line(aParams: dict) -> dict:
    """Create auxiliary line element for construction purposes"""
    try:
        import element_controller as ec
        
        # Validate required arguments
        lStartPoint = aParams.get("start_point", [])
        lEndPoint = aParams.get("end_point", [])
        lLineType = aParams.get("line_type", "construction")
        
        if not lStartPoint or len(lStartPoint) != 3:
            return {"status": "error", "message": "start_point must be [x,y,z] coordinates"}
        
        if not lEndPoint or len(lEndPoint) != 3:
            return {"status": "error", "message": "end_point must be [x,y,z] coordinates"}
        
        # Convert to point_3d objects
        try:
            lP1 = to_point_3d(lStartPoint)
            lP2 = to_point_3d(lEndPoint)
        except Exception as e:
            return {"status": "error", "message": f"Invalid point format: {e}"}
        
        # Create auxiliary line using Cadwork API
        # Use auxiliary beam creation instead if direct auxiliary line is not available
        try:
            lLineId = ec.create_auxiliary_line(lP1, lP2)
        except AttributeError:
            # Fallback: create minimal beam as auxiliary line
            lLineId = ec.create_rectangular_beam_points(10.0, 10.0, lP1, lP2)  # 10x10mm beam
        
        if isinstance(lLineId, int) and lLineId >= 0:
            return {
                "status": "ok", 
                "id": lLineId,
                "line_type": lLineType,
                "start_point": lStartPoint,
                "end_point": lEndPoint
            }
        else:
            return {"status": "error", "message": f"Auxiliary line creation failed, returned: {lLineId}"}
            
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"create_auxiliary_line failed: {e}"}


def handle_create_solid_wood_panel(aParams: dict) -> dict:
    """Create solid wood panel with specified wood type and grain direction"""
    try:
        import element_controller as ec
        import attribute_controller as ac
        
        # Validate required arguments
        lP1 = aParams.get("p1", [])
        lP2 = aParams.get("p2", [])
        lThickness = aParams.get("thickness")
        lWoodType = aParams.get("wood_type", "Generic")
        lP3Raw = aParams.get("p3")
        
        if not lP1 or len(lP1) != 3:
            return {"status": "error", "message": "p1 must be [x,y,z] coordinates"}
        
        if not lP2 or len(lP2) != 3:
            return {"status": "error", "message": "p2 must be [x,y,z] coordinates"}
        
        if lThickness is None:
            return {"status": "error", "message": "thickness is required"}
        
        # Convert and validate arguments
        try:
            lPoint1 = to_point_3d(lP1)
            lPoint2 = to_point_3d(lP2)
            lThicknessVal = validate_positive_number(lThickness, "thickness")
        except Exception as e:
            return {"status": "error", "message": f"Invalid input: {e}"}
        
        # Handle optional p3
        if lP3Raw is None:
            import cadwork
            lPoint3 = cadwork.point_3d(lPoint1.x, lPoint1.y, lPoint1.z + 1.0)
        else:
            try:
                lPoint3 = to_point_3d(lP3Raw)
            except Exception as e:
                return {"status": "error", "message": f"Invalid p3 format: {e}"}
        
        # Create solid wood panel using standard panel creation
        # Calculate width from distance between points
        import math
        lWidth = math.sqrt((lPoint2.x - lPoint1.x)**2 + (lPoint2.y - lPoint1.y)**2 + (lPoint2.z - lPoint1.z)**2)
        
        lPanelId = ec.create_rectangular_panel_points(lWidth, lThicknessVal, lPoint1, lPoint2, lPoint3)
        
        if isinstance(lPanelId, int) and lPanelId >= 0:
            # Set wood type as material if provided
            if lWoodType != "Generic":
                try:
                    import attribute_controller as ac
                    ac.set_material(lPanelId, lWoodType)
                except:
                    pass  # Continue even if material setting fails
            
            return {
                "status": "ok", 
                "id": lPanelId,
                "wood_type": lWoodType,
                "thickness": lThicknessVal
            }
        else:
            return {"status": "error", "message": f"Solid wood panel creation failed, returned: {lPanelId}"}
            
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"create_solid_wood_panel failed: {e}"}


def handle_get_elements_in_region(aParams: dict) -> dict:
    """Get elements in a specific region/bounding box"""
    try:
        import element_controller as ec
        import geometry_controller as gc
        
        # Get region parameters
        lMinPoint = aParams.get("min_point", [])
        lMaxPoint = aParams.get("max_point", [])
        lIncludePartially = aParams.get("include_partially", True)
        
        # Validate region parameters
        if not lMinPoint or len(lMinPoint) != 3:
            return {"status": "error", "message": "min_point must be [x,y,z] coordinates"}
        
        if not lMaxPoint or len(lMaxPoint) != 3:
            return {"status": "error", "message": "max_point must be [x,y,z] coordinates"}
        
        # Validate that min < max for all dimensions
        for i in range(3):
            if lMinPoint[i] >= lMaxPoint[i]:
                return {"status": "error", "message": f"min_point[{i}] must be less than max_point[{i}]"}
        
        # Get all elements
        lAllElements = ec.get_all_identifiable_element_ids()
        lElementsInRegion = []
        
        # Check each element's position
        for lElementId in lAllElements:
            try:
                # Get element's P1 and P2 for bounding box calculation
                lP1 = gc.get_p1(lElementId)
                lP2 = gc.get_p2(lElementId)
                
                # Calculate element's bounding box
                lElemMinX = min(lP1.x, lP2.x)
                lElemMaxX = max(lP1.x, lP2.x)
                lElemMinY = min(lP1.y, lP2.y)
                lElemMaxY = max(lP1.y, lP2.y)
                lElemMinZ = min(lP1.z, lP2.z)
                lElemMaxZ = max(lP1.z, lP2.z)
                
                # Check if element is completely inside region
                lCompletelyInside = (lElemMinX >= lMinPoint[0] and lElemMaxX <= lMaxPoint[0] and
                                    lElemMinY >= lMinPoint[1] and lElemMaxY <= lMaxPoint[1] and
                                    lElemMinZ >= lMinPoint[2] and lElemMaxZ <= lMaxPoint[2])
                
                # Check if element overlaps region (bounding boxes intersect)
                lOverlaps = not (lElemMaxX < lMinPoint[0] or lElemMinX > lMaxPoint[0] or
                               lElemMaxY < lMinPoint[1] or lElemMinY > lMaxPoint[1] or
                               lElemMaxZ < lMinPoint[2] or lElemMinZ > lMaxPoint[2])
                
                # Add element based on filter mode
                if lCompletelyInside or (lIncludePartially and lOverlaps):
                    lElementsInRegion.append(lElementId)
                    
            except Exception:
                # Skip elements that can't be queried
                pass
        
        return {
            "status": "ok",
            "elements_in_region": lElementsInRegion,
            "element_count": len(lElementsInRegion),
            "total_elements_checked": len(lAllElements),
            "region_bounds": {
                "min": lMinPoint,
                "max": lMaxPoint
            },
            "include_partially": lIncludePartially
        }
        
    except ImportError as e:
        return {"status": "error", "message": f"Failed to import Cadwork modules: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"get_elements_in_region failed: {e}"}
