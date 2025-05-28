"""File parsing functions for various survey data formats"""

import pandas as pd
from ..config import COORDINATE_PATTERNS


def smart_parse_kof_file(file_content):
    """Smart parser for KOF format files"""
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
                    elif any(c.isalpha() for c in text) and any(
                        c.isdigit() for c in text
                    ):
                        if potential_id is None:
                            potential_id = text
                        else:
                            description_parts.append(text)
                    else:
                        description_parts.append(text)

                description = " ".join(description_parts) if description_parts else ""

                parsed_data.append(
                    {
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
                    }
                )

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

        table_data.append(
            {
                "ID": point_id,
                "Coord1": data["coord1"],
                "Coord2": data["coord2"],
                "Coord3": data["coord3"],
                "Description": data["description"],
                "Original_Line": data["original_line"],
            }
        )

    return pd.DataFrame(table_data)


def detect_coordinate_columns(df):
    """Smart detection of coordinate columns with N,E,Z naming patterns"""
    columns = [col.upper() for col in df.columns]
    mapping = {}

    # Find best matches for each coordinate type
    for coord_type, patterns in COORDINATE_PATTERNS.items():
        for pattern in patterns:
            # Check for exact matches first
            matches = [col for col in df.columns if col.upper() == pattern]
            if matches:
                mapping[coord_type.upper()] = matches[0]
                break
            
            # Check if pattern is contained in column name (with word boundaries)
            matches = [col for col in df.columns if pattern in col.upper().replace('_', ' ').split()]
            if matches:
                mapping[coord_type.upper()] = matches[0]
                break
            
            # Check if column contains the pattern as substring
            matches = [col for col in df.columns if pattern in col.upper()]
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
