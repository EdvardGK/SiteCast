"""
Utility to clear problematic session state values
Run this if you encounter color-related errors
"""
import streamlit as st

# Clear specific problematic keys
if 'marker_color' in st.session_state:
    if st.session_state.marker_color.startswith('#'):
        del st.session_state.marker_color
        print("Cleared hex color value from marker_color")

# Clear all session state (nuclear option)
# for key in list(st.session_state.keys()):
#     del st.session_state[key]
# print("Cleared all session state")

print("Session state cleared. Please restart the app.")
