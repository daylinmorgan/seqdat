import sys
from pathlib import Path

import click
from click_help_colors import HelpColorsCommand, HelpColorsGroup
from rich import inspect
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.traceback import install

from ._version import __version__
from .config import Config, _config_file
from .console import console
from .database import DataBase
from .project import Project

install(suppress=[click], show_locals=True)


@click.group(
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="magenta",
)
@click.version_option(__version__)
def cli():
    pass


@cli.command()
@click.option("--generate", help="interactivley generate config file", is_flag=True)
@click.option("--update", help="interactively update config file", is_flag=True)
@click.option("--path", help="print path to config file", is_flag=True)
def config(generate: bool, update: bool, path: bool):
    """Change configuration"""

    if path:
        console.print(f"config file located at:[info] {_config_file}")
    elif update:
        config = Config.load(skip_check=True)
        console.print("[yellow]Updating config file...[/]")
        config.update()
        config.save()
        console.print("[green]Config file updated[/]")
    elif generate:
        config = Config.make()
        config.show()
        config.save()
    else:
        config = Config.load()
        config.show()


with console.capture() as capture:
    console.print("additional parameters to pass to [yellow bold]bs download project")
bs_params_help = capture.get()


@cli.command()
@click.argument("project_id")
@click.option("-bs", "--bs-params", help=bs_params_help)
def download(project_id: str, bs_params: str):
    """Download data from basespace for an existing project

    \b
    Alternatively you can download the data manually using the bs-cli
    by installing in the data directory of the project in the database:
    database/<PROJECT_ID>/data
    \b
    Get the current database from your config with the below command:
    `seqdat config`
    """
    project = Project.from_metadata(project_id, Config.load().database)
    project.fetch_data(bs_params)
    console.print(
        f"Dont forget to run [code]seqdat meta [hl]{project_id}[/] --update-samples[/]!"
    )


@cli.command()
@click.argument("project_id")
@click.option("--edit", help="open README in text editor", is_flag=True)
@click.option("--editor", help="text editor to use, otherwise `$EDITOR`", default=None)
def info(project_id: str, edit: bool, editor: str):
    """Render a project's README"""
    config = Config.load()
    readme = config.database / project_id / "README.md"

    if not readme.is_file():
        console.print(f"[red]Project {project_id} does not exist")
        console.print("You can start a new project with:")
        console.print("\n\tseqdat init")
        sys.exit(1)
    if edit:
        click.edit(extension=".md", filename=readme, editor=editor)
    else:
        with readme.open("r") as f:
            md_str = f.read()
        md = Markdown(md_str)
        console.print("[blue] Job Info Sheet", justify="center", width=80)
        console.print(Panel(md), width=80)


@cli.command()
@click.option("-bs", "--bs-params", help=bs_params_help)
@click.option("-n", "--name", help="Name/Job Number for sequening project")
@click.option("--owner", help="user who originally submitted job request")
@click.option("--run-type", help="sequencer and chip type used in job")
@click.option("--skip-download", help="skip download from basespace", is_flag=True)
def init(bs_params: str, name: str, owner: str, run_type: str, skip_download: bool):
    """Interactively generate a new project"""

    console.print("Making a project folder...")
    project = Project.from_prompt(name, owner, run_type, Config.load().user)

    if not skip_download:
        project.fetch_data(bs_params)
    else:
        console.print("[info]Skipping basespace download")

    project.identify_samples()
    project.generate_info_sheet()
    project.save_metadata()

    console.print("[info]Project created successfully!")
    console.print("Don't forget to update the project info sheet!")
    console.print(f"\n[code]  seqdat info {project.name} --edit")


@cli.command(name="list")
@click.option("-l", "--limit", help="maximum number of projects to include", type=int)
@click.option(
    "-f",
    "--field",
    help="field to sort projects",
    type=click.Choice(["name", "owner"]),
    default="name",
    show_default=True,
)
@click.option(
    "--ascending", help="sort in ascending rather than descending order", is_flag=True
)
def list_jobs(limit: int, field: str, ascending: bool):
    """List all available sequencing projects"""
    db = DataBase()
    db.display_projects(projects=[], limit=limit, field=field, ascending=ascending)


@cli.command()
@click.argument("project_id")
@click.option("--update", help="interactively update metadata", is_flag=True)
@click.option(
    "--update-samples", help="update samples by walking data/ directory", is_flag=True
)
@click.option("-bs", "--basespace", help="return metadata from basespace", is_flag=True)
def meta(project_id: str, update: bool, update_samples: bool, basespace: bool):
    """Interact with project's metadata"""

    project = Project.from_metadata(project_id, database=Config.load().database)
    project.view_metadata()

    if basespace:
        project.view_basespace_meta()

    if update and update_samples:
        console.print("[info] please use --update and --update-samples seperately")
        sys.exit()

    if update:
        rule = "[green]----------[/]"
        console.print(f"\n{rule} Updating {rule}")
        project.update_metadata()
    elif update_samples:
        console.print("\n[info]Updating Sample List")
        project.identify_samples()
        project.save_metadata()


@cli.command()
@click.argument("project_id")
@click.option("-o", "--out", help="directory to move files to", required=True)
@click.option("-p", "--prefix", help="prefix for output files", default="")
@click.option(
    "-s",
    "--suffix",
    help="suffix for output files (before file extension)",
    default=".raw",
    show_default=True,
)
@click.option("--paired-end", help="move data in paired end mode", is_flag=True)
def move(project_id: str, out: str, prefix: str, suffix: str, paired_end: bool):
    """Concatenate and move files to new directory"""

    project = Project.from_metadata(project_id, database=Config.load().database)

    project.move_data(out, prefix, suffix, paired_end)

    console.print("[green]finished moving files")


@cli.command()
@click.option("-u", "--user", help="name of user who submitted job")
@click.option("-s", "--sample", help="sample id")
@click.option("-i", "--info", help="text found on job info sheet")
@click.option("-rt", "--run-type", help="run type for the job")
def query(user: str, sample: str, info: str, run_type: str):
    """Query existing projects

    Currently an experimental feature!
    """

    console.print("Searching the data...")

    db = DataBase()
    db.query(user, run_type, sample, info)


@cli.command()
@click.argument("project_id")
@click.option(
    "--data-only", help="remove only data for an individual project", is_flag=True
)
def remove(project_id: str, data_only: bool):
    """Remove a project or it's sequencing data"""

    console.print(f"Attempting to remove {project_id}")

    db = DataBase()
    db.remove_project(project_id, data_only)

    console.print("[green]Project has been remove successfully")


def main():

    head = r"""
 __  _  _   _      ___
(_  |_ / \ | \  /\  |
__) |_ \_X |_/ /--\ |
"""

    console.print(head, style="magenta", highlight=False)
    console.print("[green bold]SEQ[/]uencing [green bold]DAT[/]a manager.\n")
    cli()


if __name__ == "__main__":
    main()
