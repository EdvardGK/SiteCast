"""Coordinate verification utilities"""

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

                            # Check if coordinates match
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
