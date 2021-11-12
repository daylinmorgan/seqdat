import re
from os import PathLike
from pathlib import Path
from typing import Union

from rich.prompt import Prompt

from .console import console


def ask_name(name: str = None) -> str:
    """Ask user for job name and verify it is in the form JA#####.

    Args:
        name (str, optional): name/id for the sequencing job. Defaults to None.

    Returns:
        str: validated job name
    """

    while True:
        name = Prompt.ask("[blue]Project ID", default=name)
        if name is None:
            console.print("[error]Invalid Job Name: project name can't be empty")
            continue
        elif not re.match(r"JA\d{5}", name):
            console.print(
                "[error]Invalid Job Name:"
                " job title should be in the format [yellow b]JA#####"
            )
            name = None
            continue
        else:
            break

    return name


def ask_owner(owner: str = None, user: str = None) -> str:
    """Ask user for the owner of the sequencing job.

    Args:
        owner (str, optional): Name derived from metadata or cli. Defaults to None.
        user (str, optional): Name derived from config file. Defaults to None.

    Returns:
        str: Name of the job owner
    """

    while True:
        owner = Prompt.ask("[blue]Owner", default=(owner or user))
        if owner is None:
            console.print("[error]Invalid Owner Name: owner name can't be empty")
            continue
        else:
            break

    return owner


def ask_database(db: str) -> Path:
    """Ask user for path to the database.

    Args:
        db (str): pathlike str where database is stored in local storage

    Returns:
        Path: path to database if it exists
    """

    while True:
        db = Prompt.ask("[blue]Database Path", default=str(db))
        if not Path(db).expanduser().is_dir():
            console.print("[error]Invalid Database: must be a valid directory")
            db = ""
            continue
        else:
            break

    return Path(db).expanduser()
