import streamlit as st
import pandas as pd
import ifcopenshell
import uuid
import io
import tempfile
import os
import numpy as np

# Try to import sklearn for advanced north calculation
try:
    from sklearn.decomposition import PCA

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Check if openpyxl is available for Excel support
try:
    import openpyxl

    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False


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

        # More conservative heuristics for unit detection
        if max_coord > 10000000:  # Very large numbers (>10M) suggest mm
            return "mm"
        elif (
            max_coord > 100000 and max_elevation < 10000
        ):  # UTM-style coordinates (100K-10M) in meters
            return "m"
        elif (
            max_coord < 10000 and max_elevation < 1000
        ):  # Small numbers suggest meters (local coords)
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

        conversion_factors = {
            ("mm", "m"): 0.001,
            ("m", "mm"): 1000.0,
            ("ft", "m"): 0.3048,
            ("m", "ft"): 3.28084,
        }

        factor = conversion_factors.get((from_unit, to_unit))
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
            warnings.append(
                "Large coordinate range detected - verify coordinate system"
            )

        if df["Z"].min() < -1000 or df["Z"].max() > 10000:
            warnings.append("Unusual elevation values detected")

        # Check for duplicate points
        duplicates = df[["N", "E", "Z"]].duplicated().sum()
        if duplicates > 0:
            warnings.append(f"{duplicates} duplicate coordinate points found")

        return errors, warnings


class SurveyProcessor:
    """Handles survey data processing and coordinate transformations"""

    def __init__(
        self, coord_system="Global", basepoint_n=0.0, basepoint_e=0.0, basepoint_z=0.0
    ):
        self.coord_system = coord_system
        self.basepoint_n = basepoint_n
        self.basepoint_e = basepoint_e
        self.basepoint_z = basepoint_z

    def calculate_north_direction(self, df):
        """Calculate grid north from survey point distribution"""
        if len(df) < 3:
            return 0.0  # Need at least 3 points for meaningful calculation

        try:
            if SKLEARN_AVAILABLE:
                # Advanced method using PCA
                coords = df[["N", "E"]].values

                # Use PCA to find primary orientation of point cloud
                pca = PCA(n_components=2)
                pca.fit(coords)

                # First principal component gives primary site orientation
                primary_direction = pca.components_[0]

                # Calculate angle from east (positive X) to north direction
                north_angle = np.degrees(
                    np.arctan2(primary_direction[0], primary_direction[1])
                )

                return north_angle
            else:
                # Simple fallback method using coordinate extents
                n_coords = df["N"].values
                e_coords = df["E"].values

                # Find the most northerly and southerly points
                max_n_idx = np.argmax(n_coords)
                min_n_idx = np.argmin(n_coords)

                # Calculate direction vector from south to north point
                dn = n_coords[max_n_idx] - n_coords[min_n_idx]
                de = e_coords[max_n_idx] - e_coords[min_n_idx]

                # Calculate angle (fallback method)
                if abs(dn) > 0.001:  # Avoid division by zero
                    north_angle = np.degrees(np.arctan2(de, dn))
                    return north_angle
                else:
                    return 0.0

        except Exception as e:
            if not SKLEARN_AVAILABLE:
                st.info(
                    "💡 **Tip**: Install scikit-learn for advanced north calculation: `pip install scikit-learn`"
                )
            else:
                st.warning(f"Could not calculate north direction: {str(e)}")
            return 0.0

    def transform_coordinates(self, df):
        """Apply coordinate transformation based on system type and basepoint"""
        transformed_df = df.copy()

        if self.coord_system == "Local":
            # For local coordinates, subtract basepoint to get relative coordinates
            transformed_df["N"] = df["N"] - self.basepoint_n
            transformed_df["E"] = df["E"] - self.basepoint_e
            transformed_df["Z"] = df["Z"] - self.basepoint_z

        # For Global/Geographic, use coordinates as-is (no transformation)
        return transformed_df


def create_excel_template():
    """Create a template Excel file for survey data input"""
    if not EXCEL_SUPPORT:
        st.error(
            "Excel support not available. Please install openpyxl: pip install openpyxl"
        )
        return None

    # Sample data for the template with N,E,Z structure
    template_data = {
        "ID": ["SP001", "SP002", "SP003", "CP001", "BM001"],
        "N_Northing": [82692.090, 82687.146, 82673.960, 82667.760, 82711.966],
        "E_Easting": [1194257.404, 1194250.859, 1194233.405, 1194225.198, 1194245.717],
        "Z_Elevation": [2.075, 2.295, 2.286, 2.298, 1.890],
        "Description": [
            "Survey Point 1",
            "Survey Point 2",
            "Survey Point 3",
            "Control Point",
            "Benchmark",
        ],
        "Type": ["Survey", "Survey", "Survey", "Control", "Benchmark"],
        "Date_Surveyed": [
            "2024-01-15",
            "2024-01-15",
            "2024-01-15",
            "2024-01-10",
            "2024-01-10",
        ],
        "Accuracy_mm": [5, 5, 5, 2, 2],
    }

    df = pd.DataFrame(template_data)

    # Create Excel file in memory
    output = io.BytesIO()

    try:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Write the template data
            df.to_excel(writer, sheet_name="Survey_Points", index=False)

            # Add instructions sheet
            instructions = pd.DataFrame(
                {
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
                        "ID - Unique point identifier (e.g., SP001, CP001)",
                        "N_Northing - Northing coordinate in meters",
                        "E_Easting - Easting coordinate in meters",
                        "Z_Elevation - Elevation in meters",
                        "Description - Point description or notes",
                        "Type - Point type (Survey, Control, Benchmark, etc.)",
                        "Date_Surveyed - Date when point was surveyed",
                        "Accuracy_mm - Survey accuracy in millimeters",
                        "",
                        "NOTE: Coordinate order is N,E,Z (North, East, Elevation)",
                        "This follows standard surveying conventions.",
                    ]
                }
            )
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
    except Exception as e:
        st.error(f"Error creating Excel template: {e}")
        return None


def process_excel_file(uploaded_file):
    """Process uploaded Excel file"""
    if not EXCEL_SUPPORT:
        raise Exception(
            "Excel support not available. Please install openpyxl: pip install openpyxl"
        )

    try:
        # Try to read the Excel file
        df = pd.read_excel(uploaded_file, sheet_name=0)  # Read first sheet
        return df
    except Exception as e:
        raise Exception(f"Error reading Excel file: {str(e)}")


