from abc import ABC

# Import the RegistryVisibility and RegistryType enums from the StructuralRegistry module.
from Registry.Enum import RegistryVisibility, RegistryType

# Import the IParser interface from the Parser module.
from ParserModule.Parser.Interface import IParser


class Parser( IParser, ABC ):
    """
    The Parser class represents a Parser. It inherits from the IParser ABC (Abstract Base Class).
    """
    def __init__( self ):
        """
        Initialize the Parser with the visibility and type mappings.
        """
        # Mapping for visibility
        self.visibility_mapping = {
            'public': RegistryVisibility.PUBLIC,
            'protected': RegistryVisibility.PROTECTED,
            'private': RegistryVisibility.PRIVATE
        }

        self.type_mapping = {
            'string': RegistryType.STRING,
            'int': RegistryType.INT,
            'float': RegistryType.FLOAT,
            'bool': RegistryType.BOOL,
            'array': RegistryType.ARRAY,
            'object': RegistryType.OBJECT,
            'null': RegistryType.NULL,
            'void': RegistryType.VOID,
            'resource': RegistryType.RESOURCE,
            'mixed': RegistryType.MIXED,
            'class': RegistryType.CLASS,
            'trait': RegistryType.TRAIT,
            'function': RegistryType.FUNCTION,
            'constant': RegistryType.CONSTANT,
            'interface': RegistryType.INTERFACE,
            'enum': RegistryType.ENUM,
            'namespace': RegistryType.NAMESPACE,
            'tuple': RegistryType.TUPLE,
            'union': RegistryType.UNION,
            'keyword': RegistryType.KEYWORD,
            'unknown': RegistryType.UNKNOWN,
        }

    def get_visibility(self, visibility: str) -> RegistryVisibility:
        """
        Get the visibility from the visibility mapping.

        Args:
            visibility (str): The visibility to get.

        Returns:
            RegistryVisibility: The corresponding RegistryVisibility.
        """
        return self.visibility_mapping.get(visibility, RegistryVisibility.PUBLIC).value

    def get_type(self, element_type: str) -> RegistryType:
        """
        Get the type from the type mapping.

        Args:
            element_type (str): The type to get.

        Returns:
            RegistryType: The corresponding RegistryType.
        """
        return self.type_mapping.get(element_type, RegistryType.UNKNOWN).value