import re
import tarfile
import unittest
from pathlib import Path
from subprocess import check_call
from tempfile import TemporaryDirectory
from typing import Any, List
from unittest.mock import patch

from click.testing import CliRunner

from squatter.__main__ import generate
from squatter.templates import Env


class SquatterEnvTest(unittest.TestCase):
    def test_env_smoke(self) -> None:
        with TemporaryDirectory() as d:
            env = Env(d)
            env.generate("foo", "Author Name", "email@example.com")
            env.sdist()

            tarballs = list(Path(d).rglob("*.tar.gz"))
            self.assertEqual(
                [Path(d) / "dist" / "foo-0.0.0a1.tar.gz"],
                tarballs,
            )

            with tarfile.open(tarballs[0]) as tar:
                members = [
                    member
                    for member in tar.getmembers()
                    if member.name.endswith("PKG-INFO")
                ]
                pkg_info = tar.extractfile(members[0])
                assert pkg_info is not None
                egg_info_text = pkg_info.read()

                self.assertIn(b"\nName: foo\n", egg_info_text)
                self.assertIn(
                    b"\nAuthor-email: Author Name <email@example.com>\n", egg_info_text
                )

    @patch("squatter.templates.check_output")
    def test_env_git_prompts(self, check_output_mock: Any) -> None:
        tbl = {
            ("git", "config", "user.name"): "Bob",
            ("git", "config", "user.email"): "email@example.com",
        }
        check_output_mock.side_effect = lambda cmd, **kwargs: tbl[tuple(cmd)]

        with TemporaryDirectory() as d:
            env = Env(d)
            env.generate("foo")
            env.sdist()

            tarballs = list(Path(d).rglob("*.tar.gz"))
            self.assertEqual(
                [Path(d) / "dist" / "foo-0.0.0a1.tar.gz"],
                tarballs,
            )

            with tarfile.open(tarballs[0]) as tar:
                members = [
                    member
                    for member in tar.getmembers()
                    if member.name.endswith("PKG-INFO")
                ]
                pkg_info = tar.extractfile(members[0])
                assert pkg_info is not None
                egg_info_text = pkg_info.read()

                self.assertIn(b"\nName: foo\n", egg_info_text)
                self.assertIn(
                    b"\nAuthor-email: Bob <email@example.com>\n", egg_info_text
                )

    @patch("squatter.templates.check_output")
    @patch("squatter.templates.check_call")
    def test_cli_functional(self, check_call_mock: Any, check_output_mock: Any) -> None:
        tbl = {
            ("git", "config", "user.name"): "Bob",
            ("git", "config", "user.email"): "email@example.com",
        }
        check_output_mock.side_effect = lambda cmd, **kwargs: tbl[tuple(cmd)]

        uploads = 0

        def patched_check_call(cmd: List[str], **kwargs: Any) -> Any:
            nonlocal uploads
            if cmd[0] == "hatch":
                if "publish" in cmd:
                    uploads += 1
                else:
                    return check_call(cmd, **kwargs)
            elif cmd[0] == "twine":
                if "upload" in cmd:
                    uploads += 1
            else:
                return check_call(cmd, **kwargs)

        check_call_mock.side_effect = patched_check_call

        runner = CliRunner()
        result = runner.invoke(generate, ["foo"])
        self.assertEqual("Rerun with --upload to upload\n", result.output)
        self.assertFalse(result.exception)
        self.assertEqual(0, uploads)

        runner = CliRunner()
        result = runner.invoke(generate, ["--upload", "foo"])
        self.assertEqual("", result.output)
        self.assertFalse(result.exception)
        self.assertEqual(1, uploads)

    @patch("squatter.templates.check_output")
    @patch("squatter.templates.check_call")
    def test_cli_keep_flag(self, check_call_mock: Any, check_output_mock: Any) -> None:
        runner = CliRunner()
        result = runner.invoke(generate, ["--keep", "foo"])
        m = re.match("Generating in (.+)", result.output)
        assert m is not None
        assert Path(m.group(1)).exists()
        assert Path(m.group(1), "pyproject.toml")
        self.assertFalse(result.exception)