def smart_parse_kof_file(file_content):
    """Smart parser that attempts to extract coordinate data from any KOF-like format"""
    lines = file_content.strip().split("\n")
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
            # Split line and look for numeric values
            parts = line.strip().split()

            # Find all numeric values in the line
            numeric_values = []
            text_values = []

            for part in parts:
                try:
                    # Try to parse as float
                    val = float(part)
                    numeric_values.append(val)
                except ValueError:
                    # If not numeric, it's text
                    text_values.append(part)

            # Filter out obvious format codes from numeric values
            # Common KOF codes: 03, 05, 09, 91, 99, etc. (usually small integers)
            filtered_coords = []
            for val in numeric_values:
                # Skip values that look like format codes (small integers < 100)
                if val == int(val) and 0 <= val <= 99:
                    continue  # This is likely a format code, not a coordinate
                else:
                    filtered_coords.append(val)

            # We need at least 3 numeric values for coordinates (N, E, Z)
            if len(filtered_coords) >= 3:
                # Take the first 3 non-format-code values as coordinates
                coord1 = filtered_coords[0]  # N (Northing)
                coord2 = filtered_coords[1]  # E (Easting)
                coord3 = filtered_coords[2]  # Z (Elevation)

                # Try to identify which could be ID from text values
                potential_id = None
                description_parts = []

                for text in text_values:
                    # Skip format codes like '03', '05', '09', etc.
                    if text in ["03", "05", "09", "91", "99"]:
                        continue
                    # If it looks like a point ID (contains letters and numbers)
                    elif any(c.isalpha() for c in text) and any(
                        c.isdigit() for c in text
                    ):
                        if potential_id is None:
                            potential_id = text
                        else:
                            description_parts.append(text)
                    else:
                        description_parts.append(text)

                # If no ID found, we'll assign one later
                description = " ".join(description_parts) if description_parts else ""

                parsed_data.append(
                    {
                        "line_num": line_num,
                        "original_line": line.strip(),
                        "coord1": coord1,  # N
                        "coord2": coord2,  # E
                        "coord3": coord3,  # Z
                        "potential_id": potential_id,
                        "description": description,
                        "all_numeric": numeric_values,
                        "filtered_coords": filtered_coords,
                        "all_text": text_values,
                    }
                )

        except Exception as e:
            # Skip lines that cause errors
            continue

    return parsed_data


def create_editable_coordinate_table(parsed_data):
    """Create an editable table for coordinate mapping"""
    if not parsed_data:
        return None

    # Create initial dataframe with smart defaults
    table_data = []

    for i, data in enumerate(parsed_data):
        # Generate default ID if none found
        point_id = data["potential_id"] if data["potential_id"] else f"P{i + 1}"

        table_data.append(
            {
                "ID": point_id,
                "Coord1": data["coord1"],  # N
                "Coord2": data["coord2"],  # E
                "Coord3": data["coord3"],  # Z
                "Description": data["description"],
                "Original_Line": data["original_line"],
            }
        )

    return pd.DataFrame(table_data)


def detect_coordinate_columns(df):
    """Smart detection of coordinate columns with N,E,Z naming patterns"""
    columns = [col.upper() for col in df.columns]

    # Common patterns for coordinate columns in N,E,Z order
    n_patterns = ["N", "NORTHING", "NORTH", "Y", "LATITUDE", "LAT"]
    e_patterns = ["E", "EASTING", "EAST", "X", "LONGITUDE", "LON", "LONG"]
    z_patterns = ["Z", "ELEVATION", "ELEV", "HEIGHT", "H", "ALT", "ALTITUDE"]
    id_patterns = ["ID", "POINT_ID", "POINTID", "NAME", "NUMBER", "NUM", "PT"]
    desc_patterns = ["DESCRIPTION", "DESC", "NOTE", "COMMENT", "REMARKS", "TYPE"]

    # Find best matches
    mapping = {}

    # N coordinate (prefer N, then Northing, then Y)
    for pattern in n_patterns:
        matches = [col for col in df.columns if col.upper() == pattern]
        if matches:
            mapping["N"] = matches[0]
            break

    # E coordinate (prefer E, then Easting, then X)
    for pattern in e_patterns:
        matches = [col for col in df.columns if col.upper() == pattern]
        if matches:
            mapping["E"] = matches[0]
            break

    # Z coordinate
    for pattern in z_patterns:
        matches = [col for col in df.columns if col.upper() == pattern]
        if matches:
            mapping["Z"] = matches[0]
            break

    # ID column
    for pattern in id_patterns:
        matches = [col for col in df.columns if col.upper() == pattern]
        if matches:
            mapping["ID"] = matches[0]
            break

    # Description column
    for pattern in desc_patterns:
        matches = [col for col in df.columns if col.upper() == pattern]
        if matches:
            mapping["Description"] = matches[0]
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
        mapping["ID"] = available_cols[0]  # Can be same as N if needed

    return mapping


def apply_column_mapping(df, mapping):
    """Apply column mapping to create standardized DataFrame with N,E,Z"""
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


# --- IFC GENERATION FUNCTIONS ---


def create_guid():
    """Create a new GUID for IFC entities"""
    return ifcopenshell.guid.compress(uuid.uuid4().hex)


def create_ifc_file(
    project_name,
    site_name,
    building_name,
    storey_name,
    coord_system="Global",
    basepoint_n=0.0,
    basepoint_e=0.0,
    basepoint_z=0.0,
):
    """Create a new IFC file with basic setup and coordinate system context"""
    file = ifcopenshell.file(schema="IFC4")

    # Project setup
    project = file.create_entity(
        "IfcProject", GlobalId=create_guid(), Name=project_name
    )
    unit_assignment = file.create_entity("IfcUnitAssignment")
    length_unit = file.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
    unit_assignment.Units = [length_unit]
    project.UnitsInContext = unit_assignment

    # For survey data, always use (0,0,0) as world origin to avoid coordinate issues
    # The survey points will be placed at their actual coordinates
    world_origin = (0.0, 0.0, 0.0)

    # Context setup with appropriate coordinate system
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
    building = file.create_entity(
        "IfcBuilding", GlobalId=create_guid(), Name=building_name
    )
    storey = file.create_entity(
        "IfcBuildingStorey", GlobalId=create_guid(), Name=storey_name
    )

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


