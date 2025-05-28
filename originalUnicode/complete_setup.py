"""
Script to create the remaining files for SiteCast
"""

from pathlib import Path


def write_file_utf8(path, content):
    """Write file with UTF-8 encoding"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def create_marker_preview(base_path):
    """Create marker_preview.py"""

    content = '''"""Marker preview functionality using matplotlib"""
import streamlit as st
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

def create_marker_preview(marker_type, color_rgb, height, diameter, inverted=True):
    """Create a 3D preview of the marker using matplotlib"""
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')
    
    # Set up the plot
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_box_aspect([1, 1, 1])
    
    # Create marker geometry based on type
    if marker_type == "Cone":
        vertices, faces = create_cone_mesh(height, diameter/2, inverted)
    elif marker_type == "Pyramid":
        vertices, faces = create_pyramid_mesh(height, diameter, inverted)
    elif marker_type == "Cylinder":
        vertices, faces = create_cylinder_mesh(height, diameter/2)
    elif marker_type == "Sphere":
        vertices, faces = create_sphere_mesh(diameter/2)
    else:
        vertices, faces = create_cone_mesh(height, diameter/2, inverted)
    
    # Create the 3D polygon collection
    poly = Poly3DCollection([vertices[face] for face in faces], 
                           facecolors=color_rgb, 
                           edgecolors='black',
                           linewidths=0.5,
                           alpha=0.8)
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
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    
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
            [0, 0, 0]  # Apex
        ]
    else:
        vertices = [
            [-half_size, -half_size, 0],
            [half_size, -half_size, 0],
            [half_size, half_size, 0],
            [-half_size, half_size, 0],
            [0, 0, height]  # Apex
        ]
    
    faces = [
        [0, 1, 2, 3],  # Base
        [0, 1, 4],     # Side faces
        [1, 2, 4],
        [2, 3, 4],
        [3, 0, 4]
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
'''

    path = base_path / "sitecast" / "ui" / "marker_preview.py"
    write_file_utf8(path, content)
    print(f"✅ Created: sitecast/ui/marker_preview.py")


def create_marker_configuration(base_path):
    """Create marker_configuration.py"""

    content = '''"""Marker configuration UI component"""
import streamlit as st
from ..config import MARKER_SHAPES, MARKER_COLORS, DEFAULT_MARKER_SETTINGS
from .marker_preview import create_marker_preview

def create_marker_configuration():
    """Create the marker configuration UI section"""
    st.subheader("🔻 Survey Marker Style")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Shape selection
        marker_shape = st.selectbox(
            "Marker Shape",
            options=MARKER_SHAPES,
            index=MARKER_SHAPES.index(st.session_state.get("marker_shape", DEFAULT_MARKER_SETTINGS["marker_shape"])),
            key="marker_shape"
        )
        
        # Color selection
        marker_color_name = st.selectbox(
            "Marker Color",
            options=list(MARKER_COLORS.keys()),
            index=list(MARKER_COLORS.keys()).index(
                st.session_state.get("marker_color", DEFAULT_MARKER_SETTINGS["marker_color"])
            ),
            key="marker_color"
        )
        
        # Dimension controls
        marker_height = st.slider(
            "Height (m)",
            min_value=0.1,
            max_value=2.0,
            value=st.session_state.get("marker_height", DEFAULT_MARKER_SETTINGS["marker_height"]),
            step=0.1,
            key="marker_height"
        )
        
        marker_diameter = st.slider(
            "Diameter/Width (m)",
            min_value=0.05,
            max_value=0.5,
            value=st.session_state.get("marker_diameter", DEFAULT_MARKER_SETTINGS["marker_diameter"]),
            step=0.05,
            key="marker_diameter"
        )
        
        # Orientation option
        if marker_shape in ["Cone", "Pyramid"]:
            use_inverted = st.checkbox(
                "Inverted (pointing down)",
                value=st.session_state.get("use_inverted", DEFAULT_MARKER_SETTINGS["use_inverted"]),
                key="use_inverted"
            )
        else:
            use_inverted = False
    
    with col2:
        # Live preview
        st.write("**Preview**")
        
        if st.session_state.get("show_preview", DEFAULT_MARKER_SETTINGS["show_preview"]):
            # Get color RGB
            color_rgb = MARKER_COLORS[marker_color_name]
            
            # Create and display preview
            try:
                fig = create_marker_preview(
                    marker_shape,
                    color_rgb,
                    marker_height,
                    marker_diameter,
                    use_inverted
                )
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)  # Clean up
            except Exception as e:
                st.error(f"Preview error: {str(e)}")
                st.info("Make sure matplotlib is installed: pip install matplotlib")
            
            # Preview info
            st.caption(f"Shape: {marker_shape}")
            st.caption(f"Color: {marker_color_name}")
            st.caption(f"Dimensions: {marker_height:.1f}m × {marker_diameter:.1f}m")
    
    return {
        "shape": marker_shape,
        "color": marker_color_name,
        "height": marker_height,
        "diameter": marker_diameter,
        "inverted": use_inverted
    }
'''

    path = base_path / "sitecast" / "ui" / "marker_configuration.py"
    write_file_utf8(path, content)
    print(f"✅ Created: sitecast/ui/marker_configuration.py")


def create_info_cube_configuration(base_path):
    """Create info_cube_configuration.py"""

    content = '''"""Information cube configuration UI"""
import streamlit as st
from ..config import INFO_CUBE_SETTINGS

def create_info_cube_configuration():
    """Create the information cube configuration UI"""
    st.subheader("📦 Information Cube")
    
    use_info_cube = st.checkbox(
        "Add Information Cube above Nullpunkt",
        value=st.session_state.get("use_info_cube", INFO_CUBE_SETTINGS["use_info_cube"]),
        key="use_info_cube",
        help="Adds a cube above the basepoint with project information"
    )
    
    if use_info_cube:
        col1, col2 = st.columns(2)
        
        with col1:
            cube_size = st.slider(
                "Cube Size (m)",
                min_value=1.0,
                max_value=5.0,
                value=st.session_state.get("cube_size", INFO_CUBE_SETTINGS["cube_size"]),
                step=0.5,
                key="cube_size"
            )
            
        with col2:
            cube_elevation = st.slider(
                "Elevation above ground (m)",
                min_value=5.0,
                max_value=20.0,
                value=st.session_state.get("cube_elevation", INFO_CUBE_SETTINGS["cube_elevation"]),
                step=1.0,
                key="cube_elevation"
            )
        
        # Link management
        st.write("**Information Links**")
        
        if "info_cube_links" not in st.session_state:
            st.session_state.info_cube_links = INFO_CUBE_SETTINGS["cube_links"].copy()
        
        # Display existing links
        links_to_remove = []
        for i, link in enumerate(st.session_state.info_cube_links):
            col1, col2, col3 = st.columns([2, 3, 1])
            with col1:
                link["name"] = st.text_input(
                    f"Name {i+1}",
                    value=link["name"],
                    key=f"link_name_{i}"
                )
            with col2:
                link["url"] = st.text_input(
                    f"URL {i+1}",
                    value=link["url"],
                    key=f"link_url_{i}"
                )
            with col3:
                if st.button("🗑️", key=f"remove_link_{i}"):
                    links_to_remove.append(i)
        
        # Remove marked links
        for i in reversed(links_to_remove):
            st.session_state.info_cube_links.pop(i)
            st.rerun()
        
        # Add new link
        with st.form("add_link_form", clear_on_submit=True):
            col1, col2, col3 = st.columns([2, 3, 1])
            with col1:
                new_name = st.text_input("Link Name")
            with col2:
                new_url = st.text_input("Link URL")
            with col3:
                submitted = st.form_submit_button("➕ Add")
            
            if submitted and new_name and new_url:
                st.session_state.info_cube_links.append({
                    "name": new_name,
                    "url": new_url
                })
                st.success(f"Added link: {new_name}")
                st.rerun()
    
    return {
        "enabled": use_info_cube,
        "size": st.session_state.get("cube_size", INFO_CUBE_SETTINGS["cube_size"]),
        "elevation": st.session_state.get("cube_elevation", INFO_CUBE_SETTINGS["cube_elevation"]),
        "links": st.session_state.get("info_cube_links", [])
    }
'''

    path = base_path / "sitecast" / "ui" / "info_cube_configuration.py"
    write_file_utf8(path, content)
    print(f"✅ Created: sitecast/ui/info_cube_configuration.py")


def create_info_cube(base_path):
    """Create info_cube.py"""

    content = '''"""Information cube creation for IFC"""
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
        "IfcProductDefinitionShape",
        Representations=[shape]
    )
    
    # Create local placement
    placement = file.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity("IfcCartesianPoint", Coordinates=(x, y, z_position)),
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
            Name=f"Link_{i+1}_{link['name'].replace(' ', '_')}",
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
'''

    path = base_path / "sitecast" / "ifc" / "info_cube.py"
    write_file_utf8(path, content)
    print(f"✅ Created: sitecast/ifc/info_cube.py")


def fix_marker_configuration_import(base_path):
    """Fix the matplotlib import in marker_configuration.py"""

    marker_config_path = base_path / "sitecast" / "ui" / "marker_configuration.py"
    if marker_config_path.exists():
        with open(marker_config_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Add matplotlib import
        if "import matplotlib.pyplot as plt" not in content:
            lines = content.split("\n")
            import_index = 0
            for i, line in enumerate(lines):
                if line.startswith("from .marker_preview"):
                    import_index = i + 1
                    break

            lines.insert(import_index, "import matplotlib.pyplot as plt")
            content = "\n".join(lines)

            with open(marker_config_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Fixed matplotlib import in marker_configuration.py")


def main():
    """Create all remaining files"""
    base_path = Path(r"C:\LokalMappe_Blade15\CodingProjects\SiteCast")

    print("🚀 Creating remaining SiteCast files...")
    print(f"📁 Base directory: {base_path}")

    # Create all files
    create_marker_preview(base_path)
    create_marker_configuration(base_path)
    create_info_cube_configuration(base_path)
    create_info_cube(base_path)
    fix_marker_configuration_import(base_path)

    print("\n✨ All files created successfully!")
    print("\n📝 Final steps:")
    print("1. Install matplotlib if not already installed:")
    print("   pip install matplotlib")
    print("2. Test the application:")
    print("   streamlit run main.py")
    print("\n✅ Your SiteCast is now fully updated with:")
    print("   - Live 3D marker preview")
    print("   - Multiple marker shapes and colors")
    print("   - Norwegian-style basepoints")
    print("   - Information cube support")
    print("   - Complete UI integration")


if __name__ == "__main__":
    main()
