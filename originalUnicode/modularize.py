"""
Setup script to create the modular structure for SiteCast
Run this script in your SiteCast directory to create the folder structure
and split the monolithic script into modules.
"""

import os
import shutil
from pathlib import Path


def create_folder_structure(base_path):
    """Create the folder structure for the modular SiteCast application"""

    # Define the folder structure
    folders = [
        "sitecast",
        "sitecast/core",
        "sitecast/ifc",
        "sitecast/ui",
        "sitecast/utils",
    ]

    # Create folders
    for folder in folders:
        folder_path = base_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created folder: {folder_path}")

    # Create __init__.py files for all packages
    init_files = [
        "sitecast/__init__.py",
        "sitecast/core/__init__.py",
        "sitecast/ifc/__init__.py",
        "sitecast/ui/__init__.py",
        "sitecast/utils/__init__.py",
    ]

    for init_file in init_files:
        init_path = base_path / init_file
        init_path.write_text('"""Package initialization"""', encoding="utf-8")
        print(f"✅ Created: {init_file}")


def create_config_file(base_path):
    """Create config.py with configuration constants"""
    config_content = '''"""Configuration constants and settings for SiteCast"""

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
    "marker_color": "#FF0000",
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
    "desc": ["DESCRIPTION", "DESC", "NOTE", "COMMENT", "REMARKS", "TYPE"]
}

# Unit conversion factors
CONVERSION_FACTORS = {
    ("mm", "m"): 0.001,
    ("m", "mm"): 1000.0,
    ("ft", "m"): 0.3048,
    ("m", "ft"): 3.28084,
}
'''

    config_path = base_path / "sitecast" / "config.py"
    # Write all files with UTF-8 encoding
    for path, content in [
        (config_path, config_content),
        (validators_path, validators_content),
        (processors_path, processors_content),
        (parsers_path, parsers_content),
        (builder_path, builder_content),
        (geometry_path, geometry_content),
        (materials_path, materials_content),
        (properties_path, properties_content),
        (session_path, session_content),
        (templates_path, templates_content),
        (verification_path, verification_content),
        (components_path, components_content),
        (requirements_path, requirements_content),
        (readme_path, readme_content),
    ]:
        path.write_text(content, encoding="utf-8")
    print(f"✅ Created: sitecast/config.py")


