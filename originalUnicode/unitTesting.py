"""
Unit tests for the modularized SiteCast application
Run with: pytest tests/ -v
"""

# ===== tests/__init__.py =====
"""Test package for SiteCast"""

# ===== tests/conftest.py =====
"""Pytest configuration and shared fixtures"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_coordinate_data():
    """Create sample coordinate data for testing"""
    return pd.DataFrame(
        {
            "ID": ["SP001", "SP002", "SP003", "CP001", "BM001"],
            "N": [82692.090, 82687.146, 82673.960, 82667.760, 82711.966],
            "E": [1194257.404, 1194250.859, 1194233.405, 1194225.198, 1194245.717],
            "Z": [2.075, 2.295, 2.286, 2.298, 1.890],
            "Description": [
                "Survey Point 1",
                "Survey Point 2",
                "Survey Point 3",
                "Control Point",
                "Benchmark",
            ],
        }
    )


@pytest.fixture
def sample_kof_content():
    """Sample KOF file content"""
    return """05 AEP4 82692.090 1194257.404 2.075
05 AEP3 82687.146 1194250.859 2.295
05 AEP2 82673.960 1194233.405 2.286
-05 DISABLED 82667.760 1194225.198 2.298
09 BM001 82711.966 1194245.717 1.890"""


@pytest.fixture
def sample_csv_content():
    """Sample CSV file content"""
    return """ID,N,E,Z,Description
