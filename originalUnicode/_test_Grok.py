import streamlit as st
import pandas as pd
import ifcopenshell
import ifcopenshell.api
import uuid
import io
import tempfile
import os
import re
import logging
import plotly.express as px
from typing import Tuple, Optional, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Localization dictionary
TRANSLATIONS = {
    "en": {
        "title": "SiteCast",
        "subtitle": "Convert Survey Data to BIM in 30 Seconds",
        "step1": "1. Upload Survey Data",
        "step2": "2. Project Settings",
        "step3": "3. Review & Map Data",
        "generate_ifc": "Generate IFC File",
        "error_file": "Error processing file: Ensure valid format and data.",
        "help_upload": "Upload CSV, KOF, or Excel files with survey coordinates.",
        "preview": "Data Preview",
        "mapping": "Column Mapping",
        "edit_mapping": "Edit Column Mapping",
        "generate_ready": "Ready to generate IFC file!",
        "generate_not_ready": "Please upload a file and verify data to generate IFC.",
    },
    "no": {
        "title": "SiteCast",
        "subtitle": "Konverter måledata til BIM på 30 sekunder",
        "step1": "1. Last opp måledata",
        "step2": "2. Prosjektinnstillinger",
        "step3": "3. Gjennomgå og tilordne data",
        "generate_ifc": "Generer IFC-fil",
        "error_file": "Feil ved behandling av fil: Sørg for gyldig format og data.",
        "help_upload": "Last opp CSV, KOF eller Excel-filer med målekoordinater.",
        "preview": "Dataforhåndsvisning",
        "mapping": "Kolonne-tilordning",
        "edit_mapping": "Rediger kolonne-tilordning",
        "generate_ready": "Klar til å generere IFC-fil!",
        "generate_not_ready": "Last opp en fil og verifiser data for å generere IFC.",
    },
}

# Check for openpyxl
try:
    import openpyxl

    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False


