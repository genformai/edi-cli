"""
Shared pytest fixtures for EDI test suite.
"""

import pytest
from packages.core.parser import EdiParser


@pytest.fixture
def schema_835_path():
    """Path to the EDI 835 schema file."""
    return "packages/core/schemas/x12/835.json"


@pytest.fixture
def schema_270_path():
    """Path to the EDI 270 schema file."""
    return "packages/core/schemas/x12/270.json"


@pytest.fixture
def schema_276_path():
    """Path to the EDI 276 schema file."""
    return "packages/core/schemas/x12/276.json"


@pytest.fixture
def schema_837p_path():
    """Path to the EDI 837P schema file."""
    return "packages/core/schemas/x12/837p.json"


@pytest.fixture
def base_isa_segment():
    """Base ISA segment for EDI envelope."""
    return (
        "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
        "*241226*1430*^*00501*000012345*0*P*:~"
    )


@pytest.fixture
def base_gs_segment():
    """Base GS segment for functional group."""
    return "GS*HP*SENDER*RECEIVER*20241226*1430*000006789*X*005010X221A1~"


@pytest.fixture
def base_envelope_trailer():
    """Base envelope trailer segments."""
    return (
        "GE*1*000006789~"
        "IEA*1*000012345~"
    )


@pytest.fixture
def base_835_headers():
    """Complete base headers for 835 transactions."""
    return (
        "ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       "
        "*241226*1430*^*00501*000012345*0*P*:~"
        "GS*HP*SENDER*RECEIVER*20241226*1430*000006789*X*005010X221A1~"
        "ST*835*0001~"
        "BPR*I*1000.00*C*ACH*CCP*01*123456789*DA*987654321*9876543210*20241226~"
        "TRN*1*12345*1234567890~"
        "N1*PR*ACME INSURANCE COMPANY~"
        "N1*PE*PROVIDER CLINIC*XX*1234567890~"
        "REF*TJ*1234567890~"
    )


@pytest.fixture
def base_835_trailer():
    """Base trailer for 835 transactions."""
    return (
        "SE*{{segment_count}}*0001~"
        "GE*1*000006789~"
        "IEA*1*000012345~"
    )


@pytest.fixture
def sample_claim_clp():
    """Sample CLP (Claim Payment Information) segment."""
    return "CLP*CLAIM001*1*500.00*400.00*100.00*MC*PAYER123*11~"


@pytest.fixture
def sample_service_svc():
    """Sample SVC (Service Line) segment."""
    return "SVC*HC:99213*100.00*80.00*UN*1~"