SP001,82692.090,1194257.404,2.075,Control Point
SP002,82687.146,1194250.859,2.295,Survey Point
SP003,82673.960,1194233.405,2.286,Benchmark"""


@pytest.fixture
def sample_config():
    """Sample configuration dictionary"""
    return {
        "project_name": "Test Project",
        "site_name": "Test Site",
        "building_name": "Test Building",
        "storey_name": "Test Level",
        "coord_system": "Local",
        "basepoint_n": 82000.0,
        "basepoint_e": 1194000.0,
        "basepoint_z": 0.0,
        "use_basepoint": True,
        "use_rotation_point": False,
        "rotation_n": 0.0,
        "rotation_e": 0.0,
        "rotation_z": 0.0,
        "marker_color": "#FF0000",
        "creator_name": "Test User",
        "external_link": "",
        "pset_name": "Test_Properties",
        "custom_properties": [{"name": "Test_Property", "value": "Test_Value"}],
        "verify_coordinates": True,
        "coordinate_units": "m (meters)",
        "unit_code": "m",
        "auto_detect_units": True,
    }


# ===== tests/test_validators.py =====
"""Test the coordinate validation module"""
import pytest
import pandas as pd
import numpy as np
from sitecast.core.validators import CoordinateValidator


class TestCoordinateValidator:
    def test_detect_units_meters(self, sample_coordinate_data):
        """Test unit detection for meter coordinates"""
        validator = CoordinateValidator()
        detected_units = validator.detect_units(sample_coordinate_data)
        assert detected_units == "m"

    def test_detect_units_millimeters(self):
        """Test unit detection for millimeter coordinates"""
        # Create data with large values suggesting millimeters
        df = pd.DataFrame(
            {
                "N": [82692090.0, 82687146.0, 82673960.0],
                "E": [1194257404.0, 1194250859.0, 1194233405.0],
                "Z": [2075.0, 2295.0, 2286.0],
            }
        )
        validator = CoordinateValidator()
        detected_units = validator.detect_units(df)
        assert detected_units == "mm"

    def test_convert_units_mm_to_m(self):
        """Test unit conversion from millimeters to meters"""
        df = pd.DataFrame(
            {
                "N": [1000.0, 2000.0, 3000.0],
                "E": [4000.0, 5000.0, 6000.0],
                "Z": [7000.0, 8000.0, 9000.0],
            }
        )
        validator = CoordinateValidator()
        converted_df = validator.convert_units(df, "mm", "m")

        assert converted_df["N"].iloc[0] == pytest.approx(1.0)
        assert converted_df["E"].iloc[1] == pytest.approx(5.0)
        assert converted_df["Z"].iloc[2] == pytest.approx(9.0)

    def test_convert_units_no_conversion(self, sample_coordinate_data):
        """Test that no conversion returns a copy"""
        validator = CoordinateValidator()
        converted_df = validator.convert_units(sample_coordinate_data, "m", "m")

        # Should be a copy, not the same object
        assert converted_df is not sample_coordinate_data
        # But values should be identical
        pd.testing.assert_frame_equal(converted_df, sample_coordinate_data)

    def test_validate_coordinates_success(self, sample_coordinate_data):
        """Test successful coordinate validation"""
        validator = CoordinateValidator()
        errors, warnings = validator.validate_coordinates(sample_coordinate_data)

        assert len(errors) == 0
        # May have warnings for large ranges or duplicates

    def test_validate_coordinates_missing_columns(self):
        """Test validation with missing required columns"""
        df = pd.DataFrame(
            {
                "ID": ["SP001", "SP002"],
                "N": [82692.090, 82687.146],
                # Missing E and Z columns
            }
        )
        validator = CoordinateValidator()
        errors, warnings = validator.validate_coordinates(df)

        assert len(errors) > 0
        assert any("Missing required columns" in error for error in errors)

    def test_validate_coordinates_non_numeric(self):
        """Test validation with non-numeric coordinate values"""
        df = pd.DataFrame(
            {
                "N": ["not", "numeric"],
                "E": [1194257.404, 1194250.859],
                "Z": [2.075, 2.295],
            }
        )
        validator = CoordinateValidator()
        errors, warnings = validator.validate_coordinates(df)

        assert len(errors) > 0
        assert any("must contain numeric values" in error for error in errors)

    def test_validate_coordinates_with_nulls(self):
        """Test validation with null values"""
        df = pd.DataFrame(
            {
                "N": [82692.090, np.nan, 82673.960],
                "E": [1194257.404, 1194250.859, np.nan],
                "Z": [2.075, 2.295, 2.286],
            }
        )
        validator = CoordinateValidator()
        errors, warnings = validator.validate_coordinates(df)

        assert len(errors) > 0
        assert any("missing values" in error for error in errors)

    def test_validate_coordinates_duplicate_warning(self):
        """Test duplicate coordinate detection"""
        df = pd.DataFrame(
            {
                "N": [82692.090, 82692.090, 82673.960],  # Duplicate first point
                "E": [1194257.404, 1194257.404, 1194233.405],
                "Z": [2.075, 2.075, 2.286],
            }
        )
        validator = CoordinateValidator()
        errors, warnings = validator.validate_coordinates(df)

        assert len(errors) == 0
        assert any("duplicate coordinate points" in warning for warning in warnings)


# ===== tests/test_processors.py =====
"""Test the survey data processor module"""
import pytest
import pandas as pd
import numpy as np
from sitecast.core.processors import SurveyProcessor


class TestSurveyProcessor:
    def test_transform_coordinates_local(self, sample_coordinate_data):
        """Test local coordinate transformation"""
        processor = SurveyProcessor(
            coord_system="Local",
            basepoint_n=82000.0,
            basepoint_e=1194000.0,
            basepoint_z=0.0,
        )

        transformed_df = processor.transform_coordinates(sample_coordinate_data)

        # Check that basepoint was subtracted
        assert transformed_df["N"].iloc[0] == pytest.approx(692.090)
        assert transformed_df["E"].iloc[0] == pytest.approx(257.404)
        assert transformed_df["Z"].iloc[0] == pytest.approx(2.075)

    def test_transform_coordinates_global(self, sample_coordinate_data):
        """Test global coordinate transformation (no change)"""
        processor = SurveyProcessor(
            coord_system="Global",
            basepoint_n=82000.0,
            basepoint_e=1194000.0,
            basepoint_z=0.0,
        )

        transformed_df = processor.transform_coordinates(sample_coordinate_data)

        # Should be unchanged for global coordinates
        pd.testing.assert_frame_equal(transformed_df, sample_coordinate_data)

    def test_calculate_north_direction_insufficient_points(self):
        """Test north calculation with insufficient points"""
        df = pd.DataFrame(
            {
                "N": [82692.090, 82687.146],  # Only 2 points
                "E": [1194257.404, 1194250.859],
            }
        )
        processor = SurveyProcessor()
        north_angle = processor.calculate_north_direction(df)

        assert north_angle == 0.0  # Should return 0 for < 3 points

    def test_calculate_north_direction_with_points(self, sample_coordinate_data):
        """Test north calculation with sufficient points"""
        processor = SurveyProcessor()
        north_angle = processor.calculate_north_direction(sample_coordinate_data)

        # Should return a valid angle
        assert isinstance(north_angle, (int, float))
        assert -180 <= north_angle <= 180


# ===== tests/test_parsers.py =====
"""Test the file parsing module"""
import pytest
import pandas as pd
from sitecast.core.parsers import (
    smart_parse_kof_file,
    create_editable_coordinate_table,
    detect_coordinate_columns,
    apply_column_mapping,
)


class TestParsers:
    def test_smart_parse_kof_file(self, sample_kof_content):
        """Test KOF file parsing"""
        parsed_data = smart_parse_kof_file(sample_kof_content)

        # Should parse 4 lines (disabled line excluded)
        assert len(parsed_data) == 4

        # Check first parsed line
        first_point = parsed_data[0]
        assert first_point["coord1"] == 82692.090
        assert first_point["coord2"] == 1194257.404
        assert first_point["coord3"] == 2.075
        assert first_point["potential_id"] == "AEP4"

    def test_smart_parse_kof_file_empty(self):
        """Test parsing empty KOF content"""
        parsed_data = smart_parse_kof_file("")
        assert len(parsed_data) == 0

    def test_smart_parse_kof_file_disabled_lines(self):
        """Test that disabled lines are skipped"""
        content = """-05 DISABLED 82667.760 1194225.198 2.298