@st.cache_data
def create_excel_template() -> Optional[bytes]:
    """Create an Excel template with sample survey data."""
    if not EXCEL_SUPPORT:
        st.warning("Excel support unavailable. Install openpyxl: pip install openpyxl")
        return None
    template_data = {
        "ID": ["SP001", "SP002", "SP003"],
        "X_Easting": [1194257.404, 1194250.859, 1194233.405],
        "Y_Northing": [82692.090, 82687.146, 82673.960],
        "Z_Elevation": [2.075, 2.295, 2.286],
        "Description": ["Survey Point 1", "Survey Point 2", "Survey Point 3"],
    }
    df = pd.DataFrame(template_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Survey_Points", index=False)
        pd.DataFrame(
            {
                "Instructions": [
                    "1. Fill out the Survey_Points sheet with your coordinate data",
                    "2. Required columns: ID, X_Easting, Y_Northing, Z_Elevation",
                ]
            }
        ).to_excel(writer, sheet_name="Instructions", index=False)
    output.seek(0)
    return output.getvalue()


@st.cache_data
def parse_kof_file(file_content: str) -> List[Dict]:
    """Parse KOF file using regex for efficiency."""
    pattern = re.compile(r"^(?:03|05)\s+(\w+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)")
    parsed_data = []
    for line_num, line in enumerate(file_content.strip().split("\n"), 1):
        if not line.strip() or line.strip().startswith("-"):
            continue
        if match := pattern.match(line.strip()):
            parsed_data.append(
                {
                    "line_num": line_num,
                    "original_line": line.strip(),
                    "coord1": float(match.group(2)),
                    "coord2": float(match.group(3)),
                    "coord3": float(match.group(4)),
                    "potential_id": match.group(1),
                    "description": "",
                }
            )
    return parsed_data


def create_editable_table(parsed_data: List[Dict]) -> pd.DataFrame:
    """Create an editable DataFrame from parsed KOF data."""
    table_data = [
        {
            "ID": data["potential_id"] if data["potential_id"] else f"P{i + 1}",
            "Coord1": data["coord1"],
            "Coord2": data["coord2"],
            "Coord3": data["coord3"],
            "Description": data["description"],
        }
        for i, data in enumerate(parsed_data)
    ]
    return pd.DataFrame(table_data)


def detect_coordinate_columns(df: pd.DataFrame) -> Dict[str, str]:
    """Detect coordinate columns based on common naming patterns."""
    columns = [col.upper() for col in df.columns]
    x_patterns = ["X", "EASTING", "E", "EAST"]
    y_patterns = ["Y", "NORTHING", "N", "NORTH"]
    z_patterns = ["Z", "ELEVATION", "ELEV", "HEIGHT"]
    id_patterns = ["ID", "POINT_ID", "NAME"]
    mapping = {}
    for col, patterns in [
        ("ID", id_patterns),
        ("X", x_patterns),
        ("Y", y_patterns),
        ("Z", z_patterns),
    ]:
        for pattern in patterns:
            matches = [c for c in df.columns if c.upper() == pattern]
            if matches:
                mapping[col] = matches[0]
                break
    if "ID" not in mapping and df.columns:
        mapping["ID"] = df.columns[0]
    if "X" not in mapping and df.columns:
        mapping["X"] = df.columns[0]
    if "Y" not in mapping and len(df.columns) > 1:
        mapping["Y"] = df.columns[1]
    if "Z" not in mapping and len(df.columns) > 2:
        mapping["Z"] = df.columns[2]
    return mapping


def apply_column_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """Apply column mapping to standardize DataFrame."""
    mapped_df = pd.DataFrame()
    for standard_col, source_col in mapping.items():
        if source_col and source_col in df.columns:
            mapped_df[standard_col] = df[source_col]
    if "ID" not in mapped_df.columns:
        mapped_df["ID"] = [f"P{i + 1}" for i in range(len(df))]
    if "Description" not in mapped_df.columns:
        mapped_df["Description"] = ""
    return mapped_df


def create_ifc_file(
    project_name: str,
    site_name: str,
    building_name: str,
    storey_name: str,
    coord_system: str,
    basepoint_x: float,
    basepoint_y: float,
    basepoint_z: float,
) -> Tuple:
    """Create an IFC file with project hierarchy and coordinate system context."""
    file = ifcopenshell.file(schema="IFC4")
    project = ifcopenshell.api.run(
        "root.create_entity", file, ifc_class="IfcProject", name=project_name
    )
    ifcopenshell.api.run(
        "unit.assign_unit",
        file,
        units=[{"type": "IfcSIUnit", "UnitType": "LENGTHUNIT", "Name": "METRE"}],
    )
    world_origin = (
        (basepoint_x, basepoint_y, basepoint_z)
        if coord_system == "Local"
        else (0.0, 0.0, 0.0)
    )
    context = ifcopenshell.api.run(
        "context.add_context",
        file,
        context_type="Model",
        context_identifier=None,
        target_view="MODEL_VIEW",
        parent=None,
    )
    body_context = ifcopenshell.api.run(
        "context.add_context",
        file,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=context,
    )
    site = ifcopenshell.api.run(
        "root.create_entity", file, ifc_class="IfcSite", name=site_name
    )
    building = ifcopenshell.api.run(
        "root.create_entity", file, ifc_class="IfcBuilding", name=building_name
    )
    storey = ifcopenshell.api.run(
        "root.create_entity", file, ifc_class="IfcBuildingStorey", name=storey_name
    )
    ifcopenshell.api.run(
        "aggregate.assign_object", file, relating_object=project, related_object=site
    )
    ifcopenshell.api.run(
        "aggregate.assign_object", file, relating_object=site, related_object=building
    )
    ifcopenshell.api.run(
        "aggregate.assign_object", file, relating_object=building, related_object=storey
    )
    return file, storey, body_context


def create_survey_point(
    file, storey, context, point_data: Dict, material, creator_name: str
) -> None:
    """Create a survey point as a cone in the IFC file."""
    x, y, z = (
        float(point_data.get("X", 0)),
        float(point_data.get("Y", 0)),
        float(point_data.get("Z", 0)),
    )
    point_id = point_data.get("ID", "Unknown")
    description = point_data.get("Description", "")
    cone = file.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=file.create_entity(
            "IfcCircleProfileDef", ProfileType="AREA", Radius=0.2
        ),
        Position=file.create_entity(
            "IfcAxis2Placement3D",
            Location=file.create_entity(
                "IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)
            ),
        ),
        ExtrudedDirection=file.create_entity(
            "IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)
        ),
        Depth=0.5,
    )
    shape = ifcopenshell.api.run(
        "geometry.add_representation",
        file,
        context=context,
        representation_data={
            "RepresentationIdentifier": "Body",
            "RepresentationType": "SweptSolid",
            "Items": [cone],
        },
    )
    point = ifcopenshell.api.run(
        "root.create_entity",
        file,
        ifc_class="IfcBuildingElementProxy",
        name=f"Survey Point {point_id}",
        description=description,
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", file, product=point, representation=shape
    )
    ifcopenshell.api.run(
        "spatial.assign_container",
        file,
        relating_structure=storey,
        related_element=point,
    )
    props = [
        {
            "Name": "Created By",
            "NominalValue": {"type": "IfcText", "value": creator_name},
        },
        {
            "Name": "Point ID",
            "NominalValue": {"type": "IfcText", "value": str(point_id)},
        },
        {
            "Name": "Coordinates",
            "NominalValue": {
                "type": "IfcText",
                "value": f"X:{x:.3f}, Y:{y:.3f}, Z:{z:.3f}",
            },
        },
    ]
    ifcopenshell.api.run(
        "property.add_property_set",
        file,
        element=point,
        name="Survey_Properties",
        properties=props,
    )


