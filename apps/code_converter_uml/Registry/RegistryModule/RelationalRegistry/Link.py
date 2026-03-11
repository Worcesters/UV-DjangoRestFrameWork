from abc import ABC
from Registry.RelationalElement import Pole, RelationalElement

class Link( RelationalElement, ABC ):
    """
    This class represents a link in the system.
    It provides methods for getting the source and destination of the link.
    """

    def set_destination(self, pole: Pole) -> Pole:
        previous = self._destination
        self._destination = pole
        return previous

    def set_source(self, pole: Pole) -> Pole:
        previous = self._source
        self._source = pole
        return previous

    def get_destination(self) -> Pole:
        return self._destination

    def get_source(self) -> Pole:
        return self._source

class Composition( Link ):
    """
    This class represents a composition link in the system.

    A composition link is a link that has an ownership semantics, which means that
    the source owns the destination.

    This class provides methods for getting the source and destination of the link.
    """

    def buildUml( self ):
        return str(self.get_source().get_value()) + ' *-- ' + str(self.get_destination().get_value()) + '\n\n\n'

class Heritage( Link ):
    """
    This class represents a heritage link in the system.

    A heritage link is a link that has an inheritance semantics,
    which means that the destination is a subtype of the source.

    This class provides methods for getting the source and destination of the link.
    """

    def buildUml( self ):
        """
        Builds the UML representation of this heritage link.

        Returns:
            str: The UML representation of this heritage link.
        """
        return str(self.get_source().get_value()) + ' --|> ' + str(self.get_destination().get_value()) + '\n'

class Association(Link):
    """
    This class represents an association link in the system.

    An association link is a link that has a 'has-a' relationship,
    which means that the source has a relationship with the destination.

    This class provides methods for getting the source and destination of the link.
    """

    def buildUml(self):
        """
        Builds the UML representation of this association link.

        Returns:
            str: The UML representation of this association link.
        """
        return str(self.get_source().get_value()) + ' --> ' + str(self.get_destination().get_value()) + '\n'

class Aggregation(Link):
    """
    Represents an aggregation link in the system.

    An aggregation link is a link that has an 'is-part-of' relationship,
    which means that the destination is part of the source.

    This class provides methods for getting the source and destination of the link.
    """

    def buildUml(self):
        """
        Builds the UML representation of this aggregation link.

        Returns:
            str: The UML representation of this aggregation link.
        """
        return str(self.get_source().get_value()) + ' o-- ' + str(self.get_destination().get_value()) + '\n'

class Implementation(Link):
    """
    Represents an implementation link in the system.

    An implementation link is a link that has an 'implements' relationship,
    which means that the source implements the destination.

    This class provides methods for getting the source and destination of the link.
    """

    def buildUml(self):
        """
        Builds the UML representation of this implementation link.

        Returns:
            str: The UML representation of this implementation link.
        """
        return str(self.get_source().get_value()) + ' <|.. ' + str(self.get_destination().get_value()) + '\n'



class Dependance(Link):
    """
    Represents a dependece link in the system.

    A dependece link is a link that has a 'depends-on' relationship,
    which means that the destination depends on the source.

    This class provides methods for getting the source and destination of the link.
    """

    def buildUml( self ):
        """
        A method that builds a UML representation by concatenating the source and destination.
        """
        return str(self.get_source().get_value()) + ' ..> ' + str(self.get_destination().get_value()) + '\n'