"""Material creation functions for IFC entities"""


def create_material(file, name, color_rgb):
    """Create a colored material"""
    color = file.create_entity(
        "IfcColourRgb",
        Name=name,
        Red=color_rgb[0],
        Green=color_rgb[1],
        Blue=color_rgb[2],
    )
    surface_style_rendering = file.create_entity(
        "IfcSurfaceStyleRendering",
        SurfaceColour=color,
        Transparency=0.0,
        ReflectanceMethod="FLAT",
    )
    surface_style = file.create_entity(
        "IfcSurfaceStyle",
        Name=f"{name} Material",
        Side="BOTH",
        Styles=[surface_style_rendering],
    )
    material = file.create_entity("IfcMaterial", Name=f"{name} Material")

    # Get the first representation context
    context = file.by_type("IfcRepresentationContext")[0]
    styled_representation = file.create_entity(
        "IfcStyledRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Material",
        RepresentationType="Material",
        Items=[file.create_entity("IfcStyledItem", Item=None, Styles=[surface_style])],
    )
    file.create_entity(
        "IfcMaterialDefinitionRepresentation",
        Representations=[styled_representation],
        RepresentedMaterial=material,
    )
    return material


def create_coordination_material(file):
    """Create a special material for coordination objects (blue)"""
    return create_material(file, "Coordination", (0.0, 0.5, 1.0))


# Additional material functions
def create_red_material(file):
    """Create a red material for survey markers"""
    return create_material(file, "Red", (1.0, 0.0, 0.0))


def create_magenta_material(file):
    """Create a magenta material for pie slices"""
    return create_material(file, "Magenta", (1.0, 0.0, 1.0))


def create_teal_material(file):
    """Create a teal material for north arrow and cylinder"""
    return create_material(file, "Teal", (0.0, 0.5, 0.5))
