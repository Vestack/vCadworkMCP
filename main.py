"""
New clean Cadwork MCP Server with Axis Configuration Support
"""
import os
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP
from core.server import create_mcp_server
from core.logging import get_logger

# Import Cadwork axis configuration
try:
    from config.cadwork_axis_config import CADWORK_AXIS_INFO, CadworkAxisHelper
    AXIS_CONFIG_AVAILABLE = True
except ImportError:
    CADWORK_AXIS_INFO = "Cadwork axis configuration not available"
    AXIS_CONFIG_AVAILABLE = False
from controllers.element_controller import ElementController
from controllers.geometry_controller import GeometryController
from controllers.attribute_controller import AttributeController
from controllers.visualization_controller import VisualizationController
from controllers.utility_controller import UtilityController
from controllers.shop_drawing_controller import ShopDrawingController
from controllers.roof_controller import RoofController
from controllers.machine_controller import MachineController
from controllers.measurement_controller import MeasurementController
from controllers.material_controller import MaterialController
from controllers.export_controller import ExportController
from controllers.import_controller import ImportController
from controllers.container_controller import ContainerController
from controllers.transformation_controller import TransformationController
from controllers.optimization_controller import OptimizationController
from controllers.list_controller import ListController

# Domain extension: Vestack modular construction. Remove this import, the
# instance below, the tool at the end of this file and the vestack/ package to
# return to a purely generic Cadwork MCP server.
from vestack.mcp_controller import VestackController

# Create MCP server
mcp = create_mcp_server()

# Initialize controllers
element_ctrl = ElementController()
geometry_ctrl = GeometryController()
attribute_ctrl = AttributeController()
visualization_ctrl = VisualizationController()
utility_ctrl = UtilityController()
shop_drawing_ctrl = ShopDrawingController()
roof_ctrl = RoofController()
machine_ctrl = MachineController()
measurement_ctrl = MeasurementController()
material_ctrl = MaterialController()
export_ctrl = ExportController()
import_ctrl = ImportController()
container_ctrl = ContainerController()
transformation_ctrl = TransformationController()
optimization_ctrl = OptimizationController()
list_ctrl = ListController()
vestack_ctrl = VestackController()

# --- ELEMENT TOOLS ---

@mcp.tool(
    name="create_beam",
    description=f"Creates a rectangular beam element. Requires start point p1 ([x,y,z]), end point p2 ([x,y,z]), width, and height. Optional orientation point p3 ([x,y,z]).\n\nIMPORTANT AXIS DIRECTIONS:\n{CADWORK_AXIS_INFO if AXIS_CONFIG_AVAILABLE else 'For vertical beams: p1/p2 must be in Z-direction'}"
)
async def create_beam(p1: List[float], p2: List[float], width: float, height: float, p3: Optional[List[float]] = None) -> Dict[str, Any]:
    result = await element_ctrl.create_beam(p1, p2, width, height, p3)
    
    # Add axis validation if helper is available
    if AXIS_CONFIG_AVAILABLE:
        helper = CadworkAxisHelper()
        if p1[0] == p2[0] and p1[1] == p2[1]:  # Vertical beam detected
            is_correct = helper.validate_beam_orientation(p1, p2, 'Z')
            if not is_correct:
                result["axis_warning"] = "WARNING: Vertical beam may have incorrect axis orientation. Use Z-direction for longitudinal axis."
    
    return result

@mcp.tool(
    name="create_panel", 
    description="Creates a rectangular panel element. Requires start point p1 ([x,y,z]), end point p2 ([x,y,z]), width, and thickness. IMPORTANT: When p1 and p2 define only a line (same x,y coordinates for vertical panels, or along a single axis), you MUST provide orientation point p3 ([x,y,z]) to define the panel's width direction and orientation, otherwise the panel will appear as a line. P3 defines the direction in which the panel's width extends from the p1-p2 line."
)
async def create_panel(p1: List[float], p2: List[float], width: float, thickness: float, p3: Optional[List[float]] = None) -> Dict[str, Any]:
    return await element_ctrl.create_panel(p1, p2, width, thickness, p3)

@mcp.tool(
    name="get_active_element_ids",
    description="Retrieves a list of integer IDs for all elements currently active (selected) in Cadwork 3D."
)
async def get_active_element_ids() -> Dict[str, Any]:
    return await element_ctrl.get_active_element_ids()

@mcp.tool(
    name="get_all_element_ids", 
    description="Retrieves a list of integer IDs for ALL elements in the Cadwork 3D model, regardless of selection or visibility state."
)
async def get_all_element_ids() -> Dict[str, Any]:
    return await element_ctrl.get_all_element_ids()

@mcp.tool(
    name="get_visible_element_ids",
    description="Retrieves a list of integer IDs for all elements that are currently visible in the Cadwork 3D viewport."
)
async def get_visible_element_ids() -> Dict[str, Any]:
    return await element_ctrl.get_visible_element_ids()

@mcp.tool(
    name="get_element_info",
    description="Retrieves detailed geometric information and common attributes for a specific Cadwork element."
)
async def get_element_info(element_id: int) -> Dict[str, Any]:
    return await element_ctrl.get_element_info(element_id)

@mcp.tool(
    name="delete_elements",
    description="Deletes a list of elements from the Cadwork 3D model. Takes a list of element IDs to delete. This operation cannot be undone."
)
async def delete_elements(element_ids: List[int]) -> Dict[str, Any]:
    return await element_ctrl.delete_elements(element_ids)

@mcp.tool(
    name="copy_elements", 
    description="Copies elements with a vector offset. Takes element IDs list and copy_vector [x,y,z]. Returns new element IDs of the copied elements."
)
async def copy_elements(element_ids: List[int], copy_vector: List[float]) -> Dict[str, Any]:
    return await element_ctrl.copy_elements(element_ids, copy_vector)

@mcp.tool(
    name="move_element",
    description="Moves elements by a vector offset. Takes element IDs list and move_vector [x,y,z]. Modifies the original elements in place."
)
async def move_element(element_ids: List[int], move_vector: List[float]) -> Dict[str, Any]:
    return await element_ctrl.move_element(element_ids, move_vector)

@mcp.tool(
    name="duplicate_elements",
    description="Duplicates elements at the same location (no offset). Takes element IDs and returns new element IDs of duplicated elements."
)
async def duplicate_elements(element_ids: List[int]) -> Dict[str, Any]:
    return await element_ctrl.duplicate_elements(element_ids)

@mcp.tool(
    name="stretch_elements",
    description="Stretch/extend elements along a specified vector with given factor. Takes element IDs, stretch vector [x,y,z], and stretch factor."
)
async def stretch_elements(element_ids: List[int], stretch_vector: List[float], stretch_factor: float = 1.0) -> Dict[str, Any]:
    return await element_ctrl.stretch_elements(element_ids, stretch_vector, stretch_factor)

@mcp.tool(
    name="scale_elements",
    description="Scale elements by a factor around an origin point. Takes element IDs, scale factor, and optional origin point [x,y,z]."
)
async def scale_elements(element_ids: List[int], scale_factor: float, origin_point: Optional[List[float]] = None) -> Dict[str, Any]:
    return await element_ctrl.scale_elements(element_ids, scale_factor, origin_point)

@mcp.tool(
    name="mirror_elements",
    description="Mirror elements across a plane defined by a point and normal vector. Takes element IDs, plane point [x,y,z], and plane normal vector [x,y,z]."
)
async def mirror_elements(element_ids: List[int], mirror_plane_point: List[float], mirror_plane_normal: List[float]) -> Dict[str, Any]:
    return await element_ctrl.mirror_elements(element_ids, mirror_plane_point, mirror_plane_normal)

@mcp.tool(
    name="create_solid_wood_panel",
    description="Creates a solid wood panel with specified wood type and grain direction. Takes start point p1 [x,y,z], end point p2 [x,y,z], thickness, wood type. IMPORTANT: When p1 and p2 define only a line (same x,y coordinates for vertical panels, or along a single axis), you MUST provide orientation point p3 ([x,y,z]) to define the panel's width direction, orientation, and wood grain direction, otherwise the panel will appear as a line. P3 defines the direction in which the panel's width extends from the p1-p2 line and determines grain orientation."
)
async def create_solid_wood_panel(p1: List[float], p2: List[float], thickness: float, wood_type: str = "Generic", p3: Optional[List[float]] = None) -> Dict[str, Any]:
    return await element_ctrl.create_solid_wood_panel(p1, p2, thickness, wood_type, p3)

@mcp.tool(
    name="get_user_element_ids", 
    description="Prompts user to select elements in Cadwork 3D and returns their IDs. Optional count parameter limits selection to specific number of elements."
)
async def get_user_element_ids(count: Optional[int] = None) -> Dict[str, Any]:
    return await element_ctrl.get_user_element_ids(count)

# --- EXTENDED ELEMENT CREATION TOOLS ---

@mcp.tool(
    name="create_circular_beam_points",
    description="Creates a circular beam element using points. Requires diameter, start point p1 ([x,y,z]), end point p2 ([x,y,z]). IMPORTANT: For vertical beams or when p1 and p2 have same x,y coordinates, you MUST provide orientation point p3 ([x,y,z]) to define the beam's rotation around its axis, otherwise default orientation is used. P3 defines the reference direction for the circular cross-section."
)
async def create_circular_beam_points(diameter: float, p1: List[float], p2: List[float], p3: Optional[List[float]] = None) -> Dict[str, Any]:
    return await element_ctrl.create_circular_beam_points(diameter, p1, p2, p3)