def apply_coordinate_transformation(
    df: pd.DataFrame,
    coord_system: str,
    basepoint_x: float,
    basepoint_y: float,
    basepoint_z: float,
) -> pd.DataFrame:
    """Apply coordinate transformation in-place."""
    if coord_system == "Local":
        df["X"] -= basepoint_x
        df["Y"] -= basepoint_y
        df["Z"] -= basepoint_z
    return df


def handle_error(e: Exception, message: str) -> None:
    """Centralized error handler."""
    logger.error(f"{message}: {str(e)}")
    st.error(f"{message}: {str(e)}")


def main():
    st.set_page_config(page_title="SiteCast", page_icon="📍", layout="wide")

    # Language selection
    lang = st.session_state.get("lang", "en")
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🇳🇴", help="Norsk"):
            st.session_state.lang = "no"
        if st.button("🇬🇧", help="English"):
            st.session_state.lang = "en"

    t = TRANSLATIONS[lang]
    st.title(t["title"])
    st.subheader(t["subtitle"])

    # Progress indicator
    progress_steps = ["Upload", "Settings", "Data Ready"]
    progress_cols = st.columns(len(progress_steps))
    for i, step in enumerate(progress_steps):
        with progress_cols[i]:
            st.markdown(
                f"**{step}** {'✅' if i < (2 if 'transformed_df' in st.session_state else 1 if 'uploaded_file' in st.session_state else 0) else ''}"
            )

    # Step 1: Upload
    st.header(t["step1"])
    with st.expander("Supported Formats"):
        st.write("**CSV Example:**\n```ID,X,Y,Z\nSP001,100.5,200.3,10.2```")
        st.write("**KOF Example:**\n```05 AEP4 1194257.404 82692.090 2.075```")

    uploaded_file = st.file_uploader(
        t["step1"], type=["csv", "kof", "xlsx", "xls"], help=t["help_upload"]
    )
    if EXCEL_SUPPORT:
        template_file = create_excel_template()
        if template_file:
            st.download_button(
                label="📥 Download Excel Template",
                data=template_file,
                file_name="SiteCast_Survey_Template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # Step 2: Project Settings
    st.header(t["step2"])
    col_settings = st.columns(3)
    with col_settings[0]:
        project_name = st.text_input(
            "Project Name",
            value="Survey Project",
            help="Name of the project for IFC file",
        )
    with col_settings[1]:
        coord_system = st.radio(
            "Coordinate System",
            ["Global", "Local"],
            help="Local uses project basepoint offsets",
        )
    with col_settings[2]:
        use_basepoint = st.checkbox(
            "Use Basepoint",
            value=(coord_system == "Local"),
            help="Offset coordinates from a project basepoint",
        )

    if use_basepoint:
        with st.expander("Basepoint Settings"):
            col_x, col_y = st.columns(2)
            with col_x:
                basepoint_x = st.number_input(
                    "X (Easting)", value=1194000.0, format="%.3f"
                )
            with col_y:
                basepoint_y = st.number_input(
                    "Y (Northing)", value=82000.0, format="%.3f"
                )
            basepoint_z = st.number_input("Z (Elevation)", value=0.0, format="%.3f")
    else:
        basepoint_x = basepoint_y = basepoint_z = 0.0

    # Step 3: Data Review and Mapping
    if uploaded_file:
        st.header(t["step3"])
        try:
            file_extension = uploaded_file.name.split(".")[-1].lower()
            if file_extension == "csv":
                df = pd.read_csv(uploaded_file)
            elif file_extension in ["xlsx", "xls"]:
                df = pd.read_excel(uploaded_file, sheet_name=0)
            elif file_extension == "kof":
                file_content = uploaded_file.read().decode("utf-8", errors="ignore")
                parsed_data = parse_kof_file(file_content)
                if not parsed_data:
                    st.error("No valid coordinate data found in KOF file.")
                    st.stop()
                df = create_editable_table(parsed_data)
                st.subheader(t["mapping"])
                coord_order = st.selectbox(
                    "Coordinate Order",
                    ["X-Y-Z", "Y-X-Z", "X-Z-Y"],
                    help="Select the order of coordinates in the KOF file",
                )
                mapping = {
                    "ID": "ID",
                    "X": "Coord1"
                    if coord_order == "X-Y-Z"
                    else "Coord2"
                    if coord_order == "Y-X-Z"
                    else "Coord1",
                    "Y": "Coord2"
                    if coord_order == "X-Y-Z"
                    else "Coord1"
                    if coord_order == "Y-X-Z"
                    else "Coord3",
                    "Z": "Coord3"
                    if coord_order == "X-Y-Z"
                    else "Coord3"
                    if coord_order == "Y-X-Z"
                    else "Coord2",
                }
                df = apply_column_mapping(df, mapping)
            else:
                st.error("Unsupported file format.")
                st.stop()

            # Auto-detect for CSV/Excel
            if file_extension in ["csv", "xlsx", "xls"]:
                mapping = detect_coordinate_columns(df)
                df = apply_column_mapping(df, mapping)
                with st.expander(t["edit_mapping"]):
                    available_columns = [""] + list(df.columns)
                    col_map = {}
                    for col in ["ID", "X", "Y", "Z"]:
                        col_map[col] = st.selectbox(
                            f"{col} Column",
                            available_columns,
                            index=available_columns.index(mapping.get(col, ""))
                            if mapping.get(col) in available_columns
                            else 0,
                            key=f"{col}_col",
                        )
                    if st.button("Apply Mapping"):
                        df = apply_column_mapping(df, col_map)

            # Validate data
            if not all(col in df.columns for col in ["ID", "X", "Y", "Z"]):
                st.error("Missing required columns: ID, X, Y, Z")
                st.stop()

            # Apply transformation
            transformed_df = apply_coordinate_transformation(
                df.copy(), coord_system, basepoint_x, basepoint_y, basepoint_z
            )

            # Data preview
            st.subheader(t["preview"])
            st.data_editor(
                transformed_df[["ID", "X", "Y", "Z", "Description"]],
                use_container_width=True,
                column_config={
                    "ID": st.column_config.TextColumn("Point ID", required=True),
                    "X": st.column_config.NumberColumn("X (Easting)", format="%.3f"),
                    "Y": st.column_config.NumberColumn("Y (Northing)", format="%.3f"),
                    "Z": st.column_config.NumberColumn("Z (Elevation)", format="%.3f"),
                    "Description": st.column_config.TextColumn("Description"),
                },
            )

            # Plotly preview
            if "X" in transformed_df.columns and "Y" in transformed_df.columns:
                fig = px.scatter(
                    transformed_df,
                    x="X",
                    y="Y",
                    text="ID",
                    title="Survey Points Preview",
                )
                st.plotly_chart(fig, use_container_width=True)

            st.session_state.transformed_df = transformed_df
            st.success("✅ Data ready for IFC generation!")
        except Exception as e:
            handle_error(e, t["error_file"])

    # Generate IFC button (always visible)
    st.markdown("---")
    generate_disabled = "transformed_df" not in st.session_state
    st.button(
        t["generate_ifc"],
        type="primary",
        disabled=generate_disabled,
        help=t["generate_not_ready"] if generate_disabled else t["generate_ready"],
    )
    if not generate_disabled:
        with st.spinner("Creating IFC file..."):
            try:
                file, storey, context = create_ifc_file(
                    project_name,
                    "Project Site",
                    "Survey Building",
                    "Survey Level",
                    coord_system,
                    basepoint_x,
                    basepoint_y,
                    basepoint_z,
                )
                for _, row in st.session_state.transformed_df.iterrows():
                    create_survey_point(file, storey, context, row, None, "SiteCast")

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".ifc"
                ) as tmp_file:
                    file.write(tmp_file.name)
                    with open(tmp_file.name, "rb") as f:
                        ifc_data = f.read()
                    os.unlink(tmp_file.name)

                st.success("✅ IFC file generated!")
                st.download_button(
                    label="📥 Download IFC File",
                    data=ifc_data,
                    file_name=f"{project_name.replace(' ', '_')}_survey.ifc",
                    mime="application/octet-stream",
                )
                st.balloons()
            except Exception as e:
                handle_error(e, "Error generating IFC file")


if __name__ == "__main__":
    main()
