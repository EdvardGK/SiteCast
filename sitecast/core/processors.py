"""Survey data processing and coordinate transformations"""

import numpy as np

# Try to import sklearn for advanced north calculation
try:
    from sklearn.decomposition import PCA

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


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
                north_angle = np.degrees(
                    np.arctan2(primary_direction[0], primary_direction[1])
                )

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
