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
from core.transactions.t837p.parser import Parser837P
from core.transactions.t270.parser import Parser270
from core.transactions.t276.parser import Parser276
from core.validation.engine import ValidationEngine
from core.validation.yaml_loader import YamlValidationLoader

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
    elif schema_name in ["x12-837p-5010", "837p", "837"]:
        parser = Parser837P(segments)
        return parser.parse()
    elif schema_name in ["x12-270-5010", "270", "271", "270/271"]:
        parser = Parser270(segments)
        return parser.parse()
    elif schema_name in ["x12-276-5010", "276", "277", "276/277"]:
        parser = Parser276(segments)
        return parser.parse()
    else:
        raise ValueError(f"Unsupported schema: {schema_name}. Currently supported: 835, 837p, 270/271, 276/277")

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

def validate_command(input_file: str, schema: str = "x12-835-5010", verbose: bool = False, rules_file: str = None, rule_set: str = None):
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
        
        # Initialize validation engine
        engine = ValidationEngine()
        
        # Load validation rules
        rules_loaded = 0
        if rules_file:
            if not os.path.exists(rules_file):
                print(f"❌ Rules file not found: {rules_file}")
                return 1
            try:
                loader = YamlValidationLoader()
                yaml_rules = loader.load_from_file(rules_file)
                for rule in yaml_rules:
                    engine.register_rule_plugin(rule)
                rules_loaded += len(yaml_rules)
                print(f"📋 Loaded {len(yaml_rules)} custom rules from {rules_file}")
            except Exception as e:
                print(f"❌ Error loading rules file: {e}")
                return 1
        
        elif rule_set:
            # Load predefined rule sets based on schema
            rule_files = []
            if schema in ["x12-837p-5010", "837p", "837"]:
                # 837P Professional Claims rules
                if rule_set == "basic":
                    rule_files = ["validation-rules/837p-basic.yml"]
                elif rule_set == "business":
                    rule_files = ["validation-rules/837p-basic.yml"]
                elif rule_set == "all":
                    rule_files = ["validation-rules/837p-basic.yml"]
                else:
                    print(f"❌ Rule set '{rule_set}' not supported for 837P. Available: basic, business, all")
                    return 1
            elif schema in ["x12-270-5010", "270", "271", "270/271"]:
                # 270/271 Eligibility Inquiry/Response rules
                if rule_set == "basic":
                    rule_files = ["validation-rules/270-271-basic.yml"]
                elif rule_set == "business":  
                    rule_files = ["validation-rules/270-271-basic.yml"]
                elif rule_set == "all":
                    rule_files = ["validation-rules/270-271-basic.yml"]
                else:
                    print(f"❌ Rule set '{rule_set}' not supported for 270/271. Available: basic, business, all")
                    return 1
            elif schema in ["x12-276-5010", "276", "277", "276/277"]:
                # 276/277 Claim Status Inquiry/Response rules
                if rule_set == "basic":
                    rule_files = ["validation-rules/276-277-basic.yml"]
                elif rule_set == "business":
                    rule_files = ["validation-rules/276-277-basic.yml"]
                elif rule_set == "all":
                    rule_files = ["validation-rules/276-277-basic.yml"]
                else:
                    print(f"❌ Rule set '{rule_set}' not supported for 276/277. Available: basic, business, all")
                    return 1
            else:
                # 835 Healthcare Claim Payment/Advice rules
                if rule_set == "basic":
                    rule_files = ["validation-rules/835-basic.yml"]
                elif rule_set == "business":
                    rule_files = ["validation-rules/835-basic.yml", "validation-rules/835-business.yml"]
                elif rule_set == "hipaa":
                    rule_files = ["validation-rules/835-basic.yml", "validation-rules/hipaa-835.yml"]
                elif rule_set == "hipaa-advanced":
                    rule_files = ["validation-rules/835-basic.yml", "validation-rules/hipaa-835.yml", "validation-rules/hipaa-advanced.yml"]
                elif rule_set == "enhanced-business":
                    # Use enhanced business rule engine instead of YAML rules
                    from core.validation.business_rule_plugin import BusinessRuleValidationPlugin, FieldLevelValidationPlugin
                    business_plugin = BusinessRuleValidationPlugin()
                    field_plugin = FieldLevelValidationPlugin()
                    engine.register_rule_plugin(business_plugin)
                    engine.register_rule_plugin(field_plugin)
                    rules_loaded += 2
                    print(f"📋 Loaded enhanced business rule engine with field-level validation")
                elif rule_set == "all":
                    rule_files = ["validation-rules/835-basic.yml", "validation-rules/835-business.yml", "validation-rules/hipaa-835.yml"]
                elif rule_set == "comprehensive":
                    # Load all YAML rules + enhanced business engine
                    rule_files = ["validation-rules/835-basic.yml", "validation-rules/835-business.yml", "validation-rules/hipaa-835.yml"]
                    from core.validation.business_rule_plugin import BusinessRuleValidationPlugin, FieldLevelValidationPlugin
                    business_plugin = BusinessRuleValidationPlugin()
                    field_plugin = FieldLevelValidationPlugin()
                    engine.register_rule_plugin(business_plugin)
                    engine.register_rule_plugin(field_plugin)
                    rules_loaded += 2
                    print(f"📋 Loaded enhanced business rule engine with field-level validation")
                else:
                    print(f"❌ Unknown rule set: {rule_set}. Available: basic, business, hipaa, hipaa-advanced, enhanced-business, comprehensive, all")
                    return 1
            
            loader = YamlValidationLoader()
            for rule_file in rule_files:
                if os.path.exists(rule_file):
                    try:
                        yaml_rules = loader.load_from_file(rule_file)
                        for rule in yaml_rules:
                            engine.register_rule_plugin(rule)
                        rules_loaded += len(yaml_rules)
                        print(f"📋 Loaded {len(yaml_rules)} rules from {rule_file}")
                    except Exception as e:
                        print(f"⚠️  Warning: Could not load {rule_file}: {e}")
        
        # Run validation if rules are loaded
        if rules_loaded > 0:
            print(f"\n🔍 Running validation with {rules_loaded} rules...")
            validation_result = engine.validate(result)
            
            # Display results
            if validation_result.is_valid:
                print("✅ Validation passed")
            else:
                print("❌ Validation failed")
            
            print(f"\n📊 Validation Summary:")
            print(f"  • Rules executed: {len(validation_result.executed_rules)}")
            print(f"  • Errors: {validation_result.error_count}")
            print(f"  • Warnings: {validation_result.warning_count}")
            print(f"  • Info: {validation_result.info_count}")
            print(f"  • Execution time: {validation_result.execution_time_ms:.2f}ms")
            
            # Show errors and warnings
            if validation_result.errors and (verbose or len(validation_result.errors) <= 5):
                print(f"\n🚨 Errors ({len(validation_result.errors)}):")
                for error in validation_result.errors[:10 if not verbose else None]:
                    print(f"  • [{error.code}] {error.message}")
                    if verbose and error.path:
                        print(f"    Path: {error.path}")
            elif validation_result.errors:
                print(f"\n🚨 {len(validation_result.errors)} errors found (use --verbose to see details)")
            
            if validation_result.warnings and (verbose or len(validation_result.warnings) <= 3):
                print(f"\n⚠️  Warnings ({len(validation_result.warnings)}):")
                for warning in validation_result.warnings[:5 if not verbose else None]:
                    print(f"  • [{warning.code}] {warning.message}")
                    if verbose and warning.path:
                        print(f"    Path: {warning.path}")
            elif validation_result.warnings:
                print(f"\n⚠️  {len(validation_result.warnings)} warnings found (use --verbose to see details)")
                
            if validation_result.info and verbose:
                print(f"\nℹ️  Info messages ({len(validation_result.info)}):")
                for info in validation_result.info:
                    print(f"  • [{info.code}] {info.message}")
            
            # Count document structure
            transaction_count = 0
            claim_count = 0
            for interchange in result.interchanges:
                for group in interchange.functional_groups:
                    for transaction in group.transactions:
                        transaction_count += 1
                        if hasattr(transaction, 'transaction_data') and transaction.transaction_data:
                            if hasattr(transaction.transaction_data, 'claims'):
                                claim_count += len(transaction.transaction_data.claims)
            
            print(f"\n📋 Document Structure:")
            print(f"  • Interchanges: {len(result.interchanges)}")
            print(f"  • Functional Groups: {sum(len(i.functional_groups) for i in result.interchanges)}")
            print(f"  • Transactions: {transaction_count}")
            print(f"  • Claims: {claim_count}")
            
            return 0 if validation_result.is_valid else 1
        
        else:
            # Fall back to basic validation
            print("ℹ️  No validation rules specified. Use --rules or --rule-set for advanced validation.")
            print("ℹ️  Running basic structural validation only...")
            
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

