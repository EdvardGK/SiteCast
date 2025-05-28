"""Marker configuration UI component"""

import streamlit as st
from ..config import MARKER_SHAPES, MARKER_COLORS, DEFAULT_MARKER_SETTINGS
from .marker_preview import create_marker_preview
import matplotlib.pyplot as plt


def create_marker_configuration():
    """Create the marker configuration UI section"""
    st.subheader("🔻 Survey Marker Style")

    col1, col2 = st.columns([1, 1])

    with col1:
        # Shape selection
        current_shape = st.session_state.get(
            "marker_shape", DEFAULT_MARKER_SETTINGS["marker_shape"]
        )
        if current_shape not in MARKER_SHAPES:
            current_shape = DEFAULT_MARKER_SETTINGS["marker_shape"]

        marker_shape = st.selectbox(
            "Marker Shape",
            options=MARKER_SHAPES,
            index=MARKER_SHAPES.index(current_shape),
            key="marker_shape",
        )

        # Color selection - with error handling for legacy hex values
        current_color = st.session_state.get(
            "marker_color", DEFAULT_MARKER_SETTINGS["marker_color"]
        )

        # Handle legacy hex color values
        hex_to_name = {
            "#FF0000": "Red",
            "#FF00FF": "Magenta",
            "#008080": "Teal",
            "#808080": "Gray",
            "#FFFF00": "Yellow",
        }

        if current_color in hex_to_name:
            current_color = hex_to_name[current_color]
        elif current_color not in MARKER_COLORS:
            current_color = DEFAULT_MARKER_SETTINGS["marker_color"]

        marker_color_name = st.selectbox(
            "Marker Color",
            options=list(MARKER_COLORS.keys()),
            index=list(MARKER_COLORS.keys()).index(current_color),
            key="marker_color",
        )

        # Dimension controls
        marker_height = st.slider(
            "Height (m)",
            min_value=0.1,
            max_value=2.0,
            value=st.session_state.get(
                "marker_height", DEFAULT_MARKER_SETTINGS["marker_height"]
            ),
            step=0.1,
            key="marker_height",
        )

        marker_diameter = st.slider(
            "Diameter/Width (m)",
            min_value=0.05,
            max_value=0.5,
            value=st.session_state.get(
                "marker_diameter", DEFAULT_MARKER_SETTINGS["marker_diameter"]
            ),
            step=0.05,
            key="marker_diameter",
        )

        # Orientation option
        if marker_shape in ["Cone", "Pyramid"]:
            use_inverted = st.checkbox(
                "Inverted (pointing down)",
                value=st.session_state.get(
                    "use_inverted", DEFAULT_MARKER_SETTINGS["use_inverted"]
                ),
                key="use_inverted",
            )
        else:
            use_inverted = False
            # For non-invertible shapes, store false in session state
            st.session_state["use_inverted"] = False

    with col2:
        # Live preview
        st.write("**Preview**")

        if st.session_state.get(
            "show_preview", DEFAULT_MARKER_SETTINGS["show_preview"]
        ):
            # Get color RGB
            color_rgb = MARKER_COLORS[marker_color_name]

            # Create and display preview
            try:
                fig = create_marker_preview(
                    marker_shape,
                    color_rgb,
                    marker_height,
                    marker_diameter,
                    use_inverted,
                )
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)  # Clean up
            except Exception as e:
                st.error(f"Preview error: {str(e)}")
                st.info("Make sure matplotlib is installed: pip install matplotlib")

            # Preview info
            st.caption(f"Shape: {marker_shape}")
            st.caption(f"Color: {marker_color_name}")
            st.caption(f"Dimensions: {marker_height:.1f}m × {marker_diameter:.1f}m")

    return {
        "shape": marker_shape,
        "color": marker_color_name,
        "height": marker_height,
        "diameter": marker_diameter,
        "inverted": use_inverted,
    }