def create_core_modules(base_path):
    """Create core module files"""

    # validators.py
    validators_content = '''"""Coordinate validation and quality checks"""
import pandas as pd
from ..config import CONVERSION_FACTORS

class CoordinateValidator:
    """Handles coordinate validation and quality checks"""
    
    @staticmethod
    def detect_units(df):
        """Detect likely units based on coordinate ranges"""
        if not all(col in df.columns for col in ["N", "E", "Z"]):
            return "unknown"
            
        # Calculate ranges
        n_range = df["N"].max() - df["N"].min() if len(df) > 1 else abs(df["N"].iloc[0])
        e_range = df["E"].max() - df["E"].min() if len(df) > 1 else abs(df["E"].iloc[0])
        z_range = df["Z"].max() - df["Z"].min() if len(df) > 1 else abs(df["Z"].iloc[0])
        
        # Check coordinate magnitudes
        max_coord = max(df["N"].abs().max(), df["E"].abs().max())
        max_elevation = df["Z"].abs().max()
        
        # Conservative heuristics for unit detection
        if max_coord > 10000000:  # Very large numbers (>10M) suggest mm
            return "mm"
        elif max_coord > 100000 and max_elevation < 10000:  # UTM-style coordinates
            return "m"
        elif max_coord < 10000 and max_elevation < 1000:  # Small numbers suggest meters
            return "m"
        elif max_elevation > 10000:  # Very large elevation suggests mm
            return "mm"
        else:
            return "m"  # Default to meters
    
    @staticmethod
    def convert_units(df, from_unit, to_unit="m"):
        """Convert coordinates between units"""
        if from_unit == to_unit:
            return df.copy()
            
        factor = CONVERSION_FACTORS.get((from_unit, to_unit))
        if factor is None:
            raise ValueError(f"Conversion from {from_unit} to {to_unit} not supported")
            
        converted_df = df.copy()
        for col in ["N", "E", "Z"]:
            if col in converted_df.columns:
                converted_df[col] = converted_df[col] * factor
                
        return converted_df
    
    @staticmethod
    def validate_coordinates(df):
        """Comprehensive coordinate validation"""
        errors = []
        warnings = []
        
        # Check for required columns
        required_cols = ["N", "E", "Z"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
            return errors, warnings
            
        # Check for numeric data
        for col in required_cols:
            if not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column {col} must contain numeric values")
            elif df[col].isnull().any():
                null_count = df[col].isnull().sum()
                errors.append(f"Column {col} has {null_count} missing values")
                
        if errors:
            return errors, warnings
            
        # Check coordinate ranges (warnings only)
        n_range = df["N"].max() - df["N"].min()
        e_range = df["E"].max() - df["E"].min()
        
        if n_range > 100000 or e_range > 100000:
            warnings.append("Large coordinate range detected - verify coordinate system")
            
        if df["Z"].min() < -1000 or df["Z"].max() > 10000:
            warnings.append("Unusual elevation values detected")
            
        # Check for duplicate points
        duplicates = df[["N", "E", "Z"]].duplicated().sum()
        if duplicates > 0:
            warnings.append(f"{duplicates} duplicate coordinate points found")
            
        return errors, warnings
'''

    # processors.py
    processors_content = '''"""Survey data processing and coordinate transformations"""
import numpy as np

# Try to import sklearn for advanced north calculation
try:
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class SurveyProcessor:
    """Handles survey data processing and coordinate transformations"""
    
    def __init__(self, coord_system="Global", basepoint_n=0.0, basepoint_e=0.0, basepoint_z=0.0):
        self.coord_system = coord_system
        self.basepoint_n = basepoint_n
        self.basepoint_e = basepoint_e
        self.basepoint_z = basepoint_z
        
    def calculate_north_direction(self, df):
        """Calculate grid north from survey point distribution"""
        if len(df) < 3:
            return 0.0  # Need at least 3 points
            
        try:
            if SKLEARN_AVAILABLE:
                # Advanced method using PCA
                coords = df[["N", "E"]].values
                
                # Use PCA to find primary orientation
                pca = PCA(n_components=2)
                pca.fit(coords)
                
                # First principal component gives primary site orientation
                primary_direction = pca.components_[0]
                
                # Calculate angle from east to north direction
                north_angle = np.degrees(np.arctan2(primary_direction[0], primary_direction[1]))
                
                return north_angle
            else:
                # Simple fallback method
                n_coords = df["N"].values
                e_coords = df["E"].values
                
                # Find most northerly and southerly points
                max_n_idx = np.argmax(n_coords)
                min_n_idx = np.argmin(n_coords)
                
                # Calculate direction vector
                dn = n_coords[max_n_idx] - n_coords[min_n_idx]
                de = e_coords[max_n_idx] - e_coords[min_n_idx]
                
                # Calculate angle
                if abs(dn) > 0.001:
                    north_angle = np.degrees(np.arctan2(de, dn))
                    return north_angle
                else:
                    return 0.0
                    
        except Exception:
            return 0.0
            
    def transform_coordinates(self, df):
        """Apply coordinate transformation based on system type and basepoint"""
        transformed_df = df.copy()
        
        if self.coord_system == "Local":
            # For local coordinates, subtract basepoint
            transformed_df["N"] = df["N"] - self.basepoint_n
            transformed_df["E"] = df["E"] - self.basepoint_e
            transformed_df["Z"] = df["Z"] - self.basepoint_z
            
        return transformed_df
'''

    # parsers.py
    parsers_content = '''"""File parsing functions for various survey data formats"""
import pandas as pd
from ..config import COORDINATE_PATTERNS

def smart_parse_kof_file(file_content):
    """Smart parser for KOF format files"""
    lines = file_content.strip().split("\\n")
    parsed_data = []
    
    for line_num, line in enumerate(lines, 1):
        # Skip empty lines
        if not line.strip():
            continue
            
        # Skip disabled lines (starting with minus)
        if line.strip().startswith("-"):
            continue
            
        # Try to extract numeric data from each line
        try:
            parts = line.strip().split()
            
            # Find all numeric values
            numeric_values = []
            text_values = []
            
            for part in parts:
                try:
                    val = float(part)
                    numeric_values.append(val)
                except ValueError:
                    text_values.append(part)
                    
            # Filter out format codes
            filtered_coords = []
            for val in numeric_values:
                # Skip values that look like format codes
                if val == int(val) and 0 <= val <= 99:
                    continue
                else:
                    filtered_coords.append(val)
                    
            # Need at least 3 numeric values for coordinates
            if len(filtered_coords) >= 3:
                coord1 = filtered_coords[0]  # N
                coord2 = filtered_coords[1]  # E
                coord3 = filtered_coords[2]  # Z
                
                # Try to identify ID from text values
                potential_id = None
                description_parts = []
                
                for text in text_values:
                    if text in ["03", "05", "09", "91", "99"]:
                        continue
                    elif any(c.isalpha() for c in text) and any(c.isdigit() for c in text):
                        if potential_id is None:
                            potential_id = text
                        else:
                            description_parts.append(text)
                    else:
                        description_parts.append(text)
                        
                description = " ".join(description_parts) if description_parts else ""
                
                parsed_data.append({
                    "line_num": line_num,
                    "original_line": line.strip(),
                    "coord1": coord1,
                    "coord2": coord2,
                    "coord3": coord3,
                    "potential_id": potential_id,
                    "description": description,
                    "all_numeric": numeric_values,
                    "filtered_coords": filtered_coords,
                    "all_text": text_values,
                })
                
        except Exception:
            continue
            
    return parsed_data

def create_editable_coordinate_table(parsed_data):
    """Create an editable table for coordinate mapping"""
    if not parsed_data:
        return None
        
    table_data = []
    
    for i, data in enumerate(parsed_data):
        point_id = data["potential_id"] if data["potential_id"] else f"P{i + 1}"
        
        table_data.append({
            "ID": point_id,
            "Coord1": data["coord1"],
            "Coord2": data["coord2"],
            "Coord3": data["coord3"],
            "Description": data["description"],
            "Original_Line": data["original_line"],
        })
        
    return pd.DataFrame(table_data)

def detect_coordinate_columns(df):
    """Smart detection of coordinate columns with N,E,Z naming patterns"""
    columns = [col.upper() for col in df.columns]
    mapping = {}
    
    # Find best matches for each coordinate type
    for coord_type, patterns in COORDINATE_PATTERNS.items():
        for pattern in patterns:
            matches = [col for col in df.columns if col.upper() == pattern]
            if matches:
                mapping[coord_type.upper()] = matches[0]
                break
                
    # Fallback to first available columns if no matches
    available_cols = list(df.columns)
    if "N" not in mapping and available_cols:
        mapping["N"] = available_cols[0]
    if "E" not in mapping and len(available_cols) > 1:
        mapping["E"] = available_cols[1]
    if "Z" not in mapping and len(available_cols) > 2:
        mapping["Z"] = available_cols[2]
    if "ID" not in mapping and available_cols:
        mapping["ID"] = available_cols[0]
        
    return mapping

def apply_column_mapping(df, mapping):
    """Apply column mapping to create standardized DataFrame"""
    mapped_df = pd.DataFrame()
    
    # Apply mappings
    for standard_col, source_col in mapping.items():
        if source_col and source_col in df.columns:
            mapped_df[standard_col] = df[source_col]
            
    # Ensure required columns exist with defaults
    if "ID" not in mapped_df.columns:
        mapped_df["ID"] = range(1, len(df) + 1)
    if "Description" not in mapped_df.columns:
        mapped_df["Description"] = ""
        
    return mapped_df
'''

    # Write core module files
    validators_path = base_path / "sitecast" / "core" / "validators.py"
    validators_path.write_text(validators_content)
    print(f"✅ Created: sitecast/core/validators.py")

    processors_path = base_path / "sitecast" / "core" / "processors.py"
    processors_path.write_text(processors_content)
    print(f"✅ Created: sitecast/core/processors.py")

    parsers_path = base_path / "sitecast" / "core" / "parsers.py"
    parsers_path.write_text(parsers_content)
    print(f"✅ Created: sitecast/core/parsers.py")


