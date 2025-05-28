"""Reusable UI components"""

import streamlit as st
from ..ifc.builder import create_guid
from ..ifc.geometry import create_cone_geometry, create_sphere_geometry
from ..ifc.properties import create_enhanced_property_set


# Note: The updated create_enhanced_survey_point function is defined below (line 358+)


def create_coordination_object(
    file, storey, context, name, n, e, z, material, description="Coordination Point"
):
    """Create a coordination object (small sphere) at specified coordinates"""
    # Create sphere geometry
    sphere = create_sphere_geometry(file, radius=0.1)

    # Create shape representation
    shape_representation = file.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Body",
        RepresentationType="CSG",
        Items=[sphere],
    )

    # Create product definition shape
    product_shape = file.create_entity(
        "IfcProductDefinitionShape", Representations=[shape_representation]
    )

    # Create local placement
    local_placement = file.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity("IfcCartesianPoint", Coordinates=(e, n, z)),
        ),
    )

    # Create building element proxy
    coord_object = file.create_entity(
        "IfcBuildingElementProxy",
        GlobalId=create_guid(),
        Name=name,
        Description=description,
        ObjectPlacement=local_placement,
        Representation=product_shape,
    )

    # Create containment relationship
    file.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=create_guid(),
        RelatingStructure=storey,
        RelatedElements=[coord_object],
    )

    # Create custom properties
    properties = []
    prop_type = file.create_entity(
        "IfcPropertySingleValue",
        Name="Object Type",
        NominalValue=file.create_entity("IfcText", "Coordination Object"),
    )
    properties.append(prop_type)

    prop_coords = file.create_entity(
        "IfcPropertySingleValue",
        Name="Coordinates",
        NominalValue=file.create_entity("IfcText", f"N:{n:.3f}, E:{e:.3f}, Z:{z:.3f}"),
    )
    properties.append(prop_coords)

    property_set = file.create_entity(
        "IfcPropertySet",
        GlobalId=create_guid(),
        Name="Coordination_Properties",
        HasProperties=properties,
    )
    file.create_entity(
        "IfcRelDefinesByProperties",
        GlobalId=create_guid(),
        RelatedObjects=[coord_object],
        RelatingPropertyDefinition=property_set,
    )

    return coord_object


def create_norwegian_basepoint(
    file,
    storey,
    context,
    name,
    n,
    e,
    z,
    materials,
    angle_degrees=18,
    start_angle_degrees=270,
    add_cylinder=False,
    add_north_arrow=False,
):
    """Create a Norwegian-style basepoint with pie slice marker"""
    from ..ifc.geometry import (
        create_pie_slice_geometry,
        create_hollow_cylinder_geometry,
        create_north_arrow_geometry,
    )

    # Create pie slice
    pie_slice_geom = create_pie_slice_geometry(
        file,
        context,
        radius=5.0,
        height=3.0,
        angle_degrees=angle_degrees,
        start_angle_degrees=start_angle_degrees,
    )

    # Create shape representation for pie slice
    pie_shape = file.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Body",
        RepresentationType="Brep",
        Items=[pie_slice_geom],
    )

    # Create product definition shape
    pie_product_shape = file.create_entity(
        "IfcProductDefinitionShape", Representations=[pie_shape]
    )

    # Create local placement
    pie_placement = file.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity("IfcCartesianPoint", Coordinates=(e, n, z)),
        ),
    )

    # Create annotation for pie slice
    pie_slice = file.create_entity(
        "IfcAnnotation",
        GlobalId=create_guid(),
        Name=name,
        Description=f'Norwegian basepoint marker "{name}"',
        ObjectType="Referansepunkt",
        ObjectPlacement=pie_placement,
        Representation=pie_product_shape,
    )

    # Assign material
    file.create_entity(
        "IfcRelAssociatesMaterial",
        GlobalId=create_guid(),
        RelatedObjects=[pie_slice],
        RelatingMaterial=materials["magenta"],
    )

    # Add to storey
    file.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=create_guid(),
        RelatingStructure=storey,
        RelatedElements=[pie_slice],
    )

    elements = [pie_slice]

    # Optionally add hollow cylinder
    if add_cylinder:
        cylinder_geom = create_hollow_cylinder_geometry(
            file, context, inner_radius=5.0, wall_thickness=0.5, height=3.0
        )

        cylinder_shape = file.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=context,
            RepresentationIdentifier="Body",
            RepresentationType="SolidModel",
            Items=[cylinder_geom],
        )

        cylinder_product = file.create_entity(
            "IfcProductDefinitionShape", Representations=[cylinder_shape]
        )

        cylinder = file.create_entity(
            "IfcAnnotation",
            GlobalId=create_guid(),
            Name=f"{name}_Cylinder",
            Description="Reference cylinder",
            ObjectType="Reference Cylinder",
            ObjectPlacement=pie_placement,
            Representation=cylinder_product,
        )

        file.create_entity(
            "IfcRelAssociatesMaterial",
            GlobalId=create_guid(),
            RelatedObjects=[cylinder],
            RelatingMaterial=materials["teal"],
        )

        file.create_entity(
            "IfcRelContainedInSpatialStructure",
            GlobalId=create_guid(),
            RelatingStructure=storey,
            RelatedElements=[cylinder],
        )

        elements.append(cylinder)

    # Optionally add north arrow
    if add_north_arrow:
        arrow_geom = create_north_arrow_geometry(file, context)

        arrow_shape = file.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=context,
            RepresentationIdentifier="Body",
            RepresentationType="SolidModel",
            Items=[arrow_geom],
        )

        arrow_product = file.create_entity(
            "IfcProductDefinitionShape", Representations=[arrow_shape]
        )

        # Place arrow 5.5m north of basepoint
        arrow_placement = file.create_entity(
            "IfcLocalPlacement",
            RelativePlacement=file.create_entity(
                "IfcAxis2Placement3D",
                Location=file.create_entity(
                    "IfcCartesianPoint", Coordinates=(e, n + 5.5, z)
                ),
            ),
        )

        arrow = file.create_entity(
            "IfcAnnotation",
            GlobalId=create_guid(),
            Name="North_Arrow",
            Description="North direction indicator",
            ObjectType="North Arrow",
            ObjectPlacement=arrow_placement,
            Representation=arrow_product,
        )

        file.create_entity(
            "IfcRelAssociatesMaterial",
            GlobalId=create_guid(),
            RelatedObjects=[arrow],
            RelatingMaterial=materials["teal"],
        )

        file.create_entity(
            "IfcRelContainedInSpatialStructure",
            GlobalId=create_guid(),
            RelatingStructure=storey,
            RelatedElements=[arrow],
        )

        elements.append(arrow)

    return elements