05 ENABLED 82667.760 1194225.198 2.298"""
        parsed_data = smart_parse_kof_file(content)

        assert len(parsed_data) == 1
        assert parsed_data[0]["coord1"] == 82667.760

    def test_create_editable_coordinate_table(self):
        """Test creating editable table from parsed data"""
        parsed_data = [
            {
                "coord1": 82692.090,
                "coord2": 1194257.404,
                "coord3": 2.075,
                "potential_id": "AEP4",
                "description": "Test point",
                "original_line": "05 AEP4 82692.090 1194257.404 2.075",
            }
        ]

        df = create_editable_coordinate_table(parsed_data)

        assert len(df) == 1
        assert "ID" in df.columns
        assert df["ID"].iloc[0] == "AEP4"
        assert df["Coord1"].iloc[0] == 82692.090

    def test_detect_coordinate_columns(self):
        """Test automatic column detection"""
        df = pd.DataFrame(
            {
                "Point_ID": ["SP001", "SP002"],
                "Northing": [82692.090, 82687.146],
                "Easting": [1194257.404, 1194250.859],
                "Elevation": [2.075, 2.295],
                "Desc": ["Point 1", "Point 2"],
            }
        )

        mapping = detect_coordinate_columns(df)

        assert mapping["ID"] == "Point_ID"
        assert mapping["N"] == "Northing"
        assert mapping["E"] == "Easting"
        assert mapping["Z"] == "Elevation"
        assert mapping.get("DESC") == "Desc" or mapping.get("DESCRIPTION") == "Desc"

    def test_detect_coordinate_columns_fallback(self):
        """Test column detection fallback for non-standard names"""
        df = pd.DataFrame(
            {
                "Col1": ["SP001", "SP002"],
                "Col2": [82692.090, 82687.146],
                "Col3": [1194257.404, 1194250.859],
                "Col4": [2.075, 2.295],
            }
        )

        mapping = detect_coordinate_columns(df)

        # Should fallback to first available columns
        assert mapping["N"] == "Col1"  # First column
        assert mapping["E"] == "Col2"  # Second column
        assert mapping["Z"] == "Col3"  # Third column

    def test_apply_column_mapping(self):
        """Test applying column mapping"""
        df = pd.DataFrame(
            {
                "MyID": ["SP001", "SP002"],
                "MyN": [82692.090, 82687.146],
                "MyE": [1194257.404, 1194250.859],
                "MyZ": [2.075, 2.295],
                "MyDesc": ["Point 1", "Point 2"],
            }
        )

        mapping = {
            "ID": "MyID",
            "N": "MyN",
            "E": "MyE",
            "Z": "MyZ",
            "Description": "MyDesc",
        }

        mapped_df = apply_column_mapping(df, mapping)

        assert "ID" in mapped_df.columns
        assert "N" in mapped_df.columns
        assert mapped_df["ID"].iloc[0] == "SP001"
        assert mapped_df["N"].iloc[0] == 82692.090

    def test_apply_column_mapping_missing_columns(self):
        """Test mapping with missing optional columns"""
        df = pd.DataFrame(
            {
                "MyN": [82692.090, 82687.146],
                "MyE": [1194257.404, 1194250.859],
                "MyZ": [2.075, 2.295],
            }
        )

        mapping = {
            "N": "MyN",
            "E": "MyE",
            "Z": "MyZ",
            "ID": None,  # No ID column
            "Description": None,  # No description
        }

        mapped_df = apply_column_mapping(df, mapping)

        # Should create default ID and empty description
        assert "ID" in mapped_df.columns
        assert "Description" in mapped_df.columns
        assert mapped_df["ID"].iloc[0] == 1
        assert mapped_df["Description"].iloc[0] == ""


# ===== tests/test_ifc_builder.py =====
"""Test IFC file building functionality"""
import pytest
import ifcopenshell
from sitecast.ifc.builder import create_guid, create_ifc_file


class TestIFCBuilder:
    def test_create_guid(self):
        """Test GUID creation"""
        guid1 = create_guid()
        guid2 = create_guid()

        # Should be valid IFC GUID format (22 characters)
        assert len(guid1) == 22
        assert len(guid2) == 22

        # Should be unique
        assert guid1 != guid2

    def test_create_ifc_file(self, sample_config):
        """Test IFC file creation"""
        file, storey, context = create_ifc_file(
            sample_config["project_name"],
            sample_config["site_name"],
            sample_config["building_name"],
            sample_config["storey_name"],
            sample_config["coord_system"],
            sample_config["basepoint_n"],
            sample_config["basepoint_e"],
            sample_config["basepoint_z"],
        )

        # Check file is created
        assert file is not None
        assert isinstance(file, ifcopenshell.file)

        # Check hierarchy is created
        projects = file.by_type("IfcProject")
        assert len(projects) == 1
        assert projects[0].Name == sample_config["project_name"]

        sites = file.by_type("IfcSite")
        assert len(sites) == 1
        assert sites[0].Name == sample_config["site_name"]

        buildings = file.by_type("IfcBuilding")
        assert len(buildings) == 1
        assert buildings[0].Name == sample_config["building_name"]

        storeys = file.by_type("IfcBuildingStorey")
        assert len(storeys) == 1
        assert storeys[0].Name == sample_config["storey_name"]

        # Check context is valid
        assert context is not None
        assert context.is_a("IfcGeometricRepresentationSubContext")


# ===== tests/test_integration.py =====
"""Integration tests for the complete workflow"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path