def create_ifc_modules(base_path):
    """Create IFC module files"""

    # builder.py
    builder_content = '''"""IFC file creation and structure"""
import ifcopenshell
import uuid

def create_guid():
    """Create a new GUID for IFC entities"""
    return ifcopenshell.guid.compress(uuid.uuid4().hex)

def create_ifc_file(project_name, site_name, building_name, storey_name, 
                   coord_system="Global", basepoint_n=0.0, basepoint_e=0.0, basepoint_z=0.0):
    """Create a new IFC file with basic setup"""
    file = ifcopenshell.file(schema="IFC4")
    
    # Project setup
    project = file.create_entity("IfcProject", GlobalId=create_guid(), Name=project_name)
    unit_assignment = file.create_entity("IfcUnitAssignment")
    length_unit = file.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
    unit_assignment.Units = [length_unit]
    project.UnitsInContext = unit_assignment
    
    # Use (0,0,0) as world origin
    world_origin = (0.0, 0.0, 0.0)
    
    # Context setup
    context = file.create_entity(
        "IfcGeometricRepresentationContext",
        ContextIdentifier=None,
        ContextType="Model",
        CoordinateSpaceDimension=3,
        Precision=1.0e-5,
        WorldCoordinateSystem=file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity("IfcCartesianPoint", Coordinates=world_origin),
        ),
    )
    body_context = file.create_entity(
        "IfcGeometricRepresentationSubContext",
        ContextIdentifier="Body",
        ContextType="Model",
        ParentContext=context,
        TargetView="MODEL_VIEW",
    )
    
    # Hierarchy setup
    site = file.create_entity("IfcSite", GlobalId=create_guid(), Name=site_name)
    building = file.create_entity("IfcBuilding", GlobalId=create_guid(), Name=building_name)
    storey = file.create_entity("IfcBuildingStorey", GlobalId=create_guid(), Name=storey_name)
    
    # Relationships
    file.create_entity(
        "IfcRelAggregates",
        GlobalId=create_guid(),
        RelatingObject=project,
        RelatedObjects=[site],
    )
    file.create_entity(
        "IfcRelAggregates",
        GlobalId=create_guid(),
        RelatingObject=site,
        RelatedObjects=[building],
    )
    file.create_entity(
        "IfcRelAggregates",
        GlobalId=create_guid(),
        RelatingObject=building,
        RelatedObjects=[storey],
    )
    
    return file, storey, body_context
'''

    # geometry.py
    geometry_content = '''"""Geometry creation functions for IFC entities"""

def create_cone_geometry(file, context, radius=0.2, height=0.5):
    """Create a cone geometry"""
    # Create base circle profile
    circle = file.create_entity(
        "IfcCircleProfileDef",
        ProfileType="AREA",
        Radius=radius
    )
    
    # Create extrusion direction
    direction = file.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    
    # Create extruded area solid
    cone = file.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=circle,
        Position=file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)),
        ),
        ExtrudedDirection=direction,
        Depth=height,
    )
    
    return cone

def create_sphere_geometry(file, radius=0.1):
    """Create sphere geometry for coordination objects"""
    sphere = file.create_entity("IfcSphere", Radius=radius)
    return sphere
'''

    # materials.py
    materials_content = '''"""Material creation functions for IFC entities"""

def create_material(file, name, color_rgb):
    """Create a colored material"""
    color = file.create_entity(
        "IfcColourRgb",
        Name=name,
        Red=color_rgb[0],
        Green=color_rgb[1],
        Blue=color_rgb[2]
    )
    surface_style_rendering = file.create_entity(
        "IfcSurfaceStyleRendering",
        SurfaceColour=color,
        Transparency=0.0,
        ReflectanceMethod="FLAT",
    )
    surface_style = file.create_entity(
        "IfcSurfaceStyle",
        Name=f"{name} Material",
        Side="BOTH",
        Styles=[surface_style_rendering],
    )
    material = file.create_entity("IfcMaterial", Name=f"{name} Material")
    
    # Get the first representation context
    context = file.by_type("IfcRepresentationContext")[0]
    styled_representation = file.create_entity(
        "IfcStyledRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Material",
        RepresentationType="Material",
        Items=[file.create_entity("IfcStyledItem", Item=None, Styles=[surface_style])],
    )
    file.create_entity(
        "IfcMaterialDefinitionRepresentation",
        Representations=[styled_representation],
        RepresentedMaterial=material,
    )
    return material

def create_coordination_material(file):
    """Create a special material for coordination objects (blue)"""
    return create_material(file, "Coordination", (0.0, 0.5, 1.0))
'''

    # properties.py
    properties_content = '''"""Property set creation functions"""
from .builder import create_guid

def create_enhanced_property_set(file, survey_point, point_data, pset_name,
                               custom_properties, original_coords, local_coords,
                               offsets, source_filename, creator_name, external_link):
    """Create enhanced property set with coordinates and custom properties"""
    properties = []
    
    # Source information
    prop_source = file.create_entity(
        "IfcPropertySingleValue",
        Name="Source",
        NominalValue=file.create_entity("IfcText", source_filename),
    )
    properties.append(prop_source)
    
    prop_creator = file.create_entity(
        "IfcPropertySingleValue",
        Name="Created_By",
        NominalValue=file.create_entity("IfcText", creator_name),
    )
    properties.append(prop_creator)
    
    # Point ID
    prop_point_id = file.create_entity(
        "IfcPropertySingleValue",
        Name="Point_ID",
        NominalValue=file.create_entity("IfcText", str(point_data.get("ID", "Unknown"))),
    )
    properties.append(prop_point_id)
    
    # Original coordinates
    prop_northing = file.create_entity(
        "IfcPropertySingleValue",
        Name="Northing_Y",
        NominalValue=file.create_entity("IfcReal", float(original_coords["N"])),
        Unit=file.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE"),
    )
    properties.append(prop_northing)
    
    prop_easting = file.create_entity(
        "IfcPropertySingleValue",
        Name="Easting_X",
        NominalValue=file.create_entity("IfcReal", float(original_coords["E"])),
        Unit=file.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE"),
    )
    properties.append(prop_easting)
    
    prop_altitude = file.create_entity(
        "IfcPropertySingleValue",
        Name="Altitude_Z",
        NominalValue=file.create_entity("IfcReal", float(original_coords["Z"])),
        Unit=file.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE"),
    )
    properties.append(prop_altitude)
    
    # Offsets
    prop_offsets = file.create_entity(
        "IfcPropertySingleValue",
        Name="Offsets",
        NominalValue=file.create_entity(
            "IfcText",
            f"[N:{offsets['N']:.3f}, E:{offsets['E']:.3f}, Z:{offsets['Z']:.3f}]",
        ),
    )
    properties.append(prop_offsets)
    
    # Local coordinates
    prop_local_coords = file.create_entity(
        "IfcPropertySingleValue",
        Name="Local_Coordinates",
        NominalValue=file.create_entity(
            "IfcText",
            f"[N:{local_coords['N']:.3f}, E:{local_coords['E']:.3f}, Z:{local_coords['Z']:.3f}]",
        ),
    )
    properties.append(prop_local_coords)
    
    # Add custom properties
    for custom_prop in custom_properties:
        if custom_prop["name"] and custom_prop["value"]:
            prop_custom = file.create_entity(
                "IfcPropertySingleValue",
                Name=custom_prop["name"].replace(" ", "_"),
                NominalValue=file.create_entity("IfcText", str(custom_prop["value"])),
            )
            properties.append(prop_custom)
            
    # External link if provided
    if external_link:
        prop_link = file.create_entity(
            "IfcPropertySingleValue",
            Name="External_Link",
            NominalValue=file.create_entity("IfcText", external_link),
        )
        properties.append(prop_link)
        
    # Create the property set
    property_set = file.create_entity(
        "IfcPropertySet",
        GlobalId=create_guid(),
        Name=pset_name,
        HasProperties=properties,
    )
    
    # Attach to survey point
    file.create_entity(
        "IfcRelDefinesByProperties",
        GlobalId=create_guid(),
        RelatedObjects=[survey_point],
        RelatingPropertyDefinition=property_set,
    )
    
    return property_set
'''

    # Write IFC module files
    builder_path = base_path / "sitecast" / "ifc" / "builder.py"
    builder_path.write_text(builder_content)
    print(f"✅ Created: sitecast/ifc/builder.py")

    geometry_path = base_path / "sitecast" / "ifc" / "geometry.py"
    geometry_path.write_text(geometry_content)
    print(f"✅ Created: sitecast/ifc/geometry.py")

    materials_path = base_path / "sitecast" / "ifc" / "materials.py"
    materials_path.write_text(materials_content)
    print(f"✅ Created: sitecast/ifc/materials.py")

    properties_path = base_path / "sitecast" / "ifc" / "properties.py"
    properties_path.write_text(properties_content)
    print(f"✅ Created: sitecast/ifc/properties.py")


