#!/usr/bin/env python3
"""
QA Test Suite for 835 Parser Edge Cases

Tests the 835 parser against challenging edge cases including:
- Multiple CAS codes and PLB adjustments
- Multiple ST/SE transactions per GS
- Control number validation
- Segment count validation
- Financial balance validation
"""

import json
from decimal import Decimal
from typing import Dict, List, Any, Optional
from packages.core.transactions.t835.parser import Parser835

def parse_edi_string(edi_content: str) -> List[List[str]]:
    """Convert EDI string to segments list for parser."""
    # Replace ~ with newlines for segment separation
    lines = edi_content.replace('~', '\n').strip().split('\n')
    segments = []
    
    for line in lines:
        if line.strip():
            # Split by * for elements, handle composite elements
            elements = line.split('*')
            segments.append(elements)
    
    return segments

def calculate_balance_delta(bpr_amount: float, claims: List[Dict], plb_adjustments: List[Dict]) -> float:
    """Calculate the balance delta for financial validation."""
    claims_paid = sum(claim.get('paid_amount', 0) for claim in claims)
    plb_total = sum(plb.get('amount', 0) for plb in plb_adjustments)
    expected_amount = claims_paid + plb_total
    return bpr_amount - expected_amount

def validate_control_numbers(segments: List[List[str]]) -> List[Dict[str, str]]:
    """Validate control number matches between envelope segments."""
    errors = []
    
    # Find control segments
    isa_seg = next((seg for seg in segments if seg[0] == 'ISA'), None)
    iea_seg = next((seg for seg in segments if seg[0] == 'IEA'), None)
    gs_seg = next((seg for seg in segments if seg[0] == 'GS'), None)
    ge_seg = next((seg for seg in segments if seg[0] == 'GE'), None)
    st_seg = next((seg for seg in segments if seg[0] == 'ST'), None)
    se_seg = next((seg for seg in segments if seg[0] == 'SE'), None)
    
    # ISA13 vs IEA02
    if isa_seg and iea_seg:
        isa_control = isa_seg[13] if len(isa_seg) > 13 else ""
        iea_control = iea_seg[2] if len(iea_seg) > 2 else ""
        if isa_control != iea_control:
            errors.append({
                "code": "ISA13_IEA02_MISMATCH",
                "message": f"ISA13 ({isa_control}) != IEA02 ({iea_control})",
                "path": "$.isa"
            })
    
    # GS06 vs GE02
    if gs_seg and ge_seg:
        gs_control = gs_seg[6] if len(gs_seg) > 6 else ""
        ge_control = ge_seg[2] if len(ge_seg) > 2 else ""
        if gs_control != ge_control:
            errors.append({
                "code": "GS06_GE02_MISMATCH", 
                "message": f"GS06 ({gs_control}) != GE02 ({ge_control})",
                "path": "$.groups[0]"
            })
    
    # ST02 vs SE02
    if st_seg and se_seg:
        st_control = st_seg[2] if len(st_seg) > 2 else ""
        se_control = se_seg[2] if len(se_seg) > 2 else ""
        if st_control != se_control:
            errors.append({
                "code": "ST02_SE02_MISMATCH",
                "message": f"ST02 ({st_control}) != SE02 ({se_control})",
                "path": "$.groups[0].transactions[0]"
            })
    
    return errors

def validate_segment_count(segments: List[List[str]]) -> List[Dict[str, str]]:
    """Validate SE01 segment count matches actual count."""
    errors = []
    
    # Find ST and SE segments
    st_indices = [i for i, seg in enumerate(segments) if seg[0] == 'ST']
    se_indices = [i for i, seg in enumerate(segments) if seg[0] == 'SE']
    
    for st_idx, se_idx in zip(st_indices, se_indices):
        se_seg = segments[se_idx]
        if len(se_seg) > 1:
            try:
                reported_count = int(se_seg[1])
                actual_count = se_idx - st_idx + 1  # Include ST and SE
                
                if reported_count != actual_count:
                    errors.append({
                        "code": "SE01_COUNT_INVALID",
                        "message": f"Reported {reported_count}, actual {actual_count}",
                        "path": "$.groups[0].transactions[0]"
                    })
            except ValueError:
                errors.append({
                    "code": "SE01_INVALID_FORMAT",
                    "message": f"SE01 is not a valid number: {se_seg[1]}",
                    "path": "$.groups[0].transactions[0]"
                })
    
    return errors

