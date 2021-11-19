import operator
import shutil
import sys
from typing import Iterable, List

from rich import box
from rich.columns import Columns
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from .config import Config
from .console import console
from .project import Project


class DataBase:
    """Database of sequencing projects."""

    def __init__(self):
        self.config: Config = Config.load()
        self.projects: List[Project] = self._initialize_projects()

    def _initialize_projects(self) -> List[Project]:
        """Generate a list of projects from database directory.

        Returns:
            List[Project]: project derived from database directory, dependent on valid metadata
        """
        projects = [
            Project.from_metadata(project_dir.name, self.config.database)
            for project_dir in self.config.database.iterdir()
        ]
        for project in projects:
            if project.samples is None:
                project.identify_samples()

        return projects

    def display_projects(
        self,
        projects: Iterable[Project],
        limit: int = None,
        field: str = "name",
        ascending: bool = False,
    ):
        """Print a table of projects.

        Args:
            projects (Iterable[Project]): list of project to display.
            limit (int, optional): max number of projects to display. Defaults to None.
            field (str, optional): field to sort by (name or owner). Defaults to "name".
            ascending (bool, optional): if true make sort ascending. Defaults to False.
        """

        if not projects:
            projects = self.projects

        table = Table(box=box.ROUNDED)

        table.add_column("Project", style="bold cyan")
        table.add_column("Owner", style="yellow")
        table.add_column("# of Samples", style="magenta")
        table.add_column("Run Type", style="orange1")

        sorted_projects = sorted(
            projects, key=operator.attrgetter(field), reverse=ascending
        )

        for project in sorted_projects[:limit]:

            num_samples = str(len(project.samples) if project.samples else "n/a")
            table.add_row(project.name, project.owner, num_samples, project.run_type)

        console.print(table)

    def query(
        self,
        owner: str,
        run_type: str,
        sample: str,
        info: str,
    ):
        """Search for projects that match any of the given queries.

        Current implementation doesn't require a match of all search fields.

        Args:
            owner (str, optional): owner/user to search for. Defaults to None.
            run_type (str, optional): type of run to search for. Defaults to None.
            sample (str, optional): samples to search for in metadata. Defaults to None.
            info (str, optional): short text to look for in info sheet. Defaults to None.
        """
        console.print(
            "[magenta]Warning![/] This feature is still experimental and subject to change in future releases\n"
        )

        if all(v is None for v in [owner, run_type, sample, info]):
            console.print("Please specify at least one search parameter")
            console.print("See: [code]seqdat query --help[/code] for more information")
            sys.exit()

        if owner:
            console.print(f"Searching for user: [cyan]{owner}")
        if sample:
            console.print(f"Searching for sample: [cyan]{sample}")
        if info:
            console.print(f"Searching for info: [cyan]{info}")
        if run_type:
            console.print(f"Searching for run type: [cyan]{run_type}")

        matched_projects = []
        if owner:
            projects = [
                project
                for project in self.projects
                if owner.lower() in project.owner.lower()
            ]
            matched_projects.extend(projects)
        if run_type:
            projects = [
                project
                for project in self.projects
                if project.run_type and run_type.lower() in project.run_type.lower()
            ]
            matched_projects.extend(projects)
        if sample:
            projects = [
                project
                for project in self.projects
                if project.samples
                and sample.lower() in [s.lower() for s in project.samples]
            ]
            matched_projects.extend(projects)
        if info:
            projects_info = []
            for project in self.projects:
                try:
                    with (self.config.database / project.name / "README.md").open(
                        "r"
                    ) as f:
                        if info.lower() in f.read().lower():
                            projects_info.append(project)
                except FileNotFoundError:
                    console.print(f"[info]>>>[/]No job info sheet for {project.name}")
            matched_projects.extend(projects_info)

        if not matched_projects:
            console.print("No matching projects found.")
        else:
            self.display_projects(projects=matched_projects)

    def remove_project(self, name: str, data_only: bool):
        """Remove a project or it's data subdirectory

        Args:
            name (str): name/id of project
            data_only (bool): if true remove only data and retain job info/metadata
        """

        try:
            project = {project.name: project for project in self.projects}[name]
            console.print(f"Found project: [hl]{name}")

        except KeyError:
            console.print(f"[error]Project [hl]{name}[/] not found")
            console.print(
                "Please use [code]seqdat list[/] or [code]seqdat query[/] to view projects"
            )
            sys.exit()

        if self.config.user != project.owner:
            console.print("[error]You are about to delete another user's project/data")

        if data_only:
            project_data_dir = self.config.database / project.name / "data"

            data = [
                sample_dir
                for sample_dir in (project_data_dir).iterdir()
                if sample_dir.is_dir()
            ]

            if not project.samples:
                project.identify_samples()

            if project.samples:
                console.print(f"Found the following data for project: [hl]{name}")
                samples = [Panel(sample) for sample in project.samples]
            else:
                console.print(f"[error]Project {project.name} has no sample files.")
            num_samples = len(samples)
            width = 70
            console.print(f"[blue]{num_samples} Samples")
            console.print(Columns(samples), width=width)
            if Confirm.ask("Would you like to remove this data [info]permanently?"):
                for sample_dir in data:
                    try:
                        shutil.rmtree(sample_dir)
                    except OSError as e:
                        print(f"[error]Error: {e.filename} - {e.strerror}.")

        else:
            pass
