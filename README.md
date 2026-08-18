# Cadwork MCP Server

A **Model Context Protocol (MCP) server** for Cadwork 3D that lets Claude and other AI assistants interact directly with Cadwork 3D.

> **About this document.** This is the English translation of the original German README, kept as [`README_DE.md`](README_DE.md). The function inventory below is the author's roadmap: **29 of the declared tools have no implementation** and answer `Unknown operation` — the exact list is in [`.claude/skills/cadwork-model/tool-inventory.md`](.claude/skills/cadwork-model/tool-inventory.md), generated from the code. See [`CLAUDE.md`](CLAUDE.md) for the verified architecture.

> **Driving a model with an AI assistant?** Read the [`cadwork-model` skill](.claude/skills/cadwork-model/SKILL.md) first. It frames the two use cases — reading a model (module inventory, element counts) and changing one (the guarded procedure for moving an element) — and there is no undo on the write path.

## 🚀 Installation

### 1. Prerequisites
- **Python 3.12** installed (`mypy.ini` targets 3.12)
- **Cadwork 3D**
- **Claude Desktop**

### 2. Clone the repository and install the dependencies
⚠️ **IMPORTANT:** the project **must** live on the C: drive, at `C:\cadworkMCP`. That path is hardcoded in `start.txt`, in the Cadwork plugin and in `claude_desktop_config.json`.

```bash
git clone <repository-url> C:\cadworkMCP
cd C:\cadworkMCP
pip install -r requirements.txt
```

### 3. Set up the Cadwork bridge
The `bridge` folder is activated automatically through the MCP Bridge plugin. To install the plugin itself, see [`API.x64/MCPBridge/README.md`](API.x64/MCPBridge/README.md).

**Starting the bridge:**
1. Start Cadwork 3D
2. Go to **Window → Plugins → MCP Bridge**
3. Click **"Start Bridge"** to open the connection
4. After changing bridge code: **"Stop Bridge"** → **"Start Bridge"** to restart (restart Cadwork if modules were already imported)

### 4. Configure Claude Desktop

The MCP configuration goes into the Claude Desktop `config.json`:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the following:
```json
{
  "mcpServers": {
    "cadwork": {
      "command": "python",
      "args": ["C:\\cadworkMCP\\main.py"],
      "env": {}
    }
  }
}
```

### 5. The server starts automatically
Claude Desktop starts the MCP server itself when you chat with Claude. No manual start required. 🚀

## 📋 Function status

### ✅ Element operations (54 functions)
- **Creation:** `create_beam`, `create_panel`, `create_surface`, `create_beam_from_points`, `create_auxiliary_line`, `create_circular_beam_points`, `create_square_beam_points`, `create_standard_beam_points`, `create_standard_panel_points`, `create_drilling_points`, `create_polygon_beam`, `create_auxiliary_beam_points`, `create_solid_wood_panel`
- **Queries:** `get_active_element_ids`, `get_all_element_ids`, `get_visible_element_ids`, `get_element_info`, `get_user_element_ids`
- **Editing:** `delete_elements`, `copy_elements`, `move_element`, `duplicate_elements`, `stretch_elements`, `scale_elements`, `mirror_elements`, `chamfer_edge`, `round_edge`, `split_element`
- **Filtering:** `get_elements_by_type`, `filter_elements_by_material`, `get_elements_in_group`, `get_elements_by_color`, `get_elements_by_layer`, `get_elements_by_dimension_range`, `get_elements_in_region`
- **Statistics:** `get_element_count_by_type`, `get_material_statistics`, `get_group_statistics`
- **Connections:** `join_elements`, `unjoin_elements`
- **Timber joints:** `cut_corner_lap`, `cut_cross_lap`, `cut_half_lap`, `cut_double_tenon`, `cut_scarf_joint`, `cut_shoulder`
- **Conversion:** `convert_beam_to_panel`, `convert_panel_to_beam`, `convert_auxiliary_to_beam`
- **Containers:** `create_auto_container_from_standard`, `get_container_content_elements`

### ✅ Geometry operations (37 functions)
- **Dimensions:** `get_element_width`, `get_element_height`, `get_element_length`, `get_element_volume`, `get_element_weight`
- **Bounding box:** `get_bounding_box`
- **Outlines:** `get_element_outline`, `get_section_outline`
- **Boolean operations:** `intersect_elements`, `subtract_elements`, `unite_elements`
- **Vectors & points:** `get_element_xl`, `get_element_yl`, `get_element_zl`, `get_element_p1`, `get_element_p2`, `get_element_p3`
- **Centre of gravity:** `get_center_of_gravity`, `get_center_of_gravity_for_list`, `calculate_center_of_mass`
- **Vertices & faces:** `get_element_vertices`, `get_element_facets`, `get_element_reference_face_area`, `get_total_area_of_all_faces`
- **Analysis:** `get_minimum_distance_between_elements`, `get_closest_point_on_element`, `get_element_type`, `project_point_to_element`, `check_collisions`, `validate_joints`
- **Transformations:** `rotate_elements`, `apply_global_scale`, `invert_model`, `rotate_height_axis_90`, `rotate_length_axis_90`
- **Calculations:** `calculate_total_volume`, `calculate_total_weight`

