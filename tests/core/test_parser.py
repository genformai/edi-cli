import pytest
from packages.core.parser import EdiParser
from packages.core.emitter import EdiEmitter

@pytest.fixture
def edi_835_file():
    return "tests/fixtures/835.edi"

@pytest.fixture
def edi_835_json_file():
    return "tests/fixtures/835.json"

def test_parse_835_edi_file(edi_835_file, edi_835_json_file):
    parser = EdiParser(edi_string=open(edi_835_file).read(), schema_path="packages/core/schemas/x12/835.json")
    edi_root = parser.parse()
    emitter = EdiEmitter(edi_root)
    json_output = emitter.to_json(pretty=True)

    with open(edi_835_json_file, 'r') as f:
        expected_json = f.read()

    assert json_output == expected_json
