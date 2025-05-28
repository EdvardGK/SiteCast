"""Enhanced geometry creation with multiple marker shapes"""

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
    apex_point = file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))

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


def create_pyramid_geometry(file, context, base_size=0.2, height=0.5, inverted=True):
    """Create a pyramid geometry (square base)"""
    half_size = base_size / 2

    # Create base points (square)
    if inverted:
        # Base at top
        base_points = [
            file.create_entity(
                "IfcCartesianPoint", Coordinates=(-half_size, -half_size, height)
            ),
            file.create_entity(
                "IfcCartesianPoint", Coordinates=(half_size, -half_size, height)
            ),
            file.create_entity(
                "IfcCartesianPoint", Coordinates=(half_size, half_size, height)
            ),
            file.create_entity(
                "IfcCartesianPoint", Coordinates=(-half_size, half_size, height)
            ),
        ]
        apex = file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    else:
        # Base at bottom
        base_points = [
            file.create_entity(
                "IfcCartesianPoint", Coordinates=(-half_size, -half_size, 0.0)
            ),
            file.create_entity(
                "IfcCartesianPoint", Coordinates=(half_size, -half_size, 0.0)
            ),
            file.create_entity(
                "IfcCartesianPoint", Coordinates=(half_size, half_size, 0.0)
            ),
            file.create_entity(
                "IfcCartesianPoint", Coordinates=(-half_size, half_size, 0.0)
            ),
        ]
        apex = file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, height))

    # Create base face
    base_loop = file.create_entity("IfcPolyLoop", Polygon=base_points)
    base_face_bound = file.create_entity(
        "IfcFaceOuterBound", Bound=base_loop, Orientation=True
    )
    base_face = file.create_entity("IfcFace", Bounds=[base_face_bound])

    # Create triangular faces
    pyramid_faces = [base_face]
    for i in range(4):
        next_i = (i + 1) % 4
        tri_points = [apex, base_points[i], base_points[next_i]]
        tri_loop = file.create_entity("IfcPolyLoop", Polygon=tri_points)
        tri_face_bound = file.create_entity(
            "IfcFaceOuterBound", Bound=tri_loop, Orientation=True
        )
        tri_face = file.create_entity("IfcFace", Bounds=[tri_face_bound])
        pyramid_faces.append(tri_face)

    # Create closed shell
    shell = file.create_entity("IfcClosedShell", CfsFaces=pyramid_faces)
    brep = file.create_entity("IfcFacetedBrep", Outer=shell)

    return brep


def create_cylinder_marker_geometry(file, context, radius=0.1, height=0.5):
    """Create a cylinder geometry for markers"""
    # Create circular profile
    circle = file.create_entity(
        "IfcCircleProfileDef", ProfileType="AREA", Radius=radius
    )

    # Position for extrusion
    position = file.create_entity(
        "IfcAxis2Placement3D",
        Location=file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
    )

    # Extrude direction (upward)
    direction = file.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))

    # Create extruded solid
    cylinder = file.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=circle,
        Position=position,
        ExtrudedDirection=direction,
        Depth=height,
    )

    return cylinder


def create_sphere_marker_geometry(file, context, radius=0.1):
    """Create a sphere geometry for markers"""
    sphere = file.create_entity("IfcSphere", Radius=radius)
    return sphere


def create_pie_slice_geometry(
    file, context, radius=5.0, height=3.0, angle_degrees=18, start_angle_degrees=270
):
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


def create_hollow_cylinder_geometry(
    file, context, inner_radius=5.0, wall_thickness=0.5, height=3.0
):
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
    head_width = pie_radius * 0.4  # 40% of pie radius for more prominence
    head_height = pie_height * 1  # Same as pie height

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


def create_information_cube_geometry(file, context, size=2.0):
    """Create a cube geometry for information display"""
    half_size = size / 2

    # Create 8 vertices of the cube
    vertices = []
    for x in [-half_size, half_size]:
        for y in [-half_size, half_size]:
            for z in [-half_size, half_size]:
                vertices.append(
                    file.create_entity("IfcCartesianPoint", Coordinates=(x, y, z))
                )

    # Define faces (6 faces, each with 4 vertices)
    # Bottom, Top, Front, Back, Left, Right
    face_indices = [
        [0, 1, 3, 2],  # Bottom
        [4, 6, 7, 5],  # Top
        [0, 4, 5, 1],  # Front
        [2, 3, 7, 6],  # Back
        [0, 2, 6, 4],  # Left
        [1, 5, 7, 3],  # Right
    ]

    faces = []
    for indices in face_indices:
        face_points = [vertices[i] for i in indices]
        loop = file.create_entity("IfcPolyLoop", Polygon=face_points)
        face_bound = file.create_entity(
            "IfcFaceOuterBound", Bound=loop, Orientation=True
        )
        face = file.create_entity("IfcFace", Bounds=[face_bound])
        faces.append(face)

    # Create closed shell
    shell = file.create_entity("IfcClosedShell", CfsFaces=faces)
    brep = file.create_entity("IfcFacetedBrep", Outer=shell)

    return brep
