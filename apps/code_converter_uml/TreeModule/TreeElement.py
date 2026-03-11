from typing import List, Optional
class TreeElement:
    """
    Represents a tree element, which is an element of a tree structure.

    A tree element has a parent element and zero or more child elements.
    """

    def __init__(self, element: Optional[object] = None):
        """
        Initializes the tree element.

        The tree element is empty after initialization.
        """
        self.element = element
        self.children: List['TreeElement'] = []
        self.heritages: List['TreeElement'] = []

    def add_child(self, child: 'TreeElement') -> None:
        """
        Adds a child element to the tree element.

        Args:
            child: The child element to add.
        """
        self.children.append(child)

    def add_herits(self, heritage: 'TreeElement') -> None:
        """
        Adds a child element to the tree element.
        Args:
            heritage: The child element to add.
        """
        self.heritages.append(heritage)

    def get_child(self, element) -> Optional['TreeElement']:
        """
        Returns a child element with the given element or None.

        Args:
            element: The element to search for.

        Returns:
            The child element with the given element or None.
        """
        for child in self.children:
            if child.element == element:
                return child
        return None

    def get_children(self) -> List['TreeElement']:
        """
        Returns a list of all child elements.

        Returns:
            A list of all child elements.
        """
        return self.children

    def get_herits(self) -> List['TreeElement']:
        return self.heritages

    def reset_children(self) -> None:
        """
        Clears the children of the current element.
        """
        self.children = []