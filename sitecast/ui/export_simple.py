"""Simplified export functionality using custom IFC writer"""

import streamlit as st
import pandas as pd
import tempfile
import os
import time

from ..ifc.ifc_writer import IFCBuilder
from ..core.processors import apply_rotation_point
from ..utils.verification import verify_ifc_coordinates_simple


def create_export_section(uploaded_file, df, df_meters, config):
    """Create export section with IFC generation"""
    
    st.header("📦 Export to IFC")
    
    if df is None or df.empty:
        st.info("👆 Please upload a file and map coordinates first")
        return
        
    # Export button
    if st.button("🚀 Generate IFC File", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Initialize
            status_text.text("Initializing IFC export...")
            progress_bar.progress(10)
            
            # Create IFC builder
            builder = IFCBuilder()
            builder.create_project(config["project_name"])
            
            # Step 2: Process points
            status_text.text("Processing survey points...")
            progress_bar.progress(30)
            
            # Apply rotation if configured
            if config.get("use_rotation_point", False):
                df_processed = apply_rotation_point(
                    df.copy(),
                    config["rotation_n"],
                    config["rotation_e"],
                    config["rotation_angle"]
                )
            else:
                df_processed = df.copy()
            
            # Step 3: Add survey points
            total_points = len(df_processed)
            for idx, row in df_processed.iterrows():
                # Update progress
                point_progress = 30 + int((idx / total_points) * 50)
                progress_bar.progress(point_progress)
                status_text.text(f"Creating survey point {idx + 1} of {total_points}...")
                
                # Get point data
                point_id = str(row.get("ID", f"PT{idx+1}"))
                n = float(row["N"])
                e = float(row["E"]) 
                z = float(row["Z"])
                desc = str(row.get("Description", ""))
                
                # Add basepoint offset
                if config.get("use_basepoint", False):
                    e_final = e - config["basepoint_e"]
                    n_final = n - config["basepoint_n"]
                    z_final = z - config["basepoint_z"]
                else:
                    e_final = e
                    n_final = n
                    z_final = z
                
                # Get color based on config
                color_map = {
                    "Red": (1.0, 0.0, 0.0),
                    "Magenta": (1.0, 0.0, 1.0),
                    "Teal": (0.0, 0.5, 0.5),
                    "Gray": (0.5, 0.5, 0.5),
                    "Yellow": (1.0, 1.0, 0.0)
                }
                color = color_map.get(config.get("marker_color", "Red"), (1.0, 0.0, 0.0))
                
                # Add to IFC
                builder.add_survey_point(
                    point_id=point_id,
                    x=e_final,
                    y=n_final,
                    z=z_final,
                    description=desc,
                    color=color
                )
            
            # Step 4: Save IFC file
            status_text.text("Saving IFC file...")
            progress_bar.progress(80)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ifc") as tmp_file:
                tmp_file_path = tmp_file.name
            
            # Write IFC
            builder.write(tmp_file_path)
            
            # Step 5: Read for download
            status_text.text("Preparing download...")
            progress_bar.progress(90)
            
            with open(tmp_file_path, "rb") as f:
                ifc_data = f.read()
            
            # Clean up
            try:
                os.unlink(tmp_file_path)
            except:
                pass
            
            # Complete
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
            
            # Summary
            coord_system = config.get('coord_system', 'Local')
            st.info(f"📊 **Summary**: {len(df)} survey points converted to IFC format using {coord_system.lower()} coordinates")
            
            # Clear progress
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            st.error(f"❌ Error generating IFC: {str(e)}")
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