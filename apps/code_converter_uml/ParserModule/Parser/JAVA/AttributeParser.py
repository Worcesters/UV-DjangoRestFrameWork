import re
from ParserModule.Parser.JAVA.Parser import Parser
from Registry.Registry import Registry
from Registry.RegistryModule.StructuralRegistry.Structure import RegistryAttribute
from TreeModule.TreeElement import TreeElement


class AttributeParser(Parser):
    """
    Parser for JAVA attributes.

    This parser is responsible for parsing JAVA lines and adding attributes to the registry.
    """

    def parse(self, line: str, registry: Registry, tree_element: TreeElement):
        """
        Parse a JAVA line and add attributes to the registry.

        Args:
            line (str): The JAVA line to parse.
            registry (Registry): The registry to add attributes to.
        """

        # Define the pattern to find JAVA attributes
        attribute_pattern = re.compile(r"""(?P<visibility>public|protected|private)(?!\s+class)\s*"""
                                       r"""\b(?P<mutability>(static|void|synchronized|native|abstract|transient|volatile|final|\w+)\s+)*"""
                                       r"""(?P<type>\w+)\s+"""
                                       r"""(?P<attribute_name>\w+)(?!\s*\()""")

        # Find all matches in the line
        for match in re.finditer(attribute_pattern, line):
            if match.group('visibility'):
                # Create a new attribute element
                attribute_element = RegistryAttribute()
                # Set the attribute name and visibility
                attribute_element.set_type(match.group('type'))
                attribute_element.set_name(match.group('attribute_name'))
                attribute_element.set_mutability(match.group('mutability'))
                attribute_element.set_visibility(self.get_visibility(match.group('visibility')))
                # Add the attribute to the registry
                if attribute_element is not None:
                    active_tree_element = registry.get_active_element()
                    if active_tree_element is not None:
                        attribute_element.set_parent(active_tree_element)
                        tree_element.add_child(attribute_element)