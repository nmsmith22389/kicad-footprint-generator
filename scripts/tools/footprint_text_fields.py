from KicadModTree import Text, Property, Vector2D

from scripts.tools.global_config_files.global_config import GlobalConfig, FieldProperties, FieldPosition


def _roundToBase(value, base):
    return round(value/base) * base


def _getTextFieldDetails(
    global_config: GlobalConfig,
    field_definition: FieldProperties,
    body_edges,
    courtyard,
    text_y_inside_position: float | str="center",
    allow_rotation=False,
):
    body_size = [body_edges['right'] - body_edges['left'], body_edges['bottom'] - body_edges['top']]
    body_center = Vector2D((body_edges['right'] + body_edges['left'])/2, (body_edges['bottom'] + body_edges['top'])/2)

    # Pull out the layer config for the field
    layer_config = global_config.get_text_properties_for_layer(field_definition.layer)

    # We have some internal options like "inside left/right", so use a string
    position_y: str = field_definition.position_y.value
    at = Vector2D(body_center)

    if body_size[0] < body_size[1] and allow_rotation and position_y == FieldPosition.INSIDE.value:
        rotation = 1
    else:
        rotation = 0

    if not field_definition.autosize:
        size = layer_config.size_nom
        fontwidth = layer_config.thickness_ratio * size
    else:
        # We want at least 3 char reference designators space. If we can't fit these we move the reverence to the outside.
        size_max = layer_config.size_max
        size_min = layer_config.size_min

        if body_size[rotation] >= 4*size_max:
            if body_size[0] >= 4*size_max:
                rotation = 0
            size = size_max
        elif body_size[rotation] < 4*size_min:
            size = size_min
            if body_size[rotation] < 3*size_min:
                if position_y == FieldPosition.INSIDE.value:
                    rotation = 0
                    position_y = FieldPosition.OUTSIDE_TOP.value
        else:
            fs = _roundToBase(body_size[rotation]/4, 0.01)
            size = fs

        if size > body_size[(rotation+1)%2]-0.2:
            fs = max(body_size[(rotation+1)%2]-0.2, size_min)
            size = fs

        fontwidth = _roundToBase(layer_config.thickness_ratio * size, 0.01)

    if position_y == FieldPosition.INSIDE.value:
        if text_y_inside_position == 'top':
            position_y = "inside_top"
        elif text_y_inside_position == 'bottom':
            position_y = "inside_bottom"
        elif text_y_inside_position == 'left':
            position_y = "inside_left"
        elif text_y_inside_position == 'right':
            position_y = "inside_right"
        elif isinstance(text_y_inside_position, int) or isinstance(text_y_inside_position, float):
            at[1] = text_y_inside_position

    text_edge_offset = size / 2 + 0.2

    if position_y == "outside_top":
        at = [body_center[0], courtyard['top']-text_edge_offset]
    elif position_y == "inside_top":
        at = [body_center[0], body_edges['top']+text_edge_offset]
    elif position_y == "inside_left":
        at = [body_edges['left'] + text_edge_offset, body_center[1]]
        rotation = 1
    elif position_y == "inside_right":
        at = [body_edges['right'] - text_edge_offset, body_center[1]]
        rotation = 1
    elif position_y == "outside_bottom":
        at = [body_center[0], courtyard['bottom']+text_edge_offset]
    elif position_y == "inside_bottom":
        at = [body_center[0], body_edges['bottom']-text_edge_offset]

    at = [_roundToBase(at[0],0.01), _roundToBase(at[1],0.01)]

    return {
        "at": at,
        "size": Vector2D(size, layer_config.width_ratio * size),
        "layer": field_definition.layer,
        "thickness": fontwidth,
        "rotation": rotation * 90,
    }


def addTextFields(kicad_mod,
                  configuration: dict | GlobalConfig,
                  body_edges, courtyard, fp_name,
                  text_y_inside_position: float | str = 'center',
                  allow_rotation = False):
    """
    Automatically add reference and value fields to a footprint, placing them in the body according to the
    GlobalConfig settings.

    :param kicad_mod: The footprint to add the fields to
    :param configuration: The GlobalConfig object or dictionary to use for the field placement
    :param body_edges: The bounding box of the body of the footprint
    :param courtyard: The bounding box of the courtyard of the footprint
    :param fp_name: The name of the footprint
    :param text_y_inside_position: The position of the text inside the body. This can be
        'center', 'top', 'bottom', 'left', 'right', or a specific Y position.
    :param allow_rotation: Allow the text to be rotated if it fits better
    """

    if isinstance(configuration, dict):
        # Legacy "direct-configuration" code passing in dictionaries
        # This dictionary IS a GlobalConfig definition, so construct it here. This is a
        # stopgap until generator code is updated to use GlobalConfig directly.
        # Don't write new code that passes in dictionaries.
        global_config = GlobalConfig(configuration)
    else:
        # it's already a GlobalConfig object
        global_config = configuration

    kicad_mod.append(Property(name='Reference', text='REF**',
        **_getTextFieldDetails(global_config, global_config.reference_fields[0], body_edges, courtyard, text_y_inside_position, allow_rotation)))

    for additional_ref in global_config.reference_fields[1:]:
        kicad_mod.append(Text(text='${REFERENCE}',
        **_getTextFieldDetails(global_config, additional_ref, body_edges, courtyard, text_y_inside_position, allow_rotation)))

    kicad_mod.append(Property(name='Value', text=fp_name,
        **_getTextFieldDetails(global_config, global_config.value_fields[0], body_edges, courtyard, text_y_inside_position, allow_rotation)))

    for additional_value in global_config.value_fields[1:]:
        kicad_mod.append(Text(text='%V',
            **_getTextFieldDetails(global_config, additional_value, body_edges, courtyard, text_y_inside_position, allow_rotation)))
