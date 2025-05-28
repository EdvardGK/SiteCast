"""Information cube creation for IFC"""

from .builder import create_guid
from .geometry_enhanced import create_information_cube_geometry


def create_information_cube(file, storey, context, material, basepoint_coords, config):
    """Create an information cube above the basepoint"""
    # Calculate position (above basepoint)
    x, y, z = basepoint_coords
    z_position = z + config["elevation"]

    # Create geometry
    cube_geom = create_information_cube_geometry(file, context, config["size"])

    # Create shape representation
    shape = file.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Body",
        RepresentationType="Brep",
        Items=[cube_geom],
    )

    # Create product definition shape
    product_shape = file.create_entity(
        "IfcProductDefinitionShape", Representations=[shape]
    )

    # Create local placement
    placement = file.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity(
                "IfcCartesianPoint", Coordinates=(x, y, z_position)
            ),
        ),
    )

    # Create annotation element
    info_cube = file.create_entity(
        "IfcAnnotation",
        GlobalId=create_guid(),
        Name="Information_Cube",
        Description="Project information and links",
        ObjectType="Information",
        ObjectPlacement=placement,
        Representation=product_shape,
    )

    # Assign material
    file.create_entity(
        "IfcRelAssociatesMaterial",
        GlobalId=create_guid(),
        RelatedObjects=[info_cube],
        RelatingMaterial=material,
    )

    # Add to storey
    file.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=create_guid(),
        RelatingStructure=storey,
        RelatedElements=[info_cube],
    )

    # Create property set with links
    properties = []

    # Add project info
    prop_info = file.create_entity(
        "IfcPropertySingleValue",
        Name="Project_Info",
        NominalValue=file.create_entity("IfcText", "SiteCast Project Information Cube"),
    )
    properties.append(prop_info)

    # Add links
    for i, link in enumerate(config["links"]):
        prop_link = file.create_entity(
            "IfcPropertySingleValue",
            Name=f"Link_{i + 1}_{link['name'].replace(' ', '_')}",
            NominalValue=file.create_entity("IfcText", link["url"]),
        )
        properties.append(prop_link)

    # Create property set
    property_set = file.create_entity(
        "IfcPropertySet",
        GlobalId=create_guid(),
        Name="Information_Links",
        HasProperties=properties,
    )

    # Attach properties
    file.create_entity(
        "IfcRelDefinesByProperties",
        GlobalId=create_guid(),
        RelatedObjects=[info_cube],
        RelatingPropertyDefinition=property_set,
    )

    return info_cube
