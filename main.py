"""Main Streamlit application entry point for SiteCast"""

import streamlit as st
import sys
from pathlib import Path

# Add sitecast package to path
sys.path.append(str(Path(__file__).parent))

from sitecast.utils.session import initialize_session_state
from sitecast.ui.sidebar import create_sidebar
from sitecast.ui.upload import create_upload_section
from sitecast.ui.mapping import create_mapping_section
from sitecast.ui.export import create_export_section


def main():
    st.set_page_config(page_title="SiteCast", page_icon="📍", layout="wide")

    # Initialize session state
    initialize_session_state()

    # Language selector
    col1, col2, col3 = st.columns([8, 1, 1])
    with col2:
        if st.button("🇳🇴", help="Norsk"):
            st.info("Norsk oversettelse kommer snart!")
    with col3:
        if st.button("🇬🇧", help="English"):
            pass

    st.title("📍 SiteCast")
    st.subheader("Convert Survey Data to BIM in 30 Seconds")

    # Create sidebar
    sidebar_config = create_sidebar()

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = create_upload_section()

    with col2:
        if uploaded_file is not None:
            df, errors, warnings = create_mapping_section(uploaded_file, sidebar_config)

            if df is not None and not errors:
                # Export section
                create_export_section(df, uploaded_file, sidebar_config, warnings)
        else:
            st.header("📊 Column Mapping & Preview")
            st.info("👆 Upload a file and complete column mapping to get started")

    # Footer
    st.markdown("---")
    st.markdown("**SiteCast Enhanced** - Convert survey data to BIM-ready IFC files")


if __name__ == "__main__":
    main()