@mcp.tool(
    name="create_square_beam_points", 
    description="Creates a square beam element using points. Requires width, start point p1 ([x,y,z]), end point p2 ([x,y,z]). IMPORTANT: For vertical beams or when p1 and p2 have same x,y coordinates, you MUST provide orientation point p3 ([x,y,z]) to define the beam's cross-section orientation, otherwise the beam will appear as a line. P3 defines the direction of one side of the square cross-section."
)
async def create_square_beam_points(width: float, p1: List[float], p2: List[float], p3: Optional[List[float]] = None) -> Dict[str, Any]:
    return await element_ctrl.create_square_beam_points(width, p1, p2, p3)

@mcp.tool(
    name="create_standard_beam_points",
    description="Creates a standard beam element using points from Cadwork library. Requires standard_element_name, start point p1 ([x,y,z]), end point p2 ([x,y,z]). IMPORTANT: For vertical beams or when p1 and p2 have same x,y coordinates, you MUST provide orientation point p3 ([x,y,z]) to define the beam's cross-section orientation, otherwise the beam may appear incorrectly oriented. P3 defines the direction of the beam's local coordinate system."
)
async def create_standard_beam_points(standard_element_name: str, p1: List[float], p2: List[float], p3: Optional[List[float]] = None) -> Dict[str, Any]:
    return await element_ctrl.create_standard_beam_points(standard_element_name, p1, p2, p3)

@mcp.tool(
    name="create_standard_panel_points",
    description="Creates a standard panel element using points from Cadwork library. Requires standard_element_name, start point p1 ([x,y,z]), end point p2 ([x,y,z]). IMPORTANT: When p1 and p2 define only a line (same x,y coordinates for vertical panels, or along a single axis), you MUST provide orientation point p3 ([x,y,z]) to define the panel's width direction and orientation, otherwise the panel may appear as a line or incorrectly oriented. P3 defines the direction in which the panel's width extends from the p1-p2 line."
)
async def create_standard_panel_points(standard_element_name: str, p1: List[float], p2: List[float], p3: Optional[List[float]] = None) -> Dict[str, Any]:
    return await element_ctrl.create_standard_panel_points(standard_element_name, p1, p2, p3)

@mcp.tool(
    name="create_drilling_points",
    description="Creates a drilling element using points. Requires diameter and start point p1 ([x,y,z]), end point p2 ([x,y,z])."
)
async def create_drilling_points(diameter: float, p1: List[float], p2: List[float]) -> Dict[str, Any]:
    return await element_ctrl.create_drilling_points(diameter, p1, p2)

@mcp.tool(
    name="create_polygon_beam",
    description="Creates a polygon beam element. Requires polygon_vertices (list of [x,y,z] points), thickness, xl vector ([x,y,z] length direction), and zl vector ([x,y,z] height direction)."
)
async def create_polygon_beam(polygon_vertices: List[List[float]], thickness: float, xl: List[float], zl: List[float]) -> Dict[str, Any]:
    return await element_ctrl.create_polygon_beam(polygon_vertices, thickness, xl, zl)

# --- ELEMENT QUERY/FILTER TOOLS ---

@mcp.tool(
    name="get_elements_by_type",
    description="Finds all elements of a specific type in the model. Takes element_type string ('beam', 'panel', 'drilling', etc.) and returns list of matching element IDs."
)
async def get_elements_by_type(element_type: str) -> Dict[str, Any]:
    return await element_ctrl.get_elements_by_type(element_type)

@mcp.tool(
    name="filter_elements_by_material",
    description="Filters all elements by material name. Takes material_name string and returns list of element IDs with that material."
)
async def filter_elements_by_material(material_name: str) -> Dict[str, Any]:
    return await element_ctrl.filter_elements_by_material(material_name)

@mcp.tool(
    name="get_elements_in_group",
    description="Finds all elements in a specific group. Takes group_name string and returns list of element IDs in that group."
)
async def get_elements_in_group(group_name: str) -> Dict[str, Any]:
    return await element_ctrl.get_elements_in_group(group_name)

@mcp.tool(
    name="get_elements_by_color",
    description="Finds all elements with a specific color ID. Takes color_id (1-255 from Cadwork color palette) and returns list of element IDs with that color."
)
async def get_elements_by_color(color_id: int) -> Dict[str, Any]:
    return await element_ctrl.get_elements_by_color(color_id)

@mcp.tool(
    name="get_elements_by_layer",
    description="Finds all elements on a specific layer. Takes layer_name string and returns list of element IDs on that layer."
)
async def get_elements_by_layer(layer_name: str) -> Dict[str, Any]:
    return await element_ctrl.get_elements_by_layer(layer_name)

@mcp.tool(
    name="get_elements_by_dimension_range",
    description="Finds all elements within a specific dimension range. Takes dimension_type ('width', 'height', 'length', 'volume', 'weight'), min_value, and max_value."
)
async def get_elements_by_dimension_range(dimension_type: str, min_value: float, max_value: float) -> Dict[str, Any]:
    return await element_ctrl.get_elements_by_dimension_range(dimension_type, min_value, max_value)

@mcp.tool(
    name="get_elements_in_region",
    description="Find all elements within a 3D bounding box region. Takes min_point [x,y,z], max_point [x,y,z], and optional include_partially flag to include elements that partially overlap the region."
)
async def get_elements_in_region(min_point: List[float], max_point: List[float], include_partially: bool = True) -> Dict[str, Any]:
    return await element_ctrl.get_elements_in_region(min_point, max_point, include_partially)

@mcp.tool(
    name="get_element_count_by_type",
    description="Gets count statistics of all elements by type in the model. Returns total counts and percentages for each element type."
)
async def get_element_count_by_type() -> Dict[str, Any]:
    return await element_ctrl.get_element_count_by_type()

@mcp.tool(
    name="get_material_statistics",
    description="Gets material usage statistics for the entire model. Returns counts and percentages for each material used."
)
async def get_material_statistics() -> Dict[str, Any]:
    return await element_ctrl.get_material_statistics()

@mcp.tool(
    name="get_group_statistics",
    description="Gets group usage statistics for the entire model. Returns counts and percentages for each group used."
)
async def get_group_statistics() -> Dict[str, Any]:
    return await element_ctrl.get_group_statistics()

@mcp.tool(
    name="join_elements",
    description="Joins multiple elements together. Takes a list of element IDs (minimum 2 elements) to create connections between them."
)
async def join_elements(element_ids: List[int]) -> Dict[str, Any]:
    return await element_ctrl.join_elements(element_ids)

@mcp.tool(
    name="unjoin_elements", 
    description="Unjoins/disconnects previously joined elements. Takes a list of element IDs to remove their connections."
)
async def unjoin_elements(element_ids: List[int]) -> Dict[str, Any]:
    return await element_ctrl.unjoin_elements(element_ids)

