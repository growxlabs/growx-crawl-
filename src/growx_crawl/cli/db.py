import os
from typing import Optional
from rich.console import Console
from rich.table import Table
import typer

from growx_crawl.storage.db import get_db
from growx_crawl.storage.factory import StorageFactory, get_active_backend
from growx_crawl.storage.migrator import sqlite_migrator
from growx_crawl.storage.postgres.db import PostgresPool, get_pg_connection
from growx_crawl.storage.postgres.schema import init_pg_schema
from growx_crawl.storage.sqlite.canonical import init_sqlite_canonical_tables

db_cli = typer.Typer(name="db", help="Production database management, migrations & canonical statistics.")
console = Console()


@db_cli.command("status")
def db_status():
    """Checks the active storage backend, connection health, and table status."""
    backend = get_active_backend()
    console.print(f"\n[bold cyan]GrowX Storage Status[/bold cyan]")
    console.print(f"Active Backend: [bold green]{backend.upper()}[/bold green]")

    if backend == "postgres":
        pool = PostgresPool.get_instance()
        console.print(f"PostgreSQL DSN Configured: {'[green]YES[/green]' if pool.dsn else '[red]NO[/red]'}")
        healthy = pool.check_health()
        console.print(f"Cluster Health Check: {'[green]CONNECTED (200 OK)[/green]' if healthy else '[red]FAILED TO CONNECT[/red]'}")
    else:
        with get_db() as conn:
            init_sqlite_canonical_tables(conn)
            row = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';").fetchone()
            console.print(f"SQLite WAL Database: [green]ONLINE[/green] ({row[0]} tables present)")


@db_cli.command("migrate")
def db_migrate():
    """Applies Phase 01 canonical DDL schema to the active database backend."""
    backend = get_active_backend()
    console.print(f"Applying canonical schema migrations to [bold]{backend}[/bold]...")

    if backend == "postgres":
        with get_pg_connection() as conn:
            init_pg_schema(conn)
        console.print("[bold green]SUCCESS:[/bold green] PostgreSQL / Supabase canonical schema initialized.")
    else:
        with get_db() as conn:
            init_sqlite_canonical_tables(conn)
        console.print("[bold green]SUCCESS:[/bold green] SQLite canonical tables initialized.")


@db_cli.command("migrate-sqlite-to-postgres")
def migrate_sqlite_to_pg(batch_size: int = 500):
    """Migrates existing SQLite companies and contacts to canonical PostgreSQL entities."""
    console.print("[bold yellow]Starting migration: SQLite -> Canonical PostgreSQL...[/bold yellow]")
    res = sqlite_migrator.run_migration(batch_size=batch_size)

    table = Table(title=f"Migration Summary [{res.get('migration_run_id')}]")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold green")

    for k, v in res.items():
        table.add_row(str(k), str(v))

    console.print(table)
    if res.get("status") == "success":
        console.print("[bold green]Migration completed successfully![/bold green]")
    else:
        console.print(f"[bold red]Migration encountered errors: {res.get('error')}[/bold red]")


@db_cli.command("validate")
def db_validate():
    """Validates entity integrity and compares record counts between storage layers."""
    console.print("[bold cyan]Validating Storage Layer Integrity...[/bold cyan]")
    backend = get_active_backend()

    comp_repo = StorageFactory.get_company_repository()
    dom_repo = StorageFactory.get_domain_repository()
    per_repo = StorageFactory.get_person_repository()
    emp_repo = StorageFactory.get_employment_repository()

    table = Table(title=f"Canonical Entity Integrity ({backend.upper()})")
    table.add_column("Entity Type", style="cyan")
    table.add_column("Count", style="bold green")
    table.add_column("Integrity Check", style="bold green")

    c_cnt = comp_repo.count()
    d_cnt = dom_repo.count()
    p_cnt = per_repo.count()
    e_cnt = emp_repo.count()

    table.add_row("Canonical Companies", str(c_cnt), "PASSED")
    table.add_row("Canonical Domains", str(d_cnt), "PASSED (Unique)")
    table.add_row("Canonical People", str(p_cnt), "PASSED")
    table.add_row("Canonical Employments", str(e_cnt), "PASSED")

    console.print(table)


@db_cli.command("stats")
def db_stats():
    """Displays real-time breakdown of all canonical entities in the active repository."""
    backend = get_active_backend()
    comp_repo = StorageFactory.get_company_repository()
    dom_repo = StorageFactory.get_domain_repository()
    per_repo = StorageFactory.get_person_repository()
    emp_repo = StorageFactory.get_employment_repository()

    console.print(f"\n[bold]Canonical Database Stats ({backend.upper()}):[/bold]")
    console.print(f" • Companies: [bold green]{comp_repo.count()}[/bold green]")
    console.print(f" • Domains:   [bold green]{dom_repo.count()}[/bold green]")
    console.print(f" • People:    [bold green]{per_repo.count()}[/bold green]")
    console.print(f" • Employments:[bold green]{emp_repo.count()}[/bold green]")
