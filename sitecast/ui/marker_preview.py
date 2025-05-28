"""Marker preview functionality using matplotlib"""

import streamlit as st
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np


def create_marker_preview(marker_type, color_rgb, height, diameter, inverted=True):
    """Create a 3D preview of the marker using matplotlib"""
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection="3d")

    # Set up the plot
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_box_aspect([1, 1, 1])

    # Create marker geometry based on type
    if marker_type == "Cone":
        vertices, faces = create_cone_mesh(height, diameter / 2, inverted)
    elif marker_type == "Pyramid":
        vertices, faces = create_pyramid_mesh(height, diameter, inverted)
    elif marker_type == "Cylinder":
        vertices, faces = create_cylinder_mesh(height, diameter / 2)
    elif marker_type == "Sphere":
        vertices, faces = create_sphere_mesh(diameter / 2)
    elif marker_type == "Pie Slice":
        vertices, faces = create_pie_slice_mesh(height, diameter / 2)
    elif marker_type == "Hollow Cylinder":
        vertices, faces = create_hollow_cylinder_mesh(height, diameter / 2, diameter * 0.1)
    elif marker_type == "North Arrow":
        vertices, faces = create_north_arrow_mesh(height, diameter)
    else:
        vertices, faces = create_cone_mesh(height, diameter / 2, inverted)

    # Create the 3D polygon collection
    poly = Poly3DCollection(
        [vertices[face] for face in faces],
        facecolors=color_rgb,
        edgecolors="black",
        linewidths=0.5,
        alpha=0.8,
    )
    ax.add_collection3d(poly)

    # Set the view limits
    max_dim = max(height, diameter) * 0.6
    ax.set_xlim([-max_dim, max_dim])
    ax.set_ylim([-max_dim, max_dim])
    ax.set_zlim([0, height * 1.2])

    # Set viewing angle
    ax.view_init(elev=20, azim=45)

    # Remove background
    ax.grid(True, alpha=0.3)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    return fig


def create_cone_mesh(height, radius, inverted=True):
    """Create mesh data for a cone"""
    n_segments = 16
    vertices = []
    faces = []

    # Create base circle vertices
    for i in range(n_segments):
        angle = 2 * np.pi * i / n_segments
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        if inverted:
            vertices.append([x, y, height])
        else:
            vertices.append([x, y, 0])

    # Add apex
    if inverted:
        vertices.append([0, 0, 0])  # Apex at bottom
    else:
        vertices.append([0, 0, height])  # Apex at top

    apex_idx = len(vertices) - 1

    # Create faces
    for i in range(n_segments):
        next_i = (i + 1) % n_segments
        faces.append([i, next_i, apex_idx])

    # Add base face
    faces.append(list(range(n_segments)))

    return np.array(vertices), faces


def create_pyramid_mesh(height, base_size, inverted=True):
    """Create mesh data for a pyramid"""
    half_size = base_size / 2
    vertices = []

    # Base vertices
    if inverted:
        vertices = [
            [-half_size, -half_size, height],
            [half_size, -half_size, height],
            [half_size, half_size, height],
            [-half_size, half_size, height],
            [0, 0, 0],  # Apex
        ]
    else:
        vertices = [
            [-half_size, -half_size, 0],
            [half_size, -half_size, 0],
            [half_size, half_size, 0],
            [-half_size, half_size, 0],
            [0, 0, height],  # Apex
        ]

    faces = [
        [0, 1, 2, 3],  # Base
        [0, 1, 4],  # Side faces
        [1, 2, 4],
        [2, 3, 4],
        [3, 0, 4],
    ]

    return np.array(vertices), faces


def create_cylinder_mesh(height, radius):
    """Create mesh data for a cylinder"""
    n_segments = 16
    vertices = []
    faces = []

    # Create circles for top and bottom
    for z in [0, height]:
        for i in range(n_segments):
            angle = 2 * np.pi * i / n_segments
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            vertices.append([x, y, z])

    # Create side faces
    for i in range(n_segments):
        next_i = (i + 1) % n_segments
        # Bottom triangle
        faces.append([i, next_i, i + n_segments])
        # Top triangle
        faces.append([next_i, next_i + n_segments, i + n_segments])

    # Add top and bottom faces
    faces.append(list(range(n_segments)))  # Bottom
    faces.append(list(range(n_segments, 2 * n_segments)))  # Top

    return np.array(vertices), faces


