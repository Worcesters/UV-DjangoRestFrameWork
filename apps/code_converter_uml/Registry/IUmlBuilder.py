from abc import ABC, abstractmethod
class IUmlBuilder( ABC ):
    """
    An interface class for building UML code from a Registry instance
    """

    @abstractmethod
    def buildUml( self ) -> str:
        """
        Builds UML code from a Registry instance

        Returns:
            A string of UML code
        """
