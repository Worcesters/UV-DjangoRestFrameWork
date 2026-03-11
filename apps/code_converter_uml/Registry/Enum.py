from enum import Enum
class RegistryVisibility( Enum ):
    """
    The RegistryVisibility Enum represents the different visibility
    modifiers that can be used to indicate how an element can be
    accessed from outside its defining scope.

    Attributes:
        PUBLIC: The public visibility modifier.
        PROTECTED: The protected visibility modifier.
        PRIVATE: The private visibility modifier.
    """
    PUBLIC = "+"
    PROTECTED = "#"
    PRIVATE = "-"
    # STATIC = "{static}"
    # FINAL = "{final}"
    # VOLATILE = "{volatile}"
    # TRANSIENT = "{transient}"
    # SYNCHRONIZED = "{synchronized}"
    # NATIVE =  "{native}"
    # VOID = "{void}"

class RegistryType( Enum ):
    """
    The RegistryType Enum represents the different types
    of elements that can be stored in the registry.

    Attributes:
        STRING: The string type.
        INT: The integer type.
        FLOAT: The float type.
        BOOL: The boolean type.
        ARRAY: The array type.
        OBJECT: The object type.
        NULL: The null type.
        VOID: The void type.
        RESOURCE: The resource type.
        MIXED: The mixed type.
    """

    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"
    VOID = "void"
    RESOURCE = "resource"
    MIXED = "mixed"
    CLASS = "class"
    TRAIT = "trait"
    FUNCTION = "function"
    CONSTANT = "constant"
    INTERFACE = "interface"
    ENUM = "enum"
    NAMESPACE = "namespace"
    TUPLE = "tuple"
    UNION = "union"
    KEYWORD = "keyword"
    UNKNOWN = "unknown"
    BYTE = "byte"
    SHORT = "short"
    LONG = "long"
    DOUBLE = "double"
    CHAR = "char"