### ✅ Attribute management (16 functions)
- **Queries:** `get_standard_attributes`, `get_user_attributes`, `list_defined_user_attributes`, `get_element_attribute_display_name`
- **Setters:** `set_name`, `set_material`, `set_group`, `set_comment`, `set_subgroup`, `set_user_attribute`
- **Advanced:** `clear_user_attribute`, `copy_attributes`
- **Batch operations:** `batch_set_user_attributes`, `validate_attribute_consistency`
- **Business intelligence:** `search_elements_by_attributes`, `export_attribute_report`

### ✅ Visualisation (15 functions)
- **Properties:** `set_color`, `set_visibility`, `set_transparency`, `get_color`, `get_transparency`
- **Global control:** `show_all_elements`, `hide_all_elements`, `refresh_display`, `get_visible_element_count`
- **Smart visualisation:** `create_visual_filter`, `apply_color_scheme`
- **Animation & camera:** `create_assembly_animation`, `set_camera_position`, `create_walkthrough`

### ✅ Utility functions (6 functions)
- **Display:** `disable_auto_display_refresh`, `enable_auto_display_refresh`
- **Messages:** `print_error`, `print_warning`
- **Project:** `get_3d_file_path`, `get_project_data`, `get_cadwork_version_info`

### ✅ Specialised modules
- **Shop drawings (2):** `add_wall_section_x`, `add_wall_section_y`
- **Roof analysis (2):** `get_roof_surfaces`, `calculate_roof_area`
- **Machine integration (1):** `check_production_list_discrepancies`
- **Measurements (3):** `measure_distance`, `measure_angle`, `measure_area`
- **Material management (3):** `create_material`, `get_material_properties`, `list_available_materials`
- **Shop drawings (4):** `add_wall_section_x`, `add_wall_section_y`, `add_wall_section_vertical`, `export_2d_wireframe`
- **Export/import (24):** `export_to_btl`, `export_element_list`, `export_to_ifc`, `export_to_dxf`, `export_workshop_drawings`, `export_cutting_list`, `export_to_step`, `export_to_3dm`, `export_to_obj`, `export_to_ply`, `export_to_stl`, `export_to_gltf`, `export_to_x3d`, `export_production_data`, `export_to_fbx`, `export_to_webgl`, `export_to_sat`, `export_to_dstv`, `export_step_with_drillings`, `export_btl_for_nesting`, `import_from_step`, `import_from_sat`, `import_from_rhino`, `import_from_btl`

**Current count: 164 declared functions** (recent additions: collision detection, material lists, animations, camera control, joint validation, walkthrough, cutting optimisation)

## 🎯 Tests

```bash
python -m unittest discover -s tests -t .     # 72 tests, no Cadwork needed
```

The suite runs outside Cadwork by stubbing it: handler modules are replaced by
`tests/stub_handlers*.py`, and the Vestack adapter tests inject fake
`element_controller` / `geometry_controller` / `attribute_controller` modules into
`sys.modules`. That works only because every handler imports the Cadwork modules
*inside* its functions — keep it that way.

Covered: the module inventory logic, the dispatcher's handler discovery and
response contract, and the Cadwork API router. **Not covered: anything against a
live Cadwork installation.**

The older suite the original document advertised (37/37, 25/25, …) was deleted in
commit `8e01527` and is unrelated.

## ❌ Missing Cadwork API functions (still to implement)

**Remaining: 82 of the roughly 238 planned functions**

### 🏠 Buildings & structures (9 functions) — **HIGHEST PRIORITY**
- `create_wall_system`, `create_floor_system`, `create_roof_system`
- `generate_frame_structure`, `optimize_timber_structure`
- `perform_structural_analysis`, `create_foundation_elements`
- `generate_load_paths`, `calculate_load_distribution`

### 📊 Extended export & import (12 functions) — **CRITICAL**
- `export_to_hundegger`, `export_to_weinmann`, `export_to_krusi`
- `import_from_cad`, `export_assembly_instructions`
- `generate_production_data`, `create_cnc_program`
- `export_material_optimization`, `import_point_cloud`
- `export_vr_model`, `import_survey_data`, `export_energy_analysis`

### 📋 Lists & reports (8 functions) — **IMPORTANT**
- **Implemented:** `create_element_list`, `generate_material_list`
- **Remaining:** `create_cost_calculation`, `export_assembly_drawings`, `create_production_schedule`, `generate_quality_report`, `create_delivery_note`, `generate_waste_report`, `create_timeline_report`, `generate_compliance_report`

