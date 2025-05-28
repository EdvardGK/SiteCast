"""Enhanced export section UI for IFC generation"""

import streamlit as st
import tempfile
import os
import time
import ifcopenshell

from ..ifc.builder import create_ifc_file
from ..ifc.materials import (
    create_material,
    create_coordination_material,
    create_red_material,
    create_magenta_material,
    create_teal_material,
)
from ..config import MARKER_COLORS
from .components import (
    create_enhanced_survey_point,
    create_coordination_object,
    create_norwegian_basepoint,
)
from ..utils.verification import verify_ifc_coordinates
from ..ifc.info_cube import create_information_cube


def create_export_section(df, uploaded_file, config, warnings):
    """Create export section for IFC file generation"""
    st.header("🚀 Generate IFC File")

    # Generate IFC button
    if st.button("🚀 Generate IFC File", type="primary", use_container_width=True):
        try:
            generate_ifc_file(df, uploaded_file, config)
        except Exception as e:
            st.error(f"Error generating IFC file: {str(e)}")
            import traceback

            st.code(traceback.format_exc())


def generate_ifc_file(df, uploaded_file, config):
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
        config["basepoint_z"],
    )

    # Step 2: Create materials
    status_text.text("Creating materials...")
    progress_bar.progress(20)

    # Create all materials
    materials = {
        "red": create_red_material(file),
        "magenta": create_magenta_material(file),
        "teal": create_teal_material(file),
        "coord": create_coordination_material(file),
        "gray": create_material(file, "Gray", (0.5, 0.5, 0.5)),
        "yellow": create_material(file, "Yellow", (1.0, 1.0, 0.0)),
    }

    # Get selected marker color
    marker_color_rgb = MARKER_COLORS.get(
        config.get("marker_color", "Red"), (1.0, 0.0, 0.0)
    )
    marker_material = create_material(
        file, config.get("marker_color", "Red"), marker_color_rgb
    )

    # Step 3: Create coordination objects
    status_text.text("Creating coordination objects...")
    progress_bar.progress(30)

    coordination_objects_created = 0

    if config["use_basepoint"]:
        if config.get("use_norwegian_basepoints", True):
            # Create Norwegian-style basepoint
            create_norwegian_basepoint(
                file,
                storey,
                context,
                "Nullpunkt_BIMK",
                0.0,
                0.0,
                0.0,
                materials,
                angle_degrees=config.get("pie_angle", 18),
                start_angle_degrees=config.get("basepoint_orientation", 300),
                add_cylinder=config.get("add_cylinder", True),
                add_north_arrow=config.get("add_north_arrow", True),
            )
            coordination_objects_created += 1

            # Add information cube if enabled
            if config.get("use_info_cube", False):
                info_cube_config = {
                    "size": config.get("info_cube_size", 2.0),
                    "elevation": config.get("info_cube_elevation", 10.0),
                    "links": config.get("info_cube_links", []),
                }
                create_information_cube(
                    file,
                    storey,
                    context,
                    materials["gray"],
                    (0.0, 0.0, 0.0),
                    info_cube_config,
                )
        else:
            # Original coordination object
            create_coordination_object(
                file,
                storey,
                context,
                "Project Basepoint",
                0.0,
                0.0,
                0.0,
                materials["coord"],
                f"Project basepoint: N={config['basepoint_n']:.3f}, E={config['basepoint_e']:.3f}, Z={config['basepoint_z']:.3f}",
            )
            coordination_objects_created += 1

    if config["use_rotation_point"]:
        if config.get("use_norwegian_basepoints", True):
            # Calculate rotation point in local coordinates
            if config["use_basepoint"]:
                local_rot_n = config["rotation_n"] - config["basepoint_n"]
                local_rot_e = config["rotation_e"] - config["basepoint_e"]
                local_rot_z = config["rotation_z"] - config["basepoint_z"]
            else:
                local_rot_n = config["rotation_n"]
                local_rot_e = config["rotation_e"]
                local_rot_z = config["rotation_z"]

            create_norwegian_basepoint(
                file,
                storey,
                context,
                "Rotasjonspunkt_BIMK",
                local_rot_n,
                local_rot_e,
                local_rot_z,
                materials,
                angle_degrees=config.get("pie_angle", 18),
                start_angle_degrees=config.get("rotation_orientation", 270),
                add_cylinder=False,
                add_north_arrow=False,
            )
            coordination_objects_created += 1
        else:
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
                file,
                storey,
                context,
                "Survey/Rotation Point",
                local_rot_n,
                local_rot_e,
                local_rot_z,
                materials["coord"],
                f"Rotation point: N={config['rotation_n']:.3f}, E={config['rotation_e']:.3f}, Z={config['rotation_z']:.3f}",
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
            "Z": df_meters.loc[idx, "Z"],
        }

        local_coords = {"N": row["N"], "E": row["E"], "Z": row["Z"]}

        offsets = {
            "N": config["basepoint_n"],
            "E": config["basepoint_e"],
            "Z": config["basepoint_z"],
        }

        # Create survey point with selected marker type
        create_enhanced_survey_point(
            file,
            storey,
            context,
            point_data,
            marker_material,
            original_coords,
            local_coords,
            offsets,
            config["pset_name"],
            config["custom_properties"],
            uploaded_file.name if uploaded_file else "Unknown",
            config["creator_name"],
            config["external_link"],
            marker_shape=config.get("marker_shape", "Cone"),
            marker_height=config.get("marker_height", 0.5),
            marker_diameter=config.get("marker_diameter", 0.2),
            use_inverted=config.get("use_inverted", True),
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
                tmp_file_path, df_meters, offsets
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
        use_container_width=True,
    )

    # Summary stats
    coord_summary = (
        f" + {coordination_objects_created} coordination objects"
        if coordination_objects_created > 0
        else ""
    )
    calculated_north = st.session_state.get("calculated_north", None)
    north_summary = (
        f" (Grid North: {calculated_north:.1f}°)" if calculated_north else ""
    )

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
            st.success(
                f"🎯 **Perfect Match**: All {total_points} points verified successfully!"
            )
        else:
            st.warning(
                f"⚠️ **Partial Match**: {all_matches}/{total_points} points verified successfully"
            )

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