def create_utils_modules(base_path):
    """Create utility module files"""

    # session.py
    session_content = '''"""Session state management for Streamlit"""
import streamlit as st
from ..config import DEFAULTS

def initialize_session_state():
    """Initialize session state with default values"""
    for key, default_value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
'''

    # templates.py
    templates_content = '''"""Excel template generation utilities"""
import pandas as pd
import io

# Check if openpyxl is available
try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

def create_excel_template():
    """Create a template Excel file for survey data input"""
    if not EXCEL_SUPPORT:
        return None
        
    # Sample data for the template
    template_data = {
        "ID": ["SP001", "SP002", "SP003", "CP001", "BM001"],
        "N_Northing": [82692.090, 82687.146, 82673.960, 82667.760, 82711.966],
        "E_Easting": [1194257.404, 1194250.859, 1194233.405, 1194225.198, 1194245.717],
        "Z_Elevation": [2.075, 2.295, 2.286, 2.298, 1.890],
        "Description": ["Survey Point 1", "Survey Point 2", "Survey Point 3", 
                       "Control Point", "Benchmark"],
        "Type": ["Survey", "Survey", "Survey", "Control", "Benchmark"],
        "Date_Surveyed": ["2024-01-15", "2024-01-15", "2024-01-15", 
                         "2024-01-10", "2024-01-10"],
        "Accuracy_mm": [5, 5, 5, 2, 2],
    }
    
    df = pd.DataFrame(template_data)
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Write the template data
            df.to_excel(writer, sheet_name="Survey_Points", index=False)
            
            # Add instructions sheet
            instructions = pd.DataFrame({
                "Instructions": [
                    "1. Fill out the Survey_Points sheet with your coordinate data",
                    "2. Required columns: ID, N_Northing, E_Easting, Z_Elevation",
                    "3. Optional columns: Description, Type, Date_Surveyed, Accuracy_mm",
                    "4. You can add more rows as needed",
                    "5. Keep column headers exactly as shown",
                    "6. Use consistent coordinate system (UTM recommended)",
                    "7. Save and upload the completed file to SiteCast",
                    "",
                    "Column Descriptions:",
                    "ID - Unique point identifier",
                    "N_Northing - Northing coordinate in meters",
                    "E_Easting - Easting coordinate in meters",
                    "Z_Elevation - Elevation in meters",
                    "Description - Point description or notes",
                    "Type - Point type (Survey, Control, Benchmark, etc.)",
                    "Date_Surveyed - Date when point was surveyed",
                    "Accuracy_mm - Survey accuracy in millimeters",
                    "",
                    "NOTE: Coordinate order is N,E,Z (North, East, Elevation)",
                ]
            })
            instructions.to_excel(writer, sheet_name="Instructions", index=False)
            
            # Format the Survey_Points sheet
            workbook = writer.book
            worksheet = writer.sheets["Survey_Points"]
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 20)
                worksheet.column_dimensions[column_letter].width = adjusted_width
                
        output.seek(0)
        return output.getvalue()
    except Exception:
        return None

def process_excel_file(uploaded_file):
    """Process uploaded Excel file"""
    if not EXCEL_SUPPORT:
        raise Exception("Excel support not available. Install openpyxl")
        
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0)
        return df
    except Exception as e:
        raise Exception(f"Error reading Excel file: {str(e)}")
'''

    # verification.py
    verification_content = '''"""Coordinate verification utilities"""
import ifcopenshell
import os

def verify_ifc_coordinates(ifc_file_path, original_data, offsets):
    """Verify that IFC coordinates match original data"""
    try:
        # Read the IFC file back
        ifc_file = ifcopenshell.open(ifc_file_path)
        
        # Find all survey points
        survey_points = ifc_file.by_type("IfcBuildingElementProxy")
        
        verification_results = []
        
        for point in survey_points:
            if "Survey Point" in (point.Name or ""):
                # Get local coordinates from placement
                placement = point.ObjectPlacement
                if placement and placement.RelativePlacement:
                    location = placement.RelativePlacement.Location
                    if location and hasattr(location, "Coordinates"):
                        local_x, local_y, local_z = location.Coordinates
                        
                        # Convert back to N,E,Z
                        local_e = local_x
                        local_n = local_y
                        local_z_val = local_z
                        
                        # Calculate original coordinates
                        calc_n = local_n + offsets["N"]
                        calc_e = local_e + offsets["E"]
                        calc_z = local_z_val + offsets["Z"]
                        
                        # Find corresponding original point
                        point_id = point.Name.replace("Survey Point ", "") if point.Name else "Unknown"
                        
                        # Find matching point in original data
                        matching_point = None
                        for _, row in original_data.iterrows():
                            if str(row.get("ID", "")) == point_id:
                                matching_point = row
                                break
                                
                        if matching_point is not None:
                            orig_n = float(matching_point["N"])
                            orig_e = float(matching_point["E"])
                            orig_z = float(matching_point["Z"])
                            
                            # Check if coordinates match
                            tolerance = 0.001  # 1mm tolerance
                            n_match = abs(calc_n - orig_n) < tolerance
                            e_match = abs(calc_e - orig_e) < tolerance
                            z_match = abs(calc_z - orig_z) < tolerance
                            
                            verification_results.append({
                                "point_id": point_id,
                                "original": {"N": orig_n, "E": orig_e, "Z": orig_z},
                                "calculated": {"N": calc_n, "E": calc_e, "Z": calc_z},
                                "local": {"N": local_n, "E": local_e, "Z": local_z_val},
                                "matches": {"N": n_match, "E": e_match, "Z": z_match},
                                "all_match": n_match and e_match and z_match,
                            })
                            
        return verification_results
        
    except Exception as e:
        return f"Verification failed: {str(e)}"
'''

    # Write utils module files
    session_path = base_path / "sitecast" / "utils" / "session.py"
    session_path.write_text(session_content)
    print(f"✅ Created: sitecast/utils/session.py")

    templates_path = base_path / "sitecast" / "utils" / "templates.py"
    templates_path.write_text(templates_content)
    print(f"✅ Created: sitecast/utils/templates.py")

    verification_path = base_path / "sitecast" / "utils" / "verification.py"
    verification_path.write_text(verification_content)
    print(f"✅ Created: sitecast/utils/verification.py")