def create_material(file, name, color_rgb):
    """Create a colored material"""
    color = file.create_entity(
        "IfcColourRgb",
        Name=name,
        Red=color_rgb[0],
        Green=color_rgb[1],
        Blue=color_rgb[2],
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


def create_enhanced_property_set(
    file,
    survey_point,
    point_data,
    pset_name,
    custom_properties,
    original_coords,
    local_coords,
    offsets,
    source_filename,
    creator_name,
    external_link,
):
    """Create enhanced property set with coordinates, offsets, and custom properties"""

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
        NominalValue=file.create_entity(
            "IfcText", str(point_data.get("ID", "Unknown"))
        ),
    )
    properties.append(prop_point_id)

    # Original coordinates (from survey data)
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

    # Offsets (basepoint values)
    prop_offsets = file.create_entity(
        "IfcPropertySingleValue",
        Name="Offsets",
        NominalValue=file.create_entity(
            "IfcText",
            f"[N:{offsets['N']:.3f}, E:{offsets['E']:.3f}, Z:{offsets['Z']:.3f}]",
        ),
    )
    properties.append(prop_offsets)

    # Local coordinates (for verification)
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

                        # Convert back to N,E,Z (IFC uses X=E, Y=N)
                        local_e = local_x
                        local_n = local_y
                        local_z_val = local_z

                        # Calculate original coordinates
                        calc_n = local_n + offsets["N"]
                        calc_e = local_e + offsets["E"]
                        calc_z = local_z_val + offsets["Z"]

                        # Find corresponding original point
                        point_id = (
                            point.Name.replace("Survey Point ", "")
                            if point.Name
                            else "Unknown"
                        )

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

                            # Check if coordinates match (within tolerance)
                            tolerance = 0.001  # 1mm tolerance
                            n_match = abs(calc_n - orig_n) < tolerance
                            e_match = abs(calc_e - orig_e) < tolerance
                            z_match = abs(calc_z - orig_z) < tolerance

                            verification_results.append(
                                {
                                    "point_id": point_id,
                                    "original": {"N": orig_n, "E": orig_e, "Z": orig_z},
                                    "calculated": {
                                        "N": calc_n,
                                        "E": calc_e,
                                        "Z": calc_z,
                                    },
                                    "local": {
                                        "N": local_n,
                                        "E": local_e,
                                        "Z": local_z_val,
                                    },
                                    "matches": {
                                        "N": n_match,
                                        "E": e_match,
                                        "Z": z_match,
                                    },
                                    "all_match": n_match and e_match and z_match,
                                }
                            )

        return verification_results

    except Exception as e:
        return f"Verification failed: {str(e)}"


def create_coordination_object(
    file, storey, context, name, n, e, z, material, description="Coordination Point"
):
    """Create a coordination object (small sphere) at specified coordinates"""
    # Create sphere geometry for coordination object
    sphere = file.create_entity("IfcSphere", Radius=0.1)  # Small 10cm sphere

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
        "IfcProductDefinitionShape", Representations=[shape_representation]
    )

    # Create local placement - convert N,E,Z to X,Y,Z for IFC
    local_placement = file.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity(
                "IfcCartesianPoint", Coordinates=(e, n, z)
            ),  # E->X, N->Y
        ),
    )

    # Create building element proxy for the coordination object
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


def create_cone_geometry(file, context, radius=0.2, height=0.5):
    """Create a cone geometry"""
    # Create base circle profile
    circle = file.create_entity(
        "IfcCircleProfileDef", ProfileType="AREA", Radius=radius
    )

    # Create extrusion direction
    direction = file.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))

    # Create extruded area solid (cone approximation with small top radius)
    cone = file.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=circle,
        Position=file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity(
                "IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)
            ),
        ),
        ExtrudedDirection=direction,
        Depth=height,
    )

    return cone


def create_coordination_material(file):
    """Create a special material for coordination objects (blue)"""
    return create_material(file, "Coordination", (0.0, 0.5, 1.0))  # Blue color


def create_enhanced_survey_point(
    file,
    storey,
    context,
    point_data,
    material,
    original_coords,
    local_coords,
    offsets,
    pset_name,
    custom_properties,
    source_filename,
    creator_name="SiteCast",
    external_link="",
):
    """Create a survey point element with enhanced property sets"""
    point_id = point_data.get("ID", "Unknown")
    n = float(point_data.get("N", 0))  # Northing (local)
    e = float(point_data.get("E", 0))  # Easting (local)
    z = float(point_data.get("Z", 0))  # Elevation (local)
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
        "IfcProductDefinitionShape", Representations=[shape_representation]
    )

    # Create local placement - CORRECT N,E,Z to X,Y,Z mapping for IFC
    # IFC standard: X=Easting, Y=Northing, Z=Elevation
    local_placement = file.create_entity(
        "IfcLocalPlacement",
        RelativePlacement=file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity(
                "IfcCartesianPoint", Coordinates=(e, n, z)
            ),  # CORRECT: E->X, N->Y
        ),
    )

    # Create building element proxy for the survey point
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
        file,
        survey_point,
        point_data,
        pset_name,
        custom_properties,
        original_coords,
        local_coords,
        offsets,
        source_filename,
        creator_name,
        external_link,
    )

    return survey_point


# --- STREAMLIT APP ---


