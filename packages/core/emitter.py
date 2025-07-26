import json
from .ast import EdiRoot

def convert_floats_to_ints(obj):
    """Recursively convert float values that are whole numbers to integers."""
    if isinstance(obj, dict):
        return {k: convert_floats_to_ints(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_ints(item) for item in obj]
    elif isinstance(obj, float) and obj.is_integer():
        return int(obj)
    else:
        return obj

class EdiEmitter:
    def __init__(self, edi_root: EdiRoot):
        self.edi_root = edi_root

    def to_json(self, pretty: bool = False) -> str:
        data = self.edi_root.to_dict()
        # Convert floats that are whole numbers to integers
        data = convert_floats_to_ints(data)
        json_output = json.dumps(data, indent=4 if pretty else None)
        # Add trailing newline for pretty output to match expected format
        if pretty:
            json_output += '\n'
        return json_output

    def to_csv(self) -> str:
        # This is a placeholder for a more robust CSV implementation
        return "Not implemented yet"