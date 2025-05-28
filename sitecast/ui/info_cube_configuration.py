"""Information cube configuration UI"""

import streamlit as st
from ..config import INFO_CUBE_SETTINGS


def create_info_cube_configuration():
    """Create the information cube configuration UI"""
    st.subheader("📦 Information Cube")

    use_info_cube = st.checkbox(
        "Add Information Cube above Nullpunkt",
        value=st.session_state.get(
            "use_info_cube", INFO_CUBE_SETTINGS["use_info_cube"]
        ),
        key="use_info_cube",
        help="Adds a cube above the basepoint with project information",
    )

    if use_info_cube:
        col1, col2 = st.columns(2)

        with col1:
            cube_size = st.slider(
                "Cube Size (m)",
                min_value=1.0,
                max_value=5.0,
                value=st.session_state.get(
                    "cube_size", INFO_CUBE_SETTINGS["cube_size"]
                ),
                step=0.5,
                key="cube_size",
            )

        with col2:
            cube_elevation = st.slider(
                "Elevation above ground (m)",
                min_value=5.0,
                max_value=20.0,
                value=st.session_state.get(
                    "cube_elevation", INFO_CUBE_SETTINGS["cube_elevation"]
                ),
                step=1.0,
                key="cube_elevation",
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
                    f"Name {i + 1}", value=link["name"], key=f"link_name_{i}"
                )
            with col2:
                link["url"] = st.text_input(
                    f"URL {i + 1}", value=link["url"], key=f"link_url_{i}"
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
                st.session_state.info_cube_links.append(
                    {"name": new_name, "url": new_url}
                )
                st.success(f"Added link: {new_name}")
                st.rerun()

    return {
        "enabled": use_info_cube,
        "size": st.session_state.get("cube_size", INFO_CUBE_SETTINGS["cube_size"]),
        "elevation": st.session_state.get(
            "cube_elevation", INFO_CUBE_SETTINGS["cube_elevation"]
        ),
        "links": st.session_state.get("info_cube_links", []),
    }
