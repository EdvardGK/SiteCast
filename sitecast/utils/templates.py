"""Excel template generation utilities"""

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
        "ID": ["P01", "SP02", "SP03", "CP01", "BM02"],
        "N_Northing": [1194257.404, 1194250.859, 1194233.405, 1194225.198, 1194245.717],
        "E_Easting": [82692.090, 82687.146, 82673.960, 82667.760, 82711.966],
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
