import re
from ParserModule.Parser.PYTHON.Parser import Parser
from Registry.Registry import Registry
from Registry.RegistryModule.StructuralRegistry.Structure import RegistryAttribute
from TreeModule.TreeElement import TreeElement


class AttributeParser(Parser):
    """
    Parser for PHP attributes.

    This parser is responsible for parsing PHP lines and adding attributes to the registry.
    """

    def parse(self, line: str, registry: Registry, tree_element: TreeElement):
        """
        Parse a PHP line and add attributes to the registry.

        Args:
            line (str): The PHP line to parse.
            registry (Registry): The registry to add attributes to.
        """

        # Define the pattern to find PHP attributes
        attribute_pattern = re.compile(
            r"""
            # Match the 'self.' or 'cls.' prefix, or allow it to be absent for class variables
            ^\s*(?:(?P<prefix>self|cls)\.)?
            # Match the attribute name
            (?P<attribute_name>\w+)
            # Optionally match the type annotation
            (?:\s*:\s*(?P<type>[\w\.]+))?
            # Optionally match the assignment and value
            (?:\s*=\s*(?P<value>.*?))?
            # Match the end of the line
            \s*$
            """, re.VERBOSE | re.MULTILINE
        )

        # Find all matches in the line
        for match in re.finditer(attribute_pattern, line):
            # Create a new attribute element
            attribute_element = RegistryAttribute()

            # if match.group('visibility'):
            #     attribute_element.set_visibility(self.get_visibility(match.group('visibility')))

            # Set the attribute name and visibility
            attribute_element.set_name(match.group('attribute_name'))
            attribute_element.set_type(match.group('type'))

            # Add the attribute to the registry
            if attribute_element is not None:
                active_tree_element = registry.get_active_element()
                if active_tree_element is not None:
                    attribute_element.set_parent(active_tree_element)
                    tree_element.add_child(attribute_element)