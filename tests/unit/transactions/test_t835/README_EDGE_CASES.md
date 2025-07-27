# 835 Parser Edge Case Tests

## Overview

This test suite (`test_835_edge_cases.py`) contains challenging edge cases for the 835 parser based on comprehensive QA analysis. These tests ensure the parser handles complex real-world scenarios correctly.

## Test Cases Included

### TC-01: Multiple CAS codes, PLB adjustments, composite procedure codes ✅
**File:** `test_tc01_multiple_cas_plb_composite_codes()`
**Purpose:** Tests complex transaction with multiple adjustment types and composite codes
**Key Features:**
- Composite procedure code parsing (`HC:99213:25`)
- Multiple CAS adjustment groups (PR, OA)
- PLB provider-level adjustments
- Complete financial reconciliation

**Expected Behavior:**
- Parses composite codes with qualifier, code, and modifiers
- Extracts multiple adjustment reasons from single CAS segment
- Maintains financial integrity across all segments

### TC-02: Multiple ST/SE transactions per GS ✅
**File:** `test_tc02_multiple_transactions_per_group()`
**Purpose:** Validates parser handles multiple transactions within single functional group
**Key Features:**
- Two separate 835 transactions in one GS envelope
- Different payers/payees per transaction
- Independent financial balancing per transaction

**Expected Behavior:**
- Processes each transaction independently
- Maintains separate payer/payee contexts
- Correctly handles different claim statuses

### TC-03: Control number validation ✅
**File:** `test_tc03_control_number_validation()`
**Purpose:** Tests parser resilience with mismatched control numbers
**Key Features:**
- ISA13 ≠ IEA02 mismatch
- GS06 ≠ GE02 mismatch  
- ST02 ≠ SE02 mismatch
- Incorrect SE01 segment count

**Expected Behavior:**
- Parser continues processing despite control errors
- Can be used with validation framework to detect issues
- Graceful degradation when envelope integrity compromised

### TC-04: Segment count validation ✅
**File:** `test_tc04_segment_count_validation()`
**Purpose:** Tests handling of incorrect SE01 segment counts
**Key Features:**
- SE01 reports 99 segments, actual count is 7
- Transaction data remains intact

**Expected Behavior:**
- Parser ignores incorrect count and processes transaction
- Transaction content fully extracted despite count error
- Can detect discrepancy programmatically

### TC-05: Financial balance validation ✅
**File:** `test_tc05_financial_balance_validation()`
**Purpose:** Tests detection of out-of-balance payments
**Key Features:**
- BPR payment amount: $100.00
- Claims paid: $80.00
- PLB adjustment: -$5.00 (not yet implemented)
- Expected balance: $75.00 vs actual $100.00

**Expected Behavior:**
- Parser extracts all financial data correctly
- Balance discrepancy detectable programmatically
- Documents current PLB implementation gap

## Parametrized Tests

### Transaction Multiplicity ✅
**File:** `test_transaction_multiplicity()`
**Purpose:** Validates single vs multiple transaction scenarios
**Parameters:**
- `single_transaction`: 1 transaction expected
- `multiple_transactions`: 2 transactions expected

### Composite Procedure Code Variations ✅
**File:** `test_composite_procedure_code_variations()`
**Purpose:** Tests various procedure code formats
**Test Cases:**
- `HC:99213` (basic qualifier:code)
- `HC:99213:25` (with modifier)
- `HC:99213:25:59` (multiple modifiers)
- `99213` (no qualifier)

## Parser Capabilities Demonstrated

### ✅ Working Features:
1. **Composite Code Parsing:** Successfully handles `HC:99213:25` format
2. **Multiple Transactions:** Processes multiple ST/SE pairs in single GS
3. **CAS Adjustments:** Extracts adjustment groups and reason codes
4. **Financial Data:** Accurate BPR, CLP, and service amount extraction
5. **Error Recovery:** Continues parsing despite structural errors
6. **Control Validation:** Can detect envelope integrity issues

### ❌ Known Limitations:
1. **PLB Support:** Provider-level adjustments not implemented
2. **Multiple CAS Groups:** Only first adjustment group captured per segment
3. **Enhanced Error Handling:** 835 parser doesn't support EnhancedParser interface
4. **NPI Extraction:** REF segment NPI values not properly extracted

## Usage in CI/CD

These tests serve as:
- **Regression Detection:** Ensure parser changes don't break edge cases
- **Feature Validation:** Verify new features work with complex scenarios
- **Documentation:** Demonstrate parser capabilities and limitations
- **QA Reference:** Baseline for additional edge case discovery

## Running the Tests

```bash
# Run all edge case tests
python -m pytest tests/core/test_835_edge_cases.py -v

# Run specific test
python -m pytest tests/core/test_835_edge_cases.py::Test835EdgeCases::test_tc01_multiple_cas_plb_composite_codes -v

# Run with coverage
python -m pytest tests/core/test_835_edge_cases.py --cov=packages.core.transactions.t835
```

## Future Enhancements

1. **PLB Implementation:** Add provider-level adjustment support
2. **Enhanced Error Integration:** Convert to use EnhancedParser interface  
3. **Validation Framework:** Integrate with standardized validation rules
4. **Performance Testing:** Add timing benchmarks for complex transactions
5. **Fuzzing Support:** Generate randomized edge cases automatically

These tests provide comprehensive coverage of real-world 835 parsing challenges and serve as a foundation for continued parser improvement.