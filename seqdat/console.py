from rich.console import Console
from rich.theme import Theme

custom_theme = Theme(
    {"hl": "dim cyan", "info": "yellow", "error": "bold red", "code": "yellow"}
)

console = Console(theme=custom_theme)
