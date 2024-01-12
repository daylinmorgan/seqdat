import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import click
import tomlkit
from rich.prompt import Prompt

from ._prompts import ask_database
from .console import console

_config_file = Path(click.get_app_dir("seqdat")) / "config.toml"


@dataclass
class Config:
    """Class for keeping track of configuration options."""

    database: Path
    """valid absolute path to database"""
    user: Optional[str]
    """current user name (full name)"""

    def _sanitize_config(self) -> Dict[str, str]:
        """Sanitize config to make database a string.

        Returns:
            dict: returns dict with santized values for serialization to yaml
        """
        config_out = self.__dict__.copy()

        if config_out["database"] is not None:
            config_out["database"] = str(config_out["database"])

        return config_out

    @classmethod
    def load(self, skip_check: bool = False):
        """Load configuration values from a config.yml.

        Args:
            skip_check (bool): skip database path check
        """
        data = {"database": str(), "user": str()}

        try:
            # data.update(**yaml.load_file(_config_file))
            with _config_file.open("r") as f:
                data.update(**tomlkit.load(f))
        except FileNotFoundError:
            console.print("[error]Config file not found.[/]")
            console.print(
                "Please run [code]seqdat config --generate[/]"
                " to generate a config file."
            )
            sys.exit(1)

        if not skip_check:
            validated_database = _is_valid_database(data["database"])
        else:
            validated_database = Path(data["database"])

        return self(database=validated_database, user=data["user"])

    @classmethod
    def make(self):
        if _config_file.is_file():
            console.print("[error]Warning[/]: Config file already exists.")
            console.print("Did you mean to run [code]seqdat config --update[/]?")

        data = {"database": None, "user": ""}

        for k, v in data.items():
            if k == "database":
                data[k] = ask_database(v).resolve()
            else:
                data[k] = Prompt.ask(f"[blue]{k}", default=v)

        return self(**data)

    def update(self):
        """Iterate through the configuration values to update."""
        for k, v in self.__dict__.items():
            if k == "database":
                setattr(self, k, (ask_database(v).resolve()))
            else:
                setattr(self, k, Prompt.ask(f"[blue]{k}", default=v))

    def show(self):
        """Print the current configuration values."""
        console.print("[info]Config:")
        for k, v in self.__dict__.items():
            console.print(f"[blue]{k}[/]: {v}")

    def save(self):
        """Write configuration values to a yml file."""
        _config_file.parent.mkdir(parents=True, exist_ok=True)

        console.print(f"Saving config to {_config_file}")
        # yaml.save_file(_config_file, self._sanitize_config())
        with _config_file.open("w") as f:
            tomlkit.dump(self._sanitize_config(), f)


def _is_valid_database(database: str) -> Path:
    """Check if database str is a valid path.

    Args:
        database (Path): user defined path to database directory

    Returns:
        Path: absolute path to database directory
    """
    if Path(database).is_dir():
        return Path(database).resolve()
    else:
        console.print(f"[error]{database} is not a valid directory.[/]")
        console.print("Please run [info]seqdat config --update")
        sys.exit(1)
