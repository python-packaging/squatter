from glob import glob
from pathlib import Path
from subprocess import check_call, check_output
from typing import Optional

PYPROJECT_TEMPLATE = """\
["build-system"]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = {package_name!r}
description = "coming soon"
version = "0.0.0a1"
authors = [
    {{name={author!r}, email={author_email!r} }},
]
"""

INIT_TEMPLATE = """\
'''coming soon'''
"""


class Env:
    def __init__(self, staging_directory: str) -> None:
        self.staging_directory = staging_directory

    def generate(
        self,
        package_name: str,
        author: Optional[str] = None,
        author_email: Optional[str] = None,
    ) -> None:
        if author is None:
            author = check_output(
                ["git", "config", "user.name"], encoding="utf-8"
            ).strip()
        if author_email is None:
            author_email = check_output(
                ["git", "config", "user.email"], encoding="utf-8"
            ).strip()

        data = PYPROJECT_TEMPLATE.format(**locals())
        (Path(self.staging_directory) / "pyproject.toml").write_text(data)

        pkg_dir = Path(self.staging_directory) / package_name.replace("-", "_")
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "__init__.py").write_text(INIT_TEMPLATE)

    def sdist(self) -> None:
        check_call(["hatch", "build"], cwd=self.staging_directory)

    def upload(self) -> None:
        self.sdist()
        check_call(
            ["twine", "upload", *glob("dist/*", root_dir=self.staging_directory)],
            cwd=self.staging_directory,
        )
        # check_call(["hatch", "publish"], cwd=self.staging_directory)
