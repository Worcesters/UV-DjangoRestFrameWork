"""
Module that contains the definition of the ParserManager class.

This class is in charge of creating and storing the parsers that will be
used to parse the code. It also provides a method to parse all the files
of a given project.
"""
import os
from typing import List, Tuple

from Registry.Registry import Registry, RegistryProgram
from TreeModule.TreeElement import TreeElement


# --------------------------------------------------------------------------- #
# Class definition
# --------------------------------------------------------------------------- #


class ParserManager():
    """
    Manager of parsers.

    This class is in charge of creating and storing the parsers that will be
    used to parse the code. It also provides a method to parse all the files
    of a given project.
    """
    def __init__( self ):
        self.parsers = []
        self.config = {'root_project': 'current_project'}
        self.tree_element = TreeElement()
        self.registry = Registry( RegistryProgram(self.config, self.tree_element) )
        # print('Registry -----> [DONE]')
        # print('├──├──├──├──├──├──├──│├──├──├──├──├──├──├──│')
        # print('└───────────────────────────────────────────')

    def set_parser( self, parsers ):
        """
        Add the parsers to the manager

        Args:
            parsers (list): The list of parsers to add
        """

        self.reset_parsers()
        for parser in parsers:
            self.parsers.append( parser )

    def reset_parsers(self):
        """
        Remove all the parsers from the manager.
        """
        self.parsers.clear()

    def parse_file( self, file_paths ):
        """
        Parse all the files in the given list

        Args:
            file_paths (list): A list of file paths to parse
        """
        for file_path in file_paths:
            with open(file_path, mode="r", encoding="utf-8") as file:
                code = file.read()

            for line in code.split('\n'):
                for parser in self.parsers:
                    parser.parse( line, self.registry, self.tree_element )

    def parse_files(self, file_paths: List[Tuple[str, str]]) -> None:
        """
        Concatenate all the files in the given list and parse the result.

        Args:
            file_paths (list): A list of tuples, each containing paths of two files to concatenate and parse.
        """
        concatenated_code = ''
        for file_pair in file_paths:  # Iterate over each tuple in the list
            for file_path in file_pair:  # Iterate over each file path in the tuple
                try:
                    with open(file_path, mode="r", encoding="utf-8") as file:
                        file_content = file.read()
                        concatenated_code += file_content + '\n'  # Adding a newline character for separation
                except FileNotFoundError:
                    print(f"File {file_path} not found.")
                except Exception as e:
                    print(f"An error occurred while reading {file_path}: {e}")

        # Split the concatenated code into lines
        lines = concatenated_code.split('\n')

        # Iterate over each line and parse it with all the parsers
        for line in lines:
            for parser in self.parsers:
                parser.parse(line, self.registry, self.tree_element)

    def parse_folders(self, folder_path: str) -> None:
        '''
        Concatenate all the files in the given folder path and parse the result

        Args:
            folder_path (str): The path of the folder to concatenate and parse
            output_path (str): The path of the output file
        '''
        # Get all the file paths in the given folder
        file_paths: List[str] = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_paths.append(os.path.join(root, file))

        # Concatenate all the files into a single string
        code = ''.join([open(file_path, mode="r", encoding="utf-8").read() for file_path in file_paths])

        # Split the concatenated code into lines
        lines = code.split('\n')

        # Iterate over each line and parse it with all the parsers
        for line in lines:
            for parser in self.parsers:
                parser.parse(line, self.registry, self.tree_element)
