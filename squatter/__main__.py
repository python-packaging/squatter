import tempfile
from typing import Optional

import click

from .templates import Env


@click.group()
def cli() -> None:  # pragma: no cover
    pass


@cli.command(help="Generate a package")
@click.option("--keep", is_flag=True, default=False, help="Do not delete temp dir")
@click.option(
    "--upload", is_flag=True, default=False, help="Whether to invoke twine upload"
)
@click.option("--author", help="Author name, defaults to reading from git config")
@click.option(
    "--author-email", help="Author email, defaults to reading from git config"
)
@click.argument("package_name")
def generate(
    package_name: str,
    upload: bool,
    keep: bool,
    author: Optional[str],
    author_email: Optional[str],
) -> None:
    # TODO flag for delete
    with tempfile.TemporaryDirectory(prefix=package_name, delete=not keep) as d:
        env = Env(d)
        if keep:
            print("Generating in", d)
        env.generate(
            package_name=package_name, author=author, author_email=author_email
        )
        if upload:
            env.upload()
        else:
            print("Rerun with --upload to upload")


if __name__ == "__main__":  # pragma: no cover
    cli()
