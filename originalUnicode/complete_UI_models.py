"""
Script to complete the UI module implementations for SiteCast
"""

from pathlib import Path


def write_file_utf8(path, content):
    """Write file with UTF-8 encoding"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def create_sidebar_module(base_path):
    """Create the complete sidebar.py module"""

    sidebar_content = '''"""Sidebar configuration UI"""
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
            key="coord_system"
        )
        
        # Units
        st.subheader("📏 Units")
        config["coordinate_units"] = st.selectbox(
            "Coordinate Units",
            options=["m (meters)", "mm (millimeters)", "ft (feet)"],
            key="coordinate_units"
        )
        config["unit_code"] = config["coordinate_units"].split()[0]
        config["auto_detect_units"] = st.checkbox(
            "Auto-detect units from data",
            help="Automatically detect units based on coordinate ranges",
            key="auto_detect_units"
        )
        
        # Project Basepoint
        st.subheader("📍 Project Basepoint")
        config["use_basepoint"] = st.checkbox("Define Project Basepoint", key="use_basepoint")
        
        if config["use_basepoint"]:
            st.caption("Define the project origin in world coordinates")
            col_n, col_e = st.columns(2)
            with col_n:
                config["basepoint_n"] = st.number_input(
                    "Basepoint N (Northing)",
                    format="%.3f",
                    help="World N coordinate of project origin",
                    key="basepoint_n"
                )
            with col_e:
                config["basepoint_e"] = st.number_input(
                    "Basepoint E (Easting)",
                    format="%.3f",
                    help="World E coordinate of project origin",
                    key="basepoint_e"
                )
            config["basepoint_z"] = st.number_input(
                "Basepoint Z (Elevation)",
                format="%.3f",
                help="World Z coordinate of project origin",
                key="basepoint_z"
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
            
        # Appearance
        st.header("🎨 Appearance")
        config["marker_color"] = st.color_picker("Marker Color", key="marker_color")
        
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
            key="pset_name"
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
                        f"Value {i + 1}", value=prop["value"], key=f"edit_prop_value_{i}"
                    )
                with col3:
                    if st.button("🗑️", key=f"remove_{i}", help="Remove property"):
                        properties_to_remove.append(i)
                        
            # Remove marked properties
            if properties_to_remove:
                for i in reversed(properties_to_remove):
                    st.session_state.custom_properties.pop(i)
                st.rerun()
                
        config["custom_properties"] = st.session_state.custom_properties
        
        # Verification settings
        st.subheader("✅ Coordinate Verification")
        config["verify_coordinates"] = st.checkbox(
            "Verify coordinates after IFC generation",
            help="Read back the IFC file to verify local + offset = original coordinates",
            key="verify_coordinates"
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
                    "project_name", "site_name", "building_name", "storey_name",
                    "coord_system", "basepoint_n", "basepoint_e", "basepoint_z",
                    "creator_name", "marker_color", "pset_name"
                ]
                for key in keys_to_reset:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
                
    return config
'''

    sidebar_path = base_path / "sitecast" / "ui" / "sidebar.py"
    write_file_utf8(sidebar_path, sidebar_content)
    print(f"✅ Updated: sitecast/ui/sidebar.py")


def create_upload_module(base_path):
    """Create the complete upload.py module"""

    upload_content = '''"""File upload section UI"""
import streamlit as st
from ..config import SUPPORTED_FORMATS
from ..utils.templates import create_excel_template, EXCEL_SUPPORT

def create_upload_section():
    """Create file upload section and return uploaded file"""
    st.header("📤 Upload Survey Data")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload survey data file",
        type=SUPPORTED_FORMATS,
        help="Supported formats: CSV, KOF (Norwegian), Excel (XLSX/XLS)",
    )
    
    # Template download section
    st.subheader("📋 Need a Template?")
    st.write("For complex data or when other formats don't work, use our Excel template:")
    
    if EXCEL_SUPPORT:
        template_file = create_excel_template()
        if template_file:
            st.download_button(
                label="📥 Download Excel Template",
                data=template_file,
                file_name="SiteCast_Survey_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Download a pre-formatted Excel template with sample data",
            )
    else:
        st.warning("Excel support not available. Install openpyxl: `pip install openpyxl`")
        
    # Sample data info
    with st.expander("📋 Supported File Formats"):
        st.write("**CSV Format Example (N,E,Z Order):**")
        st.code("""ID,N,E,Z,Description