def create_ui_modules(base_path):
    """Create UI module files - Part 1 (components.py)"""

    # components.py
    components_content = '''"""Reusable UI components"""
import streamlit as st
from ..ifc.builder import create_guid
from ..ifc.geometry import create_cone_geometry, create_sphere_geometry
from ..ifc.properties import create_enhanced_property_set

def create_enhanced_survey_point(file, storey, context, point_data, material,
                               original_coords, local_coords, offsets, pset_name,
                               custom_properties, source_filename, creator_name="SiteCast",
                               external_link=""):
    """Create a survey point element with enhanced property sets"""
    point_id = point_data.get("ID", "Unknown")
    n = float(point_data.get("N", 0))
    e = float(point_data.get("E", 0))
    z = float(point_data.get("Z", 0))
    description = point_data.get("Description", "")
    
    # Create cone geometry
    cone = create_cone_geometry(file, context)
    
    # Create shape representation
    shape_representation = file.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[cone],
    )
    
    # Create product definition shape
    product_shape = file.create_entity(
        "IfcProductDefinitionShape",
        Representations=[shape_representation]
    )
    
    # Create local placement
    local_placement = file.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity("IfcCartesianPoint", Coordinates=(e, n, z)),
        ),
    )
    
    # Create building element proxy
    survey_point = file.create_entity(
        "IfcBuildingElementProxy",
        GlobalId=create_guid(),
        Name=f"Survey Point {point_id}",
        Description=description,
        ObjectPlacement=local_placement,
        Representation=product_shape,
    )
    
    # Create containment relationship
    file.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=create_guid(),
        RelatingStructure=storey,
        RelatedElements=[survey_point],
    )
    
    # Create enhanced property set
    create_enhanced_property_set(
        file, survey_point, point_data, pset_name,
        custom_properties, original_coords, local_coords,
        offsets, source_filename, creator_name, external_link
    )
    
    return survey_point

def create_coordination_object(file, storey, context, name, n, e, z, material, description="Coordination Point"):
    """Create a coordination object (small sphere) at specified coordinates"""
    # Create sphere geometry
    sphere = create_sphere_geometry(file, radius=0.1)
    
    # Create shape representation
    shape_representation = file.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Body",
        RepresentationType="CSG",
        Items=[sphere],
    )
    
    # Create product definition shape
    product_shape = file.create_entity(
        "IfcProductDefinitionShape",
        Representations=[shape_representation]
    )
    
    # Create local placement
    local_placement = file.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity("IfcCartesianPoint", Coordinates=(e, n, z)),
        ),
    )
    
    # Create building element proxy
    coord_object = file.create_entity(
        "IfcBuildingElementProxy",
        GlobalId=create_guid(),
        Name=name,
        Description=description,
        ObjectPlacement=local_placement,
        Representation=product_shape,
    )
    
    # Create containment relationship
    file.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=create_guid(),
        RelatingStructure=storey,
        RelatedElements=[coord_object],
    )
    
    # Create custom properties
    properties = []
    prop_type = file.create_entity(
        "IfcPropertySingleValue",
        Name="Object Type",
        NominalValue=file.create_entity("IfcText", "Coordination Object"),
    )
    properties.append(prop_type)
    
    prop_coords = file.create_entity(
        "IfcPropertySingleValue",
        Name="Coordinates",
        NominalValue=file.create_entity("IfcText", f"N:{n:.3f}, E:{e:.3f}, Z:{z:.3f}"),
    )
    properties.append(prop_coords)
    
    property_set = file.create_entity(
        "IfcPropertySet",
        GlobalId=create_guid(),
        Name="Coordination_Properties",
        HasProperties=properties,
    )
    file.create_entity(
        "IfcRelDefinesByProperties",
        GlobalId=create_guid(),
        RelatedObjects=[coord_object],
        RelatingPropertyDefinition=property_set,
    )
    
    return coord_object
'''

    # Write components.py
    components_path = base_path / "sitecast" / "ui" / "components.py"
    components_path.write_text(components_content)
    print(f"✅ Created: sitecast/ui/components.py")


