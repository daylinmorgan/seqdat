import json
import shutil
import sys
from pathlib import Path
from typing import Dict, Iterator, List

from rich import box
from rich.columns import Columns
from rich.json import JSON
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from ._prompts import ask_name, ask_owner
from .bs import download_data
from .config import Config
from .console import console


class Project:
    """A class for a sequencing project"""

    config: Config

    def __init__(
        self,
        name: str,
        owner: str,
        run_type: str = None,
        samples: List[str] = None,
    ):
        """initialize project.

        Args:
            name (str): name/id of sequencing project
            owner (str): user who submitted sequencing job
            run_type (Optional[str]): sequencer/kit used for job
            samples (List[str], optional): samples for the job. Defaults to None.
        """
        self.name = name
        self.owner = owner
        self.run_type = run_type
        self.samples = samples

    @classmethod
    def from_prompt(
        self,
        name: str,
        owner: str = None,
        run_type: str = None,
        user: str = None,
    ):
        """Construct Project with user prompts

        Args:
            name (str): name/id of sequencing project
            owner (str): user who submitted sequencing job
            run_type (Optional[str]): sequencer/kit used for job
            user (str): user taken from config file (will be defualt for owner prompt)
        """

        self.config = Config.load()

        name = ask_name(name)
        owner = ask_owner(owner, user)
        run_type = Prompt.ask("[blue]Run Type", default=run_type)

        if (self.config.database / name).is_dir():
            if not Confirm.ask(
                "This project already exists. Proceed with initialization?"
            ):
                sys.exit()

        return self(name, owner, run_type)

    @classmethod
    def from_metadata(self, name: str, database: Path):
        """Construct Project from metadata file

        Args:
            name (str): name/id of sequencing project
            database (Path): absolute path to the sequencing database
        """

        self.config = Config.load()

        metapath = database / name / "meta.json"

        try:
            with metapath.open("r") as f:
                metadata = json.load(f)

        except FileNotFoundError:
            console.print(f"[info]no metadata found for {name}")
            metadata = {
                "name": name,
                "owner": None,
                "run_type": None,
            }
        if not (self.config.database / name).is_dir():
            console.print(f"[error]Project: [hl]{name}[/] doesn't exist.")
            console.print(
                f"To create a new project run [code]seqdat init --name {name}"
            )
            sys.exit(1)

        return self(**metadata)

    def view_metadata(self):
        """Display metadata in current project instance"""

        metadata = self.__dict__.copy()
        console.print(f"[info]Project {self.name} Metadata")
        for k, v in metadata.items():
            console.print(f"[hl]{k}[/]: {v}", width=50)

    def view_basespace_meta(self):
        """Display the metadata from basespace json"""

        json_path = sorted((self.config.database / self.name / "data").glob("*.json"))

        if json_path:
            json_path = json_path[0]
            console.print(f"\n[info]Basespace metadata for {self.name}\n")
            console.print(Syntax.from_path(json_path, word_wrap=True))
        else:
            console.print(f"[info]no Basespace metadata found for {self.name}")

    def save_metadata(self):
        """Write Project metadata to meta.yml."""

        metapath = self.config.database / self.name / "meta.json"
        metadata = self.__dict__.copy()
        console.print(f"\nSaving metadata to {metapath}")

        if metapath.exists():
            console.print("found existing metadata file.")
            with metapath.open("r") as f:
                old_meta = json.load(f)

            if old_meta == metadata:
                console.print("metadata is the same as the old one, nothing to change")
                return

            table = Table(box=box.SIMPLE)

            table.add_column("[hl]old metadata", max_width=50)
            table.add_column("[hl]new metadata", max_width=50)
            table.add_row(JSON.from_data(old_meta), JSON.from_data(metadata))
            console.print(table)

            if Confirm.ask("would you like to overwrite it?"):
                console.print("saving metadata to meta.json")
            else:
                console.print("[info]nothing written to meta.json")
                return
        else:
            metapath.parent.mkdir(exist_ok=True)

        with metapath.open("w") as f:
            json.dump(metadata, f, indent=4)

    def update_metadata(self):
        """Update metadata attributes of Project."""

        # disallow changing name
        metadata = {k: v for k, v in self.__dict__.copy().items() if k != "name"}
        updated_metadata = {}
        console.print(f"Project: {self.name}")
        for k, v in metadata.items():
            if k == "samples":
                console.print(
                    "[hl]\n>>NOTE: [/]to update sample list run "
                    f"[yellow]seqdat meta {self.name} --update-samples"
                )
            else:
                updated_metadata[k] = Prompt.ask(f"[blue]{k}", default=v)

        self._update_attrs(updated_metadata)
        self.save_metadata()

    def _update_attrs(self, updated_attrs: dict):
        for k, v in updated_attrs.items():
            setattr(self, k, v)

    def fetch_data(self, bs_params: str):
        """Download data for Project from Basespace

        Requires that user has authorized and installed bs-cli

        Args:
            bs_params (str): parameters to pass to bs download project
        """
        console.print("Fetching data from Basespace with below command")
        cmd = "[code]  bs project download --name "
        f"[hl]{self.name}[/] -o {self.config.database}"
        f"/{self.name}/data {bs_params or ''}"
        console.print(f"\n {cmd}\n")

        download_data(self.config.database, self.name, bs_params)

    def identify_samples(self):
        """Identify samples from the downloaded data."""

        path_to_data = self.config.database / self.name / "data"

        try:
            self.samples = sorted(
                set(
                    [
                        f.name.split("_")[0]
                        for f in walk(path_to_data)
                        if f.suffixes == [".fastq", ".gz"]
                    ]
                )
            )
        except FileNotFoundError:
            console.print(f"[info]no data currently available for project: {self.name}")

    def move_data(
        self,
        out: str,
        prefix: str,
        suffix: str,
        paired_end: bool,
        move_samples_str: str,
    ):
        """Simultaneosly concatenate and move data.

        Args:
            out (str): directory to transfer data to
            prefix (str): prefix to add to file names
            suffix (str): suffix (before file extension) to add to file names
            paired_end (bool):
              if true, run in paired-end mode and concatenate R1/R2 seperately
        """

        if not self.samples:
            self.identify_samples()
            if not self.samples:
                console.print("Did you remember to download from basespace?")
                console.print(
                    "You can download directly from basespace with below command:"
                )
                console.print(
                    f"[code]bs download project -n "
                    f"{self.name} -o {self.config.database}/{self.name}/data"
                )
                console.print(f"Or rerun: [code]seqdat init --name {self.name}")
                sys.exit(1)

        out_path = Path(out)

        try:
            out_path.mkdir(parents=True)
        except FileExistsError:
            console.print(f"[error]{out} already exists I'm not going to overwrite it.")
            sys.exit(1)

        path_to_data = self.config.database / self.name / "data"

        sample_files: Dict[str, List[Path]] = {}
        for file in path_to_data.glob("**/*.fastq.gz"):
            sample_files.setdefault(file.name.split("_")[0], []).append(file)

        if move_samples_str:
            move_samples = move_samples_str.split(",")
            # TODO: refactor to add red color to bad file names
            if not all(i in sample_files.keys() for i in move_samples):
                console.print("[bold red]Error[/]: Unknown sample provided.")
                console.print(
                    "Please check that the sample names you provided: ", end=""
                )
                console.print(
                    ", ".join(
                        [
                            f"[red]{sample}"
                            if sample not in sample_files.keys()
                            else sample
                            for sample in sorted(move_samples)
                        ]
                    )
                )
                console.print(
                    f"Matches the project's samples: {' '.join(sorted(sample_files))}"
                )
                out_path.rmdir()
                sys.exit(1)
        else:
            move_samples = sorted(list(sample_files.keys()))

        samples = [
            f"[b cyan]{sample}[/]" if sample in move_samples else f"[dim]{sample}[/]"
            for sample in sorted(sample_files)
        ]

        console.print(
            Columns(
                ["\n".join(samples[start::3]) for start in range(3)],
                padding=5,
                title="[yellow]Samples to move",
            ),
            "\n",
        )

        if not Confirm.ask(
            f"Move the {len(move_samples)} [cyan]highlighted[/] samples to {out_path}"
        ):
            console.print(f"Nothing written to {out_path}")
            out_path.rmdir()
            sys.exit(0)
        else:
            sample_files = {k: v for k, v in sample_files.items() if k in move_samples}

        console.print(f"[info]Moving data to {out_path}")
        for sample, files in sorted(sample_files.items()):
            cat_fastqgz(sample, files, out_path, prefix, suffix, paired_end)

            console.print(f"[hl]{sample}[/] moved")

    def generate_info_sheet(self):
        """Generate job info sheet from Project metadata."""

        num_samples = len(self.samples) if self.samples else None

        info_sheet = f"""
# {self.name}

- Owner: {self.owner}
- Run Type: {self.run_type}
- Number of Samples: {num_samples}

"""
        info_sheet_cont = "## Additional Info\n..."

        info_sheet_path = self.config.database / self.name / "README.md"
        info_sheet_path.parent.mkdir(exist_ok=True)

        if info_sheet_path.exists():
            info_sheet_cont = get_existing_info_sheet(info_sheet_path)

        console.print("[blue] Job Info Sheet", justify="center", width=80)
        console.print(Panel(Markdown(info_sheet + info_sheet_cont), width=80))

        if info_sheet_path.exists() and not Confirm.ask(
            "Job Info Sheet Already Exists. Overwrite it?"
        ):
            console.print("[info]Nothing written to job sheet")
        else:
            with info_sheet_path.open("w") as f:
                f.write(info_sheet)
                f.write(info_sheet_cont)


