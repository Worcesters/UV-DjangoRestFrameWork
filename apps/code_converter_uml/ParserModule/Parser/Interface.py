from abc import ABC, abstractmethod
from Registry.Registry import Registry
from TreeModule.TreeElement import TreeElement

class IParser( ABC ):
    """
    Abstract base class defining the interface for a parser.

    All concrete parsers must implement the `parse` method.
    """

    @abstractmethod
    def parse(self, line: str, registry: 'Registry', tree_element: 'TreeElement') -> None:
        """
        Parses a single line of code and updates the registry and the active tree element.

        Parameters:
            line: The line of code to parse.
            registry: The registry to update.
            tree_element: The active tree element to update.

        Raises:
            NotImplementedError: If the method is not overridden in a subclass.
        """
        raise NotImplementedError("La méthode parse doit être implémentée dans les sous-classes.")
