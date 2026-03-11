"""Module providing a abstract class for python."""
from abc import ABC, abstractmethod
from enum import Enum
from Registry.RegistryElement import RegistryElement

class Relational( RegistryElement, ABC ):
    """
    This class represents a relational element
    and provides methods for setting source and destination poles.
    """

    @abstractmethod
    def set_source( self, pole: 'Pole' ) -> 'Pole':
        """
        Sets the source pole of the relational element.

        Args:
            pole (Pole): The new source pole.

        Returns:
            Pole: The previous source pole.
        """

    @abstractmethod
    def set_destination( self, pole: 'Pole' ) -> 'Pole':
        """
        Description of the set_destination method.

        Args:
            pole (str): Description of the pole parameter.

        Returns:
            Pole: Description of the return value.
        """

    @abstractmethod
    def get_source( self ) -> 'Pole':
        """
        Gets the source pole of the relational element.

        Returns:
            Pole: The source pole.
        """

    @abstractmethod
    def get_destination( self ) -> 'Pole':
        """
        Gets the destination pole of the relational element.

        Returns:
            Pole: The destination pole.
        """

class RelationalElement( Relational ):

    def __init__( self ) -> None:
        self._source = None
        self._destination = None

    def get_destination( self ) -> 'Pole':
        return self._destination

    def get_source( self ) -> 'Pole':
        return self._source

    def set_source( self, pole: 'Pole' ) -> 'Pole':
        previous = self._source
        self._source = pole
        return previous

    def set_destination( self, pole: 'Pole' ) -> 'Pole':
        previous = self._destination
        self._destination = pole
        return previous


class Pole:
    """
    This class represents a pole of a relational element.

    A pole is a named connection point on a relational element.
    """

    def __init__( self ) -> None:
        """
        Initializes a new instance of the Pole class.

        Args:
            name (str): The name of the pole.
        """
        self.name: str = ''
        self.cardinality: int = 1

    def get_value(self):
        return self.name

class Cardinality( Enum ):
    """
    Enumeration of the cardinalities that a pole can have.

    The cardinalities are:
    - ZERO: Zero or no relationships.
    - ONE: One relationship.
    - MANY: Many relationships.
    """

    ZERO = 0
    ONE = 1
    MANY = 2