def get_existing_info_sheet(info_sheet_path: Path) -> str:
    """Check for existing info sheet

    Args:
        info_sheet_path (Path): location of info sheet

    Returns:
        str: info sheet data after ## Addtional Info
    """

    info_sheet_cont = "## Additional Info\n"
    with info_sheet_path.open("r") as f:
        while "## Additional Info" not in next(f):
            pass
        for line in f:
            info_sheet_cont += line

        return info_sheet_cont


def cat_fastqgz(
    sample: str,
    files: List[Path],
    out: Path,
    prefix: str,
    suffix: str,
    paired_end: bool,
):
    """Concatenate and move fastq.gz

    Args:
        sample (str): name of sample
        files (List[Path]): list of all sample files
        out (Path): directory to transfer data to
        prefix (str): prefix to add to file names
        suffix (str): suffix (before file extension) to add to file names
        paired_end (bool):
          if true, run in paired-end mode and concatenate R1/R2 seperately
    """

    with Progress(transient=True) as progress:
        task = progress.add_task(f"[yellow]moving {sample}...", total=len(files))

        # remove user decision about concatenating paired end reads?

        r1_files = [f for f in files if "_R1_" in f.name]
        r2_files = [f for f in files if "_R2_" in f.name]

        if paired_end:
            with (out / f"{sample}.R1{suffix}.fastq.gz").open("wb") as out_f:
                for fastqgz in r1_files:
                    with fastqgz.open("rb") as in_f:
                        shutil.copyfileobj(in_f, out_f)
                        progress.update(task, advance=1)
            with (out / f"{prefix}{sample}.R2{suffix}.fastq.gz").open("wb") as out_f:
                for fastqgz in r2_files:
                    with fastqgz.open("rb") as in_f:
                        shutil.copyfileobj(in_f, out_f)
                        progress.update(task, advance=1)
        else:
            if r2_files:
                console.print(
                    f"\n[error]{sample} has R2 files. "
                    "Did you mean to run in [code]--paired-end[/] mode?"
                )
                sys.exit(1)
            with (out / f"{prefix}{sample}{suffix}.fastq.gz").open("wb") as out_f:
                for fastqgz in files:
                    with fastqgz.open("rb") as in_f:
                        shutil.copyfileobj(in_f, out_f)
                        progress.update(task, advance=1)


def walk(path: Path) -> Iterator[Path]:
    """Walk directory to get file paths.

    Args:
        path (Path): path to walk down

    Yields:
        Iterator[Path]: iterator of all files in path
    """
    for p in Path(path).iterdir():
        if p.is_dir():
            yield from walk(p)
            continue
        yield p.resolve()
