# SiteCast - Survey to BIM Converter

Convert survey data to BIM-ready IFC files in 30 seconds.

## Features

- Support for CSV, Excel (XLSX/XLS), and KOF formats
- Automatic coordinate system detection
- Unit conversion (meters, millimeters, feet)
- Project basepoint and rotation point support
- Custom property sets for survey points
- Coordinate verification
- IFC4 output format

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the Streamlit app:
```bash
streamlit run main.py
```

## Project Structure

```
sitecast/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── sitecast/           # Main package
│   ├── config.py       # Configuration
│   ├── core/           # Core logic
│   ├── ifc/            # IFC generation
│   ├── ui/             # User interface
│   └── utils/          # Utilities
```

## UI Module Implementation

The UI modules need to be completed with the full implementation from the modularized code.
Copy the implementations for:
- `sitecast/ui/sidebar.py`
- `sitecast/ui/upload.py`
- `sitecast/ui/mapping.py`
- `sitecast/ui/export.py`

## License

[Your License Here]