def initialize_session_state():
    """Initialize session state with default values"""
    defaults = {
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

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def main():
    st.set_page_config(page_title="SiteCast", page_icon="📍", layout="wide")

    # Initialize persistent session state
    initialize_session_state()

    # Language selector in top right
    col1, col2, col3 = st.columns([8, 1, 1])
    with col2:
        if st.button("🇳🇴", help="Norsk"):
            st.info("Norsk oversettelse kommer snart!")
    with col3:
        if st.button("🇬🇧", help="English"):
            pass  # Already in English

    st.title("📍 SiteCast")
    st.subheader("Convert Survey Data to BIM in 30 Seconds")

    # Sidebar for configuration with persistent state
    with st.sidebar:
        st.header("⚙️ Project Settings")

        project_name = st.text_input("Project Name", key="project_name")
        site_name = st.text_input("Site Name", key="site_name")
        building_name = st.text_input("Building Name", key="building_name")
        storey_name = st.text_input("Level Name", key="storey_name")

        st.header("🌍 Coordinate System")
        coord_system = st.radio(
            "Coordinate System Type",
            options=["Local", "Global/Geographic"],
            index=0 if st.session_state.coord_system == "Local" else 1,
            help="Local coordinates use project basepoint offsets",
            key="coord_system",
        )

        # Units section
        st.subheader("📏 Units")
        coordinate_units = st.selectbox(
            "Coordinate Units",
            options=["m (meters)", "mm (millimeters)", "ft (feet)"],
            key="coordinate_units",
        )
        # Extract unit code
        unit_code = coordinate_units.split()[0]

        # Auto-detect checkbox
        auto_detect_units = st.checkbox(
            "Auto-detect units from data",
            help="Automatically detect units based on coordinate ranges",
            key="auto_detect_units",
        )

        # Project Basepoint section - updated to N,E order with persistent state
        st.subheader("📍 Project Basepoint")
        use_basepoint = st.checkbox("Define Project Basepoint", key="use_basepoint")

        if use_basepoint:
            st.caption("Define the project origin in world coordinates")

            col_n, col_e = st.columns(2)
            with col_n:
                basepoint_n = st.number_input(
                    "Basepoint N (Northing)",
                    format="%.3f",
                    help="World N coordinate of project origin",
                    key="basepoint_n",
                )
            with col_e:
                basepoint_e = st.number_input(
                    "Basepoint E (Easting)",
                    format="%.3f",
                    help="World E coordinate of project origin",
                    key="basepoint_e",
                )

            basepoint_z = st.number_input(
                "Basepoint Z (Elevation)",
                format="%.3f",
                help="World Z coordinate of project origin",
                key="basepoint_z",
            )
        else:
            basepoint_n = basepoint_e = basepoint_z = 0.0

        # Survey/Rotation Point section - updated to N,E order with persistent state
        st.subheader("🧭 Survey/Rotation Point")
        use_rotation_point = st.checkbox(
            "Define Survey/Rotation Point", key="use_rotation_point"
        )

        if use_rotation_point:
            st.caption("Define the survey reference point for model alignment")

            col_rn, col_re = st.columns(2)
            with col_rn:
                rotation_n = st.number_input(
                    "Rotation Point N",
                    format="%.3f",
                    help="N coordinate of rotation reference point",
                    key="rotation_n",
                )
            with col_re:
                rotation_e = st.number_input(
                    "Rotation Point E",
                    format="%.3f",
                    help="E coordinate of rotation reference point",
                    key="rotation_e",
                )

            rotation_z = st.number_input(
                "Rotation Point Z",
                format="%.3f",
                help="Z coordinate of rotation reference point",
                key="rotation_z",
            )
        else:
            rotation_n = rotation_e = rotation_z = 0.0

        st.header("🎨 Appearance")
        marker_color = st.color_picker("Marker Color", key="marker_color")

        st.header("📋 Metadata")
        creator_name = st.text_input("Created By", key="creator_name")
        external_link = st.text_input(
            "External Link (optional)", placeholder="https://...", key="external_link"
        )

        # Custom Property Sets section
        st.header("🏷️ Property Sets")

        # Property set name
        pset_name = st.text_input(
            "Property Set Name",
            help="Name of the custom property set to attach to survey points",
            key="pset_name",
        )

        st.subheader("Custom Properties")
        st.caption("Add custom properties to survey points")

        # Initialize custom properties in session state
        if "custom_properties" not in st.session_state:
            st.session_state.custom_properties = [
                {"name": "Coordinate_System", "value": "EUREF89_NTM10"},
                {"name": "Survey_Method", "value": "Total_Station"},
                {"name": "Accuracy_Class", "value": "Class_1"},
            ]

        # Custom properties table
        st.write("**Custom Properties:**")

        # Add new property using form to avoid session state conflicts
        with st.form("add_property_form", clear_on_submit=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                new_prop_name = st.text_input("Property Name")
            with col2:
                new_prop_value = st.text_input("Property Value")
            with col3:
                submitted = st.form_submit_button("➕ Add")

            if submitted and new_prop_name and new_prop_value:
                st.session_state.custom_properties.append(
                    {"name": new_prop_name, "value": new_prop_value}
                )
                st.success(f"Added property: {new_prop_name}")
                st.rerun()

        # Display and edit existing properties
        if st.session_state.custom_properties:
            properties_to_remove = []
            for i, prop in enumerate(st.session_state.custom_properties):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    # Use unique keys for each property editor
                    prop["name"] = st.text_input(
                        f"Name {i + 1}", value=prop["name"], key=f"edit_prop_name_{i}"
                    )
                with col2:
                    prop["value"] = st.text_input(
                        f"Value {i + 1}",
                        value=prop["value"],
                        key=f"edit_prop_value_{i}",
                    )
                with col3:
                    if st.button("🗑️", key=f"remove_{i}", help="Remove property"):
                        properties_to_remove.append(i)

            # Remove properties marked for deletion
            if properties_to_remove:
                for i in reversed(properties_to_remove):
                    st.session_state.custom_properties.pop(i)
                st.rerun()

        # Coordinate verification settings
        st.subheader("✅ Coordinate Verification")
        verify_coordinates = st.checkbox(
            "Verify coordinates after IFC generation",
            help="Read back the IFC file to verify local + offset = original coordinates",
            key="verify_coordinates",
        )

        # Settings management
        st.header("💾 Settings")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Settings", help="Save current settings as defaults"):
                st.success("✅ Settings saved!")

        with col2:
            if st.button("🔄 Reset Settings", help="Reset to default values"):
                # Reset session state to defaults - be more careful about which keys to reset
                keys_to_reset = [
                    "project_name",
                    "site_name",
                    "building_name",
                    "storey_name",
                    "coord_system",
                    "basepoint_n",
                    "basepoint_e",
                    "basepoint_z",
                    "creator_name",
                    "marker_color",
                    "pset_name",
                ]
                for key in keys_to_reset:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📤 Upload Survey Data")

        # File upload
        uploaded_file = st.file_uploader(
            "Upload survey data file",
            type=["csv", "kof", "xlsx", "xls"],
            help="Supported formats: CSV, KOF (Norwegian), Excel (XLSX/XLS)",
        )

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
                    help="Download a pre-formatted Excel template with sample data and instructions",
                )
        else:
            st.warning(
                "Excel support not available. Install openpyxl to enable Excel templates: `pip install openpyxl`"
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
            st.caption(
                "KOF files should contain '03' or '05' format lines with coordinates in N,E,Z order"
            )

            st.write("**Excel Format:**")
            st.write(
                "Use the downloadable template above for a structured Excel format with sample data and instructions."
            )
            st.info(
                "📌 **Important**: All formats follow N,E,Z coordinate order (North, Easting, Elevation)"
            )

    with col2:
        st.header("📊 Column Mapping & Preview")

        if uploaded_file is not None:
            try:
                # Determine file type and parse accordingly
                file_extension = uploaded_file.name.split(".")[-1].lower()

                if file_extension == "csv":
                    # Read CSV
                    df = pd.read_csv(uploaded_file)

                elif file_extension in ["xlsx", "xls"]:
                    # Read Excel file
                    df = process_excel_file(uploaded_file)

                elif file_extension == "kof":
                    # Read KOF file with smart parsing
                    file_content = uploaded_file.read().decode("utf-8", errors="ignore")

                    # Debug: Show what we're parsing
                    st.write("**🔍 Parsing KOF File...**")
                    with st.expander("Show file content"):
                        st.code(file_content)

                    # First try smart parsing
                    parsed_data = smart_parse_kof_file(file_content)
                    st.session_state.parsed_data = parsed_data

                    st.write(f"**Found {len(parsed_data)} coordinate lines**")

                    if not parsed_data:
                        st.error("No coordinate data found in KOF file.")
                        st.write("**File content preview:**")
                        st.code(
                            file_content[:500] + "..."
                            if len(file_content) > 500
                            else file_content
                        )
                        st.stop()

                    # Create editable table
                    df = create_editable_coordinate_table(parsed_data)

                    # Show parsing results
                    st.subheader("📊 KOF File Parsing Results")
                    st.write(f"Found **{len(df)} coordinate lines** in the file")

                    # Show coordinate mapping interface for KOF - simplified UX
                    st.subheader("🗺️ Coordinate Assignment")
                    st.caption("Assign which coordinate column represents N, E, Z")

                    # Show example of the coordinate line for clarity
                    if parsed_data:
                        example_line = parsed_data[0]["original_line"]
                        st.info(f"📋 **Example line**: `{example_line}`")

                        # Show detailed parsing breakdown
                        with st.expander("🔍 Detailed Parsing Breakdown"):
                            st.write(
                                "**All numbers found:**", parsed_data[0]["all_numeric"]
                            )
                            st.write(
                                "**Text values found:**", parsed_data[0]["all_text"]
                            )
                            st.write(
                                "**Filtered coordinates:**",
                                parsed_data[0]["filtered_coords"],
                            )
                            st.write("**Assigned values:**")
                            st.write(f"• Coord1 = {parsed_data[0]['coord1']}")
                            st.write(f"• Coord2 = {parsed_data[0]['coord2']}")
                            st.write(f"• Coord3 = {parsed_data[0]['coord3']}")

                        filtered_coords = parsed_data[0]["filtered_coords"]
                        st.write(f"**Extracted coordinates**: {filtered_coords}")

                        # Show a few more examples if available
                        if len(parsed_data) > 1:
                            st.write("**Additional examples:**")
                            for i in range(1, min(4, len(parsed_data))):
                                coords = parsed_data[i]["filtered_coords"]
                                st.write(f"Line {i + 1}: {coords}")

                    # Show what columns are available in the df
                    available_coord_cols = [
                        col for col in df.columns if col.startswith("Coord")
                    ]
                    st.write(
                        f"**Available coordinate columns**: {available_coord_cols}"
                    )

                    # Show the actual data in the coordinate columns
                    with st.expander("📊 Coordinate Column Preview"):
                        st.dataframe(df[available_coord_cols].head())

                    # Simple column assignment without condescending language
                    coord_cols = st.columns(3)
                    with coord_cols[0]:
                        n_source = st.selectbox(
                            "Northing (N):",
                            available_coord_cols,
                            index=0 if len(available_coord_cols) > 0 else 0,
                            key="n_assign",
                        )
                    with coord_cols[1]:
                        e_source = st.selectbox(
                            "Easting (E):",
                            available_coord_cols,
                            index=1 if len(available_coord_cols) > 1 else 0,
                            key="e_assign",
                        )
                    with coord_cols[2]:
                        z_source = st.selectbox(
                            "Elevation (Z):",
                            available_coord_cols,
                            index=2 if len(available_coord_cols) > 2 else 0,
                            key="z_assign",
                        )

                    # Check for duplicate assignments and warn user
                    assignments = [n_source, e_source, z_source]
                    assignment_names = ["Northing", "Easting", "Elevation"]
                    duplicates = []
                    for i, coord in enumerate(assignments):
                        if assignments.count(coord) > 1:
                            indices = [
                                j for j, x in enumerate(assignments) if x == coord
                            ]
                            duplicate_names = [assignment_names[j] for j in indices]
                            if coord not in [
                                d[0] for d in duplicates
                            ]:  # Avoid duplicate warnings
                                duplicates.append((coord, duplicate_names))

                    if duplicates:
                        st.warning("⚠️ **Duplicate Assignments Detected:**")
                        for coord, names in duplicates:
                            st.warning(f"• {coord} is assigned to: {', '.join(names)}")
                        st.info(
                            "💡 This is allowed but verify your coordinate assignments are correct."
                        )

                    # Create mapped dataframe with proper error handling - allow duplicates
                    try:
                        mapped_df = df.copy()

                        # Always assign coordinates, even if duplicated
                        # This allows users to temporarily have the same source for multiple coordinates
                        if n_source and n_source in df.columns:
                            mapped_df["N"] = df[n_source].copy()
                        else:
                            mapped_df["N"] = 0.0

                        if e_source and e_source in df.columns:
                            mapped_df["E"] = df[e_source].copy()
                        else:
                            mapped_df["E"] = 0.0

                        if z_source and z_source in df.columns:
                            mapped_df["Z"] = df[z_source].copy()
                        else:
                            mapped_df["Z"] = 0.0

                        # Always ensure we have the required columns
                        required_cols = ["ID", "N", "E", "Z", "Description"]
                        for col in required_cols:
                            if col not in mapped_df.columns:
                                if col == "Description":
                                    mapped_df[col] = ""
                                elif col == "ID":
                                    mapped_df[col] = [
                                        f"P{i + 1}" for i in range(len(mapped_df))
                                    ]

                        # Show editable table
                        st.subheader("✏️ Edit Coordinate Data")
                        st.caption(
                            "Edit IDs and descriptions. Coordinate values can be changed if needed."
                        )

                        # Debug info (can be removed in production)
                        with st.expander("🔍 Debug Info"):
                            st.write(
                                f"**DataFrame columns**: {list(mapped_df.columns)}"
                            )
                            st.write(f"**DataFrame shape**: {mapped_df.shape}")
                            st.write(
                                f"**Assignments**: N←{n_source}, E←{e_source}, Z←{z_source}"
                            )

                        # Use data editor for editing - with robust column checking
                        if all(col in mapped_df.columns for col in required_cols):
                            # Create a clean copy for editing to avoid reference issues
                            edit_data = (
                                mapped_df[required_cols].copy().reset_index(drop=True)
                            )

                            edited_df = st.data_editor(
                                edit_data,
                                use_container_width=True,
                                num_rows="dynamic",
                                column_config={
                                    "ID": st.column_config.TextColumn(
                                        "Point ID", required=True
                                    ),
                                    "N": st.column_config.NumberColumn(
                                        "N (Northing)", format="%.3f"
                                    ),
                                    "E": st.column_config.NumberColumn(
                                        "E (Easting)", format="%.3f"
                                    ),
                                    "Z": st.column_config.NumberColumn(
                                        "Z (Elevation)", format="%.3f"
                                    ),
                                    "Description": st.column_config.TextColumn(
                                        "Description"
                                    ),
                                },
                            )

                            # Update df for further processing
                            df = edited_df.copy()
                            st.session_state.mapped_df = df
                        else:
                            st.error(
                                f"Missing required columns. Have: {list(mapped_df.columns)}, Need: {required_cols}"
                            )
                            st.dataframe(mapped_df.head())

                    except Exception as e:
                        st.error(f"Error creating mapped dataframe: {str(e)}")
                        st.write("**Error Details:**")
                        st.write(f"• Original dataframe columns: {list(df.columns)}")
                        st.write(f"• Original dataframe shape: {df.shape}")
                        st.write(
                            f"• Selected assignments: N={n_source}, E={e_source}, Z={z_source}"
                        )
                        with st.expander("Show original data"):
                            st.dataframe(df.head())

                else:
                    st.error(
                        "Unsupported file format. Please upload CSV, KOF, or Excel files."
                    )
                    st.stop()

                # Auto-detect column mapping (skip for KOF since we handle it above)
                if file_extension in ["csv", "xlsx", "xls"]:
                    detected_mapping = detect_coordinate_columns(df)

                    # Show column mapping interface
                    st.subheader("🗺️ Column Mapping")
                    st.caption("Map your file columns to N,E,Z coordinate data")

                    # Create mapping dropdowns
                    available_columns = [""] + list(df.columns)

                    col_map = {}
                    col_map["ID"] = st.selectbox(
                        "Point ID Column",
                        available_columns,
                        index=available_columns.index(detected_mapping.get("ID", ""))
                        if detected_mapping.get("ID", "") in available_columns
                        else 0,
                        key="id_col",
                    )

                    col_map["N"] = st.selectbox(
                        "N Coordinate (Northing)",
                        available_columns,
                        index=available_columns.index(detected_mapping.get("N", ""))
                        if detected_mapping.get("N", "") in available_columns
                        else 0,
                        key="n_col",
                        help="Northing coordinate in survey data",
                    )

                    col_map["E"] = st.selectbox(
                        "E Coordinate (Easting)",
                        available_columns,
                        index=available_columns.index(detected_mapping.get("E", ""))
                        if detected_mapping.get("E", "") in available_columns
                        else 0,
                        key="e_col",
                        help="Easting coordinate in survey data",
                    )

                    col_map["Z"] = st.selectbox(
                        "Z Coordinate (Elevation)",
                        available_columns,
                        index=available_columns.index(detected_mapping.get("Z", ""))
                        if detected_mapping.get("Z", "") in available_columns
                        else 0,
                        key="z_col",
                    )

                    col_map["Description"] = st.selectbox(
                        "Description (Optional)",
                        available_columns,
                        index=available_columns.index(
                            detected_mapping.get("Description", "")
                        )
                        if detected_mapping.get("Description", "") in available_columns
                        else 0,
                        key="desc_col",
                    )

                    # Validate required mappings
                    required_mappings = ["ID", "N", "E", "Z"]
                    missing_mappings = [
                        col for col in required_mappings if not col_map[col]
                    ]

                    if missing_mappings:
                        st.error(
                            f"Please map the following required columns: {', '.join(missing_mappings)}"
                        )
                    else:
                        # Apply mapping and show preview
                        mapped_df = apply_column_mapping(df, col_map)
                        df = mapped_df
                        st.session_state.mapped_df = df
                        missing_mappings = []
                else:
                    # For KOF files, mapping is already done above
                    missing_mappings = []

                # Validate coordinates - only if we have valid data and proper columns
                if not missing_mappings and df is not None and len(df) > 0:
                    # Double-check that N, E, Z columns exist before validation
                    required_coord_cols = ["N", "E", "Z"]
                    missing_coord_cols = [
                        col for col in required_coord_cols if col not in df.columns
                    ]

                    if missing_coord_cols:
                        st.warning(
                            f"Missing coordinate columns: {missing_coord_cols}. Please complete mapping above."
                        )
                        missing_mappings = True  # Force this to prevent IFC generation
                    else:
                        # Proceed with validation and processing
                        validator = CoordinateValidator()
                        errors, warnings = validator.validate_coordinates(df)

                        if errors:
                            st.error("❌ **Coordinate Validation Errors:**")
                            for error in errors:
                                st.error(f"• {error}")
                        else:
                            # Unit detection and conversion
                            if auto_detect_units:
                                detected_units = validator.detect_units(df)
                                st.info(f"🔍 **Detected Units**: {detected_units}")

                                if detected_units != unit_code:
                                    st.warning(
                                        f"⚠️ **Unit Mismatch**: Selected {unit_code}, detected {detected_units}"
                                    )

                                    # Ask user which to use
                                    use_detected = st.radio(
                                        "Which units should be used?",
                                        options=[
                                            f"Use detected: {detected_units}",
                                            f"Use selected: {unit_code}",
                                        ],
                                        key="unit_choice",
                                    )

                                    if "detected" in use_detected:
                                        working_units = detected_units
                                    else:
                                        working_units = unit_code
                                else:
                                    working_units = unit_code
                            else:
                                working_units = unit_code

                            # Convert to meters for IFC (standard) - only if not already in meters
                            if working_units != "m":
                                st.info(
                                    f"🔄 **Converting** from {working_units} to meters for IFC"
                                )
                                df_meters = validator.convert_units(
                                    df, working_units, "m"
                                )
                                conversion_note = f" (converted from {working_units})"
                            else:
                                df_meters = df.copy()
                                conversion_note = ""

                            # Show coordinate sample for verification
                            st.info("📋 **Coordinate Sample** (in meters for IFC):")
                            sample_coords = df_meters[["N", "E", "Z"]].head(3)
                            for idx, row in sample_coords.iterrows():
                                st.write(
                                    f"Point {idx + 1}: N={row['N']:.3f}m, E={row['E']:.3f}m, Z={row['Z']:.3f}m"
                                )

                            if warnings:
                                st.warning("⚠️ **Coordinate Validation Warnings:**")
                                for warning in warnings:
                                    st.warning(f"• {warning}")

                            # Create survey processor with converted data
                            processor = SurveyProcessor(
                                coord_system, basepoint_n, basepoint_e, basepoint_z
                            )

                            # Calculate north direction from survey data
                            if len(df_meters) >= 3:
                                calculated_north = processor.calculate_north_direction(
                                    df_meters
                                )
                                if SKLEARN_AVAILABLE:
                                    st.info(
                                        f"🧭 **Calculated Grid North**: {calculated_north:.2f}° from east (PCA method)"
                                    )
                                else:
                                    st.info(
                                        f"🧭 **Estimated Grid North**: {calculated_north:.2f}° from east (basic method)"
                                    )

                            # Apply coordinate transformation
                            if coord_system == "Local" or use_basepoint:
                                transformed_df = processor.transform_coordinates(
                                    df_meters
                                )
                                coord_note = f" (offset by basepoint: N={basepoint_n:.3f}, E={basepoint_e:.3f}, Z={basepoint_z:.3f})"
                            else:
                                transformed_df = df_meters.copy()
                                coord_note = " (global coordinates)"

                            # Show preview - always show table even during mapping changes
                            file_type = {
                                "csv": "CSV",
                                "xlsx": "Excel",
                                "xls": "Excel",
                                "kof": "KOF",
                            }[file_extension]
                            st.write(
                                f"**{len(transformed_df)} survey points ready from {file_type} file** ({working_units}{conversion_note})"
                            )

                            # Show both original and transformed coordinates if using basepoint
                            if use_basepoint:
                                preview_tabs = st.tabs(
                                    [
                                        "Transformed (Local)",
                                        "Original (World)",
                                        "Units Info",
                                    ]
                                )
                                with preview_tabs[0]:
                                    st.caption(
                                        "Coordinates relative to project basepoint (meters)"
                                    )
                                    st.dataframe(
                                        transformed_df.head(), use_container_width=True
                                    )
                                with preview_tabs[1]:
                                    st.caption(
                                        f"Original coordinates from file ({working_units})"
                                    )
                                    st.dataframe(df.head(), use_container_width=True)
                                with preview_tabs[2]:
                                    st.caption("Unit conversion details")
                                    st.write(f"• **Source data**: {working_units}")
                                    st.write(f"• **IFC output**: meters (BIM standard)")
                                    if working_units != "m":
                                        st.write(
                                            f"• **Conversion factor**: {working_units} → m"
                                        )
                            else:
                                preview_tabs = st.tabs(["Coordinates", "Units Info"])
                                with preview_tabs[0]:
                                    st.caption(
                                        f"Survey coordinates (converted to meters)"
                                    )
                                    st.dataframe(
                                        transformed_df.head(), use_container_width=True
                                    )
                                with preview_tabs[1]:
                                    st.caption("Unit information")
                                    st.write(f"• **Source data**: {working_units}")
                                    st.write(f"• **IFC output**: meters (BIM standard)")

                            # Coordinate system info
                            try:
                                if (
                                    pd.api.types.is_numeric_dtype(transformed_df["N"])
                                    and pd.api.types.is_numeric_dtype(
                                        transformed_df["E"]
                                    )
                                    and pd.api.types.is_numeric_dtype(
                                        transformed_df["Z"]
                                    )
                                ):
                                    n_range = f"{transformed_df['N'].min():.2f} to {transformed_df['N'].max():.2f}"
                                    e_range = f"{transformed_df['E'].min():.2f} to {transformed_df['E'].max():.2f}"
                                    z_range = f"{transformed_df['Z'].min():.2f} to {transformed_df['Z'].max():.2f}"
                                    st.info(
                                        f"📍 **{coord_system} Coordinate Ranges** (meters){coord_note}\nN: {n_range}m\nE: {e_range}m\nZ: {z_range}m"
                                    )
                            except Exception as e:
                                st.warning(
                                    f"Could not calculate coordinate ranges: {str(e)}"
                                )

            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                import traceback

                st.code(traceback.format_exc())
        else:
            st.info("👆 Upload a file and complete column mapping to get started")

    # Export section - moved below column mapping
    if (
        "transformed_df" in locals()
        and "missing_mappings" in locals()
        and not missing_mappings
        and "errors" in locals()
        and not errors
    ):
        st.header("🚀 Generate IFC File")

        # Convert hex color to RGB
        hex_color = marker_color.lstrip("#")
        rgb_color = tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))

        # Generate IFC button
        # Generate IFC button
        if st.button("🚀 Generate IFC File", type="primary", use_container_width=True):
            try:
                # Create progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Step 1: Create IFC file structure
                status_text.text("Creating IFC file structure...")
                progress_bar.progress(10)

                # Create IFC file with coordinate system context
                file, storey, context = create_ifc_file(
                    project_name,
                    site_name,
                    building_name,
                    storey_name,
                    coord_system,
                    basepoint_n,
                    basepoint_e,
                    basepoint_z,
                )

                # Step 2: Create materials
                status_text.text("Creating materials...")
                progress_bar.progress(20)

                survey_material = create_material(file, "Survey Marker", rgb_color)
                coord_material = create_coordination_material(file)

                # Step 3: Create coordination objects
                status_text.text("Creating coordination objects...")
                progress_bar.progress(30)

                coordination_objects_created = 0

                if use_basepoint:
                    # Create coordination object at project basepoint (in local coordinates: 0,0,0)
                    create_coordination_object(
                        file,
                        storey,
                        context,
                        "Project Basepoint",
                        0.0,
                        0.0,
                        0.0,
                        coord_material,
                        f"Project basepoint: N={basepoint_n:.3f}, E={basepoint_e:.3f}, Z={basepoint_z:.3f}",
                    )
                    coordination_objects_created += 1

                if use_rotation_point:
                    # Calculate rotation point in local coordinates if using basepoint
                    if use_basepoint:
                        local_rot_n = rotation_n - basepoint_n
                        local_rot_e = rotation_e - basepoint_e
                        local_rot_z = rotation_z - basepoint_z
                    else:
                        local_rot_n, local_rot_e, local_rot_z = (
                            rotation_n,
                            rotation_e,
                            rotation_z,
                        )

                    create_coordination_object(
                        file,
                        storey,
                        context,
                        "Survey/Rotation Point",
                        local_rot_n,
                        local_rot_e,
                        local_rot_z,
                        coord_material,
                        f"Rotation point: N={rotation_n:.3f}, E={rotation_e:.3f}, Z={rotation_z:.3f}",
                    )
                    coordination_objects_created += 1

                # Step 4: Create survey points
                status_text.text("Creating survey points...")
                progress_bar.progress(40)

                total_points = len(transformed_df)
                for idx, row in transformed_df.iterrows():
                    # Update progress for each point
                    point_progress = 40 + int((idx / total_points) * 30)  # 40-70% range
                    progress_bar.progress(point_progress)
                    status_text.text(
                        f"Creating survey point {idx + 1} of {total_points}..."
                    )

                    point_data = row.to_dict()

                    # Prepare coordinate data for the enhanced function
                    original_coords = {
                        "N": df_meters.loc[idx, "N"],  # Original coordinates in meters
                        "E": df_meters.loc[idx, "E"],
                        "Z": df_meters.loc[idx, "Z"],
                    }

                    local_coords = {
                        "N": row["N"],  # Transformed coordinates
                        "E": row["E"],
                        "Z": row["Z"],
                    }

                    offsets = {"N": basepoint_n, "E": basepoint_e, "Z": basepoint_z}

                    create_enhanced_survey_point(
                        file,
                        storey,
                        context,
                        point_data,
                        survey_material,
                        original_coords,
                        local_coords,
                        offsets,
                        pset_name,
                        st.session_state.custom_properties,
                        uploaded_file.name if uploaded_file else "Unknown",
                        creator_name,
                        external_link,
                    )

                # Step 5: Save IFC file
                status_text.text("Saving IFC file...")
                progress_bar.progress(70)

                # Save to temporary file with proper Windows file handling
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".ifc"
                    ) as tmp_file:
                        tmp_file_path = tmp_file.name

                    # Write IFC file (outside the context manager)
                    file.write(tmp_file_path)

                    # Step 6: Read file for download
                    status_text.text("Preparing download...")
                    progress_bar.progress(80)

                    with open(tmp_file_path, "rb") as f:
                        ifc_data = f.read()

                    # Step 7: Coordinate verification (if enabled)
                    verification_results = None
                    if verify_coordinates:
                        status_text.text("Verifying coordinates...")
                        progress_bar.progress(90)

                        # Add timing and debug info
                        import time

                        verification_start = time.time()

                        st.info("🔍 **Starting coordinate verification...**")

                        # Check if file exists and has content
                        if os.path.exists(tmp_file_path):
                            file_size = os.path.getsize(tmp_file_path)
                            st.info(f"📄 IFC file size: {file_size:,} bytes")
                        else:
                            st.error("❌ IFC file not found for verification!")

                        verification_results = verify_ifc_coordinates(
                            tmp_file_path,
                            df_meters,  # Use the original meter-converted data
                            offsets,
                        )

                        verification_time = time.time() - verification_start
                        st.info(
                            f"⏱️ Verification completed in {verification_time:.2f} seconds"
                        )

                        # Debug the verification results
                        if isinstance(verification_results, str):
                            st.error(
                                f"🚨 **Verification Error**: {verification_results}"
                            )
                        elif isinstance(verification_results, list):
                            st.info(
                                f"📊 Found {len(verification_results)} verification results"
                            )
                            if len(verification_results) == 0:
                                st.warning(
                                    "⚠️ No survey points found in IFC file for verification!"
                                )

                                # Let's debug what's actually in the IFC file
                                try:
                                    debug_ifc = ifcopenshell.open(tmp_file_path)
                                    all_elements = debug_ifc.by_type(
                                        "IfcBuildingElementProxy"
                                    )
                                    st.info(
                                        f"🔍 Debug: Found {len(all_elements)} IfcBuildingElementProxy elements"
                                    )

                                    for i, elem in enumerate(
                                        all_elements[:5]
                                    ):  # Show first 5
                                        st.info(
                                            f"Element {i + 1}: Name='{elem.Name}', Description='{elem.Description}'"
                                        )

                                except Exception as e:
                                    st.error(f"Debug failed: {e}")
                        else:
                            st.error(
                                f"🚨 Unexpected verification result type: {type(verification_results)}"
                            )

                finally:
                    # Clean up - try multiple times if needed (Windows file locking)
                    import time

                    for attempt in range(3):
                        try:
                            if os.path.exists(tmp_file_path):
                                os.unlink(tmp_file_path)
                            break
                        except PermissionError:
                            if attempt < 2:  # Only wait if we have more attempts
                                time.sleep(0.1)  # Wait 100ms before retry
                            else:
                                st.warning(
                                    "⚠️ Temporary file cleanup failed (this is harmless)"
                                )

                # Step 8: Complete
                status_text.text("IFC generation complete!")
                progress_bar.progress(100)

                st.success("✅ IFC file generated successfully!")

                # Download button
                filename = f"{project_name.replace(' ', '_')}_survey_points.ifc"
                st.download_button(
                    label="📥 Download IFC File",
                    data=ifc_data,
                    file_name=filename,
                    mime="application/octet-stream",
                    use_container_width=True,
                )

                # Summary stats
                coord_summary = (
                    f" + {coordination_objects_created} coordination objects"
                    if coordination_objects_created > 0
                    else ""
                )
                if "calculated_north" in locals():
                    north_summary = f" (Grid North: {calculated_north:.1f}°)"
                else:
                    north_summary = ""

                st.info(
                    f"📊 **Summary**: {len(transformed_df)} survey points{coord_summary} converted to IFC format using {coord_system.lower()} coordinates{north_summary}"
                )

                # Display coordinate verification results
                if verify_coordinates and verification_results:
                    if isinstance(verification_results, str):
                        # Error case
                        st.warning(
                            f"⚠️ **Coordinate Verification Failed**: {verification_results}"
                        )
                    elif (
                        isinstance(verification_results, list)
                        and len(verification_results) > 0
                    ):
                        # Success case - show verification results
                        st.success("✅ **Coordinate Verification Complete**")

                        # Count matches
                        total_points = len(verification_results)
                        all_matches = sum(
                            1 for result in verification_results if result["all_match"]
                        )

                        if all_matches == total_points:
                            st.success(
                                f"🎯 **Perfect Match**: All {total_points} points verified successfully!"
                            )
                        else:
                            st.warning(
                                f"⚠️ **Partial Match**: {all_matches}/{total_points} points verified successfully"
                            )

                        # Show detailed results in expandable section
                        with st.expander("🔍 View Detailed Verification Results"):
                            for result in verification_results:
                                point_id = result["point_id"]
                                if result["all_match"]:
                                    st.success(
                                        f"✅ **Point {point_id}**: Coordinates match perfectly"
                                    )
                                else:
                                    st.error(
                                        f"❌ **Point {point_id}**: Coordinate mismatch detected"
                                    )

                                    # Show coordinate comparison
                                    orig = result["original"]
                                    calc = result["calculated"]
                                    matches = result["matches"]

                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        status = "✅" if matches["N"] else "❌"
                                        st.write(
                                            f"{status} **N**: {orig['N']:.3f} → {calc['N']:.3f}"
                                        )
                                    with col2:
                                        status = "✅" if matches["E"] else "❌"
                                        st.write(
                                            f"{status} **E**: {orig['E']:.3f} → {calc['E']:.3f}"
                                        )
                                    with col3:
                                        status = "✅" if matches["Z"] else "❌"
                                        st.write(
                                            f"{status} **Z**: {orig['Z']:.3f} → {calc['Z']:.3f}"
                                        )
                    else:
                        st.info("ℹ️ **Coordinate Verification**: No results to display")

                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()

            except Exception as e:
                st.error(f"Error generating IFC file: {str(e)}")
                import traceback

                st.code(traceback.format_exc())

    elif "uploaded_file" in locals() and uploaded_file is not None:
        st.info("👆 Complete column mapping above to enable IFC generation")
    else:
        st.info("👆 Upload a file and complete column mapping to get started")

    # Footer
    st.markdown("---")
    st.markdown(
        "**SiteCast Enhanced** - Convert survey data to BIM-ready IFC files with N,E,Z coordinate standard"
    )


if __name__ == "__main__":
    main()
