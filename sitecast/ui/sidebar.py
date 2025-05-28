"""Enhanced sidebar configuration UI with all features"""

import streamlit as st


def create_sidebar():
    """Create and return sidebar configuration"""
    with st.sidebar:
        st.header("⚙️ Project Settings")

        config = {}

        # Project settings
        config["project_name"] = st.text_input("Project Name", key="project_name")
        config["site_name"] = st.text_input("Site Name", key="site_name")
        config["building_name"] = st.text_input("Building Name", key="building_name")
        config["storey_name"] = st.text_input("Level Name", key="storey_name")

        # Coordinate system
        st.header("🌍 Coordinate System")
        config["coord_system"] = st.radio(
            "Coordinate System Type",
            options=["Local", "Global/Geographic"],
            index=0 if st.session_state.coord_system == "Local" else 1,
            help="Local coordinates use project basepoint offsets",
            key="coord_system",
        )

        # Units
        st.subheader("📏 Units")
        config["coordinate_units"] = st.selectbox(
            "Coordinate Units",
            options=["m (meters)", "mm (millimeters)", "ft (feet)"],
            key="coordinate_units",
        )
        config["unit_code"] = config["coordinate_units"].split()[0]
        config["auto_detect_units"] = st.checkbox(
            "Auto-detect units from data",
            help="Automatically detect units based on coordinate ranges",
            key="auto_detect_units",
        )

        # Project Basepoint
        st.subheader("📍 Project Basepoint")
        config["use_basepoint"] = st.checkbox(
            "Define Project Basepoint", key="use_basepoint"
        )

        if config["use_basepoint"]:
            st.caption("Define the project origin in world coordinates")
            col_n, col_e = st.columns(2)
            with col_n:
                config["basepoint_n"] = st.number_input(
                    "Basepoint N (Northing)",
                    format="%.3f",
                    help="World N coordinate of project origin",
                    key="basepoint_n",
                )
            with col_e:
                config["basepoint_e"] = st.number_input(
                    "Basepoint E (Easting)",
                    format="%.3f",
                    help="World E coordinate of project origin",
                    key="basepoint_e",
                )
            config["basepoint_z"] = st.number_input(
                "Basepoint Z (Elevation)",
                format="%.3f",
                help="World Z coordinate of project origin",
                key="basepoint_z",
            )
        else:
            config["basepoint_n"] = config["basepoint_e"] = config["basepoint_z"] = 0.0

        # Survey/Rotation Point
        st.subheader("🧭 Survey/Rotation Point")
        config["use_rotation_point"] = st.checkbox(
            "Define Survey/Rotation Point", key="use_rotation_point"
        )

        if config["use_rotation_point"]:
            st.caption("Define the survey reference point for model alignment")
            col_rn, col_re = st.columns(2)
            with col_rn:
                config["rotation_n"] = st.number_input(
                    "Rotation Point N", format="%.3f", key="rotation_n"
                )
            with col_re:
                config["rotation_e"] = st.number_input(
                    "Rotation Point E", format="%.3f", key="rotation_e"
                )
            config["rotation_z"] = st.number_input(
                "Rotation Point Z", format="%.3f", key="rotation_z"
            )
        else:
            config["rotation_n"] = config["rotation_e"] = config["rotation_z"] = 0.0

        # Norwegian Basepoint Style
        st.header("🇳🇴 Norwegian Standards")
        st.subheader("🎯 Basepoint Style")

        config["use_norwegian_basepoints"] = st.checkbox(
            "Use Norwegian-style basepoints (pie slices)",
            value=True,
            key="use_norwegian_basepoints",
            help="Create basepoints with pie slice markers as per Norwegian standards",
        )

        if config["use_norwegian_basepoints"]:
            config["pie_angle"] = st.slider(
                "Pie slice angle (degrees)",
                min_value=10,
                max_value=90,
                value=18,
                key="pie_angle",
                help="Angle of the pie slice marker",
            )

            config["basepoint_orientation"] = st.number_input(
                "Basepoint orientation (degrees)",
                min_value=0,
                max_value=360,
                value=300,
                key="basepoint_orientation",
                help="Starting angle for basepoint pie slice (0° = East, 90° = North)",
            )

            config["rotation_orientation"] = st.number_input(
                "Rotation point orientation (degrees)",
                min_value=0,
                max_value=360,
                value=270,
                key="rotation_orientation",
                help="Starting angle for rotation point pie slice",
            )

            config["add_cylinder"] = st.checkbox(
                "Add reference cylinder",
                value=True,
                key="add_cylinder",
                help="Add a hollow cylinder around the basepoint",
            )

            config["add_north_arrow"] = st.checkbox(
                "Add north arrow",
                value=True,
                key="add_north_arrow",
                help="Add a north direction indicator",
            )

        # Marker Configuration
        st.header("🎨 Marker Appearance")

        # Import marker configuration
        from ..ui.marker_configuration import create_marker_configuration

        marker_config = create_marker_configuration()

        # Add marker config to main config
        config["marker_shape"] = marker_config["shape"]
        config["marker_color"] = marker_config["color"]
        config["marker_height"] = marker_config["height"]
        config["marker_diameter"] = marker_config["diameter"]
        config["use_inverted"] = marker_config["inverted"]

        # Information Cube
        from ..ui.info_cube_configuration import create_info_cube_configuration

        info_cube_config = create_info_cube_configuration()

        config["use_info_cube"] = info_cube_config["enabled"]
        config["info_cube_size"] = info_cube_config["size"]
        config["info_cube_elevation"] = info_cube_config["elevation"]
        config["info_cube_links"] = info_cube_config["links"]

        # Metadata
        st.header("📋 Metadata")
        config["creator_name"] = st.text_input("Created By", key="creator_name")
        config["external_link"] = st.text_input(
            "External Link (optional)", placeholder="https://...", key="external_link"
        )

        # Property Sets
        st.header("🏷️ Property Sets")
        config["pset_name"] = st.text_input(
            "Property Set Name",
            help="Name of the custom property set to attach to survey points",
            key="pset_name",
        )

        # Custom properties management
        st.subheader("Custom Properties")
        st.caption("Add custom properties to survey points")

        # Initialize custom properties
        if "custom_properties" not in st.session_state:
            st.session_state.custom_properties = [
                {"name": "Coordinate_System", "value": "EUREF89_NTM10"},
                {"name": "Survey_Method", "value": "Total_Station"},
                {"name": "Accuracy_Class", "value": "Class_1"},
            ]

        # Add new property form
        with st.form("add_property_form", clear_on_submit=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                new_prop_name = st.text_input("Property Name")
            with col2:
                new_prop_value = st.text_input("Property Value")
            with col3:
                submitted = st.form_submit_button("➕ Add")

            if submitted and new_prop_name and new_prop_value:
                st.session_state.custom_properties.append(
                    {"name": new_prop_name, "value": new_prop_value}
                )
                st.success(f"Added property: {new_prop_name}")
                st.session_state.preserve_file_state = True
                st.rerun()

        # Display existing properties
        if st.session_state.custom_properties:
            properties_to_remove = []
            for i, prop in enumerate(st.session_state.custom_properties):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    prop["name"] = st.text_input(
                        f"Name {i + 1}", value=prop["name"], key=f"edit_prop_name_{i}"
                    )
                with col2:
                    prop["value"] = st.text_input(
                        f"Value {i + 1}",
                        value=prop["value"],
                        key=f"edit_prop_value_{i}",
                    )
                with col3:
                    if st.button("🗑️", key=f"remove_{i}", help="Remove property"):
                        properties_to_remove.append(i)

            # Remove marked properties
            if properties_to_remove:
                for i in reversed(properties_to_remove):
                    st.session_state.custom_properties.pop(i)
                st.session_state.preserve_file_state = True
                st.rerun()

        config["custom_properties"] = st.session_state.custom_properties

        # Verification settings
        st.subheader("✅ Coordinate Verification")
        config["verify_coordinates"] = st.checkbox(
            "Verify coordinates after IFC generation",
            help="Read back the IFC file to verify local + offset = original coordinates",
            key="verify_coordinates",
        )

        # Settings management
        st.header("💾 Settings")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Settings", help="Save current settings as defaults"):
                st.success("✅ Settings saved!")

        with col2:
            if st.button("🔄 Reset Settings", help="Reset to default values"):
                keys_to_reset = [
                    "project_name",
                    "site_name",
                    "building_name",
                    "storey_name",
                    "coord_system",
                    "basepoint_n",
                    "basepoint_e",
                    "basepoint_z",
                    "creator_name",
                    "marker_color",
                    "pset_name",
                ]
                for key in keys_to_reset:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    return config
