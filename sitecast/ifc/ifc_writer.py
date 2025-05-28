"""Custom IFC writer - no dependencies required"""

import uuid
import datetime
from typing import List, Tuple, Dict, Any


class IFCWriter:
    """Lightweight IFC4 file writer"""
    
    def __init__(self):
        self.entities = []
        self.entity_counter = 0
        self.file_schema = "IFC4"
        self.header_info = {
            'description': ('ViewDefinition [CoordinationView]',),
            'implementation_level': '2;1',
            'name': 'SiteCast Survey to IFC Converter',
            'author': ('SiteCast User',),
            'organization': ('SiteCast',),
            'preprocessor_version': 'SiteCast-1.0',
            'originating_system': 'SiteCast Survey Converter',
            'authorization': 'None'
        }
        
    def create_guid(self) -> str:
        """Create IFC compliant GUID"""
        # IFC uses a specific 22-character base64-like encoding
        guid = uuid.uuid4()
        # Simplified GUID generation (IFC uses GlobalId compression)
        return self._compress_guid(guid.hex)
    
    def _compress_guid(self, hex_string: str) -> str:
        """Compress UUID to IFC GlobalId format (simplified)"""
        # IFC uses a base64-like encoding with specific character set
        # This is a simplified version
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"
        result = ""
        num = int(hex_string, 16)
        
        for _ in range(22):
            result = chars[num % 64] + result
            num //= 64
            
        return result[:22].ljust(22, '0')
    
    def add_entity(self, entity_type: str, **attributes) -> int:
        """Add an entity and return its ID"""
        self.entity_counter += 1
        entity_id = self.entity_counter
        
        self.entities.append({
            'id': entity_id,
            'type': entity_type,
            'attributes': attributes
        })
        
        return entity_id
    
    def format_value(self, value: Any) -> str:
        """Format a value for IFC output"""
        if value is None:
            return "$"
        elif isinstance(value, bool):
            return ".T." if value else ".F."
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (list, tuple)):
            if len(value) == 0:
                return "()"
            formatted = [self.format_value(v) for v in value]
            return f"({','.join(formatted)})"
        elif isinstance(value, dict) and 'ref' in value:
            return f"#{value['ref']}"
        else:
            return str(value)
    
    def write(self, filepath: str):
        """Write IFC file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write header
            f.write("ISO-10303-21;\n")
            f.write("HEADER;\n")
            
            # File description
            f.write("FILE_DESCRIPTION(")
            f.write(self.format_value(self.header_info['description']))
            f.write(",")
            f.write(self.format_value(self.header_info['implementation_level']))
            f.write(");\n")
            
            # File name
            timestamp = datetime.datetime.now().isoformat()
            f.write("FILE_NAME(")
            f.write(f"'{filepath}',")
            f.write(f"'{timestamp}',")
            f.write(self.format_value(self.header_info['author']))
            f.write(",")
            f.write(self.format_value(self.header_info['organization']))
            f.write(",")
            f.write(self.format_value(self.header_info['preprocessor_version']))
            f.write(",")
            f.write(self.format_value(self.header_info['originating_system']))
            f.write(",")
            f.write(self.format_value(self.header_info['authorization']))
            f.write(");\n")
            
            # File schema
            f.write(f"FILE_SCHEMA(('{self.file_schema}'));\n")
            f.write("ENDSEC;\n")
            
            # Write data section
            f.write("DATA;\n")
            
            for entity in self.entities:
                f.write(f"#{entity['id']}=")
                f.write(entity['type'].upper())
                f.write("(")
                
                # Write attributes in order
                attrs = entity['attributes']
                attr_values = []
                
                # Handle ordered attributes based on entity type
                if entity['type'] == 'IfcProject':
                    attr_order = ['GlobalId', 'OwnerHistory', 'Name', 'Description', 'ObjectType', 'LongName', 'Phase', 'RepresentationContexts', 'UnitsInContext']
                elif entity['type'] == 'IfcCartesianPoint':
                    attr_order = ['Coordinates']
                elif entity['type'] == 'IfcDirection':
                    attr_order = ['DirectionRatios']
                else:
                    attr_order = sorted(attrs.keys())
                
                for key in attr_order:
                    if key in attrs:
                        attr_values.append(self.format_value(attrs[key]))
                    else:
                        attr_values.append("$")
                
                f.write(",".join(attr_values))
                f.write(");\n")
            
            f.write("ENDSEC;\n")
            f.write("END-ISO-10303-21;\n")


class IFCBuilder:
    """Builder for creating IFC files with survey points"""
    
    def __init__(self):
        self.writer = IFCWriter()
        self.project_id = None
        self.site_id = None
        self.building_id = None
        self.storey_id = None
        self.context_id = None
        
    def create_project(self, name: str = "Survey Project") -> 'IFCBuilder':
        """Create project hierarchy"""
        # Create units
        meter_id = self.writer.add_entity(
            'IfcSIUnit',
            UnitType='LENGTHUNIT',
            Name='METRE'
        )
        
        unit_assignment_id = self.writer.add_entity(
            'IfcUnitAssignment',
            Units=[{'ref': meter_id}]
        )
        
        # Create geometric context
        origin_id = self.writer.add_entity(
            'IfcCartesianPoint',
            Coordinates=[0.0, 0.0, 0.0]
        )
        
        z_dir_id = self.writer.add_entity(
            'IfcDirection',
            DirectionRatios=[0.0, 0.0, 1.0]
        )
        
        x_dir_id = self.writer.add_entity(
            'IfcDirection',
            DirectionRatios=[1.0, 0.0, 0.0]
        )
        
        axis_placement_id = self.writer.add_entity(
            'IfcAxis2Placement3D',
            Location={'ref': origin_id},
            Axis={'ref': z_dir_id},
            RefDirection={'ref': x_dir_id}
        )
        
        self.context_id = self.writer.add_entity(
            'IfcGeometricRepresentationContext',
            ContextType='Model',
            CoordinateSpaceDimension=3,
            Precision=0.00001,
            WorldCoordinateSystem={'ref': axis_placement_id}
        )
        
        # Create project
        self.project_id = self.writer.add_entity(
            'IfcProject',
            GlobalId=self.writer.create_guid(),
            Name=name,
            UnitsInContext={'ref': unit_assignment_id}
        )
        
        # Create site
        self.site_id = self.writer.add_entity(
            'IfcSite',
            GlobalId=self.writer.create_guid(),
            Name='Project Site'
        )
        
        # Create building
        self.building_id = self.writer.add_entity(
            'IfcBuilding',
            GlobalId=self.writer.create_guid(),
            Name='Survey Building'
        )
        
        # Create storey
        self.storey_id = self.writer.add_entity(
            'IfcBuildingStorey',
            GlobalId=self.writer.create_guid(),
            Name='Survey Level'
        )
        
        # Create relationships
        self.writer.add_entity(
            'IfcRelAggregates',
            GlobalId=self.writer.create_guid(),
            RelatingObject={'ref': self.project_id},
            RelatedObjects=[{'ref': self.site_id}]
        )
        
        self.writer.add_entity(
            'IfcRelAggregates',
            GlobalId=self.writer.create_guid(),
            RelatingObject={'ref': self.site_id},
            RelatedObjects=[{'ref': self.building_id}]
        )
        
        self.writer.add_entity(
            'IfcRelAggregates',
            GlobalId=self.writer.create_guid(),
            RelatingObject={'ref': self.building_id},
            RelatedObjects=[{'ref': self.storey_id}]
        )
        
        return self
    
    def add_survey_point(self, point_id: str, x: float, y: float, z: float, 
                        description: str = "", color: Tuple[float, float, float] = (1.0, 0.0, 0.0)) -> 'IFCBuilder':
        """Add a survey point"""
        # Create point geometry
        location_id = self.writer.add_entity(
            'IfcCartesianPoint',
            Coordinates=[x, y, z]
        )
        
        # Create a simple box to represent the point
        box_points = []
        size = 0.2  # 20cm marker
        for dx in [-size/2, size/2]:
            for dy in [-size/2, size/2]:
                for dz in [0, size]:
                    point_id_temp = self.writer.add_entity(
                        'IfcCartesianPoint',
                        Coordinates=[dx, dy, dz]
                    )
                    box_points.append({'ref': point_id_temp})
        
        # Create placement
        placement_id = self.writer.add_entity(
            'IfcLocalPlacement',
            RelativePlacement={'ref': self.writer.add_entity(
                'IfcAxis2Placement3D',
                Location={'ref': location_id}
            )}
        )
        
        # Create proxy element for survey point
        proxy_id = self.writer.add_entity(
            'IfcBuildingElementProxy',
            GlobalId=self.writer.create_guid(),
            Name=f'Survey Point {point_id}',
            Description=description,
            ObjectPlacement={'ref': placement_id}
        )
        
        # Add to storey
        self.writer.add_entity(
            'IfcRelContainedInSpatialStructure',
            GlobalId=self.writer.create_guid(),
            RelatingStructure={'ref': self.storey_id},
            RelatedElements=[{'ref': proxy_id}]
        )
        
        # Add properties
        props = []
        
        # Point ID property
        prop_id = self.writer.add_entity(
            'IfcPropertySingleValue',
            Name='PointID',
            NominalValue={'type': 'IfcText', 'value': point_id}
        )
        props.append({'ref': prop_id})
        
        # Coordinates property
        coord_prop = self.writer.add_entity(
            'IfcPropertySingleValue',
            Name='Coordinates',
            NominalValue={'type': 'IfcText', 'value': f'N:{y:.3f}, E:{x:.3f}, Z:{z:.3f}'}
        )
        props.append({'ref': coord_prop})
        
        # Create property set
        pset_id = self.writer.add_entity(
            'IfcPropertySet',
            GlobalId=self.writer.create_guid(),
            Name='SurveyPointProperties',
            HasProperties=props
        )
        
        # Relate properties to element
        self.writer.add_entity(
            'IfcRelDefinesByProperties',
            GlobalId=self.writer.create_guid(),
            RelatedObjects=[{'ref': proxy_id}],
            RelatingPropertyDefinition={'ref': pset_id}
        )
        
        return self
    
    def write(self, filepath: str):
        """Write the IFC file"""
        self.writer.write(filepath)