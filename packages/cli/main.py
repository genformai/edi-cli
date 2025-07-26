import typer
from typing_extensions import Annotated
from edi_cli.core.parser import EdiParser
from edi_cli.core.emitter import EdiEmitter

app = typer.Typer()

@app.command()
def convert(
    input_file: Annotated[str, typer.Argument(help="The path to the input EDI file.")],
    to: Annotated[str, typer.Option(help="The output format (json or csv).")] = "json",
    output_file: Annotated[str, typer.Option("--out", "-o", help="The path to the output file.")] = None,
    schema: Annotated[str, typer.Option(help="The name of the schema to use for parsing.")] = "x12-835-5010",
):
    """
    Converts an EDI file to another format.
    """
    # For now, we'll hardcode the schema path
    schema_path = f"packages/core/schemas/x12/{schema.replace('x12-', '')}.json"
    parser = EdiParser(edi_string=open(input_file).read(), schema_path=schema_path)
    edi_root = parser.parse()
    emitter = EdiEmitter(edi_root)

    if to == "json":
        output = emitter.to_json(pretty=True)
    elif to == "csv":
        output = emitter.to_csv()
    else:
        typer.echo(f"Unknown format: {to}")
        raise typer.Exit(1)

    if output_file:
        with open(output_file, "w") as f:
            f.write(output)
    else:
        typer.echo(output)

if __name__ == "__main__":
    app()