def extract_transaction_data(parsed_result, segments: List[List[str]]) -> Dict[str, Any]:
    """Extract and normalize transaction data from parser result."""
    if not parsed_result or not parsed_result.interchanges:
        return {}
    
    interchange = parsed_result.interchanges[0]
    result = {
        "isa": {
            "control_number": interchange.header.get("control_number", "")
        },
        "groups": []
    }
    
    for fg in interchange.functional_groups:
        group_data = {
            "control_number": fg.header.get("control_number", ""),
            "transactions": []
        }
        
        for transaction in fg.transactions:
            if hasattr(transaction, 'transaction_data') and transaction.transaction_data:
                t835 = transaction.transaction_data
                
                # Extract BPR info
                bpr_data = {}
                if hasattr(t835, 'financial_information') and t835.financial_information:
                    fi = t835.financial_information
                    bpr_data = {
                        "amount": fi.total_paid,
                        "method": fi.payment_method or "I",
                        "date": fi.payment_date
                    }
                
                # Extract TRN info
                trn_data = {}
                if hasattr(t835, 'reference_numbers') and t835.reference_numbers:
                    for ref in t835.reference_numbers:
                        if ref.get('type') == 'trace_number':
                            trn_data = {
                                "trace_type": "1",
                                "reference": ref.get('value', '')
                            }
                            break
                
                # Extract payer/payee
                payer_data = {}
                if hasattr(t835, 'payer') and t835.payer:
                    payer_data = {"name": t835.payer.name}
                
                payee_data = {}
                if hasattr(t835, 'payee') and t835.payee:
                    payee_data = {
                        "name": t835.payee.name,
                        "npi": t835.payee.npi
                    }
                
                # Extract claims
                claims_data = []
                if hasattr(t835, 'claims') and t835.claims:
                    for claim in t835.claims:
                        claim_data = {
                            "claim_id": claim.claim_id,
                            "status_code": str(claim.status_code),
                            "charge_amount": claim.total_charge,
                            "paid_amount": claim.total_paid,
                            "patient_responsibility": claim.patient_responsibility
                        }
                        
                        if hasattr(claim, 'payer_control_number') and claim.payer_control_number:
                            claim_data["patient_account_number"] = claim.payer_control_number
                        
                        # Extract adjustments
                        if hasattr(claim, 'adjustments') and claim.adjustments:
                            adjustments = []
                            for adj in claim.adjustments:
                                adjustments.append({
                                    "group": adj.group_code,
                                    "reason": adj.reason_code,
                                    "amount": adj.amount
                                })
                            claim_data["adjustments"] = adjustments
                        
                        # Extract services
                        if hasattr(claim, 'services') and claim.services:
                            services = []
                            for svc in claim.services:
                                service_data = {
                                    "charge": svc.charge_amount,
                                    "paid": svc.paid_amount
                                }
                                
                                # Parse composite procedure code
                                if svc.service_code:
                                    parts = svc.service_code.split(':')
                                    if len(parts) >= 2:
                                        service_data["procedure_qualifier"] = parts[0]
                                        service_data["procedure_code"] = parts[1]
                                        if len(parts) > 2:
                                            service_data["modifiers"] = parts[2:]
                                    else:
                                        service_data["procedure_code"] = svc.service_code
                                
                                if svc.service_date:
                                    service_data["dtm_472"] = svc.service_date
                                
                                services.append(service_data)
                            claim_data["services"] = services
                        
                        claims_data.append(claim_data)
                
                # Calculate segment count
                st_indices = [i for i, seg in enumerate(segments) if seg[0] == 'ST']
                se_indices = [i for i, seg in enumerate(segments) if seg[0] == 'SE']
                
                segment_count_data = {}
                if st_indices and se_indices:
                    se_seg = segments[se_indices[0]]
                    if len(se_seg) > 1:
                        try:
                            reported = int(se_seg[1])
                            actual = se_indices[0] - st_indices[0] + 1
                            segment_count_data = {
                                "reported": reported,
                                "actual": actual
                            }
                        except ValueError:
                            pass
                
                # Build transaction data
                transaction_data = {
                    "st_control_number": transaction.header.get("control_number", "")
                }
                
                if bpr_data:
                    transaction_data["bpr"] = bpr_data
                if trn_data:
                    transaction_data["trn"] = trn_data
                if payer_data:
                    transaction_data["payer"] = payer_data
                if payee_data:
                    transaction_data["payee"] = payee_data
                if claims_data:
                    transaction_data["claims"] = claims_data
                if segment_count_data:
                    transaction_data["segment_count"] = segment_count_data
                
                # Calculate balance
                if bpr_data and claims_data:
                    bpr_amount = bpr_data.get("amount", 0)
                    claims_paid = sum(claim.get("paid_amount", 0) for claim in claims_data)
                    plb_total = 0  # PLB not implemented yet in our parser
                    
                    balance_delta = bpr_amount - (claims_paid + plb_total)
                    transaction_data["out_of_balance"] = abs(balance_delta) > 0.01
                    if transaction_data["out_of_balance"]:
                        transaction_data["balance_delta"] = balance_delta
                else:
                    transaction_data["out_of_balance"] = False
                
                group_data["transactions"].append(transaction_data)
        
        result["groups"].append(group_data)
    
    return result

