"""Configuration constants and settings for SiteCast"""

# File format support
SUPPORTED_FORMATS = ["csv", "kof", "xlsx", "xls"]

# Default values
DEFAULTS = {
    "project_name": "Survey Project",
    "site_name": "Project Site",
    "building_name": "Survey Building",
    "storey_name": "Survey Level",
    "coord_system": "Local",
    "coordinate_units": "m (meters)",
    "auto_detect_units": True,
    "use_basepoint": True,
    "basepoint_n": 0.0,
    "basepoint_e": 0.0,
    "basepoint_z": 0.0,
    "use_rotation_point": False,
    "rotation_n": 0.0,
    "rotation_e": 0.0,
    "rotation_z": 0.0,
    "marker_color": "Red",
    "creator_name": "SiteCast User",
    "external_link": "",
    "parsed_data": None,
    "mapped_df": None,
    "pset_name": "NOSC_SiteCast",
    "verify_coordinates": True,
    "custom_properties": [
        {"name": "Coordinate_System", "value": "EUREF89_NTM10"},
        {"name": "Survey_Method", "value": "Total_Station"},
        {"name": "Accuracy_Class", "value": "Class_1"},
    ],
}

# Coordinate patterns for detection
COORDINATE_PATTERNS = {
    "n": ["N", "NORTHING", "NORTH", "Y", "LATITUDE", "LAT"],
    "e": ["E", "EASTING", "EAST", "X", "LONGITUDE", "LON", "LONG"],
    "z": ["Z", "ELEVATION", "ELEV", "HEIGHT", "H", "ALT", "ALTITUDE"],
    "id": ["ID", "POINT_ID", "POINTID", "NAME", "NUMBER", "NUM", "PT"],
    "desc": ["DESCRIPTION", "DESC", "NOTE", "COMMENT", "REMARKS", "TYPE"],
}

# Unit conversion factors
CONVERSION_FACTORS = {
    ("mm", "m"): 0.001,
    ("m", "mm"): 1000.0,
    ("ft", "m"): 0.3048,
    ("m", "ft"): 3.28084,
}


# Marker shape options
MARKER_SHAPES = ["Cone", "Pyramid", "Cylinder", "Sphere", "Pie Slice", "Hollow Cylinder", "North Arrow"]

# Color options with RGB values
MARKER_COLORS = {
    "Red": (1.0, 0.0, 0.0),
    "Magenta": (1.0, 0.0, 1.0),
    "Teal": (0.0, 0.5, 0.5),
    "Gray": (0.5, 0.5, 0.5),
    "Yellow": (1.0, 1.0, 0.0),
}

# Default marker settings
DEFAULT_MARKER_SETTINGS = {
    "marker_shape": "Cone",
    "marker_color": "Red",
    "marker_height": 0.5,
    "marker_diameter": 0.2,
    "use_inverted": True,
    "show_preview": True,
}

# Information cube settings
INFO_CUBE_SETTINGS = {
    "use_info_cube": False,
    "cube_size": 2.0,
    "cube_elevation": 10.0,
    "cube_links": [
        {"name": "Project Documentation", "url": "https://example.com/docs"},
        {"name": "Survey Report", "url": "https://example.com/report"},
    ],
}
