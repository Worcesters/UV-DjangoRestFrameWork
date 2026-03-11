from typing import List
from Registry.StructuralElement import StructuralElement


class Structure( StructuralElement ):
    """
    Base class for structural elements.

    Attributes:
        attributes (List[RegistryAttribute]): The list of attributes of the structure.
        methods (List[RegistryMethod]): The list of methods of the structure.
    """
    def __init__( self ):
        super().__init__()
        self.attributes: List['RegistryAttribute'] = []  # List of attributes, empty by default
        self.methods: List['RegistryMethod'] = []  # List of methods, empty by default

    def add_attribute( self, attribute: 'RegistryAttribute' ):
        """
        Add an attribute to the structure.

        Args:
            attribute (RegistryAttribute): The attribute to add.
        """
        if isinstance(attribute, RegistryAttribute):  # Check the correct element_type
            self.attributes.append(attribute)
            attribute.set_parent(self)

    def add_method( self, method: 'RegistryMethod' ):
        """
        Add a method to the structure.

        Args:
            method (RegistryMethod): The method to add.
        """
        if isinstance(method, RegistryMethod):
            self.methods.append(method)
            method.set_parent(self)

class RegistryClass( Structure ):
    """
    Class structure.
    """

    def buildUml( self ):
        """
        Build the UML representation of the class.

        Returns:
            str: The UML representation of the class.
        """

        # attributes_uml = ''.join([attr.buildUml() for attr in self.attributes])
        # methods_uml = ''.join([meth.buildUml() for meth in self.methods])
        str_uml = ''
        if self.mutability:
            str_uml += self.mutability
        str_uml += "class "+ self.name + " {\n"
        return str_uml


class RegistryInterface( Structure ):
    """
    Interface structure.
    """

    def buildUml( self ):
        """
        Build the UML representation of the interface.

        Returns:
            str: The UML representation of the interface.
        """
        methods_uml = '\n    '.join([meth.buildUml() for meth in self.methods])
        uml_str = f"interface {self.name}"
        uml_str += "{\n"
        uml_str += f"{methods_uml}\n"
        return uml_str


class RegistryEnum( Structure ):
    """
    Enum structure.
    """

    def buildUml(self):
        """
        Build the UML representation of the enum.

        Returns:
            str: The UML representation of the enum.
        """
        return f"enum {self.name}\n"


class RegistryAttribute( StructuralElement ):
    """
    Attribute structure.
    """

    def __init__(self):
        super().__init__()


    def buildUml(self):
        """
        Build the UML representation of the attribute.

        Returns:
            str: The UML representation of the attribute.
        """
        uml_str = f'{self.visibility}'
        if self.mutability:
            uml_str += f' {self.mutability}'
        uml_str += f" {self.name} : {self.element_type}\n"
        return uml_str


class RegistryMethod( StructuralElement ):
    """
    Method structure.
    """

    def __init__(self):
        super().__init__()
        self.parameters: List['RegistryParameter'] = []
        self.abstract: bool = False

    def set_abstract(self, abstract: bool):
        """
        Set the abstract status of the method.

        Args:
            abstract (bool): The new abstract status.
        """
        self.abstract = abstract

    def buildUml(self):
        self.parameters = [param.buildUml() if isinstance(param, RegistryParameter) else param for param in self.parameters]

        if self.element_type == '':
            return f"{self.visibility} {self.name}({', '.join(self.parameters)})\n"

        return f"{self.visibility} {self.name}({', '.join(self.parameters)}) {self.element_type}\n"

class RegistryParameter( StructuralElement ):
    """
    Parameter structure.
    """
    def __init__(self):
        """
        Initialize a new RegistryParameter.

        """
        super().__init__()

    def buildUml(self):
        if self.element_type == '':
            return  f"{self.name}"

        return  f"{self.name}: {self.element_type}"

class RegistryAnnotation( StructuralElement ):
    """
    Annotation structure.
    """
    def __init__(self):
        super().__init__()

    def buildUml(self):
        #TODO -- build annotation
        return f"@{self.name}"