class TestIntegration:
    def test_csv_to_ifc_workflow(self, sample_coordinate_data, sample_config):
        """Test complete workflow from CSV data to IFC file"""
        from sitecast.core.validators import CoordinateValidator
        from sitecast.core.processors import SurveyProcessor
        from sitecast.ifc.builder import create_ifc_file
        from sitecast.ifc.materials import create_material

        # Validate coordinates
        validator = CoordinateValidator()
        errors, warnings = validator.validate_coordinates(sample_coordinate_data)
        assert len(errors) == 0

        # Process coordinates
        processor = SurveyProcessor(
            sample_config["coord_system"],
            sample_config["basepoint_n"],
            sample_config["basepoint_e"],
            sample_config["basepoint_z"],
        )
        transformed_df = processor.transform_coordinates(sample_coordinate_data)

        # Create IFC file
        file, storey, context = create_ifc_file(
            sample_config["project_name"],
            sample_config["site_name"],
            sample_config["building_name"],
            sample_config["storey_name"],
        )

        # Create material
        material = create_material(file, "Test Material", (1.0, 0.0, 0.0))

        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            file.write(tmp.name)

            # Verify file exists and has content
            assert os.path.exists(tmp.name)
            assert os.path.getsize(tmp.name) > 0

            # Clean up
            os.unlink(tmp.name)

    def test_kof_parsing_integration(self, sample_kof_content):
        """Test KOF file parsing integration"""
        from sitecast.core.parsers import (
            smart_parse_kof_file,
            create_editable_coordinate_table,
        )

        # Parse KOF content
        parsed_data = smart_parse_kof_file(sample_kof_content)
        assert len(parsed_data) > 0

        # Create editable table
        df = create_editable_coordinate_table(parsed_data)
        assert len(df) == len(parsed_data)
        assert all(col in df.columns for col in ["ID", "Coord1", "Coord2", "Coord3"])


