from .code_generators import CodeGeneratorFactory
from .models import ClassDef
from .plantuml_parser import PlantUmlParser


class CodeGenerationError(Exception):
    pass


def _sort_classes_for_inheritance(classes: list[ClassDef]) -> list[ClassDef]:
    """Parents avant enfants pour éviter NameError (Python) / références avant déclaration."""
    by_name = {c.name: c for c in classes}
    memo: dict[str, int] = {}

    def rank(name: str, depth: int = 0) -> int:
        if depth > 40:
            return 0
        if name in memo:
            return memo[name]
        c = by_name.get(name)
        if not c or not c.parent or c.parent not in by_name:
            memo[name] = 0
            return 0
        r = 1 + rank(c.parent, depth + 1)
        memo[name] = r
        return r

    return sorted(classes, key=lambda c: (rank(c.name), c.name))


def generate_code_from_plantuml(plantuml_text: str, language: str) -> str:
    parser = PlantUmlParser()
    classes = _sort_classes_for_inheritance(parser.parse(plantuml_text))
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
