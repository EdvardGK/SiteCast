"""IFC file creation and structure"""

import uuid
try:
    import ifcopenshell
    USE_IFCOPENSHELL = True
except ImportError:
    USE_IFCOPENSHELL = False
    from .ifc_writer import IFCWriter, IFCBuilder


def create_guid():
    """Create a new GUID for IFC entities"""
    if USE_IFCOPENSHELL:
        return ifcopenshell.guid.compress(uuid.uuid4().hex)
    else:
        # Use our custom GUID generator
        writer = IFCWriter()
        return writer.create_guid()


def create_ifc_file(
    project_name,
    site_name,
    building_name,
    storey_name,
    coord_system="Global",
    basepoint_n=0.0,
    basepoint_e=0.0,
    basepoint_z=0.0,
):
    """Create a new IFC file with basic setup"""
    if USE_IFCOPENSHELL:
        # Original ifcopenshell implementation
        file = ifcopenshell.file(schema="IFC4")

        # Project setup
        project = file.create_entity(
            "IfcProject", GlobalId=create_guid(), Name=project_name
        )
        unit_assignment = file.create_entity("IfcUnitAssignment")
        length_unit = file.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
        unit_assignment.Units = [length_unit]
        project.UnitsInContext = unit_assignment

        # Use (0,0,0) as world origin
        world_origin = (0.0, 0.0, 0.0)

        # Context setup
        context = file.create_entity(
            "IfcGeometricRepresentationContext",
            ContextIdentifier=None,
            ContextType="Model",
            CoordinateSpaceDimension=3,
            Precision=1.0e-5,
            WorldCoordinateSystem=file.create_entity(
                "IfcAxis2Placement3D",
                Location=file.create_entity("IfcCartesianPoint", Coordinates=world_origin),
            ),
        )
        body_context = file.create_entity(
            "IfcGeometricRepresentationSubContext",
            ContextIdentifier="Body",
            ContextType="Model",
            ParentContext=context,
            TargetView="MODEL_VIEW",
        )

        # Hierarchy setup
        site = file.create_entity("IfcSite", GlobalId=create_guid(), Name=site_name)
        building = file.create_entity(
            "IfcBuilding", GlobalId=create_guid(), Name=building_name
        )
        storey = file.create_entity(
            "IfcBuildingStorey", GlobalId=create_guid(), Name=storey_name
        )

        # Relationships
        file.create_entity(
            "IfcRelAggregates",
            GlobalId=create_guid(),
            RelatingObject=project,
            RelatedObjects=[site],
        )
        file.create_entity(
            "IfcRelAggregates",
            GlobalId=create_guid(),
            RelatingObject=site,
            RelatedObjects=[building],
        )
        file.create_entity(
            "IfcRelAggregates",
            GlobalId=create_guid(),
            RelatingObject=building,
            RelatedObjects=[storey],
        )

        return file, storey, body_context
    else:
        # Use our custom IFC writer
        builder = IFCBuilder()
        builder.create_project(project_name)
        
        # Store the basepoint information in the builder
        builder.basepoint = {
            'n': basepoint_n,
            'e': basepoint_e,
            'z': basepoint_z
        }
        builder.coord_system = coord_system
        
        # Return compatible objects
        class MockFile:
            def __init__(self, builder):
                self.builder = builder
                
            def create_entity(self, entity_type, **kwargs):
                # Convert to our writer format
                entity_id = self.builder.writer.add_entity(entity_type, **kwargs)
                
                # Return a mock entity object
                class MockEntity:
                    def __init__(self, id, type):
                        self.id = id
                        self.type = type
                        
                return MockEntity(entity_id, entity_type)
                
            def write(self, filepath):
                self.builder.write(filepath)
        
        mock_file = MockFile(builder)
        
        # Return mock objects that are compatible with the rest of the code
        class MockStorey:
            def __init__(self, id):
                self.id = id
                
        class MockContext:
            def __init__(self, id):
                self.id = id
                
        return mock_file, MockStorey(builder.storey_id), MockContext(builder.context_id)