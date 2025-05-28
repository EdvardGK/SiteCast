"""
Script to apply Norwegian-style enhancements to modularized SiteCast
"""

from pathlib import Path


def apply_enhancements(base_path):
    """Apply the Norwegian-style enhancements to SiteCast"""

    print("🔧 Applying Norwegian-style enhancements to SiteCast...")

    # 1. Update geometry.py with enhanced functions
    geometry_additions = '''
# Norwegian-style geometry additions
import math

def create_inverted_cone_geometry(file, context, radius=0.1, height=0.5):
    """Create an inverted cone geometry (pointing downward)"""
    # Create a faceted brep representation for the cone
    segments = 16  # Number of segments for the circle
    base_points = []
    
    # Create the base circle points (at height above the origin)
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        px = radius * math.cos(angle)
        py = radius * math.sin(angle)
        base_points.append(
            file.create_entity("IfcCartesianPoint", Coordinates=(px, py, height))
        )
    
    # Add the apex point (at the local origin - pointing down)
    apex_point = file.create_entity(
        "IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)
    )
    
    # Create a polyloop for the base circle
    base_loop = file.create_entity("IfcPolyLoop", Polygon=base_points)
    base_face = file.create_entity(
        "IfcFaceOuterBound", Bound=base_loop, Orientation=True
    )
    
    # Create the base face
    circle_face = file.create_entity("IfcFace", Bounds=[base_face])
    
    # Create faces for the conical surface
    cone_faces = []
    for i in range(segments):
        next_i = (i + 1) % segments
        # Create a triangular face from apex to two adjacent points on the base
        tri_points = [apex_point, base_points[i], base_points[next_i]]
        tri_loop = file.create_entity("IfcPolyLoop", Polygon=tri_points)
        tri_face_bound = file.create_entity(
            "IfcFaceOuterBound", Bound=tri_loop, Orientation=True
        )
        tri_face = file.create_entity("IfcFace", Bounds=[tri_face_bound])
        cone_faces.append(tri_face)
    
    # Combine all faces
    all_faces = [circle_face] + cone_faces
    
    # Create closed shell
    shell = file.create_entity("IfcClosedShell", CfsFaces=all_faces)
    
    # Create faceted brep
    brep = file.create_entity("IfcFacetedBrep", Outer=shell)
    
    return brep

def create_pie_slice_geometry(file, context, radius=5.0, height=3.0, angle_degrees=18, start_angle_degrees=270):
    """Create a pie slice (cylindrical sector) geometry"""
    # Convert angles to radians
    start_angle_rad = math.radians(start_angle_degrees)
    angle_span_rad = math.radians(angle_degrees)
    
    # Create pie slice geometry using faceted brep
    segments = max(8, int(angle_degrees))  # More segments for smoother curves
    
    # Create center point
    center = file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    center_top = file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, height))
    
    # Create arc points on bottom and top
    bottom_arc_points = [center]  # Start with center
    top_arc_points = [center_top]  # Start with center top
    
    for i in range(segments + 1):  # +1 to close the arc
        angle = start_angle_rad + (angle_span_rad * i / segments)
        x_arc = radius * math.cos(angle)
        y_arc = radius * math.sin(angle)
        
        bottom_point = file.create_entity(
            "IfcCartesianPoint", Coordinates=(x_arc, y_arc, 0.0)
        )
        top_point = file.create_entity(
            "IfcCartesianPoint", Coordinates=(x_arc, y_arc, height)
        )
        
        bottom_arc_points.append(bottom_point)
        top_arc_points.append(top_point)
    
    # Create bottom face (pie slice)
    bottom_loop = file.create_entity("IfcPolyLoop", Polygon=bottom_arc_points)
    bottom_face_bound = file.create_entity(
        "IfcFaceOuterBound", Bound=bottom_loop, Orientation=True
    )
    bottom_face = file.create_entity("IfcFace", Bounds=[bottom_face_bound])
    
    # Create top face (pie slice)
    top_arc_points_reversed = [top_arc_points[0]] + list(reversed(top_arc_points[1:]))
    top_loop = file.create_entity("IfcPolyLoop", Polygon=top_arc_points_reversed)
    top_face_bound = file.create_entity(
        "IfcFaceOuterBound", Bound=top_loop, Orientation=True
    )
    top_face = file.create_entity("IfcFace", Bounds=[top_face_bound])
    
    # Create curved face
    curved_faces = []
    for i in range(1, len(bottom_arc_points) - 1):
        quad_points = [
            bottom_arc_points[i],
            bottom_arc_points[i + 1],
            top_arc_points[i + 1],
            top_arc_points[i],
        ]
        quad_loop = file.create_entity("IfcPolyLoop", Polygon=quad_points)
        quad_face_bound = file.create_entity(
            "IfcFaceOuterBound", Bound=quad_loop, Orientation=True
        )
        quad_face = file.create_entity("IfcFace", Bounds=[quad_face_bound])
        curved_faces.append(quad_face)
    
    # Create the two flat side faces
    # First side face
    side1_points = [center, bottom_arc_points[1], top_arc_points[1], center_top]
    side1_loop = file.create_entity("IfcPolyLoop", Polygon=side1_points)
    side1_face_bound = file.create_entity(
        "IfcFaceOuterBound", Bound=side1_loop, Orientation=True
    )
    side1_face = file.create_entity("IfcFace", Bounds=[side1_face_bound])
    
    # Second side face
    side2_points = [center, center_top, top_arc_points[-1], bottom_arc_points[-1]]
    side2_loop = file.create_entity("IfcPolyLoop", Polygon=side2_points)
    side2_face_bound = file.create_entity(
        "IfcFaceOuterBound", Bound=side2_loop, Orientation=True
    )
    side2_face = file.create_entity("IfcFace", Bounds=[side2_face_bound])
    
    # Combine all faces
    all_faces = [bottom_face, top_face, side1_face, side2_face] + curved_faces
    
    # Create closed shell
    shell = file.create_entity("IfcClosedShell", CfsFaces=all_faces)
    
    # Create faceted brep
    brep = file.create_entity("IfcFacetedBrep", Outer=shell)
    
    return brep

def create_hollow_cylinder_geometry(file, context, inner_radius=5.0, wall_thickness=0.5, height=3.0):
    """Create a hollow cylinder geometry"""
    # Calculate outer radius
    outer_radius = inner_radius + wall_thickness
    
    # Create outer circle profile
    outer_circle = file.create_entity(
        "IfcCircle",
        Radius=outer_radius,
        Position=file.create_entity(
            "IfcAxis2Placement2D",
            Location=file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0)),
        ),
    )
    
    # Create inner circle profile (hole)
    inner_circle = file.create_entity(
        "IfcCircle",
        Radius=inner_radius,
        Position=file.create_entity(
            "IfcAxis2Placement2D",
            Location=file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0)),
        ),
    )
    
    # Create composite profile (outer circle with inner hole)
    profile = file.create_entity(
        "IfcArbitraryProfileDefWithVoids",
        ProfileType="AREA",
        OuterCurve=outer_circle,
        InnerCurves=[inner_circle],
    )
    
    # Position for extrusion
    position = file.create_entity(
        "IfcAxis2Placement3D",
        Location=file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
    )
    
    # Extrude direction (upward)
    direction = file.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    
    # Create extruded solid (hollow cylinder)
    solid = file.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile,
        Position=position,
        ExtrudedDirection=direction,
        Depth=height,
    )
    
    return solid

def create_north_arrow_geometry(file, context, pie_radius=5.0, pie_height=3.0):
    """Create a north arrow head geometry (triangular prism)"""
    # Arrow dimensions
    arrow_length = pie_radius * 0.8  # 80% of pie radius
    head_width = pie_radius * 0.4   # 40% of pie radius for more prominence
    head_height = pie_height * 1    # Same as pie height
    
    # Create arrowhead profile (triangle pointing north/Y-axis)
    head_profile_points = [
        file.create_entity(
            "IfcCartesianPoint", Coordinates=(-head_width / 2, 0.0)
        ),  # Left base corner
        file.create_entity(
            "IfcCartesianPoint", Coordinates=(head_width / 2, 0.0)
        ),  # Right base corner
        file.create_entity(
            "IfcCartesianPoint", Coordinates=(0.0, arrow_length)
        ),  # Point of arrow (north)
    ]
    
    # Create closed polyline for the triangle
    head_polyline = file.create_entity(
        "IfcPolyline", Points=head_profile_points + [head_profile_points[0]]
    )
    head_profile = file.create_entity(
        "IfcArbitraryClosedProfileDef", ProfileType="AREA", OuterCurve=head_polyline
    )
    
    # Position for extrusion
    head_position = file.create_entity(
        "IfcAxis2Placement3D",
        Location=file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
    )
    
    # Extrude direction (upward)
    head_direction = file.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    
    # Create extruded solid (triangular prism)
    head_solid = file.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=head_profile,
        Position=head_position,
        ExtrudedDirection=head_direction,
        Depth=head_height,
    )
    
    return head_solid
'''

    # 2. Update materials.py
    materials_additions = '''
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
'''

    # 3. Create backup and update files
    geometry_path = base_path / "sitecast" / "ifc" / "geometry.py"
    materials_path = base_path / "sitecast" / "ifc" / "materials.py"

    # Backup existing files
    if geometry_path.exists():
        backup_path = geometry_path.with_suffix(".py.bak")
        with open(geometry_path, "r", encoding="utf-8") as f:
            original_content = f.read()
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(original_content)
        print(f"✅ Backed up: {geometry_path.name} → {backup_path.name}")

    if materials_path.exists():
        backup_path = materials_path.with_suffix(".py.bak")
        with open(materials_path, "r", encoding="utf-8") as f:
            original_content = f.read()
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(original_content)
        print(f"✅ Backed up: {materials_path.name} → {materials_path.name}.bak")

    # Append new functions to existing files
    with open(geometry_path, "a", encoding="utf-8") as f:
        f.write("\n\n" + geometry_additions)
    print(f"✅ Enhanced: sitecast/ifc/geometry.py")

    with open(materials_path, "a", encoding="utf-8") as f:
        f.write("\n\n" + materials_additions)
    print(f"✅ Enhanced: sitecast/ifc/materials.py")

    # 4. Create enhanced components function
    enhanced_components = '''
def create_norwegian_basepoint(file, storey, context, name, n, e, z, materials, 
                             angle_degrees=18, start_angle_degrees=270,
                             add_cylinder=False, add_north_arrow=False):
    """Create a Norwegian-style basepoint with pie slice marker"""
    from .geometry import create_pie_slice_geometry, create_hollow_cylinder_geometry, create_north_arrow_geometry
    from .builder import create_guid
    
    # Create pie slice
    pie_slice_geom = create_pie_slice_geometry(
        file, context,
        radius=5.0,
        height=3.0,
        angle_degrees=angle_degrees,
        start_angle_degrees=start_angle_degrees
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
        "IfcProductDefinitionShape",
        Representations=[pie_shape]
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
        RelatingMaterial=materials['magenta'],
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
            file, context,
            inner_radius=5.0,
            wall_thickness=0.5,
            height=3.0
        )
        
        cylinder_shape = file.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=context,
            RepresentationIdentifier="Body",
            RepresentationType="SolidModel",
            Items=[cylinder_geom],
        )
        
        cylinder_product = file.create_entity(
            "IfcProductDefinitionShape",
            Representations=[cylinder_shape]
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
            RelatingMaterial=materials['teal'],
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
            "IfcProductDefinitionShape",
            Representations=[arrow_shape]
        )
        
        # Place arrow 5.5m north of basepoint
        arrow_placement = file.create_entity(
            "IfcLocalPlacement",
            RelativePlacement=file.create_entity(
                "IfcAxis2Placement3D",
                Location=file.create_entity("IfcCartesianPoint", Coordinates=(e, n + 5.5, z)),
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
            RelatingMaterial=materials['teal'],
        )
        
        file.create_entity(
            "IfcRelContainedInSpatialStructure",
            GlobalId=create_guid(),
            RelatingStructure=storey,
            RelatedElements=[arrow],
        )
        
        elements.append(arrow)
    
    return elements
'''

    # Add to components.py
    components_path = base_path / "sitecast" / "ui" / "components.py"
    with open(components_path, "a", encoding="utf-8") as f:
        f.write("\n\n" + enhanced_components)
    print(f"✅ Enhanced: sitecast/ui/components.py")

    print("\n✨ Norwegian enhancements applied successfully!")
    print("\n📝 Next steps:")
    print("1. Update your sidebar.py to add the new options")
    print("2. Update your export.py to use the enhanced features")
    print("3. Test with Norwegian-style basepoints!")

    print("\n⚠️  Note: You'll need to manually update:")
    print("   - sidebar.py: Add Norwegian basepoint options")
    print("   - export.py: Use red materials and new geometry")
    print(
        "   - components.py: Update create_enhanced_survey_point to use inverted cones"
    )


def main():
    """Apply Norwegian enhancements to SiteCast"""
    base_path = Path(r"C:\LokalMappe_Blade15\CodingProjects\SiteCast")

    print("🇳🇴 Applying Norwegian-style enhancements to SiteCast...")
    print(f"📁 Base directory: {base_path}")

    apply_enhancements(base_path)


if __name__ == "__main__":
    main()
