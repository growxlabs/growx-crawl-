from rich.console import Console
from rich.table import Table

console = Console()


def log_info(msg: str):
    console.print(f"[bold blue][INFO][/bold blue] {msg}")


def log_success(msg: str):
    console.print(f"[bold green][SUCCESS][/bold green] {msg}")


def log_warning(msg: str):
    console.print(f"[bold yellow][WARNING][/bold yellow] {msg}")


def log_error(msg: str):
    console.print(f"[bold red][ERROR][/bold red] {msg}")


def render_table(title: str, headers: list, rows: list):
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for h in headers:
        table.add_column(h)
    for r in rows:
        table.add_row(*[str(c) for c in r])
    console.print(table)
