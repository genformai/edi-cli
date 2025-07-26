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
        """Convert EDI data to CSV format focusing on claims data."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # CSV headers for claims data
        headers = [
            'interchange_sender', 'interchange_receiver', 'functional_group_sender',
            'transaction_control_number', 'total_paid', 'payment_method', 'payment_date',
            'payer_name', 'payee_name', 'payee_npi', 'claim_id', 'status_code',
            'total_charge', 'claim_total_paid', 'patient_responsibility', 
            'payer_control_number', 'service_code', 'service_charge', 'service_paid',
            'service_date', 'adjustment_group', 'adjustment_reason', 'adjustment_amount'
        ]
        writer.writerow(headers)
        
        for interchange in self.edi_root.interchanges:
            for functional_group in interchange.functional_groups:
                for transaction in functional_group.transactions:
                    # Get common transaction data
                    base_data = [
                        interchange.header['sender_id'],
                        interchange.header['receiver_id'],
                        functional_group.header['sender_id'],
                        transaction.header['control_number'],
                        transaction.financial_information.total_paid if transaction.financial_information else '',
                        transaction.financial_information.payment_method if transaction.financial_information else '',
                        transaction.financial_information.payment_date if transaction.financial_information else '',
                        transaction.payer.name if transaction.payer else '',
                        transaction.payee.name if transaction.payee else '',
                        transaction.payee.npi if transaction.payee else '',
                    ]
                    
                    if not transaction.claims:
                        # Write transaction-level data if no claims
                        row = base_data + [''] * (len(headers) - len(base_data))
                        writer.writerow(row)
                    else:
                        for claim in transaction.claims:
                            claim_data = base_data + [
                                claim.claim_id,
                                claim.status_code,
                                claim.total_charge,
                                claim.total_paid,
                                claim.patient_responsibility,
                                claim.payer_control_number,
                            ]
                            
                            if not claim.services:
                                # Write claim-level data if no services
                                row = claim_data + [''] * (len(headers) - len(claim_data))
                                writer.writerow(row)
                            else:
                                for service in claim.services:
                                    service_data = claim_data + [
                                        service.service_code,
                                        service.charge_amount,
                                        service.paid_amount,
                                        service.service_date,
                                    ]
                                    
                                    if not claim.adjustments:
                                        # Write service-level data if no adjustments
                                        row = service_data + [''] * (len(headers) - len(service_data))
                                        writer.writerow(row)
                                    else:
                                        for adjustment in claim.adjustments:
                                            adjustment_data = service_data + [
                                                adjustment.group_code,
                                                adjustment.reason_code,
                                                adjustment.amount,
                                            ]
                                            writer.writerow(adjustment_data)
        
        return output.getvalue()