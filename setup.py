"""Build the installed snapshot of the repository's inventor catalog."""

import json
from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    """Build exact non-Python runtime assets beside the installed package."""

    def run(self):
        # Setuptools reuses ``build/lib`` across local builds and otherwise leaves
        # deleted modules or schemas in later wheels.  These are generated package
        # roots, so rebuild them from the current source tree every time.
        build_lib = Path(self.build_lib)
        for package_name in ("workshop", "cli"):
            generated_package = build_lib / package_name
            if generated_package.exists():
                shutil.rmtree(generated_package)
        super().run()
        project = Path(__file__).resolve().parent
        source_skills = project / "src" / "workshop" / "make" / "skills"
        built_skills = Path(self.build_lib) / "workshop" / "make" / "skills"
        for source in source_skills.rglob("*"):
            if source.is_file() and not source.is_symlink():
                built = built_skills / source.relative_to(source_skills)
                if built.is_file():
                    shutil.copymode(source, built)

        source_agent_assets = project / ".agents"
        built_agent_assets = (
            Path(self.build_lib) / "workshop" / "runtime" / "_agent_assets"
        )
        if built_agent_assets.exists():
            shutil.rmtree(built_agent_assets)
        for relative_root in (
            Path("product-run"),
            Path("skills") / "autonomous-workshop",
        ):
            source_root = source_agent_assets / relative_root
            if not source_root.is_dir():
                raise FileNotFoundError(
                    "required product-run agent assets are missing: %s" % source_root
                )
            for source in source_root.rglob("*"):
                if not source.is_file() or source.is_symlink():
                    continue
                relative = Path(".agents") / source.relative_to(source_agent_assets)
                destination = built_agent_assets / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

        destination = (
            Path(self.build_lib)
            / "workshop"
            / "contributors"
            / "_catalog"
            / "inventors"
        )
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True)
        for inventor_id in ("alice", "bob", "eve", "ivy", "leo"):
            source = project / "inventors" / inventor_id
            target = destination / inventor_id
            target.mkdir()
            for filename in ("TASTE.md", "inventor.json"):
                source_file = source / filename
                if source_file.is_symlink() or not source_file.is_file():
                    raise FileNotFoundError(
                        "required bundled Inventor file is missing: %s" % source_file
                    )
                shutil.copy2(source_file, target / filename)

            manifest = json.loads((source / "inventor.json").read_text("utf-8"))
            if (
                not isinstance(manifest, dict)
                or manifest.get("schema_version") != 7
                or manifest.get("id") != inventor_id
                or not isinstance(manifest.get("extensions"), list)
                or not manifest["extensions"]
            ):
                raise ValueError(
                    "bundled Inventors must use the native schema-v7 skill contract"
                )
            declared = set()
            for extension in manifest["extensions"]:
                if not isinstance(extension, dict):
                    raise ValueError("bundled Inventor extension must be an object")
                name = extension.get("name")
                relative = extension.get("path")
                if (
                    extension.get("kind") != "codex-skill"
                    or not isinstance(name, str)
                    or relative != "skills/%s" % name
                ):
                    raise ValueError("bundled Inventor extension path is invalid")
                declared.add(relative)
                source_skill = source / relative
                if source_skill.is_symlink() or not source_skill.is_dir():
                    raise FileNotFoundError(
                        "required bundled Inventor skill is missing: %s" % source_skill
                    )
                files = tuple(source_skill.rglob("*"))
                if not any(
                    item.relative_to(source_skill).as_posix() == "SKILL.md"
                    and item.is_file()
                    and not item.is_symlink()
                    for item in files
                ):
                    raise FileNotFoundError(
                        "bundled Inventor skill has no SKILL.md: %s" % source_skill
                    )
                for source_file in files:
                    if source_file.is_symlink():
                        raise ValueError(
                            "bundled Inventor skills must not contain symlinks: %s"
                            % source_file
                        )
                    if source_file.is_dir():
                        continue
                    if not source_file.is_file():
                        raise ValueError(
                            "bundled Inventor skills may contain only regular files: %s"
                            % source_file
                        )
                    built = target / source_file.relative_to(source)
                    built.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, built)

            skills = source / "skills"
            observed = {
                item.relative_to(source).as_posix()
                for item in skills.iterdir()
                if item.is_dir() and not item.is_symlink()
            }
            if observed != declared:
                raise ValueError(
                    "bundled Inventor skills differ from the declared inventory: %s"
                    % source
                )


setup(cmdclass={"build_py": build_py})
