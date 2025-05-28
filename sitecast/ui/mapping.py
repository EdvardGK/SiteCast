"""Column mapping interface UI"""

import streamlit as st
import pandas as pd
from ..core.parsers import (
    smart_parse_kof_file,
    create_editable_coordinate_table,
    detect_coordinate_columns,
    apply_column_mapping,
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
            return validate_and_process_coordinates(
                df, config, uploaded_file, file_extension
            )
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
        if detected_mapping.get("ID", "") in available_columns
        else 0,
        key=f"id_col_{file_extension}",
    )

    col_map["N"] = st.selectbox(
        "N Coordinate (Northing)",
        available_columns,
        index=available_columns.index(detected_mapping.get("N", ""))
        if detected_mapping.get("N", "") in available_columns
        else 0,
        key=f"n_col_{file_extension}",
    )

    col_map["E"] = st.selectbox(
        "E Coordinate (Easting)",
        available_columns,
        index=available_columns.index(detected_mapping.get("E", ""))
        if detected_mapping.get("E", "") in available_columns
        else 0,
        key=f"e_col_{file_extension}",
    )

    col_map["Z"] = st.selectbox(
        "Z Coordinate (Elevation)",
        available_columns,
        index=available_columns.index(detected_mapping.get("Z", ""))
        if detected_mapping.get("Z", "") in available_columns
        else 0,
        key=f"z_col_{file_extension}",
    )

    col_map["Description"] = st.selectbox(
        "Description (Optional)",
        available_columns,
        index=available_columns.index(detected_mapping.get("Description", ""))
        if detected_mapping.get("Description", "") in available_columns
        else 0,
        key=f"desc_col_{file_extension}",
    )

    # Validate required mappings
    required_mappings = ["ID", "N", "E", "Z"]
    missing_mappings = [col for col in required_mappings if not col_map[col]]

    if missing_mappings:
        st.error(
            f"Please map the following required columns: {', '.join(missing_mappings)}"
        )
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
        n_source = st.selectbox(
            "Northing (N):", available_coord_cols, index=0, key="n_assign"
        )
    with coord_cols[1]:
        e_source = st.selectbox(
            "Easting (E):",
            available_coord_cols,
            index=1 if len(available_coord_cols) > 1 else 0,
            key="e_assign",
        )
    with coord_cols[2]:
        z_source = st.selectbox(
            "Elevation (Z):",
            available_coord_cols,
            index=2 if len(available_coord_cols) > 2 else 0,
            key="z_assign",
        )

    # Check for duplicates
    assignments = [n_source, e_source, z_source]
    if len(set(assignments)) < 3:
        st.warning(
            "⚠️ Duplicate assignments detected. Verify your coordinate assignments."
        )

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
            st.warning(
                f"⚠️ **Unit Mismatch**: Selected {config['unit_code']}, detected {detected_units}"
            )

            # Ask user which to use
            use_detected = st.radio(
                "Which units should be used?",
                options=[
                    f"Use detected: {detected_units}",
                    f"Use selected: {config['unit_code']}",
                ],
                key="unit_choice",
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
        st.write(
            f"Point {idx + 1}: N={row['N']:.3f}m, E={row['E']:.3f}m, Z={row['Z']:.3f}m"
        )

    if warnings:
        st.warning("⚠️ **Coordinate Validation Warnings:**")
        for warning in warnings:
            st.warning(f"• {warning}")

    # Create survey processor
    processor = SurveyProcessor(
        config["coord_system"],
        config["basepoint_n"],
        config["basepoint_e"],
        config["basepoint_z"],
    )

    # Calculate north direction
    if len(df_meters) >= 3:
        calculated_north = processor.calculate_north_direction(df_meters)
        if SKLEARN_AVAILABLE:
            st.info(
                f"🧭 **Calculated Grid North**: {calculated_north:.2f}° from east (PCA method)"
            )
        else:
            st.info(
                f"🧭 **Estimated Grid North**: {calculated_north:.2f}° from east (basic method)"
            )

    # Apply coordinate transformation
    if config["coord_system"] == "Local" or config["use_basepoint"]:
        transformed_df = processor.transform_coordinates(df_meters)
        coord_note = f" (offset by basepoint: N={config['basepoint_n']:.3f}, E={config['basepoint_e']:.3f}, Z={config['basepoint_z']:.3f})"
    else:
        transformed_df = df_meters.copy()
        coord_note = " (global coordinates)"

    # Show preview
    file_type = {"csv": "CSV", "xlsx": "Excel", "xls": "Excel", "kof": "KOF"}[
        file_extension
    ]

    st.write(
        f"**{len(transformed_df)} survey points ready from {file_type} file** ({working_units}{conversion_note})"
    )

    # Show coordinate preview tabs
    if config["use_basepoint"]:
        preview_tabs = st.tabs(
            ["Transformed (Local)", "Original (World)", "Units Info"]
        )
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
        if (
            pd.api.types.is_numeric_dtype(transformed_df["N"])
            and pd.api.types.is_numeric_dtype(transformed_df["E"])
            and pd.api.types.is_numeric_dtype(transformed_df["Z"])
        ):
            n_range = (
                f"{transformed_df['N'].min():.2f} to {transformed_df['N'].max():.2f}"
            )
            e_range = (
                f"{transformed_df['E'].min():.2f} to {transformed_df['E'].max():.2f}"
            )
            z_range = (
                f"{transformed_df['Z'].min():.2f} to {transformed_df['Z'].max():.2f}"
            )
            st.info(
                f"📍 **{config['coord_system']} Coordinate Ranges** (meters){coord_note}\nN: {n_range}m\nE: {e_range}m\nZ: {z_range}m"
            )
    except Exception as e:
        st.warning(f"Could not calculate coordinate ranges: {str(e)}")

    # Store processed data
    st.session_state.transformed_df = transformed_df
    st.session_state.df_meters = df_meters
    st.session_state.working_units = working_units
    st.session_state.conversion_note = conversion_note
    st.session_state.coord_note = coord_note
    if "calculated_north" in locals():
        st.session_state.calculated_north = calculated_north

    return transformed_df, [], warnings