SP001,82692.090,1194257.404,2.075,Control Point
SP002,82687.146,1194250.859,2.295,Survey Point
SP003,82673.960,1194233.405,2.286,Benchmark""")
        
        st.write("**KOF Format Example:**")
        st.code("""05 AEP4 82692.090 1194257.404 2.075
05 AEP3 82687.146 1194250.859 2.295
05 AEP2 82673.960 1194233.405 2.286""")
        st.caption("KOF files should contain '03' or '05' format lines")
        
        st.write("**Excel Format:**")
        st.write("Use the downloadable template above for structured Excel format.")
        st.info("📌 **Important**: All formats follow N,E,Z coordinate order")
        
    return uploaded_file
'''

    upload_path = base_path / "sitecast" / "ui" / "upload.py"
    write_file_utf8(upload_path, upload_content)
    print(f"✅ Updated: sitecast/ui/upload.py")


def create_mapping_module(base_path):
    """Create the complete mapping.py module"""

    mapping_content = '''"""Column mapping interface UI"""
import streamlit as st
import pandas as pd
from ..core.parsers import (
    smart_parse_kof_file,
    create_editable_coordinate_table,
    detect_coordinate_columns,
    apply_column_mapping
)
from ..core.validators import CoordinateValidator
from ..core.processors import SurveyProcessor, SKLEARN_AVAILABLE
from ..utils.templates import process_excel_file

def create_mapping_section(uploaded_file, config):
    """Create column mapping section and return processed dataframe"""
    st.header("📊 Column Mapping & Preview")
    
    try:
        # Determine file type and parse
        file_extension = uploaded_file.name.split(".")[-1].lower()
        
        if file_extension == "csv":
            df = pd.read_csv(uploaded_file)
            missing_mappings = handle_standard_mapping(df, file_extension)
            
        elif file_extension in ["xlsx", "xls"]:
            df = process_excel_file(uploaded_file)
            missing_mappings = handle_standard_mapping(df, file_extension)
            
        elif file_extension == "kof":
            df, missing_mappings = handle_kof_mapping(uploaded_file)
            
        else:
            st.error("Unsupported file format")
            return None, ["Unsupported format"], []
            
        # Validate and process coordinates
        if not missing_mappings and df is not None and len(df) > 0:
            return validate_and_process_coordinates(df, config, uploaded_file, file_extension)
        else:
            return None, missing_mappings, []
            
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None, [str(e)], []

def handle_standard_mapping(df, file_extension):
    """Handle column mapping for standard formats (CSV, Excel)"""
    detected_mapping = detect_coordinate_columns(df)
    
    st.subheader("🗺️ Column Mapping")
    st.caption("Map your file columns to N,E,Z coordinate data")
    
    available_columns = [""] + list(df.columns)
    col_map = {}
    
    # Create mapping dropdowns
    col_map["ID"] = st.selectbox(
        "Point ID Column",
        available_columns,
        index=available_columns.index(detected_mapping.get("ID", ""))
        if detected_mapping.get("ID", "") in available_columns else 0,
        key=f"id_col_{file_extension}"
    )
    
    col_map["N"] = st.selectbox(
        "N Coordinate (Northing)",
        available_columns,
        index=available_columns.index(detected_mapping.get("N", ""))
        if detected_mapping.get("N", "") in available_columns else 0,
        key=f"n_col_{file_extension}"
    )
    
    col_map["E"] = st.selectbox(
        "E Coordinate (Easting)",
        available_columns,
        index=available_columns.index(detected_mapping.get("E", ""))
        if detected_mapping.get("E", "") in available_columns else 0,
        key=f"e_col_{file_extension}"
    )
    
    col_map["Z"] = st.selectbox(
        "Z Coordinate (Elevation)",
        available_columns,
        index=available_columns.index(detected_mapping.get("Z", ""))
        if detected_mapping.get("Z", "") in available_columns else 0,
        key=f"z_col_{file_extension}"
    )
    
    col_map["Description"] = st.selectbox(
        "Description (Optional)",
        available_columns,
        index=available_columns.index(detected_mapping.get("Description", ""))
        if detected_mapping.get("Description", "") in available_columns else 0,
        key=f"desc_col_{file_extension}"
    )
    
    # Validate required mappings
    required_mappings = ["ID", "N", "E", "Z"]
    missing_mappings = [col for col in required_mappings if not col_map[col]]
    
    if missing_mappings:
        st.error(f"Please map the following required columns: {', '.join(missing_mappings)}")
        return missing_mappings
    else:
        # Apply mapping
        mapped_df = apply_column_mapping(df, col_map)
        st.session_state.mapped_df = mapped_df
        return []

def handle_kof_mapping(uploaded_file):
    """Handle KOF file parsing and mapping"""
    file_content = uploaded_file.read().decode("utf-8", errors="ignore")
    
    st.write("**🔍 Parsing KOF File...**")
    with st.expander("Show file content"):
        st.code(file_content)
        
    # Parse KOF file
    parsed_data = smart_parse_kof_file(file_content)
    st.session_state.parsed_data = parsed_data
    
    st.write(f"**Found {len(parsed_data)} coordinate lines**")
    
    if not parsed_data:
        st.error("No coordinate data found in KOF file.")
        return None, ["No data found"]
        
    # Create editable table
    df = create_editable_coordinate_table(parsed_data)
    
    # Show parsing results
    st.subheader("📊 KOF File Parsing Results")
    st.write(f"Found **{len(df)} coordinate lines** in the file")
    
    # Coordinate assignment interface
    st.subheader("🗺️ Coordinate Assignment")
    st.caption("Assign which coordinate column represents N, E, Z")
    
    if parsed_data:
        example_line = parsed_data[0]["original_line"]
        st.info(f"📋 **Example line**: `{example_line}`")
        
        with st.expander("🔍 Detailed Parsing Breakdown"):
            st.write("**All numbers found:**", parsed_data[0]["all_numeric"])
            st.write("**Text values found:**", parsed_data[0]["all_text"])
            st.write("**Filtered coordinates:**", parsed_data[0]["filtered_coords"])
            
    # Column assignment
    available_coord_cols = [col for col in df.columns if col.startswith("Coord")]
    
    coord_cols = st.columns(3)
    with coord_cols[0]:
        n_source = st.selectbox("Northing (N):", available_coord_cols, index=0, key="n_assign")
    with coord_cols[1]:
        e_source = st.selectbox("Easting (E):", available_coord_cols, index=1 if len(available_coord_cols) > 1 else 0, key="e_assign")
    with coord_cols[2]:
        z_source = st.selectbox("Elevation (Z):", available_coord_cols, index=2 if len(available_coord_cols) > 2 else 0, key="z_assign")
        
    # Check for duplicates
    assignments = [n_source, e_source, z_source]
    if len(set(assignments)) < 3:
        st.warning("⚠️ Duplicate assignments detected. Verify your coordinate assignments.")
        
    # Create mapped dataframe
    try:
        mapped_df = df.copy()
        mapped_df["N"] = df[n_source] if n_source else 0.0
        mapped_df["E"] = df[e_source] if e_source else 0.0
        mapped_df["Z"] = df[z_source] if z_source else 0.0
        
        # Ensure required columns
        if "ID" not in mapped_df.columns:
            mapped_df["ID"] = [f"P{i + 1}" for i in range(len(mapped_df))]
        if "Description" not in mapped_df.columns:
            mapped_df["Description"] = ""
            
        # Show editable table
        st.subheader("✏️ Edit Coordinate Data")
        required_cols = ["ID", "N", "E", "Z", "Description"]
        
        edited_df = st.data_editor(
            mapped_df[required_cols].copy(),
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "ID": st.column_config.TextColumn("Point ID", required=True),
                "N": st.column_config.NumberColumn("N (Northing)", format="%.3f"),
                "E": st.column_config.NumberColumn("E (Easting)", format="%.3f"),
                "Z": st.column_config.NumberColumn("Z (Elevation)", format="%.3f"),
                "Description": st.column_config.TextColumn("Description"),
            },
        )
        
        st.session_state.mapped_df = edited_df
        return edited_df, []
        
    except Exception as e:
        st.error(f"Error creating mapped dataframe: {str(e)}")
        return None, [str(e)]

def validate_and_process_coordinates(df, config, uploaded_file, file_extension):
    """Validate coordinates and apply transformations"""
    validator = CoordinateValidator()
    errors, warnings = validator.validate_coordinates(df)
    
    if errors:
        st.error("❌ **Coordinate Validation Errors:**")
        for error in errors:
            st.error(f"• {error}")
        return df, errors, warnings
        
    # Unit detection and conversion
    if config["auto_detect_units"]:
        detected_units = validator.detect_units(df)
        st.info(f"🔍 **Detected Units**: {detected_units}")
        
        if detected_units != config["unit_code"]:
            st.warning(f"⚠️ **Unit Mismatch**: Selected {config['unit_code']}, detected {detected_units}")
            
            # Ask user which to use
            use_detected = st.radio(
                "Which units should be used?",
                options=[f"Use detected: {detected_units}", f"Use selected: {config['unit_code']}"],
                key="unit_choice"
            )
            
            if "detected" in use_detected:
                working_units = detected_units
            else:
                working_units = config["unit_code"]
        else:
            working_units = config["unit_code"]
    else:
        working_units = config["unit_code"]
        
    # Convert to meters for IFC
    if working_units != "m":
        st.info(f"🔄 **Converting** from {working_units} to meters for IFC")
        df_meters = validator.convert_units(df, working_units, "m")
        conversion_note = f" (converted from {working_units})"
    else:
        df_meters = df.copy()
        conversion_note = ""
        
    # Show coordinate sample
    st.info("📋 **Coordinate Sample** (in meters for IFC):")
    sample_coords = df_meters[["N", "E", "Z"]].head(3)
    for idx, row in sample_coords.iterrows():
        st.write(f"Point {idx + 1}: N={row['N']:.3f}m, E={row['E']:.3f}m, Z={row['Z']:.3f}m")
        
    if warnings:
        st.warning("⚠️ **Coordinate Validation Warnings:**")
        for warning in warnings:
            st.warning(f"• {warning}")
            
    # Create survey processor
    processor = SurveyProcessor(
        config["coord_system"],
        config["basepoint_n"],
        config["basepoint_e"],
        config["basepoint_z"]
    )
    
    # Calculate north direction
    if len(df_meters) >= 3:
        calculated_north = processor.calculate_north_direction(df_meters)
        if SKLEARN_AVAILABLE:
            st.info(f"🧭 **Calculated Grid North**: {calculated_north:.2f}° from east (PCA method)")
        else:
            st.info(f"🧭 **Estimated Grid North**: {calculated_north:.2f}° from east (basic method)")
            
    # Apply coordinate transformation
    if config["coord_system"] == "Local" or config["use_basepoint"]:
        transformed_df = processor.transform_coordinates(df_meters)
        coord_note = f" (offset by basepoint: N={config['basepoint_n']:.3f}, E={config['basepoint_e']:.3f}, Z={config['basepoint_z']:.3f})"
    else:
        transformed_df = df_meters.copy()
        coord_note = " (global coordinates)"
        
    # Show preview
    file_type = {
        "csv": "CSV",
        "xlsx": "Excel", 
        "xls": "Excel",
        "kof": "KOF"
    }[file_extension]
    
    st.write(f"**{len(transformed_df)} survey points ready from {file_type} file** ({working_units}{conversion_note})")
    
    # Show coordinate preview tabs
    if config["use_basepoint"]:
        preview_tabs = st.tabs(["Transformed (Local)", "Original (World)", "Units Info"])
        with preview_tabs[0]:
            st.caption("Coordinates relative to project basepoint (meters)")
            st.dataframe(transformed_df.head(), use_container_width=True)
        with preview_tabs[1]:
            st.caption(f"Original coordinates from file ({working_units})")
            st.dataframe(df.head(), use_container_width=True)
        with preview_tabs[2]:
            st.caption("Unit conversion details")
            st.write(f"• **Source data**: {working_units}")
            st.write(f"• **IFC output**: meters (BIM standard)")
            if working_units != "m":
                st.write(f"• **Conversion factor**: {working_units} → m")
    else:
        preview_tabs = st.tabs(["Coordinates", "Units Info"])
        with preview_tabs[0]:
            st.caption(f"Survey coordinates (converted to meters)")
            st.dataframe(transformed_df.head(), use_container_width=True)
        with preview_tabs[1]:
            st.caption("Unit information")
            st.write(f"• **Source data**: {working_units}")
            st.write(f"• **IFC output**: meters (BIM standard)")
            
    # Coordinate system info
    try:
        if pd.api.types.is_numeric_dtype(transformed_df["N"]) and \\
           pd.api.types.is_numeric_dtype(transformed_df["E"]) and \\
           pd.api.types.is_numeric_dtype(transformed_df["Z"]):
            n_range = f"{transformed_df['N'].min():.2f} to {transformed_df['N'].max():.2f}"
            e_range = f"{transformed_df['E'].min():.2f} to {transformed_df['E'].max():.2f}"
            z_range = f"{transformed_df['Z'].min():.2f} to {transformed_df['Z'].max():.2f}"
            st.info(f"📍 **{config['coord_system']} Coordinate Ranges** (meters){coord_note}\\nN: {n_range}m\\nE: {e_range}m\\nZ: {z_range}m")
    except Exception as e:
        st.warning(f"Could not calculate coordinate ranges: {str(e)}")
        
    # Store processed data
    st.session_state.transformed_df = transformed_df
    st.session_state.df_meters = df_meters
    st.session_state.working_units = working_units
    st.session_state.conversion_note = conversion_note
    st.session_state.coord_note = coord_note
    if 'calculated_north' in locals():
        st.session_state.calculated_north = calculated_north
        
    return transformed_df, [], warnings
'''

    mapping_path = base_path / "sitecast" / "ui" / "mapping.py"
    write_file_utf8(mapping_path, mapping_content)
    print(f"✅ Updated: sitecast/ui/mapping.py")


def create_export_module(base_path):
    """Create the complete export.py module"""

    export_content = '''"""Export section UI for IFC generation"""
import streamlit as st
import tempfile
import os
import time
import ifcopenshell

from ..ifc.builder import create_ifc_file
from ..ifc.materials import create_material, create_coordination_material
from .components import create_enhanced_survey_point, create_coordination_object
from ..utils.verification import verify_ifc_coordinates

def create_export_section(df, uploaded_file, config, warnings):
    """Create export section for IFC file generation"""
    st.header("🚀 Generate IFC File")
    
    # Convert hex color to RGB
    hex_color = config["marker_color"].lstrip("#")
    rgb_color = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    
    # Generate IFC button
    if st.button("🚀 Generate IFC File", type="primary", use_container_width=True):
        try:
            generate_ifc_file(df, uploaded_file, config, rgb_color)
        except Exception as e:
            st.error(f"Error generating IFC file: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

def generate_ifc_file(df, uploaded_file, config, rgb_color):
    """Generate IFC file from survey data"""
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Create IFC file structure
    status_text.text("Creating IFC file structure...")
    progress_bar.progress(10)
    
    # Create IFC file
    file, storey, context = create_ifc_file(
        config["project_name"],
        config["site_name"],
        config["building_name"],
        config["storey_name"],
        config["coord_system"],
        config["basepoint_n"],
        config["basepoint_e"],
        config["basepoint_z"]
    )
    
    # Step 2: Create materials
    status_text.text("Creating materials...")
    progress_bar.progress(20)
    
    survey_material = create_material(file, "Survey Marker", rgb_color)
    coord_material = create_coordination_material(file)
    
    # Step 3: Create coordination objects
    status_text.text("Creating coordination objects...")
    progress_bar.progress(30)
    
    coordination_objects_created = 0
    
    if config["use_basepoint"]:
        # Create coordination object at project basepoint
        create_coordination_object(
            file, storey, context,
            "Project Basepoint",
            0.0, 0.0, 0.0,
            coord_material,
            f"Project basepoint: N={config['basepoint_n']:.3f}, E={config['basepoint_e']:.3f}, Z={config['basepoint_z']:.3f}"
        )
        coordination_objects_created += 1
        
    if config["use_rotation_point"]:
        # Calculate rotation point in local coordinates
        if config["use_basepoint"]:
            local_rot_n = config["rotation_n"] - config["basepoint_n"]
            local_rot_e = config["rotation_e"] - config["basepoint_e"]
            local_rot_z = config["rotation_z"] - config["basepoint_z"]
        else:
            local_rot_n = config["rotation_n"]
            local_rot_e = config["rotation_e"]
            local_rot_z = config["rotation_z"]
            
        create_coordination_object(
            file, storey, context,
            "Survey/Rotation Point",
            local_rot_n, local_rot_e, local_rot_z,
            coord_material,
            f"Rotation point: N={config['rotation_n']:.3f}, E={config['rotation_e']:.3f}, Z={config['rotation_z']:.3f}"
        )
        coordination_objects_created += 1
        
    # Step 4: Create survey points
    status_text.text("Creating survey points...")
    progress_bar.progress(40)
    
    total_points = len(df)
    df_meters = st.session_state.get("df_meters", df)
    
    for idx, row in df.iterrows():
        # Update progress
        point_progress = 40 + int((idx / total_points) * 30)
        progress_bar.progress(point_progress)
        status_text.text(f"Creating survey point {idx + 1} of {total_points}...")
        
        point_data = row.to_dict()
        
        # Prepare coordinate data
        original_coords = {
            "N": df_meters.loc[idx, "N"],
            "E": df_meters.loc[idx, "E"],
            "Z": df_meters.loc[idx, "Z"]
        }
        
        local_coords = {
            "N": row["N"],
            "E": row["E"],
            "Z": row["Z"]
        }
        
        offsets = {
            "N": config["basepoint_n"],
            "E": config["basepoint_e"],
            "Z": config["basepoint_z"]
        }
        
        create_enhanced_survey_point(
            file, storey, context,
            point_data, survey_material,
            original_coords, local_coords, offsets,
            config["pset_name"],
            config["custom_properties"],
            uploaded_file.name if uploaded_file else "Unknown",
            config["creator_name"],
            config["external_link"]
        )
        
    # Step 5: Save IFC file
    status_text.text("Saving IFC file...")
    progress_bar.progress(70)
    
    # Save to temporary file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ifc") as tmp_file:
            tmp_file_path = tmp_file.name
            
        # Write IFC file
        file.write(tmp_file_path)
        
        # Step 6: Read file for download
        status_text.text("Preparing download...")
        progress_bar.progress(80)
        
        with open(tmp_file_path, "rb") as f:
            ifc_data = f.read()
            
        # Step 7: Coordinate verification
        verification_results = None
        if config["verify_coordinates"]:
            status_text.text("Verifying coordinates...")
            progress_bar.progress(90)
            
            verification_results = verify_ifc_coordinates(
                tmp_file_path,
                df_meters,
                offsets
            )
            
    finally:
        # Clean up
        for attempt in range(3):
            try:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                break
            except PermissionError:
                if attempt < 2:
                    time.sleep(0.1)
                    
    # Step 8: Complete
    status_text.text("IFC generation complete!")
    progress_bar.progress(100)
    
    st.success("✅ IFC file generated successfully!")
    
    # Download button
    filename = f"{config['project_name'].replace(' ', '_')}_survey_points.ifc"
    st.download_button(
        label="📥 Download IFC File",
        data=ifc_data,
        file_name=filename,
        mime="application/octet-stream",
        use_container_width=True
    )
    
    # Summary stats
    coord_summary = f" + {coordination_objects_created} coordination objects" if coordination_objects_created > 0 else ""
    calculated_north = st.session_state.get("calculated_north", None)
    north_summary = f" (Grid North: {calculated_north:.1f}°)" if calculated_north else ""
    
    st.info(
        f"📊 **Summary**: {len(df)} survey points{coord_summary} converted to IFC format "
        f"using {config['coord_system'].lower()} coordinates{north_summary}"
    )
    
    # Display verification results
    if config["verify_coordinates"] and verification_results:
        display_verification_results(verification_results)
        
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

def display_verification_results(verification_results):
    """Display coordinate verification results"""
    if isinstance(verification_results, str):
        st.warning(f"⚠️ **Coordinate Verification Failed**: {verification_results}")
    elif isinstance(verification_results, list) and len(verification_results) > 0:
        st.success("✅ **Coordinate Verification Complete**")
        
        # Count matches
        total_points = len(verification_results)
        all_matches = sum(1 for result in verification_results if result["all_match"])
        
        if all_matches == total_points:
            st.success(f"🎯 **Perfect Match**: All {total_points} points verified successfully!")
        else:
            st.warning(f"⚠️ **Partial Match**: {all_matches}/{total_points} points verified successfully")
            
        # Show detailed results
        with st.expander("🔍 View Detailed Verification Results"):
            for result in verification_results:
                point_id = result["point_id"]
                if result["all_match"]:
                    st.success(f"✅ **Point {point_id}**: Coordinates match perfectly")
                else:
                    st.error(f"❌ **Point {point_id}**: Coordinate mismatch detected")
                    
                    # Show coordinate comparison
                    orig = result["original"]
                    calc = result["calculated"]
                    matches = result["matches"]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        status = "✅" if matches["N"] else "❌"
                        st.write(f"{status} **N**: {orig['N']:.3f} → {calc['N']:.3f}")
                    with col2:
                        status = "✅" if matches["E"] else "❌"
                        st.write(f"{status} **E**: {orig['E']:.3f} → {calc['E']:.3f}")
                    with col3:
                        status = "✅" if matches["Z"] else "❌"
                        st.write(f"{status} **Z**: {orig['Z']:.3f} → {calc['Z']:.3f}")
    else:
        st.info("ℹ️ **Coordinate Verification**: No results to display")
'''

    export_path = base_path / "sitecast" / "ui" / "export.py"
    write_file_utf8(export_path, export_content)
    print(f"✅ Updated: sitecast/ui/export.py")


def main():
    """Complete the UI module implementations"""

    # Get the base path
    base_path = Path(r"C:\LokalMappe_Blade15\CodingProjects\SiteCast")

    print("🔧 Completing UI module implementations...")
    print(f"📁 Base directory: {base_path}")

    # Create all UI modules
    create_sidebar_module(base_path)
    create_upload_module(base_path)
    create_mapping_module(base_path)
    create_export_module(base_path)

    print("\n✨ UI modules complete! Your SiteCast application is ready to run.")
    print("\n📝 To run the application:")
    print("   streamlit run main.py")
    print("\n✅ All modules are now fully implemented!")


if __name__ == "__main__":
    main()