# ===== tests/test_utils.py =====
"""Test utility functions"""
import pytest
import pandas as pd
from io import BytesIO


class TestUtils:
    def test_excel_template_creation(self):
        """Test Excel template generation"""
        from sitecast.utils.templates import create_excel_template, EXCEL_SUPPORT

        if not EXCEL_SUPPORT:
            pytest.skip("Excel support not available")

        template_data = create_excel_template()
        assert template_data is not None
        assert len(template_data) > 0

        # Should be valid Excel file
        df = pd.read_excel(BytesIO(template_data), sheet_name=0)
        assert len(df) > 0
        assert "ID" in df.columns
        assert "N_Northing" in df.columns
        assert "E_Easting" in df.columns
        assert "Z_Elevation" in df.columns


# ===== setup_tests.py =====
"""Script to set up the test structure"""
from pathlib import Path


def create_test_structure():
    """Create the test directory structure and files"""
    base_path = Path(r"C:\LokalMappe_Blade15\CodingProjects\SiteCast")
    tests_path = base_path / "tests"

    # Create tests directory
    tests_path.mkdir(exist_ok=True)

    # Create test files
    test_files = {
        "__init__.py": '"""Test package for SiteCast"""',
        "conftest.py": open(__file__)
        .read()
        .split("# ===== tests/conftest.py =====")[1]
        .split("# =====")[0],
        "test_validators.py": open(__file__)
        .read()
        .split("# ===== tests/test_validators.py =====")[1]
        .split("# =====")[0],
        "test_processors.py": open(__file__)
        .read()
        .split("# ===== tests/test_processors.py =====")[1]
        .split("# =====")[0],
        "test_parsers.py": open(__file__)
        .read()
        .split("# ===== tests/test_parsers.py =====")[1]
        .split("# =====")[0],
        "test_ifc_builder.py": open(__file__)
        .read()
        .split("# ===== tests/test_ifc_builder.py =====")[1]
        .split("# =====")[0],
        "test_integration.py": open(__file__)
        .read()
        .split("# ===== tests/test_integration.py =====")[1]
        .split("# =====")[0],
        "test_utils.py": open(__file__)
        .read()
        .split("# ===== tests/test_utils.py =====")[1]
        .split("# =====")[0],
    }

    for filename, content in test_files.items():
        file_path = tests_path / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created: tests/{filename}")

    # Create pytest.ini
    pytest_ini = """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
"""

    pytest_ini_path = base_path / "pytest.ini"
    with open(pytest_ini_path, "w", encoding="utf-8") as f:
        f.write(pytest_ini)
    print(f"✅ Created: pytest.ini")

    print("\n✨ Test structure created successfully!")
    print("\nTo run tests:")
    print("  pytest                    # Run all tests")
    print("  pytest -v                 # Verbose output")
    print("  pytest tests/test_validators.py  # Run specific test file")
    print("  pytest -k test_detect_units      # Run tests matching pattern")
    print("  pytest --cov=sitecast            # With coverage report")


if __name__ == "__main__":
    create_test_structure()