# Enhanced survey point function with all shape support
def create_enhanced_survey_point(
    file,
    storey,
    context,
    point_data,
    material,
    original_coords,
    local_coords,
    offsets,
    pset_name,
    custom_properties,
    source_filename,
    creator_name="SiteCast",
    external_link="",
    marker_shape="Cone",
    marker_height=0.5,
    marker_diameter=0.2,
    use_inverted=True,
):
    """Create a survey point element with enhanced property sets and configurable marker"""
    from ..ifc.geometry_enhanced import (
        create_inverted_cone_geometry,
        create_pyramid_geometry,
        create_cylinder_marker_geometry,
        create_sphere_marker_geometry,
    )

    point_id = point_data.get("ID", "Unknown")
    n = float(point_data.get("N", 0))
    e = float(point_data.get("E", 0))
    z = float(point_data.get("Z", 0))
    description = point_data.get("Description", "")

    # Create geometry based on marker type
    if marker_shape == "Cone":
        if use_inverted:
            geometry = create_inverted_cone_geometry(
                file, context, radius=marker_diameter / 2, height=marker_height
            )
        else:
            from ..ifc.geometry import create_cone_geometry

            geometry = create_cone_geometry(
                file, context, radius=marker_diameter / 2, height=marker_height
            )
    elif marker_shape == "Pyramid":
        geometry = create_pyramid_geometry(
            file,
            context,
            base_size=marker_diameter,
            height=marker_height,
            inverted=use_inverted,
        )
    elif marker_shape == "Cylinder":
        geometry = create_cylinder_marker_geometry(
            file, context, radius=marker_diameter / 2, height=marker_height
        )
    elif marker_shape == "Sphere":
        geometry = create_sphere_marker_geometry(
            file, context, radius=marker_diameter / 2
        )
    elif marker_shape == "Pie Slice":
        from ..ifc.geometry_enhanced import create_pie_slice_geometry
        geometry = create_pie_slice_geometry(
            file,
            context,
            radius=marker_diameter / 2,
            height=marker_height,
            angle_degrees=18,
            start_angle_degrees=270,
        )
    elif marker_shape == "Hollow Cylinder":
        from ..ifc.geometry_enhanced import create_hollow_cylinder_geometry
        geometry = create_hollow_cylinder_geometry(
            file,
            context,
            inner_radius=marker_diameter / 2,
            wall_thickness=marker_diameter * 0.1,
            height=marker_height,
        )
    elif marker_shape == "North Arrow":
        from ..ifc.geometry_enhanced import create_north_arrow_geometry
        geometry = create_north_arrow_geometry(
            file, context, pie_radius=marker_diameter, pie_height=marker_height
        )
    else:
        # Default to cone
        geometry = create_inverted_cone_geometry(
            file, context, radius=marker_diameter / 2, height=marker_height
        )

    # Create shape representation
    shape_representation = file.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Body",
        RepresentationType="Brep" if marker_shape not in ["Cylinder", "Hollow Cylinder"] else "SweptSolid",
        Items=[geometry],
    )

    # Create product definition shape
    product_shape = file.create_entity(
        "IfcProductDefinitionShape", Representations=[shape_representation]
    )

    # Create local placement
    local_placement = file.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity("IfcCartesianPoint", Coordinates=(e, n, z)),
        ),
    )

    # Create annotation element
    survey_point = file.create_entity(
        "IfcAnnotation",
        GlobalId=create_guid(),
        Name=f"{point_id}",
        Description=f'Fastmerke "{point_id}" - {description}'
        if description
        else f'Fastmerke "{point_id}"',
        ObjectType="Fastmerke",
        ObjectPlacement=local_placement,
        Representation=product_shape,
    )

    # Assign material to survey point
    file.create_entity(
        "IfcRelAssociatesMaterial",
        GlobalId=create_guid(),
        RelatedObjects=[survey_point],
        RelatingMaterial=material,
    )

    # Create containment relationship
    file.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=create_guid(),
        RelatingStructure=storey,
        RelatedElements=[survey_point],
    )

    # Create enhanced property set
    create_enhanced_property_set(
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
    )

    return survey_point
