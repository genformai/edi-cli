#!/usr/bin/env python3
"""
Simple CLI for EDI processing that avoids Typer compatibility issues.
"""
import sys
import os
import json
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Use new transaction-specific parsers
from core.transactions.t835.parser import Parser835

def parse_edi_content(edi_content: str, schema_name: str):
    """Parse EDI content using appropriate parser based on schema."""
    # Convert EDI string to segments
    segments = []
    for line in edi_content.replace('~', '\n').strip().split('\n'):
        if line.strip():
            segments.append(line.split('*'))
    
    # Use appropriate parser based on schema
    if schema_name in ["x12-835-5010", "835"]:
        parser = Parser835(segments)
        return parser.parse()
    else:
        raise ValueError(f"Unsupported schema: {schema_name}. Currently supported: 835")

def convert_command(input_file: str, output_format: str = "json", output_file: Optional[str] = None, schema: str = "x12-835-5010"):
    """Convert an EDI file to another format (JSON or CSV)."""
    try:
        if not os.path.exists(input_file):
            print(f"❌ Input file not found: {input_file}")
            return 1
            
        with open(input_file, 'r') as f:
            edi_content = f.read()
            
        # Parse using new architecture
        result = parse_edi_content(edi_content, schema)
        
        if output_format == "json":
            # Get the 835 transaction data if available
            if result.interchanges and result.interchanges[0].functional_groups:
                transaction = result.interchanges[0].functional_groups[0].transactions[0]
                if hasattr(transaction, 'transaction_data') and transaction.transaction_data:
                    output = json.dumps(transaction.transaction_data.to_dict(), indent=2, default=str)
                else:
                    output = json.dumps({"error": "No transaction data found"}, indent=2)
            else:
                output = json.dumps({"error": "No transactions found"}, indent=2)
        elif output_format == "csv":
            print("❌ CSV output not yet implemented for new parser architecture")
            return 1
        else:
            print(f"❌ Unknown format: {output_format}. Supported formats: json")
            return 1

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            print(f"✅ Output written to: {output_file}")
        else:
            print(output)
        return 0
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

def validate_command(input_file: str, schema: str = "x12-835-5010", verbose: bool = False):
    """Validate an EDI file against a schema."""
    try:
        if not os.path.exists(input_file):
            print(f"❌ Input file not found: {input_file}")
            return 1
            
        with open(input_file, 'r') as f:
            edi_content = f.read()
            
        # Parse the EDI file using new architecture
        result = parse_edi_content(edi_content, schema)
        
        # Basic validation - check if file was parsed successfully
        if not result.interchanges:
            print("❌ Validation failed: No valid interchanges found")
            return 1
        
        # For now, just do basic structural validation
        print("ℹ️  Basic validation only - full validation engine coming in v0.3.1")
        
        transaction_count = 0
        claim_count = 0
        
        for interchange in result.interchanges:
            for group in interchange.functional_groups:
                for transaction in group.transactions:
                    transaction_count += 1
                    if hasattr(transaction, 'transaction_data') and transaction.transaction_data:
                        if hasattr(transaction.transaction_data, 'claims'):
                            claim_count += len(transaction.transaction_data.claims)
        
        # Basic validation passed
        is_valid = transaction_count > 0
        
        if is_valid:
            print("✅ Basic validation passed")
        else:
            print("❌ Basic validation failed")
        
        print(f"\n📋 Document Structure:")
        print(f"  • Interchanges: {len(result.interchanges)}")
        print(f"  • Functional Groups: {sum(len(i.functional_groups) for i in result.interchanges)}")
        print(f"  • Transactions: {transaction_count}")
        print(f"  • Claims: {claim_count}")
        
        return 0 if is_valid else 1
            
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1

def inspect_command(input_file: str, segments: Optional[str] = None):
    """Inspect an EDI file and extract specific segments or show structure."""
    try:
        if not os.path.exists(input_file):
            print(f"❌ Input file not found: {input_file}")
            return 1
            
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
            print(f"🔍 Extracting segments: {', '.join(segment_list)}")
            print("=" * 50)
            
            for segment in edi_segments:
                if segment and segment[0] in segment_list:
                    print('*'.join(segment))
        else:
            # Show file structure
            print("📋 EDI File Structure:")
            print("=" * 50)
            
            segment_counts = {}
            for segment in edi_segments:
                if segment:
                    seg_id = segment[0]
                    segment_counts[seg_id] = segment_counts.get(seg_id, 0) + 1
            
            for seg_id, count in sorted(segment_counts.items()):
                print(f"{seg_id:>3}: {count:>3} occurrences")
        
        return 0
                
    except Exception as e:
        print(f"❌ Error inspecting file: {e}")
        return 1

def print_help():
    """Print help information."""
    print("""
EDI CLI - A modern toolkit for working with EDI files

Usage: python -m packages.cli.main_simple <command> [arguments]

Commands:
  convert <input_file> [--to json] [--out output_file] [--schema x12-835-5010]
    Convert an EDI file to another format (JSON)
    
  validate <input_file> [--schema x12-835-5010] [--verbose]
    Validate an EDI file against a schema
    
  inspect <input_file> [--segments NM1,CLP]
    Inspect an EDI file and extract specific segments or show structure
    
  help
    Show this help message

Examples:
  python -m packages.cli.main_simple convert sample.edi --to json
  python -m packages.cli.main_simple validate sample.edi --verbose
  python -m packages.cli.main_simple inspect sample.edi --segments BPR,CLP
""")

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_help()
        return 1
    
    command = sys.argv[1]
    
    if command == "help" or command == "--help" or command == "-h":
        print_help()
        return 0
    
    elif command == "convert":
        if len(sys.argv) < 3:
            print("❌ convert requires an input file")
            return 1
        
        input_file = sys.argv[2]
        output_format = "json"
        output_file = None
        schema = "x12-835-5010"
        
        # Parse additional arguments
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--to" and i + 1 < len(sys.argv):
                output_format = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--out" and i + 1 < len(sys.argv):
                output_file = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--schema" and i + 1 < len(sys.argv):
                schema = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        return convert_command(input_file, output_format, output_file, schema)
    
    elif command == "validate":
        if len(sys.argv) < 3:
            print("❌ validate requires an input file")
            return 1
        
        input_file = sys.argv[2]
        schema = "x12-835-5010"
        verbose = False
        
        # Parse additional arguments
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--schema" and i + 1 < len(sys.argv):
                schema = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--verbose" or sys.argv[i] == "-v":
                verbose = True
                i += 1
            else:
                i += 1
        
        return validate_command(input_file, schema, verbose)
    
    elif command == "inspect":
        if len(sys.argv) < 3:
            print("❌ inspect requires an input file")
            return 1
        
        input_file = sys.argv[2]
        segments = None
        
        # Parse additional arguments
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--segments" and i + 1 < len(sys.argv):
                segments = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        return inspect_command(input_file, segments)
    
    else:
        print(f"❌ Unknown command: {command}")
        print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())