import typer
import json
import os
from typing_extensions import Annotated
from pathlib import Path

# Import using relative paths since we're in the packages structure
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.parser import EdiParser
from core.emitter import EdiEmitter

app = typer.Typer(help="EDI CLI - A modern toolkit for working with EDI files")

def get_schema_path(schema_name: str) -> str:
    """Get the full path to a schema file."""
    # Map common schema names to file paths
    schema_map = {
        "x12-835-5010": "835.json",
        "835": "835.json",
    }
    
    filename = schema_map.get(schema_name, f"{schema_name}.json")
    base_dir = Path(__file__).parent.parent
    schema_path = base_dir / "core" / "schemas" / "x12" / filename
    
    if not schema_path.exists():
        typer.echo(f"Schema file not found: {schema_path}")
        raise typer.Exit(1)
    
    return str(schema_path)

@app.command()
def convert(
    input_file: Annotated[str, typer.Argument(help="The path to the input EDI file.")],
    to: Annotated[str, typer.Option(help="The output format (json or csv).")] = "json",
    output_file: Annotated[str, typer.Option("--out", "-o", help="The path to the output file.")] = None,
    schema: Annotated[str, typer.Option(help="The name of the schema to use for parsing.")] = "x12-835-5010",
):
    """Convert an EDI file to another format (JSON or CSV)."""
    try:
        if not os.path.exists(input_file):
            typer.echo(f"Input file not found: {input_file}")
            raise typer.Exit(1)
            
        schema_path = get_schema_path(schema)
        
        with open(input_file, 'r') as f:
            edi_content = f.read()
            
        parser = EdiParser(edi_string=edi_content, schema_path=schema_path)
        edi_root = parser.parse()
        emitter = EdiEmitter(edi_root)

        if to == "json":
            output = emitter.to_json(pretty=True)
        elif to == "csv":
            output = emitter.to_csv()
        else:
            typer.echo(f"Unknown format: {to}. Supported formats: json, csv")
            raise typer.Exit(1)

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            typer.echo(f"Output written to: {output_file}")
        else:
            typer.echo(output)
            
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)

