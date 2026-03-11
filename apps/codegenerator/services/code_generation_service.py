from .code_generators import CodeGeneratorFactory
from .plantuml_parser import PlantUmlParser


class CodeGenerationError(Exception):
    pass


def generate_code_from_plantuml(plantuml_text: str, language: str) -> str:
    parser = PlantUmlParser()
    classes = parser.parse(plantuml_text)
    if not classes:
        raise CodeGenerationError(
            "Aucune classe detectee dans le PlantUML. "
            "Assure-toi d'avoir des blocs 'class Nom { ... }'."
        )

    try:
        generator = CodeGeneratorFactory.build(language)
    except ValueError as exc:
        raise CodeGenerationError(str(exc)) from exc

    return generator.generate(classes)