def create_ui_modules_part2(base_path):
    """Create UI module files - Part 2 (sidebar, upload, mapping, export)"""

    # Create placeholder files - these would contain the full UI code
    ui_files = {
        "sidebar.py": "# UI sidebar module - see modularized code artifact for full implementation",
        "upload.py": "# UI upload module - see modularized code artifact for full implementation",
        "mapping.py": "# UI mapping module - see modularized code artifact for full implementation",
        "export.py": "# UI export module - see modularized code artifact for full implementation",
    }

    for filename, content in ui_files.items():
        file_path = base_path / "sitecast" / "ui" / filename
        file_path.write_text(content)
        print(f"✅ Created: sitecast/ui/{filename} (placeholder)")


def create_main_file(base_path):
    """Create the main.py entry point"""

    main_content = '''"""Main Streamlit application entry point for SiteCast"""
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
'''

    main_path = base_path / "main.py"
    main_path.write_text(main_content, encoding="utf-8")
    print(f"✅ Created: main.py")


def create_requirements_file(base_path):
    """Create requirements.txt file"""

    requirements_content = """streamlit>=1.28.0
pandas>=2.0.0
ifcopenshell>=0.7.0
numpy>=1.24.0
scikit-learn>=1.3.0
openpyxl>=3.1.0
"""

    requirements_path = base_path / "requirements.txt"
    requirements_path.write_text(requirements_content)
    print(f"✅ Created: requirements.txt")