def run_test_case(test_id: str, edi_content: str, expected_json: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single test case and return results."""
    print(f"\n=== Running {test_id} ===")
    
    try:
        # Parse EDI content
        segments = parse_edi_string(edi_content)
        
        # Validate control numbers and segment counts
        validation_errors = []
        validation_errors.extend(validate_control_numbers(segments))
        validation_errors.extend(validate_segment_count(segments))
        
        # Run parser
        parser = Parser835(segments)
        parsed_result = parser.parse()
        
        # Extract normalized data
        normalized_data = extract_transaction_data(parsed_result, segments)
        
        # Determine if test passed
        has_validation_errors = len(validation_errors) > 0
        has_balance_issues = False
        
        if normalized_data and "groups" in normalized_data:
            for group in normalized_data["groups"]:
                for transaction in group.get("transactions", []):
                    if transaction.get("out_of_balance", False):
                        has_balance_issues = True
        
        test_passed = not has_validation_errors and not has_balance_issues
        
        result = {
            "id": test_id,
            "passed": test_passed
        }
        
        if validation_errors:
            result["errors"] = validation_errors
        
        if normalized_data:
            result["parsed"] = normalized_data
        
        # Add warnings for balance issues
        if has_balance_issues and not has_validation_errors:
            result["warnings"] = ["Financial balance discrepancy detected"]
        
        return result
        
    except Exception as e:
        return {
            "id": test_id,
            "passed": False,
            "errors": [{
                "code": "PARSER_EXCEPTION",
                "message": f"Parser failed with exception: {str(e)}",
                "path": "$"
            }]
        }

def main():
    """Run all test cases."""
    
    # Test Case 01
    tc01_edi = """ISA*00*          *00*          *ZZ*PAYERID        *ZZ*PROVIDERID     *240115*1200*^*00501*000000001*0*P*>~
GS*HP*PAYER*PROVIDER*20240115*120000*1*X*005010X221A1~
ST*835*0001~
BPR*I*150.00*C*ACH*CCP*01*111111111*DA*123456*999999999**01*222222222*DA*987654*20240115~
TRN*1*12345*999999999~
DTM*405*20240114~
N1*PR*TEST PAYER~
N1*PE*TEST PROVIDER*XX*1234567890~
CLP*A1*1*200.00*150.00*50.00*12*ACCT123*11*1~
CAS*PR*1*30.00*OA*94*20.00~
SVC*HC:99213:25*200.00*150.00~
DTM*472*20240110~
AMT*B6*150.00~
AMT*AU*200.00~
PLB*1234567890*2024*WO*123456*-25.00*FB*987654*10.00~
SE*14*0001~
GE*1*1~
IEA*1*000000001~"""
    
    # Test Case 02
    tc02_edi = """ISA*00*          *00*          *ZZ*PAYERID        *ZZ*PROVIDERID     *240201*1200*^*00501*000000002*0*P*>~
GS*HP*PAY*PROV*20240201*120000*2*X*005010X221A1~
ST*835*0001~
BPR*I*50.00*C*ACH*CCP*01*111111111*DA*123456*999999999**01*222222222*DA*987654*20240201~
TRN*1*111*999999999~
N1*PR*PAYER A~
N1*PE*PROVIDER A*XX*1112223333~
CLP*CLM1*1*75.00*50.00*25.00*12*ACCT1*11*1~
SE*8*0001~
ST*835*0002~
BPR*I*25.00*C*ACH*CCP*01*111111111*DA*123456*999999999**01*222222222*DA*987654*20240201~
TRN*1*222*999999999~
N1*PR*PAYER A~
N1*PE*PROVIDER B*XX*4445556666~
CLP*CLM2*2*100.00*0.00*100.00*12*ACCT2*11*1~
CAS*PR*1*100.00~
SE*10*0002~
GE*2*2~
IEA*1*000000002~"""
    
    # Test Case 03
    tc03_edi = """ISA*00*          *00*          *ZZ*PAYERID        *ZZ*PROVIDERID     *240215*1200*^*00501*000000003*0*P*>~
GS*HP*PAY*PROV*20240215*120000*3*X*005010X221A1~
ST*835*ABC123~
BPR*I*10.00*C*ACH*CCP*01*111111111*DA*123456*999999999**01*222222222*DA*987654*20240215~
SE*10*XYZ999~
GE*1*999999~
IEA*1*000000099~"""
    
    # Test Case 04
    tc04_edi = """ISA*00*          *00*          *ZZ*PAYERID        *ZZ*PROVIDERID     *240216*1200*^*00501*000000004*0*P*>~
GS*HP*PAY*PROV*20240216*120000*4*X*005010X221A1~
ST*835*0003~
BPR*I*5.00*C*ACH*CCP*01*111111111*DA*123456*999999999**01*222222222*DA*987654*20240216~
TRN*1*333*999999999~
N1*PR*PAYER X~
N1*PE*PROVIDER X*XX*9998887777~
CLP*Z1*1*5.00*5.00*0.00*12*ACCTX*11*1~
SE*99*0003~
GE*1*4~
IEA*1*000000004~"""
    
    # Test Case 05
    tc05_edi = """ISA*00*          *00*          *ZZ*PAYERID        *ZZ*PROVIDERID     *240217*1200*^*00501*000000005*0*P*>~
GS*HP*PAY*PROV*20240217*120000*5*X*005010X221A1~
ST*835*0005~
BPR*I*100.00*C*ACH*CCP*01*111111111*DA*123456*999999999**01*222222222*DA*987654*20240217~
TRN*1*444*999999999~
N1*PR*PAYER Y~
N1*PE*PROVIDER Y*XX*1122334455~
CLP*Q1*1*80.00*80.00*0.00*12*ACC1*11*1~
PLB*1122334455*2024*WO*1*-5.00~
SE*11*0005~
GE*1*5~
IEA*1*000000005~"""
    
    # Run all test cases
    test_cases = [
        ("TC-01", tc01_edi, {}),
        ("TC-02", tc02_edi, {}),
        ("TC-03", tc03_edi, {}),
        ("TC-04", tc04_edi, {}),
        ("TC-05", tc05_edi, {})
    ]
    
    results = []
    for test_id, edi_content, expected in test_cases:
        result = run_test_case(test_id, edi_content, expected)
        results.append(result)
        
        print(f"Result: {result['id']} - {'PASSED' if result['passed'] else 'FAILED'}")
        if 'errors' in result:
            print(f"  Errors: {len(result['errors'])}")
            for error in result['errors']:
                print(f"    - {error['code']}: {error['message']}")
        if 'warnings' in result:
            print(f"  Warnings: {result['warnings']}")
    
    # Output results as JSON
    print(f"\n=== FINAL RESULTS ===")
    print(json.dumps(results, indent=2))
    
    # Summary table
    print(f"\n=== SUMMARY TABLE ===")
    print("id      passed  errors_count  out_of_balance  notes")
    print("------  ------  ------------  --------------  --------------------")
    
    for result in results:
        test_id = result['id']
        passed = result['passed']
        error_count = len(result.get('errors', []))
        
        # Check for balance issues
        out_of_balance = False
        notes = ""
        
        if 'parsed' in result and 'groups' in result['parsed']:
            for group in result['parsed']['groups']:
                for transaction in group.get('transactions', []):
                    if transaction.get('out_of_balance', False):
                        out_of_balance = True
                        delta = transaction.get('balance_delta', 0)
                        notes = f"delta = {delta:.2f}"
        
        if error_count > 0:
            if any('MISMATCH' in err.get('code', '') for err in result.get('errors', [])):
                notes = "control numbers mismatch"
            elif any('COUNT' in err.get('code', '') for err in result.get('errors', [])):
                notes = "SE01 bad"
        
        out_of_balance_str = "true" if out_of_balance else "false" if passed else "n/a"
        
        print(f"{test_id:<6}  {str(passed).lower():<6}  {error_count:<12}  {out_of_balance_str:<14}  {notes}")

if __name__ == "__main__":
    main()