@app.command()
def validate(
    input_file: Annotated[str, typer.Argument(help="The path to the input EDI file.")],
    schema: Annotated[str, typer.Option(help="The name of the schema to use for validation.")] = "x12-835-5010",
    rules: Annotated[str, typer.Option(help="The path to a YAML file containing validation rules.")] = None,
    rule_set: Annotated[str, typer.Option(help="Predefined rule set to use (basic, hipaa, business).")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed validation results.")] = False,
    format_output: Annotated[str, typer.Option("--format", help="Output format (text, json).")] = "text",
):
    """Validate an EDI file against a schema and business rules."""
    try:
        if not os.path.exists(input_file):
            typer.echo(f"Input file not found: {input_file}")
            raise typer.Exit(1)
            
        schema_path = get_schema_path(schema)
        
        with open(input_file, 'r') as f:
            edi_content = f.read()
            
        # Parse the EDI file
        parser = EdiParser(edi_string=edi_content, schema_path=schema_path)
        edi_root = parser.parse()
        
        # Basic validation - check if file was parsed successfully
        if not edi_root.interchanges:
            typer.echo("❌ Validation failed: No valid interchanges found")
            raise typer.Exit(1)
        
        # Initialize validation engine
        from core.validation import ValidationEngine
        from core.validators_835 import get_835_business_rules
        
        engine = ValidationEngine()
        
        # Load built-in business rules for 835
        if schema in ["x12-835-5010", "835"]:
            for rule in get_835_business_rules():
                engine.add_rule(rule)
        
        # Load predefined rule sets
        if rule_set:
            rules_dir = Path(__file__).parent.parent / "validation-rules"
            if rule_set == "basic":
                rules_file = rules_dir / "835-basic.yml"
            elif rule_set == "hipaa":
                rules_file = rules_dir / "hipaa-basic.yml"
            elif rule_set == "business":
                # Load both basic and business rules
                basic_rules = rules_dir / "835-basic.yml"
                hipaa_rules = rules_dir / "hipaa-basic.yml"
                if basic_rules.exists():
                    engine.load_rules_from_yaml(str(basic_rules))
                if hipaa_rules.exists():
                    engine.load_rules_from_yaml(str(hipaa_rules))
            else:
                typer.echo(f"Unknown rule set: {rule_set}")
                raise typer.Exit(1)
            
            if rule_set in ["basic", "hipaa"] and Path(rules_file).exists():
                loaded_count = engine.load_rules_from_yaml(str(rules_file))
                if verbose:
                    typer.echo(f"Loaded {loaded_count} rules from {rule_set} rule set")
        
        # Load custom rules file if provided
        if rules:
            if not os.path.exists(rules):
                typer.echo(f"Rules file not found: {rules}")
                raise typer.Exit(1)
            
            loaded_count = engine.load_rules_from_yaml(rules)
            if verbose:
                typer.echo(f"Loaded {loaded_count} custom rules from {rules}")
        
        # Run validation
        validation_result = engine.validate(edi_root)
        
        # Output results
        if format_output == "json":
            import json
            result_data = {
                "is_valid": validation_result.is_valid,
                "summary": validation_result.summary(),
                "errors": [
                    {
                        "code": error.code,
                        "message": error.message,
                        "severity": error.severity.value,
                        "category": error.category.value,
                        "field_path": error.field_path,
                        "value": str(error.value) if error.value is not None else None,
                        "rule_id": error.rule_id
                    }
                    for error in validation_result.get_all_issues()
                ]
            }
            typer.echo(json.dumps(result_data, indent=2))
        else:
            # Text format output
            if validation_result.is_valid:
                typer.echo("✅ Validation passed")
            else:
                typer.echo("❌ Validation failed")
            
            # Show summary
            summary = validation_result.summary()
            typer.echo(f"\n📊 Validation Summary:")
            typer.echo(f"  • Rules applied: {summary['rules_applied']}")
            typer.echo(f"  • Errors: {summary['errors']}")
            typer.echo(f"  • Warnings: {summary['warnings']}")
            typer.echo(f"  • Info: {summary['info']}")
            
            # Show document statistics
            total_interchanges = len(edi_root.interchanges)
            total_groups = sum(len(i.functional_groups) for i in edi_root.interchanges)
            total_transactions = sum(len(g.transactions) for i in edi_root.interchanges for g in i.functional_groups)
            total_claims = sum(len(t.claims) for i in edi_root.interchanges for g in i.functional_groups for t in g.transactions)
            
            typer.echo(f"\n📋 Document Structure:")
            typer.echo(f"  • Interchanges: {total_interchanges}")
            typer.echo(f"  • Functional Groups: {total_groups}")
            typer.echo(f"  • Transactions: {total_transactions}")
            typer.echo(f"  • Claims: {total_claims}")
            
            # Show errors and warnings
            if validation_result.errors and (verbose or len(validation_result.errors) <= 10):
                typer.echo(f"\n🚨 Errors ({len(validation_result.errors)}):")
                for error in validation_result.errors:
                    typer.echo(f"  • [{error.code}] {error.message}")
                    if verbose and error.field_path:
                        typer.echo(f"    Field: {error.field_path}")
                    if verbose and error.value:
                        typer.echo(f"    Value: {error.value}")
            elif validation_result.errors:
                typer.echo(f"\n🚨 {len(validation_result.errors)} errors found (use --verbose to see details)")
            
            if validation_result.warnings and (verbose or len(validation_result.warnings) <= 5):
                typer.echo(f"\n⚠️  Warnings ({len(validation_result.warnings)}):")
                for warning in validation_result.warnings:
                    typer.echo(f"  • [{warning.code}] {warning.message}")
                    if verbose and warning.field_path:
                        typer.echo(f"    Field: {warning.field_path}")
            elif validation_result.warnings:
                typer.echo(f"\n⚠️  {len(validation_result.warnings)} warnings found (use --verbose to see details)")
        
        # Exit with error code if validation failed
        if not validation_result.is_valid:
            raise typer.Exit(1)
            
    except Exception as e:
        typer.echo(f"❌ Validation failed: {e}")
        raise typer.Exit(1)

@app.command()
def inspect(
    input_file: Annotated[str, typer.Argument(help="The path to the input EDI file.")],
    segments: Annotated[str, typer.Option(help="A comma-separated list of segment IDs to extract (e.g., NM1,CLP).")] = None,
    schema: Annotated[str, typer.Option(help="The name of the schema to use for parsing.")] = "x12-835-5010",
):
    """Inspect an EDI file and extract specific segments or show structure."""
    try:
        if not os.path.exists(input_file):
            typer.echo(f"Input file not found: {input_file}")
            raise typer.Exit(1)
            
        with open(input_file, 'r') as f:
            edi_content = f.read()
        
        # Parse the raw EDI to show segments
        edi_segments = []
        for line in edi_content.replace('\n', '').replace('\r', '').split('~'):
            if line.strip():
                parts = line.split('*')
                if parts:
                    edi_segments.append(parts)
        
        if segments:
            # Extract specific segments
            segment_list = [s.strip().upper() for s in segments.split(',')]
            typer.echo(f"Extracting segments: {', '.join(segment_list)}")
            typer.echo("=" * 50)
            
            for segment in edi_segments:
                if segment and segment[0] in segment_list:
                    typer.echo('*'.join(segment))
        else:
            # Show file structure
            typer.echo("EDI File Structure:")
            typer.echo("=" * 50)
            
            segment_counts = {}
            for segment in edi_segments:
                if segment:
                    seg_id = segment[0]
                    segment_counts[seg_id] = segment_counts.get(seg_id, 0) + 1
            
            for seg_id, count in segment_counts.items():
                typer.echo(f"{seg_id:>3}: {count:>3} occurrences")
                
    except Exception as e:
        typer.echo(f"Error inspecting file: {e}")
        raise typer.Exit(1)

@app.command()
def diff(
    file_a: Annotated[str, typer.Argument(help="The path to the first EDI file.")],
    file_b: Annotated[str, typer.Argument(help="The path to the second EDI file.")],
    schema: Annotated[str, typer.Option(help="The name of the schema to use for parsing.")] = "x12-835-5010",
):
    """Compare two EDI files and show differences."""
    try:
        if not os.path.exists(file_a):
            typer.echo(f"File A not found: {file_a}")
            raise typer.Exit(1)
        if not os.path.exists(file_b):
            typer.echo(f"File B not found: {file_b}")
            raise typer.Exit(1)
            
        schema_path = get_schema_path(schema)
        
        # Parse both files
        with open(file_a, 'r') as f:
            edi_a = f.read()
        with open(file_b, 'r') as f:
            edi_b = f.read()
            
        parser_a = EdiParser(edi_string=edi_a, schema_path=schema_path)
        parser_b = EdiParser(edi_string=edi_b, schema_path=schema_path)
        
        root_a = parser_a.parse()
        root_b = parser_b.parse()
        
        emitter_a = EdiEmitter(root_a)
        emitter_b = EdiEmitter(root_b)
        
        json_a = json.loads(emitter_a.to_json())
        json_b = json.loads(emitter_b.to_json())
        
        # Simple comparison
        if json_a == json_b:
            typer.echo("✅ Files are identical when parsed")
        else:
            typer.echo("❌ Files differ when parsed")
            
            # Show high-level differences
            interchanges_a = len(json_a.get('interchanges', []))
            interchanges_b = len(json_b.get('interchanges', []))
            
            typer.echo(f"File A: {interchanges_a} interchanges")
            typer.echo(f"File B: {interchanges_b} interchanges")
            
            if interchanges_a != interchanges_b:
                typer.echo(f"Difference: {abs(interchanges_a - interchanges_b)} interchanges")
                
    except Exception as e:
        typer.echo(f"Error comparing files: {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