def create_readme_file(base_path):
    """Create README.md file"""

    readme_content = """# SiteCast - Survey to BIM Converter

Convert survey data to BIM-ready IFC files in 30 seconds.

## Features

- Support for CSV, Excel (XLSX/XLS), and KOF formats
- Automatic coordinate system detection
- Unit conversion (meters, millimeters, feet)
- Project basepoint and rotation point support
- Custom property sets for survey points
- Coordinate verification
- IFC4 output format

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the Streamlit app:
```bash
streamlit run main.py
```

## Project Structure

```
sitecast/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── sitecast/           # Main package
│   ├── config.py       # Configuration
│   ├── core/           # Core logic
│   ├── ifc/            # IFC generation
│   ├── ui/             # User interface
│   └── utils/          # Utilities
```

## License

[Your License Here]
"""

    readme_path = base_path / "README.md"
    readme_path.write_text(readme_content)
    print(f"✅ Created: README.md")


def main():
    """Main function to set up the SiteCast modular structure"""

    # Get the base path
    base_path = Path(r"C:\LokalMappe_Blade15\CodingProjects\SiteCast")

    print("🚀 Setting up SiteCast modular structure...")
    print(f"📁 Base directory: {base_path}")

    # Check if original file exists (optional)
    original_file = base_path / "sitecast_app.py"
    if original_file.exists():
        print(f"📄 Found original file: {original_file.name}")
        # Optionally backup the original file
        backup_file = base_path / "sitecast_app_backup.py"
        if not backup_file.exists():
            shutil.copy(original_file, backup_file)
            print(f"📋 Created backup: {backup_file.name}")

    # Create all components
    create_folder_structure(base_path)
    create_config_file(base_path)
    create_core_modules(base_path)
    create_ifc_modules(base_path)
    create_utils_modules(base_path)
    create_ui_modules(base_path)
    create_ui_modules_part2(base_path)
    create_main_file(base_path)
    create_requirements_file(base_path)
    create_readme_file(base_path)

    print("\n✨ Setup complete! Your modular SiteCast structure is ready.")
    print("\n📝 Next steps:")
    print(
        "1. Copy the full UI module implementations from the modularized code artifact"
    )
    print("2. Test the application with: streamlit run main.py")
    print("3. Consider adding unit tests in a tests/ directory")

    print(
        "\n⚠️  Note: The UI module files (sidebar.py, upload.py, mapping.py, export.py)"
    )
    print("    contain placeholders. Copy the full implementations from the artifact.")


if __name__ == "__main__":
    main()
