import glob
import sys
from pathlib import Path
from subprocess import check_call, check_output
from typing import Optional

SETUP_PY_TMPL = """\
from setuptools import setup

setup(
    name={package_name!r},
    description="coming soon",
    version="0.0.0a1",
    author={author!r},
    author_email={author_email!r},
)
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

        data = SETUP_PY_TMPL.format(**locals())
        (Path(self.staging_directory) / "setup.py").write_text(data)

    def sdist(self) -> None:
        check_call([sys.executable, "setup.py", "sdist"], cwd=self.staging_directory)

    def upload(self) -> None:
        self.sdist()
        check_call(
            ["twine", "upload"] + glob.glob(f"{self.staging_directory}/dist/*.tar.gz"),
            cwd=self.staging_directory,
        )
