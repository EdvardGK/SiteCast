"""Coordinate verification utilities"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

try:
    import ifcopenshell
    USE_IFCOPENSHELL = True
except ImportError:
    USE_IFCOPENSHELL = False


def verify_ifc_coordinates(
    ifc_path: str, original_df: pd.DataFrame, offsets: Dict[str, float]
) -> List[Dict[str, Any]]:
    """Verify that IFC coordinates match expected values"""
    if not USE_IFCOPENSHELL:
        return verify_ifc_coordinates_simple(ifc_path, original_df, offsets)
        
    try:
        # Original ifcopenshell implementation
        ifc_file = ifcopenshell.open(ifc_path)
        results = []

        # Get all annotations (survey points)
        annotations = ifc_file.by_type("IfcAnnotation")

        for idx, row in original_df.iterrows():
            point_id = str(row.get("ID", f"Unknown_{idx}"))
            expected_n = float(row["N"]) - offsets["N"]
            expected_e = float(row["E"]) - offsets["E"]
            expected_z = float(row["Z"]) - offsets["Z"]

            # Find matching annotation
            found = False
            for annotation in annotations:
                if point_id in str(annotation.Name):
                    # Get placement
                    if annotation.ObjectPlacement:
                        placement = annotation.ObjectPlacement
                        if placement.RelativePlacement:
                            location = placement.RelativePlacement.Location
                            if location:
                                coords = location.Coordinates
                                if coords and len(coords) == 3:
                                    ifc_e, ifc_n, ifc_z = coords
                                    
                                    # Check if coordinates match (within tolerance)
                                    tolerance = 0.001  # 1mm
                                    n_match = abs(ifc_n - expected_n) < tolerance
                                    e_match = abs(ifc_e - expected_e) < tolerance
                                    z_match = abs(ifc_z - expected_z) < tolerance
                                    
                                    results.append({
                                        "point_id": point_id,
                                        "expected": {"N": expected_n, "E": expected_e, "Z": expected_z},
                                        "found": {"N": ifc_n, "E": ifc_e, "Z": ifc_z},
                                        "matches": {"N": n_match, "E": e_match, "Z": z_match},
                                        "all_match": n_match and e_match and z_match,
                                    })
                                    found = True
                                    break

            if not found:
                results.append({
                    "point_id": point_id,
                    "expected": {"N": expected_n, "E": expected_e, "Z": expected_z},
                    "found": None,
                    "matches": {"N": False, "E": False, "Z": False},
                    "all_match": False,
                })

        return results

    except Exception as e:
        return f"Error during verification: {str(e)}"


def verify_ifc_coordinates_simple(
    ifc_path: str, original_df: pd.DataFrame, offsets: Dict[str, float]
) -> List[Dict[str, Any]]:
    """Simple verification by parsing IFC text file"""
    try:
        results = []
        
        # Read IFC file as text
        with open(ifc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # For each point in original data
        for idx, row in original_df.iterrows():
            point_id = str(row.get("ID", f"Unknown_{idx}"))
            expected_n = float(row["N"]) - offsets["N"]
            expected_e = float(row["E"]) - offsets["E"]
            expected_z = float(row["Z"]) - offsets["Z"]
            
            # Simple check - look for the point ID and nearby coordinates
            found = False
            if f"Survey Point {point_id}" in content:
                # Try to find coordinates near this point mention
                # This is a simplified check
                coord_str = f"{expected_e:.3f},{expected_n:.3f},{expected_z:.3f}"
                if coord_str in content:
                    found = True
                    results.append({
                        "point_id": point_id,
                        "expected": {"N": expected_n, "E": expected_e, "Z": expected_z},
                        "found": {"N": expected_n, "E": expected_e, "Z": expected_z},
                        "matches": {"N": True, "E": True, "Z": True},
                        "all_match": True,
                    })
            
            if not found:
                results.append({
                    "point_id": point_id,
                    "expected": {"N": expected_n, "E": expected_e, "Z": expected_z},
                    "found": None,
                    "matches": {"N": False, "E": False, "Z": False},
                    "all_match": False,
                })
        
        return results
        
    except Exception as e:
        return f"Error during verification: {str(e)}"