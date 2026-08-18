# Tool inventory

Generated from the code: an operation works end to end only when `main.py`
declares the tool **and** a `handle_<operation>` exists. Counts below:
**167 tools declared**, **140 handlers**,
**29 tools with no handler**.

Legend: (w) changes the model — Lane 2 rules apply. (f) writes a file to disk.
Everything unmarked is read-only.

## Attributes

- `batch_set_user_attributes` (w)
- `clear_user_attribute` (w)
- `copy_attributes` (w)
- `export_attribute_report` (f)
- `get_element_attribute_display_name`
- `get_standard_attributes`
- `get_user_attributes`
- `list_defined_user_attributes`
- `search_elements_by_attributes`
- `set_comment` (w)
- `set_group` (w)
- `set_material` (w)
- `set_name` (w)
- `set_subgroup` (w)
- `set_user_attribute` (w)
- `validate_attribute_consistency`

## Elements

- `convert_auxiliary_to_beam` (w)
- `convert_beam_to_panel` (w)
- `convert_panel_to_beam` (w)
- `copy_elements` (w)
- `create_auto_container_from_standard` (w)
- `create_auxiliary_beam_points` (w)
- `create_auxiliary_line` (w)
- `create_beam` (w)
- `create_beam_from_points` (w)
- `create_circular_beam_points` (w)
- `create_drilling_points` (w)
- `create_panel` (w)
- `create_polygon_beam` (w)
- `create_solid_wood_panel` (w)
- `create_square_beam_points` (w)
- `create_standard_beam_points` (w)
- `create_standard_panel_points` (w)
- `create_surface` (w)
- `cut_corner_lap` (w)
- `cut_cross_lap` (w)
- `cut_double_tenon` (w)
- `cut_half_lap` (w)
- `cut_scarf_joint` (w)
- `cut_shoulder` (w)
- `delete_elements` (w)
- `duplicate_elements` (w)
- `filter_elements_by_material`
- `get_active_element_ids`
- `get_all_element_ids`
- `get_container_content_elements`
- `get_element_count_by_type`
- `get_element_info`
- `get_elements_by_type`
- `get_elements_in_group`
- `get_elements_in_region`
- `get_group_statistics`
- `get_material_statistics`
- `get_user_element_ids`
- `get_visible_element_ids`
- `join_elements` (w)
- `move_element` (w)
- `unjoin_elements` (w)

## Export

- `export_btl_for_nesting` (f)
- `export_production_data` (f)
- `export_step_with_drillings` (f)
- `export_to_3dm` (f)
- `export_to_dstv` (f)
- `export_to_fbx` (f)
- `export_to_gltf` (f)
- `export_to_obj` (f)
- `export_to_ply` (f)
- `export_to_sat` (f)
- `export_to_step` (f)
- `export_to_stl` (f)
- `export_to_webgl` (f)
- `export_to_x3d` (f)

## Geometry

- `apply_global_scale` (w)
- `calculate_total_volume`
- `calculate_total_weight`
- `check_collisions`
- `get_bounding_box`
- `get_center_of_gravity`
- `get_center_of_gravity_for_list`
- `get_element_facets`
- `get_element_height`
- `get_element_length`
- `get_element_p1`
- `get_element_p2`
- `get_element_p3`
- `get_element_reference_face_area`
- `get_element_type`
- `get_element_vertices`
- `get_element_volume`
- `get_element_weight`
- `get_element_width`
- `get_element_xl`
- `get_element_yl`
- `get_element_zl`
- `get_minimum_distance_between_elements`
- `get_total_area_of_all_faces`
- `invert_model` (w)
- `rotate_elements` (w)
- `rotate_height_axis_90` (w)
- `rotate_length_axis_90` (w)
- `validate_joints`

## Import

- `import_from_btl` (f)
- `import_from_rhino` (f)
- `import_from_sat` (f)
- `import_from_step` (f)

## Lists

- `create_element_list` (w)
- `generate_material_list`

## Machine

- `check_production_list_discrepancies`

## Optimisation

- `optimize_cutting_list`

## Roof

- `calculate_roof_area`
- `get_roof_surfaces`

## Shop drawings

- `add_wall_section_vertical` (w)
- `add_wall_section_x` (w)
- `add_wall_section_y` (w)
- `export_2d_wireframe` (f)

## Utility / project

- `disable_auto_display_refresh`
- `enable_auto_display_refresh`
- `get_3d_file_path`
- `get_cadwork_version_info`
- `get_project_data`
- `print_error`
- `print_warning`

## Visualisation

- `apply_color_scheme`
- `create_assembly_animation` (w)
- `create_visual_filter` (w)
- `create_walkthrough` (w)
- `get_color`
- `get_transparency`
- `get_visible_element_count`
- `hide_all_elements`
- `refresh_display`
- `set_camera_position` (w)
- `set_color` (w)
- `set_transparency` (w)
- `set_visibility` (w)
- `show_all_elements`

## Vestack (domain extension)

- `get_module_inventory`

## Declared but not implemented

These answer `Unknown operation`. Do not retry or rephrase — tell the user the
tool is not implemented. Implementing one means writing its `handle_<operation>`
in the matching `bridge/handlers/` module; the dispatcher then picks it up with
no further wiring.

- `calculate_center_of_mass`
- `chamfer_edge`
- `create_material`
- `export_cutting_list`
- `export_element_list`
- `export_to_btl`
- `export_to_dxf`
- `export_to_ifc`
- `export_workshop_drawings`
- `get_closest_point_on_element`
- `get_element_outline`
- `get_elements_by_color`
- `get_elements_by_dimension_range`
- `get_elements_by_layer`
- `get_material_properties`
- `get_section_outline`
- `intersect_elements`
- `list_available_materials`
- `measure_angle`
- `measure_area`
- `measure_distance`
- `mirror_elements`
- `project_point_to_element`
- `round_edge`
- `scale_elements`
- `split_element`
- `stretch_elements`
- `subtract_elements`
- `unite_elements`

## Bridge-only operations

Reachable on the socket but not exposed as MCP tools:

- `get_model_name`
- `get_version_info`
- `ping`

`ping` is what `CadworkConnection.test_connection()` uses for the handshake.

## Never call to "test"

Model-wide or irreversible, whatever the scope you think you passed:

- `delete_elements` — no recycle bin on the bridge side
- `invert_model`, `apply_global_scale` — whole model
- `join_elements` / `unjoin_elements` — restructures assemblies
- `cut_*` — removes material permanently

Try these on a copy of the .3d file, never on the modeller's open project.
