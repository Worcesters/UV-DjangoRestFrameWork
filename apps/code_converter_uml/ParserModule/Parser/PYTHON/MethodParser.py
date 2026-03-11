"""
This module imports necessary dependencies and defines the MethodParser class.
"""

import re

# Import the Parser class from the PYTHON.Parser module
from ParserModule.Parser.PYTHON.Parser import Parser

# Import the Registry class from the Registry module
from Registry.Registry import Registry

# Import the necessary classes from the StructuralRegistry.Structure module
from Registry.RegistryModule.StructuralRegistry.Structure import RegistryMethod, RegistryParameter, RegistryAnnotation


from TreeModule.TreeElement import TreeElement


class MethodParser( Parser ):
    """
    This class parses methods.
    """

    def parse( self, line: str, registry: Registry, tree_element: TreeElement ):

        annotation_pattern = re.compile(r"""^[ \t]*\@(?P<mutability>\w+).*$""", re.VERBOSE | re.MULTILINE | re.DOTALL)

        for match in re.finditer( annotation_pattern, line ):
            #TODO -- Instance de RegistryMethod
            method_element = RegistryAnnotation()
            print(f"match annotation {match.group('mutability')}")
            method_element.set_mutability(match.group('mutability'))


        method_pattern = re.compile(
            r"""\bdef\s+(?P<method_name>\w+)\s*\((?P<method_params>.*?)\)(?:\s*->\s*(?P<return_type>[\w\.]+))?\s*:""",
            re.VERBOSE | re.MULTILINE | re.DOTALL
        )

        for match in re.finditer( method_pattern, line ):
            #TODO -- si Instance de RegistryMethod exist deja via le decorator, sinon en lancer une nouvelle
            method_element = RegistryMethod()
            method_element.set_name(match.group('method_name'))

            #method_element.set_visibility(self.get_visibility(match.group('visibility')))
            method_element.set_type(match.group('return_type'))

            params_str = match.group( 'method_params' )
            method_element.parameters = self.parse_parameters(params_str, method_element)

            if method_element is not None:
                active_tree_element = registry.get_active_element()
                if active_tree_element is not None:
                    method_element.set_parent(active_tree_element)
                    tree_element.add_child(method_element)

    def parse_parameters(self, params_str, method_element):
        """
        This function parses the parameters of a method.

        Args:
            params_str (str): The string containing the parameters.
            method_element (RegistryMethod): The method element to set the registry for.

        Returns:
            list: A list of RegistryParameter objects.
        """

        param_pattern = re.compile(
            r"""
            (?P<param_name>\w+)
            (?:\s*:\s*(?P<param_type>[\w\.\[\], ]+))?
            """,
            re.VERBOSE | re.MULTILINE | re.DOTALL
        )

        param_elements = []
        for match in re.finditer(param_pattern, params_str):
            param_element = RegistryParameter()
            param_name = match.group('param_name')
            if param_name == "self":
                continue

            param_element.set_name(param_name)
            param_element.set_type(match.group('param_type'))

            # Set the parent of the parameter element to the method element
            param_element.set_parent(method_element)
            param_elements.append(param_element)
        return param_elements
