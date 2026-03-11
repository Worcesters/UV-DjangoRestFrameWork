"""
This module provides a factory for creating parser instances.
"""
from typing import Optional
from typing import List
from Definition.Language import Language
from ParserModule.Parser.Interface import IParser



class ParserFactory():
    """
    This class represents a factory for creating parser instances.
    """
    __parser_factory_instance: 'Optional[ParserFactory]' = None
    __language: 'Optional[Language]' = None
    __parser_instance: 'Optional[List[IParser]]' = None

    @classmethod
    def get_instance( cls, language: Language ):
        """
        Get an instance of the ParserFactory for a specific language.

        Args:
            language: The Language object for which the ParserFactory instance is needed.

        Returns:
            An instance of the ParserFactory.
        """
        if language is None and cls.__language is None:
            raise ValueError("La langue n'a pas été initialisée")

        if cls.__parser_factory_instance is None or cls.__language != language:
            cls.__parser_factory_instance = ParserFactory()
            cls.__language = language
            # Reset parser cache when the selected language changes.
            cls.__parser_instance = None

        return cls.__parser_factory_instance

    @classmethod
    def get_parsers( cls ) -> List[IParser]:
        """
        Get the parsers for the specified language.

        Returns:
            List[IParser]: A list of instances of the parser for the specified language.
        """

        if cls.__parser_instance is not None:
            return cls.__parser_instance

        parser_names = ["StructureParser", "MethodParser", "AttributeParser"]

        try:
            if cls.__language == Language.PHP:
                from ParserModule.Parser.PHP.StructureParser import StructureParser as PhpStructureParser
                from ParserModule.Parser.PHP.MethodParser import MethodParser as PhpMethodParser
                from ParserModule.Parser.PHP.AttributeParser import AttributeParser as PhpAttributeParser
                cls.__parser_instance = [PhpStructureParser(), PhpMethodParser(), PhpAttributeParser()]
            elif cls.__language == Language.PYTHON:
                from ParserModule.Parser.PYTHON.StructureParser import StructureParser as PythonStructureParser
                from ParserModule.Parser.PYTHON.MethodParser import MethodParser as PythonMethodParser
                from ParserModule.Parser.PYTHON.AttributeParser import AttributeParser as PythonAttributeParser
                cls.__parser_instance = [PythonStructureParser(), PythonMethodParser(), PythonAttributeParser()]
            elif cls.__language == Language.JAVA:
                from ParserModule.Parser.JAVA.StructureParser import StructureParser as JavaStructureParser
                from ParserModule.Parser.JAVA.MethodParser import MethodParser as JavaMethodParser
                from ParserModule.Parser.JAVA.AttributeParser import AttributeParser as JavaAttributeParser
                cls.__parser_instance = [JavaStructureParser(), JavaMethodParser(), JavaAttributeParser()]
            else:
                raise ValueError("La langue du parser n'a pas ete initialisee.")
        except ModuleNotFoundError as exc:
            raise ImportError(f"Parser not found for the specified language. {parser_names}") from exc

        return cls.__parser_instance