Usage: edi <command> [arguments]

Commands:
  convert <input_file> [--to json] [--out output_file] [--schema x12-835-5010|x12-837p-5010]
    Convert an EDI file to another format (JSON)
    
  validate <input_file> [--schema x12-835-5010|x12-837p-5010] [--verbose] [--rules file.yml] [--rule-set <rule_set>]
    Validate an EDI file against a schema with custom validation rules
    
  inspect <input_file> [--segments NM1,CLP]
    Inspect an EDI file and extract specific segments or show structure
    
  help
    Show this help message

Examples:
  edi convert sample-835.edi --to json --schema 835
  edi convert sample-837.edi --to json --schema 837p
  edi validate sample-835.edi --rule-set basic --verbose
  edi validate sample-837.edi --schema 837p --rule-set basic --verbose
  edi validate sample-835.edi --rule-set hipaa --verbose
  edi validate sample.edi --rules custom-rules.yml
  edi inspect sample.edi --segments BPR,CLP

Supported Transaction Sets:
  835: Healthcare Claim Payment/Advice (ERA)
  837P: Professional Healthcare Claims

Rule Sets by Transaction:
  835: basic, business, hipaa, hipaa-advanced, enhanced-business, comprehensive, all
  837P: basic, business, all
      
Advanced validation options:
  enhanced-business: Advanced business rule engine with field-level validation (835 only)
  comprehensive: All YAML rules + enhanced business engine (835 only)
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
        rules_file = None
        rule_set = None
        
        # Parse additional arguments
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--schema" and i + 1 < len(sys.argv):
                schema = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--verbose" or sys.argv[i] == "-v":
                verbose = True
                i += 1
            elif sys.argv[i] == "--rules" and i + 1 < len(sys.argv):
                rules_file = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--rule-set" and i + 1 < len(sys.argv):
                rule_set = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        return validate_command(input_file, schema, verbose, rules_file, rule_set)
    
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

def app():
    """Entry point for the edi command."""
    return main()

if __name__ == "__main__":
    sys.exit(app())