@mcp.tool(
    name="cut_corner_lap",
    description="Creates corner lap cuts between elements for wood connections. Takes element IDs (minimum 2) and optional cut parameters (depth, width, etc.)."
)
async def cut_corner_lap(element_ids: List[int], cut_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return await element_ctrl.cut_corner_lap(element_ids, cut_params)

@mcp.tool(
    name="cut_cross_lap", 
    description="Creates cross lap cuts between elements for wood connections. Takes element IDs (minimum 2) and optional cut parameters (depth, width, position, etc.)."
)
async def cut_cross_lap(element_ids: List[int], cut_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return await element_ctrl.cut_cross_lap(element_ids, cut_params)

@mcp.tool(
    name="cut_half_lap",
    description="Creates half lap cuts between elements. One element is cut to half its thickness while the other is cut completely. Takes element IDs (minimum 2) and optional cut parameters."
)
async def cut_half_lap(element_ids: List[int], cut_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return await element_ctrl.cut_half_lap(element_ids, cut_params)

@mcp.tool(
    name="cut_double_tenon",
    description="Creates double tenon and mortise connections between exactly 2 elements. Creates two parallel tenons on one element and corresponding mortises on the other."
)
async def cut_double_tenon(element_ids: List[int], cut_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return await element_ctrl.cut_double_tenon(element_ids, cut_params)

@mcp.tool(
    name="cut_scarf_joint",
    description="Creates scarf joint connections between exactly 2 elements for beam extensions or seamless connections. Takes scarf type, length, angle parameters."
)
async def cut_scarf_joint(element_ids: List[int], cut_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return await element_ctrl.cut_scarf_joint(element_ids, cut_params)

@mcp.tool(
    name="cut_shoulder",
    description="Creates shoulder cuts between elements for load-bearing connections. One element supports another with a shoulder cut. Takes depth, width, type parameters."
)
async def cut_shoulder(element_ids: List[int], cut_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return await element_ctrl.cut_shoulder(element_ids, cut_params)

@mcp.tool(
    name="create_surface",
    description="Creates a surface element from vertices. Requires list of vertex points as [x,y,z] coordinates (minimum 3 points) and optional surface_type ('flat', 'curved', 'ruled')."
)
async def create_surface(vertices: List[List[float]], surface_type: str = "flat") -> Dict[str, Any]:
    return await element_ctrl.create_surface(vertices, surface_type)

@mcp.tool(
    name="chamfer_edge",
    description="Create a chamfer on element edges. Takes element_id, edge_vertices (list of vertex pairs), chamfer_distance, and optional chamfer_type ('symmetric', 'asymmetric', 'rounded')."
)
async def chamfer_edge(element_id: int, edge_vertices: List[List[List[float]]], chamfer_distance: float, chamfer_type: str = "symmetric") -> Dict[str, Any]:
    return await element_ctrl.chamfer_edge(element_id, edge_vertices, chamfer_distance, chamfer_type)

@mcp.tool(
    name="round_edge",
    description="Create a rounded edge on element edges. Takes element_id, edge_vertices (list of vertex pairs), round_radius, and optional round_type ('full', 'quarter', 'half')."
)
async def round_edge(element_id: int, edge_vertices: List[List[List[float]]], round_radius: float, round_type: str = "full") -> Dict[str, Any]:
    return await element_ctrl.round_edge(element_id, edge_vertices, round_radius, round_type)

@mcp.tool(
    name="split_element",
    description="Split an element with a cutting plane. Takes element_id, split_plane_point [x,y,z], split_plane_normal [x,y,z], and optional keep_both_parts flag."
)
async def split_element(element_id: int, split_plane_point: List[float], split_plane_normal: List[float], keep_both_parts: bool = True) -> Dict[str, Any]:
    return await element_ctrl.split_element(element_id, split_plane_point, split_plane_normal, keep_both_parts)

@mcp.tool(
    name="create_beam_from_points",
    description="Create a beam element from a series of points defining its centerline. Takes points list, cross_section dict, and optional material."
)
async def create_beam_from_points(points: List[List[float]], cross_section: Dict[str, Any], material: str = "Wood") -> Dict[str, Any]:
    return await element_ctrl.create_beam_from_points(points, cross_section, material)

@mcp.tool(
    name="create_auxiliary_line",
    description="Create an auxiliary line element for construction purposes. Takes start_point [x,y,z], end_point [x,y,z], and optional line_type."
)
async def create_auxiliary_line(start_point: List[float], end_point: List[float], line_type: str = "construction") -> Dict[str, Any]:
    return await element_ctrl.create_auxiliary_line(start_point, end_point, line_type)

# --- GEOMETRY TOOLS ---

@mcp.tool(
    name="get_element_width",
    description="Retrieves the width of a specific Cadwork element in millimeters."
)
async def get_element_width(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_width(element_id)

@mcp.tool(
    name="get_element_height", 
    description="Retrieves the height of a specific Cadwork element in millimeters."
)
async def get_element_height(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_height(element_id)

@mcp.tool(
    name="get_element_length",
    description="Retrieves the length of a specific Cadwork element in millimeters."
)
async def get_element_length(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_length(element_id)

@mcp.tool(
    name="get_element_volume",
    description="Retrieves the volume of a specific Cadwork element in cubic millimeters."
)
async def get_element_volume(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_volume(element_id)

@mcp.tool(
    name="get_element_weight",
    description="Retrieves the weight of a specific Cadwork element in kilograms."
)
async def get_element_weight(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_weight(element_id)

# --- GEOMETRY VECTORS & POINTS ---

@mcp.tool(
    name="get_element_xl",
    description="Retrieves the XL vector (length direction) of a Cadwork element as [x,y,z]. This defines the element's length axis orientation."
)
async def get_element_xl(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_xl(element_id)

@mcp.tool(
    name="get_element_yl", 
    description="Retrieves the YL vector (width direction) of a Cadwork element as [x,y,z]. This defines the element's width axis orientation."
)
async def get_element_yl(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_yl(element_id)

@mcp.tool(
    name="get_element_zl",
    description="Retrieves the ZL vector (height direction) of a Cadwork element as [x,y,z]. This defines the element's height axis orientation."
)
async def get_element_zl(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_zl(element_id)

@mcp.tool(
    name="get_element_p1",
    description="Retrieves the P1 point (start point) of a Cadwork element as [x,y,z] coordinates in mm."
)
async def get_element_p1(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_p1(element_id)

@mcp.tool(
    name="get_element_p2",
    description="Retrieves the P2 point (end point) of a Cadwork element as [x,y,z] coordinates in mm."
)
async def get_element_p2(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_p2(element_id)

@mcp.tool(
    name="get_element_p3",
    description="Retrieves the P3 point (orientation point) of a Cadwork element as [x,y,z] coordinates in mm. Defines the element's local coordinate system."
)
async def get_element_p3(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_p3(element_id)

@mcp.tool(
    name="get_center_of_gravity",
    description="Retrieves the center of gravity (centroid) of a single Cadwork element as [x,y,z] coordinates in mm."
)
async def get_center_of_gravity(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_center_of_gravity(element_id)

@mcp.tool(
    name="get_center_of_gravity_for_list",
    description="Retrieves the combined center of gravity for multiple Cadwork elements as [x,y,z] coordinates in mm."
)
async def get_center_of_gravity_for_list(element_ids: List[int]) -> Dict[str, Any]:
    return await geometry_ctrl.get_center_of_gravity_for_list(element_ids)

@mcp.tool(
    name="calculate_center_of_mass",
    description="Calculates the center of mass for multiple elements considering their material properties and densities. Takes element_ids and optional include_material_properties flag."
)
async def calculate_center_of_mass(element_ids: List[int], include_material_properties: bool = True) -> Dict[str, Any]:
    return await geometry_ctrl.calculate_center_of_mass(element_ids, include_material_properties)

@mcp.tool(
    name="get_element_vertices",
    description="Retrieves all corner points (vertices) of a Cadwork element as list of [x,y,z] coordinates in mm."
)
async def get_element_vertices(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_vertices(element_id)

@mcp.tool(
    name="get_bounding_box",
    description="Retrieves the bounding box (min/max coordinates) of a Cadwork element as [min_x, min_y, min_z, max_x, max_y, max_z] in mm."
)
async def get_bounding_box(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_bounding_box(element_id)

@mcp.tool(
    name="get_element_outline",
    description="Retrieves the 2D outline/contour of a Cadwork element projected to a plane. Returns outline coordinates for drawing purposes."
)
async def get_element_outline(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_outline(element_id)

@mcp.tool(
    name="get_section_outline",
    description="Retrieves the outline of an element cut by a section plane. Takes element ID, section plane point [x,y,z], and plane normal vector [x,y,z]."
)
async def get_section_outline(element_id: int, section_plane_point: List[float], section_plane_normal: List[float]) -> Dict[str, Any]:
    return await geometry_ctrl.get_section_outline(element_id, section_plane_point, section_plane_normal)

@mcp.tool(
    name="intersect_elements",
    description="Intersect multiple elements to create new elements from their common volume. Takes element IDs list and optional keep_originals flag."
)
async def intersect_elements(element_ids: List[int], keep_originals: bool = True) -> Dict[str, Any]:
    return await geometry_ctrl.intersect_elements(element_ids, keep_originals)

@mcp.tool(
    name="subtract_elements",
    description="Subtract elements from a target element (Boolean difference operation). Takes target_element_id, subtract_element_ids list, and optional keep_originals flag."
)
async def subtract_elements(target_element_id: int, subtract_element_ids: List[int], keep_originals: bool = False) -> Dict[str, Any]:
    return await geometry_ctrl.subtract_elements(target_element_id, subtract_element_ids, keep_originals)

@mcp.tool(
    name="unite_elements",
    description="Unite/merge multiple elements into one (Boolean union operation). Takes element_ids list (minimum 2) and optional keep_originals flag."
)
async def unite_elements(element_ids: List[int], keep_originals: bool = False) -> Dict[str, Any]:
    return await geometry_ctrl.unite_elements(element_ids, keep_originals)

# --- GEOMETRY ANALYSIS ---

@mcp.tool(
    name="project_point_to_element",
    description="Project a 3D point onto an element surface and find the closest point. Takes point coordinates [x,y,z] and element_id. Returns the projected point coordinates and distance."
)
async def project_point_to_element(point: List[float], element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.project_point_to_element(point, element_id)

@mcp.tool(
    name="get_minimum_distance_between_elements",
    description="Calculates the minimum distance between two Cadwork elements in mm. Useful for collision detection and clearance checks."
)
async def get_minimum_distance_between_elements(first_element_id: int, second_element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_minimum_distance_between_elements(first_element_id, second_element_id)

@mcp.tool(
    name="get_closest_point_on_element",
    description="Finds the closest point on a Cadwork element to a given reference point. Takes element_id and reference_point [x,y,z] coordinates."
)
async def get_closest_point_on_element(element_id: int, reference_point: List[float]) -> Dict[str, Any]:
    return await geometry_ctrl.get_closest_point_on_element(element_id, reference_point)

@mcp.tool(
    name="get_element_facets",
    description="Retrieves all facets (faces) of a Cadwork element. Returns geometric face data for detailed mesh analysis."
)
async def get_element_facets(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_facets(element_id)

@mcp.tool(
    name="get_element_reference_face_area", 
    description="Retrieves the reference face area of a Cadwork element in mm². This is typically the main face used for calculations."
)
async def get_element_reference_face_area(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_reference_face_area(element_id)

@mcp.tool(
    name="get_total_area_of_all_faces",
    description="Retrieves the total surface area of all faces of a Cadwork element in mm². Useful for material calculations."
)
async def get_total_area_of_all_faces(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_total_area_of_all_faces(element_id)

# --- GEOMETRY TRANSFORMATIONS ---

@mcp.tool(
    name="rotate_elements",
    description="Rotates elements around a specified axis. Takes element IDs, origin point [x,y,z], rotation axis vector [x,y,z], and angle in degrees."
)
async def rotate_elements(element_ids: List[int], origin: List[float], rotation_axis: List[float], rotation_angle: float) -> Dict[str, Any]:
    return await geometry_ctrl.rotate_elements(element_ids, origin, rotation_axis, rotation_angle)

@mcp.tool(
    name="apply_global_scale",
    description="Applies global scaling to elements. Takes element IDs, scale factor (e.g., 2.0 = double size), and origin point [x,y,z] for scaling."
)
async def apply_global_scale(element_ids: List[int], scale: float, origin: List[float]) -> Dict[str, Any]:
    return await geometry_ctrl.apply_global_scale(element_ids, scale, origin)

@mcp.tool(
    name="invert_model",
    description="Inverts/mirrors elements. This flips the element geometry. Useful for creating mirrored versions."
)
async def invert_model(element_ids: List[int]) -> Dict[str, Any]:
    return await geometry_ctrl.invert_model(element_ids)

@mcp.tool(
    name="rotate_height_axis_90",
    description="Rotates the height axis of elements by exactly 90 degrees. Quick rotation for standard orientations."
)
async def rotate_height_axis_90(element_ids: List[int]) -> Dict[str, Any]:
    return await geometry_ctrl.rotate_height_axis_90(element_ids)

@mcp.tool(
    name="rotate_length_axis_90", 
    description="Rotates the length axis of elements by exactly 90 degrees. Quick rotation for standard orientations."
)
async def rotate_length_axis_90(element_ids: List[int]) -> Dict[str, Any]:
    return await geometry_ctrl.rotate_length_axis_90(element_ids)

@mcp.tool(
    name="get_element_type",
    description="Retrieves the type of a Cadwork element (beam, panel, drilling, etc.). Takes element ID and returns type information."
)
async def get_element_type(element_id: int) -> Dict[str, Any]:
    return await geometry_ctrl.get_element_type(element_id)

# --- GEOMETRY CALCULATIONS ---

@mcp.tool(
    name="calculate_total_volume",
    description="Calculates the total volume of a list of elements. Takes element IDs and returns total volume in multiple units (mm³, cm³, dm³, m³)."
)
async def calculate_total_volume(element_ids: List[int]) -> Dict[str, Any]:
    return await geometry_ctrl.calculate_total_volume(element_ids)

@mcp.tool(
    name="calculate_total_weight",
    description="Calculates the total weight of a list of elements. Takes element IDs and returns total weight in multiple units (g, kg, t)."
)
async def calculate_total_weight(element_ids: List[int]) -> Dict[str, Any]:
    return await geometry_ctrl.calculate_total_weight(element_ids)

@mcp.tool(
    name="check_collisions",
    description="Check for collisions between elements with specified tolerance. Takes element IDs and optional tolerance value."
)
async def check_collisions(element_ids: List[int], tolerance: float = 0.1) -> Dict[str, Any]:
    return await geometry_ctrl.check_collisions(element_ids, tolerance)

@mcp.tool(
    name="validate_joints",
    description="Validate joints between elements for structural integrity and feasibility. Takes element IDs, joint type, load conditions, and material properties."
)
async def validate_joints(element_ids: List[int],
                        joint_type: str = "auto",
                        load_conditions: Optional[Dict[str, Any]] = None,
                        safety_factor: float = 2.0,
                        wood_grade: str = "C24") -> Dict[str, Any]:
    return await geometry_ctrl.validate_joints(element_ids, joint_type, load_conditions, safety_factor, wood_grade)

# --- ATTRIBUTE TOOLS ---

@mcp.tool(
    name="get_standard_attributes",
    description="Retrieves common standard attributes (name, group, subgroup, material, comment) for a list of element IDs."
)
async def get_standard_attributes(element_ids: List[int]) -> Dict[str, Any]:
    return await attribute_ctrl.get_standard_attributes(element_ids)

@mcp.tool(
    name="get_user_attributes", 
    description="Retrieves specific user-defined attributes for a list of element IDs."
)
async def get_user_attributes(element_ids: List[int], attribute_numbers: List[int]) -> Dict[str, Any]:
    return await attribute_ctrl.get_user_attributes(element_ids, attribute_numbers)

@mcp.tool(
    name="list_defined_user_attributes",
    description="Retrieves a list of all user-defined attribute numbers that have names configured."
)
async def list_defined_user_attributes() -> Dict[str, Any]:
    return await attribute_ctrl.list_defined_user_attributes()

# --- ATTRIBUTE SETTER TOOLS ---

@mcp.tool(
    name="set_name",
    description="Sets the name for a list of elements. Takes element IDs and the name string to set."
)
async def set_name(element_ids: List[int], name: str) -> Dict[str, Any]:
    return await attribute_ctrl.set_name(element_ids, name)

@mcp.tool(
    name="set_material",
    description="Sets the material for a list of elements. Takes element IDs and the material name string to set."
)
async def set_material(element_ids: List[int], material: str) -> Dict[str, Any]:
    return await attribute_ctrl.set_material(element_ids, material)

# --- VISUALIZATION TOOLS ---

@mcp.tool(
    name="set_color",
    description="Sets the color for a list of elements. Takes element IDs and color_id (1-255 from Cadwork color palette)."
)
async def set_color(element_ids: List[int], color_id: int) -> Dict[str, Any]:
    return await visualization_ctrl.set_color(element_ids, color_id)

@mcp.tool(
    name="set_visibility", 
    description="Sets the visibility for a list of elements. Takes element IDs and visible flag (True=show, False=hide)."
)
async def set_visibility(element_ids: List[int], visible: bool) -> Dict[str, Any]:
    return await visualization_ctrl.set_visibility(element_ids, visible)

@mcp.tool(
    name="set_transparency",
    description="Sets the transparency for a list of elements. Takes element IDs and transparency value (0-100, 0=opaque, 100=fully transparent)."
)
async def set_transparency(element_ids: List[int], transparency: int) -> Dict[str, Any]:
    return await visualization_ctrl.set_transparency(element_ids, transparency)

# --- VISUALIZATION GETTERS ---

@mcp.tool(
    name="get_color",
    description="Gets the color of an element. Takes element ID and returns color information (color_id and color_name)."
)
async def get_color(element_id: int) -> Dict[str, Any]:
    return await visualization_ctrl.get_color(element_id)

@mcp.tool(
    name="get_transparency",
    description="Gets the transparency of an element. Takes element ID and returns transparency value (0-100) and opacity info."
)
async def get_transparency(element_id: int) -> Dict[str, Any]:
    return await visualization_ctrl.get_transparency(element_id)

# --- GLOBAL VISIBILITY TOOLS ---

@mcp.tool(
    name="show_all_elements",
    description="Makes all elements in the model visible. No parameters needed. Returns count of elements made visible."
)
async def show_all_elements() -> Dict[str, Any]:
    return await visualization_ctrl.show_all_elements()

@mcp.tool(
    name="hide_all_elements",
    description="Hides all elements in the model. No parameters needed. Returns count of elements hidden."
)
async def hide_all_elements() -> Dict[str, Any]:
    return await visualization_ctrl.hide_all_elements()

# --- DISPLAY MANAGEMENT TOOLS ---

@mcp.tool(
    name="refresh_display",
    description="Refreshes the display/viewport after changes. No parameters needed. Important for updating view after many operations."
)
async def refresh_display() -> Dict[str, Any]:
    return await visualization_ctrl.refresh_display()

@mcp.tool(
    name="get_visible_element_count",
    description="Gets count of currently visible elements in the model. Returns visibility statistics and percentages."
)
async def get_visible_element_count() -> Dict[str, Any]:
    return await visualization_ctrl.get_visible_element_count()

@mcp.tool(
    name="create_visual_filter",
    description="Creates and applies visual filters based on element attributes. Takes filter name, criteria (like search), and visual properties (color, transparency, visibility) to automatically style matching elements."
)
async def create_visual_filter(filter_name: str, filter_criteria: Dict[str, Any], visual_properties: Dict[str, Any]) -> Dict[str, Any]:
    return await visualization_ctrl.create_visual_filter(filter_name, filter_criteria, visual_properties)

@mcp.tool(
    name="apply_color_scheme",
    description="Applies predefined color schemes to elements based on various criteria. Takes scheme name, optional element IDs, and scheme basis (material, group, element_type, etc.) for intelligent automatic coloring."
)
async def apply_color_scheme(scheme_name: str, element_ids: List[int] = [], scheme_basis: str = "material") -> Dict[str, Any]:
    return await visualization_ctrl.apply_color_scheme(scheme_name, element_ids, scheme_basis)

@mcp.tool(
    name="create_assembly_animation",
    description="Create assembly animation showing construction sequence. Takes element IDs and animation parameters like type, duration, and movement path."
)
async def create_assembly_animation(element_ids: List[int], 
                                  animation_type: str = "sequential",
                                  duration: float = 10.0,
                                  start_delay: float = 0.0,
                                  element_delay: float = 0.5,
                                  fade_in: bool = True,
                                  movement_path: str = "gravity") -> Dict[str, Any]:
    return await visualization_ctrl.create_assembly_animation(element_ids, animation_type, duration, 
                                                            start_delay, element_delay, fade_in, movement_path)

@mcp.tool(
    name="set_camera_position",
    description="Set camera position and orientation for optimal viewing. Takes position, target point, and camera parameters."
)
async def set_camera_position(position: List[float],
                            target: List[float],
                            up_vector: List[float] = [0.0, 0.0, 1.0],
                            fov: float = 45.0,
                            animate_transition: bool = True,
                            transition_duration: float = 2.0,
                            camera_name: str = "default") -> Dict[str, Any]:
    return await visualization_ctrl.set_camera_position(position, target, up_vector, fov, 
                                                      animate_transition, transition_duration, camera_name)

@mcp.tool(
    name="create_walkthrough",
    description="Create interactive 3D walkthrough for VR and presentations. Takes waypoint positions and various walkthrough parameters."
)
async def create_walkthrough(waypoints: List[List[float]],
                           duration: float = 30.0,
                           camera_height: float = 1700.0,
                           movement_speed: str = "smooth",
                           focus_elements: Optional[List[int]] = None,
                           include_audio: bool = False,
                           output_format: str = "mp4",
                           resolution: str = "1920x1080") -> Dict[str, Any]:
    return await visualization_ctrl.create_walkthrough(waypoints, duration, camera_height, movement_speed,
                                                     focus_elements, include_audio, output_format, resolution)

# --- EXTENDED ATTRIBUTE TOOLS ---

@mcp.tool(
    name="set_group",
    description="Sets the group for a list of elements. Takes element IDs and group name string."
)
async def set_group(element_ids: List[int], group: str) -> Dict[str, Any]:
    return await attribute_ctrl.set_group(element_ids, group)

@mcp.tool(
    name="set_comment",
    description="Sets the comment for a list of elements. Takes element IDs and comment text string."
)
async def set_comment(element_ids: List[int], comment: str) -> Dict[str, Any]:
    return await attribute_ctrl.set_comment(element_ids, comment)

@mcp.tool(
    name="set_subgroup",
    description="Sets the subgroup for a list of elements. Takes element IDs and subgroup name string."
)
async def set_subgroup(element_ids: List[int], subgroup: str) -> Dict[str, Any]:
    return await attribute_ctrl.set_subgroup(element_ids, subgroup)

@mcp.tool(
    name="set_user_attribute",
    description="Sets a user-defined attribute for a list of elements. Takes element IDs, attribute number (1-999), and attribute value string."
)
async def set_user_attribute(element_ids: List[int], attribute_number: int, attribute_value: str) -> Dict[str, Any]:
    return await attribute_ctrl.set_user_attribute(element_ids, attribute_number, attribute_value)

@mcp.tool(
    name="get_element_attribute_display_name",
    description="Gets the display name for a user-defined attribute number. Takes attribute number and returns configured display name."
)
async def get_element_attribute_display_name(attribute_number: int) -> Dict[str, Any]:
    return await attribute_ctrl.get_element_attribute_display_name(attribute_number)

@mcp.tool(
    name="clear_user_attribute",
    description="Clears/deletes a user-defined attribute for a list of elements. Takes element IDs and attribute number to clear."
)
async def clear_user_attribute(element_ids: List[int], attribute_number: int) -> Dict[str, Any]:
    return await attribute_ctrl.clear_user_attribute(element_ids, attribute_number)

@mcp.tool(
    name="copy_attributes",
    description="Copies attributes from a source element to target elements. Takes source element ID, target element IDs, and optional flags for which attribute types to copy."
)
async def copy_attributes(source_element_id: int, target_element_ids: List[int], 
                         copy_user_attributes: bool = True, copy_standard_attributes: bool = True) -> Dict[str, Any]:
    return await attribute_ctrl.copy_attributes(source_element_id, target_element_ids, copy_user_attributes, copy_standard_attributes)

@mcp.tool(
    name="batch_set_user_attributes",
    description="Sets multiple user-defined attributes for elements in a single operation. Takes element IDs and a dictionary mapping attribute numbers to values for efficient batch processing."
)
async def batch_set_user_attributes(element_ids: List[int], attribute_mappings: Dict[int, str]) -> Dict[str, Any]:
    return await attribute_ctrl.batch_set_user_attributes(element_ids, attribute_mappings)

@mcp.tool(
    name="validate_attribute_consistency",
    description="Validates attribute consistency across multiple elements. Checks for completeness (all elements have attributes) and/or uniqueness (no duplicate values). Takes element IDs, attribute numbers, and validation flags."
)
async def validate_attribute_consistency(element_ids: List[int], attribute_numbers: List[int], 
                                       check_completeness: bool = True, check_uniqueness: bool = False) -> Dict[str, Any]:
    return await attribute_ctrl.validate_attribute_consistency(element_ids, attribute_numbers, check_completeness, check_uniqueness)

@mcp.tool(
    name="search_elements_by_attributes",
    description="Searches elements by flexible attribute criteria. Supports standard attributes, user attributes, and dimensions with various search modes (AND, OR, CONTAINS, etc.). Takes search criteria dictionary and search mode."
)
async def search_elements_by_attributes(search_criteria: Dict[str, Any], search_mode: str = "AND") -> Dict[str, Any]:
    return await attribute_ctrl.search_elements_by_attributes(search_criteria, search_mode)

@mcp.tool(
    name="export_attribute_report",
    description="Exports comprehensive attribute reports for elements in various formats (JSON, CSV, XML, HTML, PDF). Takes element IDs, format, and options for which data to include and how to group it."
)
async def export_attribute_report(element_ids: List[int], report_format: str = "JSON",
                                include_standard_attributes: bool = True, include_user_attributes: bool = True,
                                user_attribute_numbers: List[int] = [], include_dimensions: bool = False,
                                group_by: str = "") -> Dict[str, Any]:
    return await attribute_ctrl.export_attribute_report(element_ids, report_format, include_standard_attributes, 
                                                       include_user_attributes, user_attribute_numbers, include_dimensions, group_by)

# --- UTILITY TOOLS ---
@mcp.tool(
    name="disable_auto_display_refresh",
    description="Disables automatic display refresh for performance during batch operations. Important: Remember to enable it again afterwards."
)
async def disable_auto_display_refresh() -> Dict[str, Any]:
    return await utility_ctrl.disable_auto_display_refresh()

@mcp.tool(
    name="enable_auto_display_refresh", 
    description="Re-enables automatic display refresh after batch operations. Should be called after disable_auto_display_refresh()."
)
async def enable_auto_display_refresh() -> Dict[str, Any]:
    return await utility_ctrl.enable_auto_display_refresh()

@mcp.tool(
    name="print_error",
    description="Displays an error message in Cadwork. Takes a message string to show in the Cadwork interface."
)
async def print_error(message: str) -> Dict[str, Any]:
    return await utility_ctrl.print_error(message)

@mcp.tool(
    name="print_warning",
    description="Displays a warning message in Cadwork. Takes a message string to show in the Cadwork interface."
)
async def print_warning(message: str) -> Dict[str, Any]:
    return await utility_ctrl.print_warning(message)

@mcp.tool(
    name="get_3d_file_path",
    description="Retrieves the file path of the currently opened 3D file in Cadwork. Returns file path and file information."
)
async def get_3d_file_path() -> Dict[str, Any]:
    return await utility_ctrl.get_3d_file_path()

@mcp.tool(
    name="get_project_data", 
    description="Retrieves general project data and metadata from the current Cadwork project. Returns project information like name, path, etc."
)
async def get_project_data() -> Dict[str, Any]:
    return await utility_ctrl.get_project_data()

# --- VERSION TOOL ---

@mcp.tool(
    name="get_cadwork_version_info",
    description="Retrieves version information from the connected Cadwork application."
)
async def get_cadwork_version_info() -> Dict[str, Any]:
    from core.connection import get_connection
    try:
        connection = get_connection()
        return connection.send_command("get_version_info")
    except Exception as e:
        return {"status": "error", "message": f"Failed to get version info: {e}"}

@mcp.tool(
    name="create_auxiliary_beam_points",
    description="Creates an auxiliary beam element using points. Auxiliary elements are used for construction purposes and can be converted to regular beams later. Requires start point p1 ([x,y,z]), end point p2 ([x,y,z]). IMPORTANT: For vertical beams or when p1 and p2 have same x,y coordinates, you MUST provide orientation point p3 ([x,y,z]) to define the beam's orientation, otherwise the beam will appear as a line. P3 defines the direction for the beam's local coordinate system."
)
async def create_auxiliary_beam_points(p1: List[float], p2: List[float], p3: Optional[List[float]] = None) -> Dict[str, Any]:
    return await element_ctrl.create_auxiliary_beam_points(p1, p2, p3)

@mcp.tool(
    name="convert_beam_to_panel", 
    description="Converts beam elements to panel elements. The geometry is adjusted accordingly - width becomes thickness, height becomes width of the resulting panel. Takes a list of element IDs to convert."
)
async def convert_beam_to_panel(element_ids: List[int]) -> Dict[str, Any]:
    return await element_ctrl.convert_beam_to_panel(element_ids)

@mcp.tool(
    name="convert_panel_to_beam",
    description="Converts panel elements to beam elements. The geometry is adjusted accordingly - thickness becomes width, width becomes height of the resulting beam. Takes a list of element IDs to convert."
)
async def convert_panel_to_beam(element_ids: List[int]) -> Dict[str, Any]:
    return await element_ctrl.convert_panel_to_beam(element_ids)

@mcp.tool(
    name="convert_auxiliary_to_beam",
    description="Converts auxiliary elements to regular beam elements. Auxiliary elements become full-featured beams while preserving their geometry. Takes a list of auxiliary element IDs to convert."
)
async def convert_auxiliary_to_beam(element_ids: List[int]) -> Dict[str, Any]:
    return await element_ctrl.convert_auxiliary_to_beam(element_ids)

@mcp.tool(
    name="create_auto_container_from_standard",
    description="Creates an automatic container from standard elements. Containers are groups that organize multiple elements together. Useful for complex structures and assemblies. Takes element IDs and container name."
)
async def create_auto_container_from_standard(element_ids: List[int], container_name: str) -> Dict[str, Any]:
    return await element_ctrl.create_auto_container_from_standard(element_ids, container_name)

@mcp.tool(
    name="get_container_content_elements", 
    description="Retrieves all elements contained within a specific container. Returns list of element IDs and detailed information about each contained element. Takes container ID."
)
async def get_container_content_elements(container_id: int) -> Dict[str, Any]:
    return await element_ctrl.get_container_content_elements(container_id)

@mcp.tool(
    name="add_wall_section_x",
    description="Adds a wall section in X-direction for technical drawings. Creates cross-sectional views parallel to X-axis for workshop drawings. Takes wall element ID and optional section parameters (position, depth, display options)."
)
async def add_wall_section_x(wall_id: int, section_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return await shop_drawing_ctrl.add_wall_section_x(wall_id, section_params)

@mcp.tool(
    name="add_wall_section_y", 
    description="Adds a wall section in Y-direction for technical drawings. Creates cross-sectional views parallel to Y-axis for workshop drawings. Takes wall element ID and optional section parameters (position, depth, display options)."
)
async def add_wall_section_y(wall_id: int, section_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return await shop_drawing_ctrl.add_wall_section_y(wall_id, section_params)

@mcp.tool(
    name="add_wall_section_vertical",
    description="Adds a vertical wall section for shop drawings. Creates vertical section cuts through wall elements for technical drawings and piece-by-piece shop drawing generation. Takes wall element ID, optional position vector, and section parameters."
)
async def add_wall_section_vertical(wall_id: int, position_vector: Optional[List[float]] = None, section_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return await shop_drawing_ctrl.add_wall_section_vertical(wall_id, position_vector, section_params)

@mcp.tool(
    name="export_2d_wireframe",
    description="Exports 2D wireframe drawings for shop drawings from clipboard. Essential for creating technical documentation and shop drawings in various formats (DXF, DWG, PDF, PNG). Takes clipboard number, layout options, and export settings."
)
async def export_2d_wireframe(clipboard_number: int = 3, with_layout: bool = False, export_format: str = "dxf", file_path: Optional[str] = None, scale: float = 1.0, line_weights: bool = True) -> Dict[str, Any]:
    return await shop_drawing_ctrl.export_2d_wireframe(clipboard_number, with_layout, export_format, file_path, scale, line_weights)

@mcp.tool(
    name="get_roof_surfaces",
    description="Retrieves roof surface information for specified elements. Analyzes roof elements and returns detailed information about roof surfaces, slopes, orientations and geometric properties. Takes list of element IDs to analyze as roof elements."
)
async def get_roof_surfaces(element_ids: List[int]) -> Dict[str, Any]:
    return await roof_ctrl.get_roof_surfaces(element_ids)

@mcp.tool(
    name="calculate_roof_area",
    description="Calculates total roof area for specified roof elements. Performs specialized roof area calculations considering slopes, overhangs and complex roof geometries. Takes list of roof element IDs for area calculation."
)
async def calculate_roof_area(roof_element_ids: List[int]) -> Dict[str, Any]:
    return await roof_ctrl.calculate_roof_area(roof_element_ids)

@mcp.tool(
    name="check_production_list_discrepancies",
    description="Checks production lists for discrepancies and conflicts. Analyzes production lists for potential issues like missing elements, inconsistent dimensions, material errors or CNC machining conflicts. Essential for quality-assured manufacturing. Takes production list ID."
)
async def check_production_list_discrepancies(production_list_id: int) -> Dict[str, Any]:
    return await machine_ctrl.check_production_list_discrepancies(production_list_id)

# --- MEASUREMENT TOOLS ---

@mcp.tool(
    name="measure_distance",
    description="Measures the distance between two 3D points. Takes point1 [x,y,z] and point2 [x,y,z] coordinates and returns the 3D distance plus individual axis distances in millimeters."
)
async def measure_distance(point1: List[float], point2: List[float]) -> Dict[str, Any]:
    return await measurement_ctrl.measure_distance(point1, point2)

@mcp.tool(
    name="measure_angle",
    description="Measures the angle between two 3D vectors. Takes vector1 [x,y,z] and vector2 [x,y,z] and returns the angle in degrees and radians, plus additional vector analysis information."
)
async def measure_angle(vector1: List[float], vector2: List[float]) -> Dict[str, Any]:
    return await measurement_ctrl.measure_angle(vector1, vector2)

@mcp.tool(
    name="measure_area",
    description="Measures the area of a polygon defined by vertices. Takes vertices (list of [x,y,z] points) and returns area in mm² and m², plus perimeter and geometric analysis."
)
async def measure_area(vertices: List[List[float]]) -> Dict[str, Any]:
    return await measurement_ctrl.measure_area(vertices)

# --- MATERIAL TOOLS ---

@mcp.tool(
    name="create_material",
    description="Creates a new material with specified properties. Takes material_name and optional properties like density (kg/m³), thermal_conductivity (W/mK), elastic_modulus (N/mm²), and color_id (1-255)."
)
async def create_material(material_name: str, density: Optional[float] = None, 
                         thermal_conductivity: Optional[float] = None, 
                         elastic_modulus: Optional[float] = None,
                         color_id: Optional[int] = None) -> Dict[str, Any]:
    return await material_ctrl.create_material(material_name, density, thermal_conductivity, elastic_modulus, color_id)

@mcp.tool(
    name="get_material_properties",
    description="Retrieves properties of an existing material. Takes material_name and returns density, thermal properties, and other material characteristics."
)
async def get_material_properties(material_name: str) -> Dict[str, Any]:
    return await material_ctrl.get_material_properties(material_name)

@mcp.tool(
    name="list_available_materials",
    description="Lists all available materials in the current Cadwork project. Returns material names and basic properties."
)
async def list_available_materials() -> Dict[str, Any]:
    return await material_ctrl.list_available_materials()

# --- EXPORT TOOLS ---

@mcp.tool(
    name="export_to_btl",
    description="Exports elements to BTL (Biesse Transfer Language) format for CNC machines. Takes optional element_ids, file_path, btl_version, and processing flags."
)
async def export_to_btl(element_ids: Optional[List[int]] = None, 
                       file_path: Optional[str] = None,
                       btl_version: str = "10.5",
                       include_processing: bool = True,
                       include_geometry: bool = True) -> Dict[str, Any]:
    return await export_ctrl.export_to_btl(element_ids, file_path, btl_version, include_processing, include_geometry)

@mcp.tool(
    name="export_element_list",
    description="Exports element list with properties to various formats (csv, xlsx, json, xml). Takes element_ids, export_format, and optional property flags."
)
async def export_element_list(element_ids: List[int], 
                             export_format: str = "csv",
                             include_properties: bool = True,
                             include_materials: bool = True,
                             file_path: Optional[str] = None) -> Dict[str, Any]:
    return await export_ctrl.export_element_list(element_ids, export_format, include_properties, include_materials, file_path)

@mcp.tool(
    name="export_to_ifc",
    description="Exports elements to IFC (Industry Foundation Classes) format for BIM applications like Revit, ArchiCAD, Tekla. Takes optional element_ids, file_path, ifc_version, and BIM flags."
)
async def export_to_ifc(element_ids: Optional[List[int]] = None,
                       file_path: Optional[str] = None,
                       ifc_version: str = "IFC4",
                       include_geometry: bool = True,
                       include_materials: bool = True,
                       include_properties: bool = True,
                       coordinate_system: str = "project") -> Dict[str, Any]:
    return await export_ctrl.export_to_ifc(element_ids, file_path, ifc_version, include_geometry, include_materials, include_properties, coordinate_system)

@mcp.tool(
    name="export_to_dxf",
    description="Exports elements to DXF format for 2D CAD applications. Takes optional element_ids, file_path, dxf_version, view_type, and drawing settings."
)
async def export_to_dxf(element_ids: Optional[List[int]] = None,
                       file_path: Optional[str] = None,
                       dxf_version: str = "R2018",
                       view_type: str = "plan",
                       include_dimensions: bool = True,
                       line_weight: float = 0.25) -> Dict[str, Any]:
    return await export_ctrl.export_to_dxf(element_ids, file_path, dxf_version, view_type, include_dimensions, line_weight)

@mcp.tool(
    name="export_workshop_drawings",
    description="Exports workshop drawings for manufacturing in various formats (PDF, DXF, DWG, PNG, JPG). Takes optional element_ids and comprehensive drawing settings."
)
async def export_workshop_drawings(element_ids: Optional[List[int]] = None,
                                 drawing_format: str = "pdf",
                                 include_dimensions: bool = True,
                                 include_processing: bool = True,
                                 scale: str = "1:10",
                                 sheet_size: str = "A3") -> Dict[str, Any]:
    return await export_ctrl.export_workshop_drawings(element_ids, drawing_format, include_dimensions, include_processing, scale, sheet_size)

@mcp.tool(
    name="export_to_step",
    description="Exports elements to STEP format for CAD interoperability (SolidWorks, Fusion360, CATIA). Takes optional element_ids, file_path, step_version, units, and precision settings."
)
async def export_to_step(element_ids: Optional[List[int]] = None,
                        file_path: Optional[str] = None,
                        step_version: str = "AP214",
                        units: str = "mm",
                        precision: float = 0.01) -> Dict[str, Any]:
    return await export_ctrl.export_to_step(element_ids, file_path, step_version, units, precision)

@mcp.tool(
    name="export_to_3dm",
    description="Exports elements to Rhino 3DM format for parametric design and advanced modeling. Takes optional element_ids, file_path, rhino_version, and 3D modeling settings."
)
async def export_to_3dm(element_ids: Optional[List[int]] = None,
                       file_path: Optional[str] = None,
                       rhino_version: str = "7",
                       include_materials: bool = True,
                       include_layers: bool = True,
                       mesh_quality: str = "medium") -> Dict[str, Any]:
    return await export_ctrl.export_to_3dm(element_ids, file_path, rhino_version, include_materials, include_layers, mesh_quality)

@mcp.tool(
    name="export_to_obj",
    description="Exports elements to OBJ format for 3D modeling and visualization (Blender, Maya, 3ds Max). Takes optional element_ids, file_path, and mesh settings for materials, normals, textures."
)
async def export_to_obj(element_ids: Optional[List[int]] = None,
                       file_path: Optional[str] = None,
                       include_materials: bool = True,
                       include_normals: bool = True,
                       include_textures: bool = False,
                       mesh_resolution: str = "medium") -> Dict[str, Any]:
    return await export_ctrl.export_to_obj(element_ids, file_path, include_materials, include_normals, include_textures, mesh_resolution)

@mcp.tool(
    name="export_to_ply",
    description="Exports elements to PLY format for point clouds and mesh analysis (CloudCompare, MeshLab). Takes optional element_ids, file_path, ply_format, and precision settings."
)
async def export_to_ply(element_ids: Optional[List[int]] = None,
                       file_path: Optional[str] = None,
                       ply_format: str = "binary",
                       include_colors: bool = True,
                       include_normals: bool = True,
                       coordinate_precision: int = 6) -> Dict[str, Any]:
    return await export_ctrl.export_to_ply(element_ids, file_path, ply_format, include_colors, include_normals, coordinate_precision)

@mcp.tool(
    name="export_to_stl",
    description="Exports elements to STL format for 3D printing (Ultimaker Cura, PrusaSlicer). Takes optional element_ids, file_path, stl_format, mesh_quality, units, and merge settings."
)
async def export_to_stl(element_ids: Optional[List[int]] = None,
                       file_path: Optional[str] = None,
                       stl_format: str = "binary",
                       mesh_quality: str = "medium",
                       units: str = "mm",
                       merge_elements: bool = True) -> Dict[str, Any]:
    return await export_ctrl.export_to_stl(element_ids, file_path, stl_format, mesh_quality, units, merge_elements)

@mcp.tool(
    name="export_to_gltf",
    description="Exports elements to glTF format for web 3D and real-time rendering (Three.js, Babylon.js, WebXR). Takes optional element_ids, file_path, gltf_format, materials, animations, and compression settings."
)
async def export_to_gltf(element_ids: Optional[List[int]] = None,
                        file_path: Optional[str] = None,
                        gltf_format: str = "glb",
                        include_materials: bool = True,
                        include_animations: bool = False,
                        texture_resolution: int = 1024,
                        compression_level: str = "medium") -> Dict[str, Any]:
    return await export_ctrl.export_to_gltf(element_ids, file_path, gltf_format, include_materials, include_animations, texture_resolution, compression_level)

@mcp.tool(
    name="export_to_x3d",
    description="Exports elements to X3D format for web-based 3D visualization and VR/AR applications. Takes optional element_ids, file_path, x3d_version, encoding, and interactive settings."
)
async def export_to_x3d(element_ids: Optional[List[int]] = None,
                       file_path: Optional[str] = None,
                       x3d_version: str = "4.0",
                       encoding: str = "xml",
                       include_materials: bool = True,
                       include_lighting: bool = True,
                       include_navigation: bool = True,
                       compression: bool = False) -> Dict[str, Any]:
    return await export_ctrl.export_to_x3d(element_ids, file_path, x3d_version, encoding, include_materials, include_lighting, include_navigation, compression)

@mcp.tool(
    name="export_production_data",
    description="Exports comprehensive production data for manufacturing and assembly including cutting lists, assembly instructions, hardware lists, and processing data. Supports multiple formats."
)
async def export_production_data(element_ids: Optional[List[int]] = None,
                               file_path: Optional[str] = None,
                               data_format: str = "json",
                               include_cutting_list: bool = True,
                               include_assembly_instructions: bool = True,
                               include_hardware_list: bool = True,
                               include_processing_data: bool = True,
                               include_material_optimization: bool = True,
                               group_by_production_step: bool = True) -> Dict[str, Any]:
    return await export_ctrl.export_production_data(element_ids, file_path, data_format, include_cutting_list, include_assembly_instructions, include_hardware_list, include_processing_data, include_material_optimization, group_by_production_step)

@mcp.tool(
    name="export_to_fbx",
    description="Exports elements to FBX format for animation, gaming, and 3D applications (Maya, 3ds Max, Blender, Unity, Unreal Engine). Takes optional element_ids, file_path, fbx_format, and animation settings."
)
async def export_to_fbx(element_ids: Optional[List[int]] = None,
                       file_path: Optional[str] = None,
                       fbx_format: str = "binary",
                       fbx_version: str = "2020",
                       include_materials: bool = True,
                       include_textures: bool = True,
                       include_animations: bool = False) -> Dict[str, Any]:
    return await export_ctrl.export_to_fbx(element_ids, file_path, fbx_format, fbx_version, include_materials, include_textures, include_animations)

@mcp.tool(
    name="export_to_webgl",
    description="Exports elements to WebGL format for interactive web 3D visualization and presentations. Creates HTML file with embedded 3D viewer. Takes optional element_ids, file_path, and web settings."
)
async def export_to_webgl(element_ids: Optional[List[int]] = None,
                         file_path: Optional[str] = None,
                         web_quality: str = "medium",
                         include_materials: bool = True,
                         include_textures: bool = True,
                         compression: bool = True,
                         embed_viewer: bool = True) -> Dict[str, Any]:
    return await export_ctrl.export_to_webgl(element_ids, file_path, web_quality, include_materials, include_textures, compression, embed_viewer)

@mcp.tool(
    name="export_to_sat",
    description="Exports elements to SAT format (ACIS) for advanced CAD applications and solid modeling (Spatial, CATIA, SolidWorks). Takes optional element_ids, file_path, scale_factor, format settings, and drilling options."
)
async def export_to_sat(element_ids: Optional[List[int]] = None,
                       file_path: Optional[str] = None,
                       scale_factor: float = 1.0,
                       binary_format: bool = True,
                       sat_version: int = 25000,
                       include_drillings: bool = False,
                       drilling_mode: str = "none") -> Dict[str, Any]:
    return await export_ctrl.export_to_sat(element_ids, file_path, scale_factor, binary_format, sat_version, include_drillings, drilling_mode)

@mcp.tool(
    name="export_to_dstv",
    description="Exports elements to DSTV format for steel construction and CNC machines (NC1, NC2, PSL). Takes optional element_ids, file_path, dstv_version, units, and steel construction parameters."
)
async def export_to_dstv(element_ids: Optional[List[int]] = None,
                        file_path: Optional[str] = None,
                        dstv_version: str = "NC1",
                        units: str = "mm",
                        include_material_info: bool = True,
                        include_processing: bool = True,
                        steel_grade: str = "S355") -> Dict[str, Any]:
    return await export_ctrl.export_to_dstv(element_ids, file_path, dstv_version, units, include_material_info, include_processing, steel_grade)

@mcp.tool(
    name="export_step_with_drillings",
    description="Exports elements to STEP format with drilling processing for manufacturing. Supports extrude/cut drilling modes for CNC machining. Takes optional element_ids, file_path, drilling_mode, and STEP settings."
)
async def export_step_with_drillings(element_ids: Optional[List[int]] = None,
                                    file_path: Optional[str] = None,
                                    drilling_mode: str = "extrude",
                                    scale_factor: float = 1.0,
                                    step_version: int = 214,
                                    text_mode: bool = False,
                                    imperial_units: bool = False) -> Dict[str, Any]:
    return await export_ctrl.export_step_with_drillings(element_ids, file_path, drilling_mode, scale_factor, step_version, text_mode, imperial_units)

@mcp.tool(
    name="export_btl_for_nesting",
    description="Exports BTL file optimized for nesting operations and material efficiency. Includes advanced nesting parameters, optimization methods, and material waste reduction. Takes file_path and nesting settings."
)
async def export_btl_for_nesting(file_path: Optional[str] = None,
                                nesting_parameters: Optional[Dict[str, Any]] = None,
                                optimization_method: str = "area",
                                material_efficiency: bool = True,
                                sheet_size: Optional[List[float]] = None,
                                kerf_width: float = 3.0) -> Dict[str, Any]:
    return await export_ctrl.export_btl_for_nesting(file_path, nesting_parameters, optimization_method, material_efficiency, sheet_size, kerf_width)

@mcp.tool(
    name="export_cutting_list",
    description="Exports optimized cutting list for production with material optimization. Takes optional element_ids, grouping options, and optimization methods."
)
async def export_cutting_list(element_ids: Optional[List[int]] = None,
                             group_by_material: bool = True,
                             include_waste: bool = True,
                             optimization_method: str = "length") -> Dict[str, Any]:
    return await export_ctrl.export_cutting_list(element_ids, group_by_material, include_waste, optimization_method)

# --- IMPORT TOOLS ---

@mcp.tool(
    name="import_from_step",
    description="Imports elements from STEP files for CAD interoperability (SolidWorks, Fusion360, CATIA). Takes file_path, optional scale_factor, insert_position, and import settings."
)
async def import_from_step(file_path: str, scale_factor: float = 1.0,
                          hide_messages: bool = False, insert_position: Optional[List[float]] = None,
                          merge_with_existing: bool = True) -> Dict[str, Any]:
    return await import_ctrl.import_from_step(file_path, scale_factor, hide_messages, insert_position, merge_with_existing)

@mcp.tool(
    name="import_from_sat",
    description="Imports elements from SAT files (ACIS format) for solid modeling (Spatial, CATIA). Takes file_path, optional scale_factor, format settings, and import options."
)
async def import_from_sat(file_path: str, scale_factor: float = 1.0,
                         binary_format: bool = True, insert_position: Optional[List[float]] = None,
                         silent_mode: bool = False) -> Dict[str, Any]:
    return await import_ctrl.import_from_sat(file_path, scale_factor, binary_format, insert_position, silent_mode)

@mcp.tool(
    name="import_from_rhino",
    description="Imports elements from Rhino 3DM files for parametric design workflows. Takes file_path and optional import settings for layers, materials, and dialogs."
)
async def import_from_rhino(file_path: str, without_dialog: bool = False,
                           import_layers: bool = True, import_materials: bool = True,
                           scale_factor: float = 1.0) -> Dict[str, Any]:
    return await import_ctrl.import_from_rhino(file_path, without_dialog, import_layers, import_materials, scale_factor)

@mcp.tool(
    name="import_from_btl",
    description="Imports elements from BTL files for CNC data integration. Takes file_path and optional import_mode, validation, and processing settings."
)
async def import_from_btl(file_path: str, import_mode: str = "standard",
                         merge_duplicates: bool = True, validate_geometry: bool = True,
                         import_processing: bool = True) -> Dict[str, Any]:
    return await import_ctrl.import_from_btl(file_path, import_mode, merge_duplicates, validate_geometry, import_processing)


# --- LIST & REPORT TOOLS ---

@mcp.tool(
    name="create_element_list",
    description="Create a comprehensive element list with optional filtering and grouping. Takes optional element IDs and various display/sorting options."
)
async def create_element_list(element_ids: Optional[List[int]] = None,
                            include_properties: bool = True,
                            include_materials: bool = True,
                            include_dimensions: bool = True,
                            group_by: str = "type",
                            sort_by: str = "name",
                            filter_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return await list_ctrl.create_element_list(element_ids, include_properties, include_materials, 
                                             include_dimensions, group_by, sort_by, filter_criteria)

@mcp.tool(
    name="generate_material_list",
    description="Generate comprehensive material list for production and ordering. Takes optional element IDs and various calculation parameters."
)
async def generate_material_list(element_ids: Optional[List[int]] = None,
                               include_waste: bool = True,
                               waste_factor: float = 0.1,
                               group_by_material: bool = True,
                               include_costs: bool = False,
                               cost_database: str = "default",
                               optimization_mode: str = "length") -> Dict[str, Any]:
    return await list_ctrl.generate_material_list(element_ids, include_waste, waste_factor, 
                                                group_by_material, include_costs, cost_database, optimization_mode)

@mcp.tool(
    name="optimize_cutting_list",
    description="Optimize cutting lists for minimal material waste and efficient production. Takes optional element IDs and optimization parameters."
)
async def optimize_cutting_list(element_ids: Optional[List[int]] = None,
                              stock_lengths: Optional[List[float]] = None,
                              optimization_algorithm: str = "bin_packing",
                              kerf_width: float = 3.0,
                              min_offcut_length: float = 100.0,
                              max_waste_percentage: float = 5.0,
                              material_groups: Optional[Dict[str, List[str]]] = None,
                              priority_mode: str = "waste_minimization") -> Dict[str, Any]:
    return await optimization_ctrl.optimize_cutting_list(element_ids, stock_lengths, optimization_algorithm,
                                                       kerf_width, min_offcut_length, max_waste_percentage,
                                                       material_groups, priority_mode)


# --- VESTACK MODULAR TOOLS (domain extension) ---

@mcp.tool(
    name="get_module_inventory",
    description=(
        "Lists the modules of a Vestack modular building with their dimensions. "
        "A module is a rectangular box identified by an 'MXXX' id (M001, M139...) "
        "read from a Cadwork user attribute named 'Module', or failing that from "
        "the subgroup, group or element name; the field actually used is reported "
        "as id_source. Per module: length, width and height in MILLIMETRES "
        "(length and width come from the bottom floor slab, height from the whole "
        "envelope), footprint area in m2, wall count, which sides are open "
        "('-x', '+x', '-y', '+y' — an open module is one built to join into a "
        "larger room), whether a top floor is present, and the building and level "
        "from the 'Batiment' and 'Niveau' attributes. "
        "Scanning the whole model reads the vertices of every element and is slow: "
        "pass element_ids, or active_only=true to cover just the current selection."
    )
)
async def get_module_inventory(element_ids: Optional[List[int]] = None,
                               active_only: bool = False,
                               id_source: Optional[str] = None) -> Dict[str, Any]:
    return await vestack_ctrl.get_module_inventory(element_ids, active_only, id_source)


@mcp.tool(
    name="get_object_inventory",
    description=(
        "Lists the objects of each Vestack module - walls, slabs, roofs, parapets, "
        "openings - with their envelopes in MILLIMETRES, in a frame local to each "
        "module (origin at a bottom-floor corner, X along its longer side, Z up), "
        "for comparison with the Revit model. Walls come from part subgroups "
        "(M1-W5 = module 1, wall 5) and their MOB<section> body element; openings "
        "are MEX joinery attached to the wall containing them. Without module_ids "
        "it returns a summary per module (frame, counts, warnings); pass "
        "module_ids=['M1'] for that module's objects, and element_detail="
        "'envelope' or 'vertices' to also get each element in the module frame. "
        "output_path writes the full inventory (every module, every object) as "
        "JSON and still returns the summary. Reads attributes of the whole model "
        "(about 1 min on a large building) and vertices only where needed. "
        "Schema: vestack/OBJECT_INVENTORY.md."
    )
)
async def get_object_inventory(element_ids: Optional[List[int]] = None,
                               active_only: bool = False,
                               module_ids: Optional[List[str]] = None,
                               element_detail: str = "none",
                               output_path: Optional[str] = None) -> Dict[str, Any]:
    return await vestack_ctrl.get_object_inventory(element_ids, active_only, module_ids,
                                                   element_detail, output_path)


if __name__ == "__main__":
    import argparse
    logger = get_logger()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Cadwork MCP Server")
    parser.add_argument("script_name", nargs='?', help="Script name (ignored)")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio", 
                       help="Transport protocol to use")
    parser.add_argument("--port", type=int, default=8001, 
                       help="Port for HTTP transport")
    parser.add_argument("--host", default="localhost", 
                       help="Host for HTTP transport")
    
    args = parser.parse_args()
    
    if args.transport == "http":
        logger.info(f"Starting Cadwork MCP Server with HTTP transport on {args.host}:{args.port}...")
        try:
            # Use uvicorn for HTTP transport. FastMCP has no `.app`; the ASGI
            # application is built by streamable_http_app().
            import uvicorn
            uvicorn.run(mcp.streamable_http_app(), host=args.host, port=args.port)
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server failed: {e}")
            import sys
            sys.exit(1)
    else:
        logger.info("Starting Cadwork MCP Server with stdio transport...")
        try:
            mcp.run(transport='stdio')
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server failed: {e}")
            import sys
            sys.exit(1)

# Add a helper tool for axis information
@mcp.tool(
    name="get_cadwork_axis_info",
    description="Returns important Cadwork axis direction information for correct beam and panel creation."
)
async def get_cadwork_axis_info() -> Dict[str, Any]:
    if AXIS_CONFIG_AVAILABLE:
        helper = CadworkAxisHelper()
        return {
            "status": "ok",
            "axis_info": CADWORK_AXIS_INFO,
            "helper_available": True,
            "standard_dimensions": helper.get_beam_dimensions("80x80"),
            "validation_example": {
                "vertical_beam_correct": helper.validate_beam_orientation([0,0,0], [0,0,800], 'Z'),
                "horizontal_beam_x_correct": helper.validate_beam_orientation([0,0,0], [800,0,0], 'X')
            }
        }
    else:
        return {
            "status": "warning", 
            "message": "Cadwork axis configuration not loaded",
            "basic_info": "For vertical beams: p1/p2 in Z-direction, width=X-axis, height=Y-axis"
        }
