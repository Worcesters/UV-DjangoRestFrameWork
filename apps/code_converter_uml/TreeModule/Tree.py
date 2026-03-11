# Imports the TreeElement class from the TreeElement module.
from TreeModule.TreeElement import TreeElement

class Tree:
    """
    Represents a tree, which is a hierarchical structure of elements.

    The tree is composed of a root element and zero or more child elements.

    Attributes:
        root: The root element of the tree.
    """

    def __init__(self):
        """
        Initializes the tree.

        The tree is empty after initialization.
        """
        self.root = None

    def set_root(self, element):
        """
        Sets the root element of the tree.

        Args:
            element: The element to set as the root of the tree.

        Raises:
            TypeError: If the element is not a TreeElement.
        """
        if isinstance(element, TreeElement):
            self.root = element
        else:
            self.root = TreeElement(element)

    def get_root(self):
        """
        Returns the root element of the tree.

        Returns:
            The root element of the tree.
        """
        return self.root
