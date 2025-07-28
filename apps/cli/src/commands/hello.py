import typer

app = typer.Typer()

@app.command()
def hello(name: str):
    """
    Says hello to the user.
    """
    typer.echo(f"Hello, {name}!")

if __name__ == "__main__":
    app()
