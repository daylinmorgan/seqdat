import click
from click_help_colors import HelpColorsCommand, HelpColorsGroup
from rich.markdown import Markdown
from rich.prompt import Prompt

from .__init__ import version
from .console import console


@click.group(
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="blue",
)
def cli():
    pass


@cli.command()
@click.option("-u", "--user", help="name of user who submitted job")
@click.option("-s", "--sample", help="sample id")
def query(user: str, sample: str) -> None:
    """Query for the data"""

    console.print("Searching the data...")

    if user:
        console.print(f"Searching for user: [cyan]{user}")
    if sample:
        console.print(f"Searching for sample: [cyan]{sample}")


@cli.command()
def init():
    """Interactively generate a new project"""
    console.print("Making a project folder...")
    name = Prompt.ask("User")  # noqa


@cli.command()
@click.argument("project")
def info(project: str):
    """Render the individual project's README"""
    MARKDOWN = fr"""
# {project}

- User: Daylin
- \# of samples: 17
- Run Type: NovaSeq S2

## Additional Info

Here is other project specific info.

Like that this was MDA-MB-231 cells
"""

    from rich.panel import Panel

    md = Markdown(MARKDOWN)
    console.print("[blue] Job Info Sheet", justify="center", width=80)
    console.print(Panel(md), width=80)


def main():

    head = r"""
     __  _  _   _      ___
    (_  |_ / \ | \  /\  |
    __) |_ \_X |_/ /--\ |

    """
    console.print(head, style="blue", highlight=False)
    console.print("Brock lab [green bold]SEQ[/]uencing [green bold]DAT[/]a manager.\n")
    # console.print(f"version: {version}\n")

    cli()


if __name__ == "__main__":
    main()
