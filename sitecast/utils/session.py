"""Session state management for Streamlit with enhanced persistence"""

import streamlit as st
from ..config import DEFAULTS


def initialize_session_state():
    """Initialize session state with default values"""
    # Handle legacy color format conversion
    if "marker_color" in st.session_state:
        # Convert hex colors to names if needed
        hex_to_name = {
            "#FF0000": "Red",
            "#FF00FF": "Magenta",
            "#008080": "Teal",
            "#808080": "Gray",
            "#FFFF00": "Yellow",
        }
        if st.session_state.marker_color in hex_to_name:
            st.session_state.marker_color = hex_to_name[st.session_state.marker_color]

    for key, default_value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

    # Add file persistence keys
    if "uploaded_file_data" not in st.session_state:
        st.session_state.uploaded_file_data = None
    if "uploaded_file_name" not in st.session_state:
        st.session_state.uploaded_file_name = None
    if "uploaded_file_type" not in st.session_state:
        st.session_state.uploaded_file_type = None
    if "preserve_file_state" not in st.session_state:
        st.session_state.preserve_file_state = False
