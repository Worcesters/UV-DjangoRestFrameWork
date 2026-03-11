"""Module providing a abstract class for python."""
from abc import ABC, abstractmethod
from Registry.IUmlBuilder import IUmlBuilder


class RegistryElement( IUmlBuilder, ABC ):
    """
    Base class for all structural elements that can be represented in UML
    """

    @abstractmethod
    def buildUml( self ) -> str:
        """
        Builds UML representation of the structural element

        :return: UML representation of the structural element
        """
        print(f'Building uml for {self.__class__.__name__}')