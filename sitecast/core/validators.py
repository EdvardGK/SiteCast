"""Coordinate validation and quality checks"""

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
