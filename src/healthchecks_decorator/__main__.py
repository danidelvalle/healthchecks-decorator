"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Healthchecks Decorator."""


if __name__ == "__main__":
    main(prog_name="healthchecks-decorator")  # pragma: no cover
