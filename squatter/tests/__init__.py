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

            self.assertEqual(
                [Path(d) / "dist" / "foo-0.0.0a1.tar.gz"],
                list(Path(d).rglob("*.tar.gz")),
            )

            egg_info = list(Path(d).rglob("PKG-INFO"))
            self.assertEqual(1, len(egg_info))
            egg_info_text = egg_info[0].read_text()
            self.assertIn("\nName: foo\n", egg_info_text)
            self.assertIn("\nAuthor: Author Name\n", egg_info_text)
            self.assertIn("\nAuthor-email: email@example.com\n", egg_info_text)

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

            self.assertEqual(
                [Path(d) / "dist" / "foo-0.0.0a1.tar.gz"],
                list(Path(d).rglob("*.tar.gz")),
            )

            egg_info = list(Path(d).rglob("PKG-INFO"))
            self.assertEqual(1, len(egg_info))
            egg_info_text = egg_info[0].read_text()
            self.assertIn("\nName: foo\n", egg_info_text)
            self.assertIn("\nAuthor: Bob\n", egg_info_text)
            self.assertIn("\nAuthor-email: email@example.com\n", egg_info_text)

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
            if cmd[0] != "twine":
                return check_call(cmd, **kwargs)
            else:
                assert cmd[-1].endswith(".tar.gz")
                uploads += 1

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
