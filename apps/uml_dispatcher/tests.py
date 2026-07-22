from __future__ import annotations

import io
import zipfile

from django.test import SimpleTestCase

from apps.uml_dispatcher.services import (
    DispatchError,
    ZipDispatchError,
    build_dispatch_plan,
    build_placement,
    build_reorganized_zip,
    sanitize_folder_name,
)

_UML = """
@startuml
class VersionRepository { + findByConfig(conf) }
class ProfileRepository { + findOne(value) }
class AnnexeController { + upload(request) }
class Version { + getId() }
VersionRepository --|> ServiceEntityRepository
ProfileRepository --|> ServiceEntityRepository
AnnexeController --|> AbstractController
@enduml
"""


def _make_zip(names: list[str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name in names:
            zf.writestr(name, b"content")
    return buffer.getvalue()


class DispatchPlanTests(SimpleTestCase):
    """Regroupement par cible de relation."""

    def test_groups_children_under_shared_target(self) -> None:
        plan = build_dispatch_plan(_UML)
        by_target = {g.target: set(g.members) for g in plan.groups}
        self.assertEqual(
            by_target["ServiceEntityRepository"],
            {"VersionRepository", "ProfileRepository"},
        )
        self.assertEqual(by_target["AbstractController"], {"AnnexeController"})

    def test_unlinked_class_goes_to_misc(self) -> None:
        plan = build_dispatch_plan(_UML)
        self.assertIn("Version", plan.unlinked)

    def test_groups_sorted_by_member_count_desc(self) -> None:
        plan = build_dispatch_plan(_UML)
        self.assertEqual(plan.groups[0].target, "ServiceEntityRepository")

    def test_empty_input_raises(self) -> None:
        with self.assertRaises(DispatchError):
            build_dispatch_plan("   ")

    def test_multi_hub_assigns_first_target(self) -> None:
        uml = (
            "@startuml\n"
            "class C { + m() }\n"
            "C --|> A\n"
            "C ..|> B\n"
            "@enduml"
        )
        plan = build_dispatch_plan(uml)
        by_target = {g.target: set(g.members) for g in plan.groups}
        self.assertEqual(by_target.get("A"), {"C"})
        self.assertNotIn("B", by_target)


class SanitizeFolderTests(SimpleTestCase):
    """Sécurité des noms de dossiers fournis par l'UI."""

    def test_strips_path_traversal(self) -> None:
        self.assertNotIn("/", sanitize_folder_name("../../etc", "fallback"))
        self.assertNotIn("..", sanitize_folder_name("..", "fallback"))

    def test_falls_back_when_empty(self) -> None:
        self.assertEqual(sanitize_folder_name("///", "Repo"), "Repo")


class ZipBuilderTests(SimpleTestCase):
    """Assemblage du ZIP réorganisé."""

    def _reorganize(self, names: list[str]) -> dict[str, bytes]:
        plan = build_dispatch_plan(_UML)
        placement = build_placement(plan, {"ServiceEntityRepository": "ServiceEntityLink"})
        out = build_reorganized_zip(_make_zip(names), placement)
        with zipfile.ZipFile(io.BytesIO(out)) as zf:
            return {info.filename: zf.read(info) for info in zf.infolist()}

    def test_files_routed_to_group_folders(self) -> None:
        result = self._reorganize(
            ["VersionRepository.php", "AnnexeController.php", "Version.php", "README.md"]
        )
        self.assertIn("ServiceEntityLink/VersionRepository.php", result)
        self.assertIn("AbstractController/AnnexeController.php", result)
        self.assertIn("_divers/Version.php", result)
        self.assertIn("_autres/README.md", result)

    def test_case_insensitive_stem_match(self) -> None:
        result = self._reorganize(["versionrepository.PHP"])
        self.assertIn("ServiceEntityLink/versionrepository.PHP", result)

    def test_rejects_invalid_zip(self) -> None:
        with self.assertRaises(ZipDispatchError):
            build_reorganized_zip(b"not a zip", {})

    def test_path_traversal_entry_is_skipped(self) -> None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("../evil.php", b"x")
            zf.writestr("VersionRepository.php", b"x")
        plan = build_dispatch_plan(_UML)
        placement = build_placement(plan, None)
        out = build_reorganized_zip(buffer.getvalue(), placement)
        with zipfile.ZipFile(io.BytesIO(out)) as zf:
            names = zf.namelist()
        self.assertFalse(any("evil" in n for n in names))
