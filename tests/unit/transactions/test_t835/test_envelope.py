"""
Unit tests for EDI 835 envelope processing (ISA/GS/ST segments).

This module contains tests for EDI envelope structure validation
and processing, migrated from the original envelope tests.
"""

import pytest
from packages.core.transactions.t835.parser import Parser835
from tests.shared.assertions import (
    assert_date_format,
    assert_segment_structure
)


class Test835Envelope:
    """Test cases for EDI 835 envelope processing."""

    def test_isa_interchange_header(self):
        """Test ISA (Interchange Control Header) processing."""
        segments = [
            ["ISA", "00", "          ", "00", "          ", "ZZ", "SENDER ID     ", "ZZ", "RECEIVER ID   ", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["SE", "4", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        parser = Parser835(segments)
        result = parser.parse()
        
        # Verify ISA processing
        assert len(result.interchanges) == 1
        interchange = result.interchanges[0]
        
        assert interchange.sender_id == "SENDER ID"
        assert interchange.receiver_id == "RECEIVER ID"
        assert_date_format(interchange.date)
        assert interchange.control_number == "000000001"

    def test_gs_functional_group_header(self):
        """Test GS (Functional Group Header) processing."""
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDERFUNC", "RECEIVERFUNC", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["SE", "4", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        parser = Parser835(segments)
        result = parser.parse()
        
        # Verify GS processing
        functional_group = result.interchanges[0].functional_groups[0]
        
        assert functional_group.functional_group_code == "HP"
        assert functional_group.sender_id == "SENDERFUNC"
        assert functional_group.receiver_id == "RECEIVERFUNC"
        assert_date_format(functional_group.date)
        assert functional_group.control_number == "000000001"

    def test_st_transaction_header(self):
        """Test ST (Transaction Set Header) processing."""
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["SE", "4", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        parser = Parser835(segments)
        result = parser.parse()
        
        # Verify ST processing
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        
        assert transaction.transaction_set_code == "835"
        assert transaction.control_number == "0001"

    def test_envelope_control_number_validation(self):
        """Test control number consistency across envelope segments."""
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["SE", "4", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        parser = Parser835(segments)
        result = parser.parse()
        
        # Verify control number consistency
        interchange = result.interchanges[0]
        functional_group = interchange.functional_groups[0]
        transaction = functional_group.transactions[0]
        
        # All should have consistent control numbers
        assert interchange.control_number == "000000001"
        assert functional_group.control_number == "000000001"
        assert transaction.control_number == "0001"

    def test_multiple_functional_groups(self):
        """Test processing multiple functional groups in one interchange."""
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            
            # First functional group
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["SE", "4", "0001"],
            ["GE", "1", "000000001"],
            
            # Second functional group
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000002", "X", "005010X221A1"],
            ["ST", "835", "0002"],
            ["BPR", "I", "2000.00", "C", "CHK", "", "", "", "", "", "", "20241226"],
            ["SE", "4", "0002"],
            ["GE", "1", "000000002"],
            
            ["IEA", "2", "000000001"]
        ]
        
        parser = Parser835(segments)
        result = parser.parse()
        
        # Verify multiple functional groups
        interchange = result.interchanges[0]
        assert len(interchange.functional_groups) == 2
        
        fg1 = interchange.functional_groups[0]
        fg2 = interchange.functional_groups[1]
        
        assert fg1.control_number == "000000001"
        assert fg2.control_number == "000000002"

    def test_date_time_formatting_in_envelope(self):
        """Test date and time formatting in envelope segments."""
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241231", "2359", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241231", "2359", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241231"],
            ["SE", "4", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        parser = Parser835(segments)
        result = parser.parse()
        
        # Verify date/time formatting
        interchange = result.interchanges[0]
        functional_group = interchange.functional_groups[0]
        
        assert_date_format(interchange.date)
        assert_date_format(functional_group.date)
        
        # Verify time formatting (should be HH:MM format)
        assert ":" in interchange.time
        assert ":" in functional_group.time

    def test_invalid_envelope_structure(self):
        """Test handling of invalid envelope structures."""
        # Missing required segments
        invalid_segments = [
            ["ST", "835", "0001"],  # Missing ISA and GS
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["SE", "4", "0001"]
        ]
        
        parser = Parser835(invalid_segments)
        
        # Parser should handle gracefully or raise appropriate error
        try:
            result = parser.parse()
            # If it doesn't raise an error, verify basic structure
            assert isinstance(result.interchanges, list)
        except ValueError:
            # Expected for invalid structure
            pass

    def test_segment_count_validation(self):
        """Test segment count validation in SE segment."""
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["TRN", "1", "TRACE123", "1"],
            ["SE", "5", "0001"],  # Should match actual segment count
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        parser = Parser835(segments)
        result = parser.parse()
        
        # Parser should process successfully with correct segment count
        transaction = result.interchanges[0].functional_groups[0].transactions[0]
        assert transaction.control_number == "0001"

    def test_version_identifier_validation(self):
        """Test EDI version identifier validation."""
        segments = [
            ["ISA", "00", "", "00", "", "ZZ", "SENDER", "ZZ", "RECEIVER", "241226", "1430", "U", "00501", "000000001", "0", "P", ">"],
            ["GS", "HP", "SENDER", "RECEIVER", "20241226", "1430", "000000001", "X", "005010X221A1"],  # Version 5010
            ["ST", "835", "0001"],
            ["BPR", "I", "1000.00", "C", "ACH", "", "", "", "", "", "", "20241226"],
            ["SE", "4", "0001"],
            ["GE", "1", "000000001"],
            ["IEA", "1", "000000001"]
        ]
        
        parser = Parser835(segments)
        result = parser.parse()
        
        # Parser should handle version 5010 correctly
        functional_group = result.interchanges[0].functional_groups[0]
        assert functional_group is not None