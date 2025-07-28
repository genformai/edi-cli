"""Main CLI entry point for edi-cli."""

import typer
import json
import os
from typing_extensions import Annotated
from pathlib import Path

# For now, we'll implement a minimal CLI that can be extended later
app = typer.Typer(help="edi-cli - A developer-friendly CLI for parsing and testing EDI files")

def main():
    """Main entry point for the edi-cli package."""
    app()

@app.command()
def version():
    """Show the version of edi-cli."""
    print("edi-cli version 0.1.0")

@app.command()
def status():
    """Show the status of edi-cli installation."""
    print("✅ edi-cli is properly installed")
    print("📦 Package: edi-cli")
    print("🔢 Version: 0.1.0")
    print("🐍 Python: Compatible with Python >=3.7")
    print()
    print("🚧 Note: This is a minimal release to reserve the PyPI namespace.")
    print("🔜 Full EDI parsing functionality will be available in future releases.")

@app.callback(invoke_without_command=True)
def default_command(ctx: typer.Context):
    """Default command when no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        print("edi-cli is installed and running!")
        print("Version: 0.1.0")
        print()
        print("🚧 This is a minimal release to reserve the PyPI namespace.")
        print("🔜 Full EDI parsing functionality coming soon!")
        print()
        print("Available commands:")
        print("  edi-cli version    Show version information")
        print("  edi-cli status     Show installation status")
        print("  edi-cli --help     Show detailed help")

if __name__ == "__main__":
    app()