"""
Fix for the color selection error in SiteCast
"""

from pathlib import Path


def fix_session_defaults(base_path):
    """Update session.py to use color names instead of hex values"""

    session_content = '''"""Session state management for Streamlit with enhanced persistence"""
import streamlit as st
from ..config import DEFAULTS

def initialize_session_state():
    """Initialize session state with default values"""
    # Handle legacy color format conversion
    if 'marker_color' in st.session_state:
        # Convert hex colors to names if needed
        hex_to_name = {
            "#FF0000": "Red",
            "#FF00FF": "Magenta", 
            "#008080": "Teal",
            "#808080": "Gray",
            "#FFFF00": "Yellow"
        }
        if st.session_state.marker_color in hex_to_name:
            st.session_state.marker_color = hex_to_name[st.session_state.marker_color]
    
    for key, default_value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
            
    # Add file persistence keys
    if 'uploaded_file_data' not in st.session_state:
        st.session_state.uploaded_file_data = None
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None
    if 'uploaded_file_type' not in st.session_state:
        st.session_state.uploaded_file_type = None
    if 'preserve_file_state' not in st.session_state:
        st.session_state.preserve_file_state = False
'''

    session_path = base_path / "sitecast" / "utils" / "session.py"
    with open(session_path, "w", encoding="utf-8") as f:
        f.write(session_content)
    print(f"✅ Fixed: sitecast/utils/session.py")


def fix_config_defaults(base_path):
    """Update config.py to use color name in defaults"""

    config_path = base_path / "sitecast" / "config.py"

    # Read existing content
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace the marker_color default
    content = content.replace('"marker_color": "#FF0000"', '"marker_color": "Red"')

    # Write back
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Fixed: sitecast/config.py")


def fix_marker_configuration_error_handling(base_path):
    """Add better error handling to marker_configuration.py"""

    content = '''"""Marker configuration UI component"""
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
        current_shape = st.session_state.get("marker_shape", DEFAULT_MARKER_SETTINGS["marker_shape"])
        if current_shape not in MARKER_SHAPES:
            current_shape = DEFAULT_MARKER_SETTINGS["marker_shape"]
            
        marker_shape = st.selectbox(
            "Marker Shape",
            options=MARKER_SHAPES,
            index=MARKER_SHAPES.index(current_shape),
            key="marker_shape"
        )
        
        # Color selection - with error handling for legacy hex values
        current_color = st.session_state.get("marker_color", DEFAULT_MARKER_SETTINGS["marker_color"])
        
        # Handle legacy hex color values
        hex_to_name = {
            "#FF0000": "Red",
            "#FF00FF": "Magenta",
            "#008080": "Teal",
            "#808080": "Gray",
            "#FFFF00": "Yellow"
        }
        
        if current_color in hex_to_name:
            current_color = hex_to_name[current_color]
        elif current_color not in MARKER_COLORS:
            current_color = DEFAULT_MARKER_SETTINGS["marker_color"]
            
        marker_color_name = st.selectbox(
            "Marker Color",
            options=list(MARKER_COLORS.keys()),
            index=list(MARKER_COLORS.keys()).index(current_color),
            key="marker_color"
        )
        
        # Dimension controls
        marker_height = st.slider(
            "Height (m)",
            min_value=0.1,
            max_value=2.0,
            value=st.session_state.get("marker_height", DEFAULT_MARKER_SETTINGS["marker_height"]),
            step=0.1,
            key="marker_height"
        )
        
        marker_diameter = st.slider(
            "Diameter/Width (m)",
            min_value=0.05,
            max_value=0.5,
            value=st.session_state.get("marker_diameter", DEFAULT_MARKER_SETTINGS["marker_diameter"]),
            step=0.05,
            key="marker_diameter"
        )
        
        # Orientation option
        if marker_shape in ["Cone", "Pyramid"]:
            use_inverted = st.checkbox(
                "Inverted (pointing down)",
                value=st.session_state.get("use_inverted", DEFAULT_MARKER_SETTINGS["use_inverted"]),
                key="use_inverted"
            )
        else:
            use_inverted = False
    
    with col2:
        # Live preview
        st.write("**Preview**")
        
        if st.session_state.get("show_preview", DEFAULT_MARKER_SETTINGS["show_preview"]):
            # Get color RGB
            color_rgb = MARKER_COLORS[marker_color_name]
            
            # Create and display preview
            try:
                fig = create_marker_preview(
                    marker_shape,
                    color_rgb,
                    marker_height,
                    marker_diameter,
                    use_inverted
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
        "inverted": use_inverted
    }
'''

    path = base_path / "sitecast" / "ui" / "marker_configuration.py"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Fixed: sitecast/ui/marker_configuration.py")


def clear_problematic_session_state():
    """Create a utility script to clear problematic session state"""

    clear_script = '''"""
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
'''

    with open("clear_session.py", "w", encoding="utf-8") as f:
        f.write(clear_script)
    print(f"✅ Created: clear_session.py (utility script)")


def main():
    """Fix the color selection error"""
    base_path = Path(r"C:\LokalMappe_Blade15\CodingProjects\SiteCast")

    print("🔧 Fixing color selection error...")
    print(f"📁 Base directory: {base_path}")

    # Apply fixes
    fix_session_defaults(base_path)
    fix_config_defaults(base_path)
    fix_marker_configuration_error_handling(base_path)
    clear_problematic_session_state()

    print("\n✨ Fixes applied successfully!")
    print("\n📝 If the error persists:")
    print("1. Run: streamlit run clear_session.py")
    print("2. Then run: streamlit run main.py")
    print("\nThis will clear any problematic session state values.")


if __name__ == "__main__":
    main()
