"""File upload section UI with state preservation"""

import streamlit as st
import io
from ..config import SUPPORTED_FORMATS
from ..utils.templates import create_excel_template, EXCEL_SUPPORT


def create_upload_section():
    """Create file upload section and return uploaded file"""
    st.header("📤 Upload Survey Data")

    # Check if we have a stored file in session state
    if (
        hasattr(st.session_state, "uploaded_file_data")
        and st.session_state.uploaded_file_data is not None
    ):
        # Display info about the stored file
        st.info(
            f"📁 Using previously uploaded file: {st.session_state.uploaded_file_name}"
        )

        # Provide option to clear the stored file
        if st.button("🗑️ Clear uploaded file", key="clear_file"):
            st.session_state.uploaded_file_data = None
            st.session_state.uploaded_file_name = None
            st.session_state.parsed_data = None
            st.session_state.mapped_df = None
            st.session_state.transformed_df = None
            st.rerun()

        # Return the stored file as a file-like object
        return create_file_from_session_state()

    # File upload widget
    uploaded_file = st.file_uploader(
        "Upload survey data file",
        type=SUPPORTED_FORMATS,
        help="Supported formats: CSV, KOF (Norwegian), Excel (XLSX/XLS)",
        key="file_uploader",
    )

    # Store the file in session state when uploaded
    if uploaded_file is not None:
        # Read file content and store in session state
        file_content = uploaded_file.read()
        st.session_state.uploaded_file_data = file_content
        st.session_state.uploaded_file_name = uploaded_file.name
        st.session_state.uploaded_file_type = uploaded_file.type

        # Reset the file pointer for further processing
        uploaded_file.seek(0)

    # Template download section
    st.subheader("📋 Need a Template?")
    st.write(
        "For complex data or when other formats don't work, use our Excel template:"
    )

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
        st.warning(
            "Excel support not available. Install openpyxl: `pip install openpyxl`"
        )

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


def create_file_from_session_state():
    """Create a file-like object from session state data"""
    if st.session_state.uploaded_file_data is None:
        return None

    # Create a file-like object from the stored data
    file_like = io.BytesIO(st.session_state.uploaded_file_data)

    # Add attributes to mimic an uploaded file
    file_like.name = st.session_state.uploaded_file_name
    file_like.type = st.session_state.get(
        "uploaded_file_type", "application/octet-stream"
    )

    return file_like
