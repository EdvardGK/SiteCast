# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SiteCast is a Streamlit web application that converts survey data (CSV, Excel, KOF) to BIM-ready IFC files. It specializes in handling Norwegian surveying standards and coordinate transformations.

## Common Commands

### Running the Application
```bash
streamlit run main.py
```

### Running Tests
```bash
# Run all tests
pytest originalUnicode/unitTesting.py -v

# Run specific test class
pytest originalUnicode/unitTesting.py::TestValidators -v

# Run with coverage
pytest originalUnicode/unitTesting.py --cov=sitecast
```

### Installation
```bash
pip install -r requirements.txt
```

## Architecture Overview

The codebase follows a modular architecture with clear separation of concerns:

1. **sitecast/core/** - Business logic layer
   - `parsers.py`: Handles CSV, Excel, and KOF file parsing with auto-detection
   - `processors.py`: Coordinate transformations between local/global systems
   - `validators.py`: Input validation and coordinate verification

2. **sitecast/ifc/** - IFC generation layer
   - `builder.py`: Main IFC file structure and hierarchy creation
   - `geometry.py` & `geometry_enhanced.py`: 3D geometry creation for survey markers
   - `properties.py`: Custom property sets for survey metadata
   - `info_cube.py`: Special information cube for project metadata

3. **sitecast/ui/** - Streamlit UI components
   - `sidebar.py`: Main configuration interface
   - `upload.py`: File upload and initial processing
   - `mapping.py`: Column mapping interface for flexible data import
   - `marker_configuration.py`: Visual marker customization

4. **sitecast/utils/** - Support utilities
   - `session.py`: Streamlit session state management
   - `verification.py`: Post-export coordinate verification

## Key Technical Details

- **Coordinate Systems**: Supports both local (Y,X,Z) and geographic (N,E,Z) with configurable basepoints
- **Unit Handling**: Auto-detects units (meters/millimeters/feet) with manual override
- **IFC Version**: Generates IFC4 files using ifcopenshell
- **Norwegian Standards**: Implements special basepoint markers (pie slices) per Norwegian BIM requirements
- **State Management**: Uses Streamlit session state for complex multi-step workflow

## Development Notes

- The `originalUnicode/` directory contains development scripts for modularization and testing
- Test data includes Norwegian coordinate examples (EPSG:25832 typical)
- The application handles large datasets efficiently using pandas
- Coordinate transformations use numpy and scikit-learn for rotation calculations