### 🔧 Extended element operations (7 functions)
- **Implemented:** `validate_joints`
- **Remaining:** `get_nested_elements`, `get_parent_elements`, `get_child_elements`, `create_dovetail_joint`, `create_mortise_tenon`, `create_finger_joint`, `automatic_beam_processing`, `add_drilling_pattern`

### 🏭 Production integration (7 functions) — **INDUSTRY 4.0**
- `machine_time_estimation`, `production_line_optimization`
- `quality_control_integration`, `inventory_management`
- `supplier_integration`, `logistics_optimization`, `maintenance_scheduling`

### 📐 Extended geometry analysis (6 functions)
- `check_collisions`, `validate_joints`, `verify_dimensions`
- `analyze_material_usage`, `optimize_waste_reduction`, `calculate_static_properties`

### 🎨 Extended materials & textures (7 functions)
- `assign_texture`, `set_element_density`, `set_thermal_properties`
- `create_custom_material`, `material_cost_calculation`
- `material_environmental_impact`, `material_fire_resistance`

### 🎬 Extended animation & visualisation (6 functions)
- **Implemented:** `create_assembly_animation`, `set_camera_position`, `create_walkthrough`
- **Remaining:** `generate_renderings`, `set_lighting_conditions`, `create_exploded_view`, `create_section_views`, `generate_panorama_view`, `create_time_lapse`

### ⚙️ System & configuration (8 functions)
- `get_system_settings`, `set_user_preferences`, `manage_templates`
- `backup_project`, `restore_project`, `sync_with_cloud`
- `manage_licenses`, `system_diagnostics`

### 🔗 Extended connections (5 functions)
- **Implemented:** `optimize_cutting_list`
- **Remaining:** `create_custom_processing`, `create_complex_joints`, `validate_joint_strength`, `calculate_joint_forces`, `optimize_joint_placement`

**Progress claimed: 68.9% (164/238 functions)**
**Remaining: 31.1% (74/238 functions)**

## 🏗️ Project structure

```
C:\cadworkMCP/              # MUST be on C:\
├── main.py                 # Main MCP server with all tool definitions
├── requirements.txt        # Python dependencies
├── mypy.ini                # Mypy configuration for type safety
├── cadwork_bridge.py       # Bridge entry point (socket server, runs inside Cadwork)
├── claude_desktop_config.json  # Example configuration
│
├── core/                   # Core functionality
│   ├── server.py           # MCP server setup
│   ├── connection.py       # Cadwork connection management
│   └── logging.py          # Logging configuration
│
├── controllers/            # Function groups (controller pattern)
│   ├── base_controller.py         # Base controller
│   ├── element_controller.py      # Element operations
│   ├── geometry_controller.py     # Geometry operations
│   ├── attribute_controller.py    # Attribute management
│   ├── visualization_controller.py # Visualisation
│   ├── utility_controller.py      # Utility functions
│   ├── shop_drawing_controller.py # Shop drawings
│   ├── roof_controller.py         # Roof analysis
│   └── machine_controller.py      # Machine integration
│
├── bridge/                 # Cadwork bridge (runs inside Cadwork)
│   ├── dispatcher.py       # Discovers handle_* operations by convention
│   ├── cadwork_api.py      # Router to the real Cadwork API modules
│   ├── helpers.py          # Helper functions
│   └── handlers/           # Handlers that call the real cadwork API
│
├── vestack/                # Vestack modular domain extension (removable)
├── tests/                  # Unit tests, runnable without Cadwork
├── .claude/skills/         # cadwork-model skill: how to drive a live model
└── API.x64/                # Cadwork plugin files
```

## 📝 Code guidelines

### Conventions
- **Async/await:** all MCP tools are asynchronous
- **Type safety:** full mypy compatibility with `Dict[str, Any]` return types
- **Parameter types:** specific list types (`List[int]`, `List[float]`)
- **English comments:** all code comments in English
- **Controller pattern:** functions grouped by domain
- **Units:** millimetres throughout, matching Cadwork's native unit

### Adding a new function
1. **Write the bridge handler**: `handle_<operation>(args)` in the matching
   `bridge/handlers/` module. The name is what registers it — the dispatcher
   discovers it, there is no table to edit.
2. **Extend a controller** in `controllers/` (or create one) with an `async def`
   that validates its input and calls `self.send_command("<operation>", args)`.
3. **Register the MCP tool in `main.py`**.

A tool declared without a handler returns `Unknown operation`. The argument keys
are the wire contract: the handler reads them with `args.get("...")`.

### Debugging
- Logging is configured in `core/logging.py`
- The Cadwork connection is managed in `core/connection.py`
- The bridge prints to the Cadwork console; use the plugin's status display to confirm it is listening on port 53002

### Reference documentation
The authoritative Cadwork API reference is the cwapi3d Python documentation: <https://docs.cadwork.com/projects/cwapi3dpython/en/latest/> (sources: <https://github.com/cwapi3d/cwapi3dpython>).

---

*Last update of the original German document: July 2025 — 164/238 functions declared (68.9%). English translation and accuracy notes added August 2026.*
