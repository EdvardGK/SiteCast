"""Property set creation functions"""

from .builder import create_guid


def create_enhanced_property_set(
    file,
    survey_point,
    point_data,
    pset_name,
    custom_properties,
    original_coords,
    local_coords,
    offsets,
    source_filename,
    creator_name,
    external_link,
):
    """Create enhanced property set with coordinates and custom properties"""
    properties = []

    # Source information
    prop_source = file.create_entity(
        "IfcPropertySingleValue",
        Name="Source",
        NominalValue=file.create_entity("IfcText", source_filename),
    )
    properties.append(prop_source)

    prop_creator = file.create_entity(
        "IfcPropertySingleValue",
        Name="Created_By",
        NominalValue=file.create_entity("IfcText", creator_name),
    )
    properties.append(prop_creator)

    # Point ID
    prop_point_id = file.create_entity(
        "IfcPropertySingleValue",
        Name="Point_ID",
        NominalValue=file.create_entity(
            "IfcText", str(point_data.get("ID", "Unknown"))
        ),
    )
    properties.append(prop_point_id)

    # Original coordinates
    prop_northing = file.create_entity(
        "IfcPropertySingleValue",
        Name="Northing_Y",
        NominalValue=file.create_entity("IfcReal", float(original_coords["N"])),
        Unit=file.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE"),
    )
    properties.append(prop_northing)

    prop_easting = file.create_entity(
        "IfcPropertySingleValue",
        Name="Easting_X",
        NominalValue=file.create_entity("IfcReal", float(original_coords["E"])),
        Unit=file.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE"),
    )
    properties.append(prop_easting)

    prop_altitude = file.create_entity(
        "IfcPropertySingleValue",
        Name="Altitude_Z",
        NominalValue=file.create_entity("IfcReal", float(original_coords["Z"])),
        Unit=file.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE"),
    )
    properties.append(prop_altitude)

    # Offsets
    prop_offsets = file.create_entity(
        "IfcPropertySingleValue",
        Name="Offsets",
        NominalValue=file.create_entity(
            "IfcText",
            f"[N:{offsets['N']:.3f}, E:{offsets['E']:.3f}, Z:{offsets['Z']:.3f}]",
        ),
    )
    properties.append(prop_offsets)

    # Local coordinates
    prop_local_coords = file.create_entity(
        "IfcPropertySingleValue",
        Name="Local_Coordinates",
        NominalValue=file.create_entity(
            "IfcText",
            f"[N:{local_coords['N']:.3f}, E:{local_coords['E']:.3f}, Z:{local_coords['Z']:.3f}]",
        ),
    )
    properties.append(prop_local_coords)

    # Add custom properties
    for custom_prop in custom_properties:
        if custom_prop["name"] and custom_prop["value"]:
            prop_custom = file.create_entity(
                "IfcPropertySingleValue",
                Name=custom_prop["name"].replace(" ", "_"),
                NominalValue=file.create_entity("IfcText", str(custom_prop["value"])),
            )
            properties.append(prop_custom)

    # External link if provided
    if external_link:
        prop_link = file.create_entity(
            "IfcPropertySingleValue",
            Name="External_Link",
            NominalValue=file.create_entity("IfcText", external_link),
        )
        properties.append(prop_link)

    # Create the property set
    property_set = file.create_entity(
        "IfcPropertySet",
        GlobalId=create_guid(),
        Name=pset_name,
        HasProperties=properties,
    )

    # Attach to survey point
    file.create_entity(
        "IfcRelDefinesByProperties",
        GlobalId=create_guid(),
        RelatedObjects=[survey_point],
        RelatingPropertyDefinition=property_set,
    )

    return property_set