def create_sphere_mesh(radius):
    """Create mesh data for a sphere"""
    # Use a UV sphere approximation
    n_lat = 8
    n_lon = 16
    vertices = []
    faces = []

    # Generate vertices
    for i in range(n_lat + 1):
        lat = np.pi * i / n_lat
        for j in range(n_lon):
            lon = 2 * np.pi * j / n_lon
            x = radius * np.sin(lat) * np.cos(lon)
            y = radius * np.sin(lat) * np.sin(lon)
            z = radius * np.cos(lat)
            vertices.append([x, y, z])

    # Generate faces
    for i in range(n_lat):
        for j in range(n_lon):
            next_j = (j + 1) % n_lon
            # Current row
            v1 = i * n_lon + j
            v2 = i * n_lon + next_j
            # Next row
            v3 = (i + 1) * n_lon + j
            v4 = (i + 1) * n_lon + next_j

            if i > 0:  # Skip degenerate triangles at pole
                faces.append([v1, v2, v3])
            if i < n_lat - 1:  # Skip degenerate triangles at pole
                faces.append([v2, v4, v3])

    return np.array(vertices), faces


def create_pie_slice_mesh(height, radius, angle_degrees=18, start_angle_degrees=270):
    """Create mesh data for a pie slice (cylindrical sector)"""
    vertices = []
    faces = []
    
    # Convert angles to radians
    start_angle = np.radians(start_angle_degrees)
    angle = np.radians(angle_degrees)
    
    # Number of segments for the arc
    n_segments = max(4, int(angle_degrees / 10))
    
    # Create vertices for bottom and top
    for z in [0, height]:
        # Center point
        vertices.append([0, 0, z])
        # Arc points
        for i in range(n_segments + 1):
            a = start_angle + (angle * i / n_segments)
            x = radius * np.cos(a)
            y = radius * np.sin(a)
            vertices.append([x, y, z])
    
    # Bottom center index = 0, top center index = n_segments + 2
    top_offset = n_segments + 2
    
    # Create bottom face
    bottom_face = [0] + list(range(1, n_segments + 2))
    faces.append(bottom_face)
    
    # Create top face
    top_face = [top_offset] + list(range(top_offset + 1, top_offset + n_segments + 2))
    faces.append(top_face[::-1])  # Reverse for correct normal
    
    # Create side faces
    # Curved surface
    for i in range(n_segments):
        v1 = i + 1
        v2 = i + 2
        v3 = v1 + top_offset
        v4 = v2 + top_offset
        faces.append([v1, v2, v4, v3])
    
    # First radial face
    faces.append([0, 1, top_offset + 1, top_offset])
    
    # Second radial face
    faces.append([0, top_offset, top_offset + n_segments + 1, n_segments + 1])
    
    return np.array(vertices), faces


def create_hollow_cylinder_mesh(height, inner_radius, wall_thickness):
    """Create mesh data for a hollow cylinder"""
    outer_radius = inner_radius + wall_thickness
    n_segments = 16
    vertices = []
    faces = []
    
    # Create circles for inner and outer, bottom and top
    for z in [0, height]:
        for radius in [inner_radius, outer_radius]:
            for i in range(n_segments):
                angle = 2 * np.pi * i / n_segments
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                vertices.append([x, y, z])
    
    # Vertex indices:
    # 0-15: bottom inner circle
    # 16-31: bottom outer circle
    # 32-47: top inner circle
    # 48-63: top outer circle
    
    # Create faces
    for i in range(n_segments):
        next_i = (i + 1) % n_segments
        
        # Outer surface
        faces.append([16 + i, 16 + next_i, 48 + next_i, 48 + i])
        
        # Inner surface
        faces.append([i, 32 + i, 32 + next_i, next_i])
        
        # Bottom ring
        faces.append([i, next_i, 16 + next_i, 16 + i])
        
        # Top ring
        faces.append([32 + i, 32 + next_i, 48 + next_i, 48 + i])
    
    return np.array(vertices), faces


def create_north_arrow_mesh(height, width):
    """Create mesh data for a north arrow (triangular prism)"""
    vertices = []
    
    # Arrow dimensions
    arrow_length = width * 0.8
    head_width = width * 0.4
    
    # Bottom triangle
    vertices.extend([
        [-head_width/2, 0, 0],
        [head_width/2, 0, 0],
        [0, arrow_length, 0]
    ])
    
    # Top triangle
    vertices.extend([
        [-head_width/2, 0, height],
        [head_width/2, 0, height],
        [0, arrow_length, height]
    ])
    
    faces = [
        [0, 1, 2],      # Bottom triangle
        [3, 5, 4],      # Top triangle (reversed)
        [0, 3, 4, 1],   # Side face 1
        [1, 4, 5, 2],   # Side face 2
        [2, 5, 3, 0],   # Side face 3
    ]
    
    return np.array(vertices), faces
