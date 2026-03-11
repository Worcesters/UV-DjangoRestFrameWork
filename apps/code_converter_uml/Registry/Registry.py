from TreeModule.Tree import Tree
from TreeModule.TreeElement import TreeElement
from Registry.RegistryElement import RegistryElement

class Registry( Tree ):
    """
    This class implements a registry of structural elements.
    The registry is a tree, where the root is the root of the source code,
    and each branch represents a sub structure of the code.
    The registry allows to navigate through the code and to keep track of the
    current structural element.
    """

    def __init__( self, root_element ):
        super().__init__()

        if not isinstance(root_element, RegistryProgram):
            raise TypeError("The root_element should be an instance of RegistryProgram.")

        if self.get_root() is None:
            self.set_root( TreeElement(root_element) )
        self.set_active_element( root_element )

    def set_active_element( self, active_element: RegistryElement ):
        """
        Set the current structural element of the registry
        :param active_element: The structural element to be set as active
        :type active_element: StructuralElement
        """
        self.active_element = active_element

    def get_active_element( self ):
        """
        Get the current structural element of the registry
        :return: The current structural element of the registry
        :rtype: StructuralElement
        """
        return self.active_element

class RegistryProgram( RegistryElement ):
    """
    Represents a registry program, which is the top level element of the registry

    The registry program is the root of the tree and contains all the other
    structural elements of the code.
    """

    def __init__(self, config, tree_element: TreeElement) -> None:
        self.config = config
        self.tree_element = tree_element

    def buildUml( self ) -> str:

        uml_str = '\n'
        parents = set(child.get_parent() for child in self.tree_element.get_children())
        for parent in parents:
            uml_str += parent.buildUml()
            for child in self.tree_element.get_children():
                if child.get_parent() == parent:
                    uml_str += f"  {child.buildUml()}"
            uml_str += "}\n\n\n"

        for heritage in self.tree_element.heritages:
            uml_str += heritage.buildUml()

        return f"""@startuml
skinparam backgroundColor #F5F5F5
skinparam shadowing false

skinparam class {{
  BackgroundColor #FFFFFF
  BorderColor #4A4A4A
  FontName Helvetica
  FontSize 14
  FontColor #333333
  AttributeFontColor #666666
  AttributeFontSize 12
  StereotypeFontSize 12
  StereotypeFontColor #999999
  RoundCorner 15
}}

skinparam package {{
  BackgroundColor #DDDDDD
  BorderColor #4A4A4A
  FontName Helvetica
  FontSize 14
  FontColor #333333
  RoundCorner 15
}}

skinparam Arrow {{
  Color #4A4A4A
  Thickness 2
  FontName Helvetica
  FontSize 12
  FontColor #333333
}}

{uml_str}

@enduml"""
