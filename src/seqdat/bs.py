import subprocess
import sys
from pathlib import Path

from .console import console


def download_data(database: Path, name: str, bs_params: str = None):
    """Downloads the specific project into the database.

    Args:
        database (Path): path to the seqdat database
        name (str): name/job id of the sequencing project
        bs_params (str, optional): parameters to pass to `bs download project` . Defaults to None.
    """

    cmd = (
        f"bs download project --name {name} -o {database}/{name}/data {bs_params or ''}"
    )
    try:
        with console.status(
            "[hl b] downloading data from basespace",
            spinner="bouncingBar",
            spinner_style="yellow",
        ) as status:  # noqa
            process = subprocess.run(  # noqa
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,
                check=True,
                encoding="utf-8",
            )

        console.print("[info]Download finished.")

    except subprocess.CalledProcessError as err:
        console.print("[red]DOWNLOAD FAILED.")
        console.print("[red]see the below output from basespace-cli:")
        print(err.stdout)
        if "could not parse config file" in err.stdout:
            console.print("No config? Have you authenticated bs-cli?")
            console.print("Run the below command to authenticate with basespace")
            console.print("\n bs auth login")
        sys.exit(1)
