# edi-cli

A modern, open-source EDI toolkit.

**edi-cli** is a developer-first toolkit for parsing, validating, and transforming Electronic Data Interchange (EDI) files. It provides a fast, well-tested core library and a user-friendly command-line interface (CLI) to streamline working with complex EDI formats.

📖 **[Read "Why Open Source EDI?" →](why-open-source-edi.md)**

## Getting Started

### Installation

```bash
pip install edi-cli
```

### Quick Examples

**Parse an 835 Healthcare Payment file:**

```python
from packages.core.transactions.t835.parser import Parser835

# Read and parse
with open('sample-835.edi', 'r') as f:
    edi_content = f.read()

parser = Parser835()
result = parser.parse(edi_content)

# Access data
t835 = result.interchanges[0].functional_groups[0].transactions[0].transaction_data
print(f"Payer: {t835.payer.name}")
print(f"Total Paid: ${t835.financial_information.total_paid}")
```

**CLI Usage:**

```bash
# Convert EDI to JSON
edi convert sample-835.edi --to json --schema 835

# Validate with comprehensive rules
edi validate sample-835.edi --rule-set comprehensive --verbose

# Inspect EDI structure
edi inspect sample.edi --segments BPR,CLP,SV1
```

## What Works Now (v0.3.0)

### ✅ **Core Library - Production Ready**

**EDI 835 Healthcare Claim Payment/Advice** - Fully implemented with comprehensive parser:

```python
from packages.core.transactions.t835.parser import Parser835

# Parse from segments or EDI content
parser = Parser835(segments)  # or Parser835()
result = parser.parse(edi_content)

# Access parsed data
t835 = result.interchanges[0].functional_groups[0].transactions[0].transaction_data
print(f"Payer: {t835.payer.name}")
print(f"Total Claims: {len(t835.claims)}")
print(f"Total Paid: ${t835.financial_information.total_paid}")
```

**EDI 837P Professional Claims** - Complete professional claims processing:

```python
from packages.core.transactions.t837p.parser import Parser837P

parser = Parser837P(segments)
result = parser.parse()

# Access parsed data
t837p = result.interchanges[0].functional_groups[0].transactions[0].transaction_data
print(f"Submitter: {t837p.submitter.name}")
print(f"Claim ID: {t837p.claim.claim_id}")
print(f"Total Charge: ${t837p.claim.total_charge}")
print(f"Service Lines: {len(t837p.service_lines)}")
```

**Key Features:**
- ✅ **835 Features**: Comprehensive segment support, financial balancing, PLB adjustments, 100% test coverage
- ✅ **837P Features**: Complete professional claims parsing, service lines, diagnoses, provider information
- ✅ **Advanced Validation**: YAML DSL framework, HIPAA compliance rules, business rule engine
- ✅ **Field-Level Validation**: Enhanced business rule engine with detailed error reporting
- ✅ **Production CLI**: Full command-line interface with convert, validate, inspect commands
- ✅ **Multi-Transaction Support**: Schema-aware processing for both 835 and 837P transactions

### ✅ **CLI - Production Ready**

The command-line interface is fully operational with comprehensive EDI processing capabilities:

```bash
# Install the library and CLI
pip install edi-cli

# Convert EDI files to JSON
edi convert sample-835.edi --to json --schema 835
edi convert sample-837.edi --to json --schema 837p
edi convert sample-270.edi --to json --schema 270
edi convert sample-271.edi --to json --schema 271
edi convert sample-276.edi --to json --schema 276
edi convert sample-277.edi --to json --schema 277

# Validate with comprehensive rule sets
edi validate sample-835.edi --rule-set comprehensive --verbose
edi validate sample-837.edi --schema 837p --rule-set basic --verbose
edi validate sample-270.edi --schema 270 --rule-set basic --verbose
edi validate sample-271.edi --schema 271 --rule-set basic --verbose
edi validate sample-276.edi --schema 276 --rule-set basic --verbose
edi validate sample-277.edi --schema 277 --rule-set basic --verbose

# Advanced business rule validation (835 only)
edi validate sample-835.edi --rule-set enhanced-business --verbose

# HIPAA compliance validation
edi validate sample-835.edi --rule-set hipaa-advanced --verbose

# Inspect EDI structure and segments
edi inspect sample.edi --segments BPR,CLP,SV1
```

**Supported Transaction Sets:**
- **835**: Healthcare Claim Payment/Advice (ERA) - Complete implementation
- **837P**: Professional Healthcare Claims - Complete implementation
- **270/271**: Eligibility Inquiry/Response - Complete implementation
- **276/277**: Claim Status Inquiry/Response - Complete implementation

**Validation Rule Sets:**
- **835**: `basic`, `business`, `hipaa`, `hipaa-advanced`, `enhanced-business`, `comprehensive`, `all`
- **837P**: `basic`, `business`, `all`
- **270/271**: `basic`, `business`, `all`
- **276/277**: `basic`, `business`, `all`

**Advanced Validation Features:**
- ✅ **YAML DSL Framework**: Create custom validation rules without coding
- ✅ **HIPAA Compliance**: 39+ rules based on X12 005010X221A1 implementation guide
- ✅ **Enhanced Business Engine**: Field-level validation with mathematical calculations
- ✅ **Financial Balance Validation**: Automatic BPR vs Claims+PLB reconciliation 
- ✅ **Cross-Field Validation**: Consistency checks between related fields
- ✅ **Rich Error Context**: Detailed diagnostic information with field paths
- ✅ **Performance Optimized**: 1-5ms execution time for typical transactions

## Detailed Usage Examples

### Library Usage

**Parse an 835 file (Healthcare Payment Advice):**

```python
from packages.core.transactions.t835.parser import Parser835

# Read your EDI file
with open('sample-835.edi', 'r') as f:
    edi_content = f.read()

# Parse it
parser = Parser835()
result = parser.parse(edi_content)

# Access the data
t835 = result.interchanges[0].functional_groups[0].transactions[0].transaction_data

# Print summary
print(f"Payer: {t835.payer.name}")
print(f"Payee: {t835.payee.name}")
print(f"Total Paid: ${t835.financial_information.total_paid}")
print(f"Claims: {len(t835.claims)}")

# Access individual claims
for claim in t835.claims:
    print(f"Claim {claim.claim_id}: ${claim.total_paid}")
    for service in claim.services:
        print(f"  Service {service.procedure_code}: ${service.paid_amount}")
```

**Parse an 837P file (Professional Claims):**

```python
from packages.core.transactions.t837p.parser import Parser837P

# Convert EDI string to segments
segments = []
for line in edi_content.replace('~', '\n').strip().split('\n'):
    if line.strip():
        segments.append(line.split('*'))

# Parse it
parser = Parser837P(segments)
result = parser.parse()

# Access the data
t837p = result.interchanges[0].functional_groups[0].transactions[0].transaction_data

# Print claim summary
print(f"Submitter: {t837p.submitter.name}")
print(f"Billing Provider: {t837p.billing_provider.name}")
print(f"Subscriber: {t837p.subscriber.last_name}, {t837p.subscriber.first_name}")
print(f"Claim ID: {t837p.claim.claim_id}")
print(f"Total Charge: ${t837p.claim.total_charge}")
print(f"Diagnoses: {len(t837p.diagnoses)}")
print(f"Service Lines: {len(t837p.service_lines)}")

# Access service lines
for service in t837p.service_lines:
    print(f"Service {service.procedure_code}: ${service.charge_amount} x {service.units}")
```

**Parse a 270/271 file (Eligibility Inquiry/Response):**

```python
from packages.core.transactions.t270.parser import Parser270

# Read your EDI file (270 or 271)
with open('sample-270.edi', 'r') as f:
    edi_content = f.read()

# Convert to segments
segments = []
for line in edi_content.replace('~', '\\n').strip().split('\\n'):
    if line.strip():
        segments.append(line.split('*'))

# Parse it
parser = Parser270(segments)
result = parser.parse()

# Access the data
t270_271 = result.interchanges[0].functional_groups[0].transactions[0].transaction_data

# Print summary
print(f"Transaction Type: {t270_271.header.get('transaction_set_identifier')}")
print(f"Payer: {t270_271.information_source.name if t270_271.information_source else 'None'}")
print(f"Provider: {t270_271.information_receiver.name if t270_271.information_receiver else 'None'}")
print(f"Subscriber: {t270_271.subscriber.last_name if t270_271.subscriber else 'None'}")

# Access transaction-specific data
if hasattr(t270_271, 'eligibility_inquiries'):
    print(f"Inquiries (270): {len(t270_271.eligibility_inquiries)}")
    for inquiry in t270_271.eligibility_inquiries:
        print(f"  Service Type: {inquiry.service_type_code}")

if hasattr(t270_271, 'eligibility_benefits'):
    print(f"Benefits (271): {len(t270_271.eligibility_benefits)}")
    for benefit in t270_271.eligibility_benefits:
        print(f"  {benefit.service_type_code}: {benefit.eligibility_code}")

if hasattr(t270_271, 'messages'):
    print(f"Messages (271): {len(t270_271.messages)}")
    for message in t270_271.messages:
        print(f"  {message.message_text}")
```

**Parse a 276/277 file (Claim Status Inquiry/Response):**

```python
from packages.core.transactions.t276.parser import Parser276

# Read your EDI file (276 or 277)
with open('sample-276.edi', 'r') as f:
    edi_content = f.read()

# Convert to segments
segments = []
for line in edi_content.replace('~', '\\n').strip().split('\\n'):
    if line.strip():
        segments.append(line.split('*'))

# Parse it
parser = Parser276(segments)
result = parser.parse()

# Access the data
t276_277 = result.interchanges[0].functional_groups[0].transactions[0].transaction_data

# Print summary
print(f"Transaction Type: {t276_277.header.get('transaction_set_identifier')}")
print(f"Payer: {t276_277.information_source.name if t276_277.information_source else 'None'}")
print(f"Provider: {t276_277.information_receiver.name if t276_277.information_receiver else 'None'}")
print(f"Subscriber: {t276_277.subscriber.last_name if t276_277.subscriber else 'None'}")

# Access transaction-specific data
if hasattr(t276_277, 'claim_inquiries'):
    print(f"Claim Inquiries (276): {len(t276_277.claim_inquiries)}")
    for inquiry in t276_277.claim_inquiries:
        print(f"  Claim: {inquiry.claim_control_number}")
        print(f"  Amount: ${inquiry.total_claim_charge}")

if hasattr(t276_277, 'claim_status_info'):
    print(f"Status Info (277): {len(t276_277.claim_status_info)}")
    for status in t276_277.claim_status_info:
        print(f"  Status: {status.status_code} - {status.status_category_code}")
        
if hasattr(t276_277, 'messages'):
    print(f"Messages (277): {len(t276_277.messages)}")
    for message in t276_277.messages:
        print(f"  {message.message_text}")
```

**Convert to JSON:**

```python
import json
json_data = t835.to_dict()  # or t837p.to_dict()
print(json.dumps(json_data, indent=2))
```

### CLI Usage Examples

```bash
# Convert files
edi convert sample-835.edi --to json --out payment-data.json
edi convert sample-837.edi --schema 837p --to json --out claim-data.json
edi convert sample-270.edi --schema 270 --to json --out eligibility-inquiry.json
edi convert sample-271.edi --schema 271 --to json --out eligibility-response.json
edi convert sample-276.edi --schema 276 --to json --out claim-status-inquiry.json
edi convert sample-277.edi --schema 277 --to json --out claim-status-response.json

# Validate with business rules
edi validate sample-835.edi --rule-set comprehensive --verbose
edi validate sample-837.edi --schema 837p --rule-set basic --verbose
edi validate sample-270.edi --schema 270 --rule-set basic --verbose
edi validate sample-271.edi --schema 271 --rule-set basic --verbose
edi validate sample-276.edi --schema 276 --rule-set basic --verbose
edi validate sample-277.edi --schema 277 --rule-set basic --verbose

# HIPAA compliance checking
edi validate sample-835.edi --rule-set hipaa-advanced --verbose

# Advanced field-level validation
edi validate sample-835.edi --rule-set enhanced-business --verbose
```

## Roadmap

**Our Vision:** Build the "Postman for EDI" - the most comprehensive, developer-friendly EDI platform that makes reading, validating, and debugging EDI files trivial. From simple parsing to enterprise-grade integration, we're creating the infrastructure that powers modern B2B data exchange.

### 🎯 **"Postman for EDI" - The Ultimate Vision**

**Phase 1: CLI Foundation (Current)** → **Phase 2: Desktop App** → **Phase 3: Enterprise Platform**

Our roadmap now aligns with creating a **developer- and analyst-friendly desktop application** that makes EDI debugging as intuitive as Postman makes API testing. The current CLI serves as the robust foundation for a future GUI application.

### 🏥 Healthcare Track

#### **v0.1:** ✅ **Foundation** *(Released)*
*Basic 835 parsing, CLI framework, initial test coverage*

#### **v0.2:** ✅ **Enhanced 835 Parser** *(Released)*
*Comprehensive 835 parser refactor with segment dispatcher architecture, enhanced parsing logic (REF*TJ, CAS triplets, composite SVC), PLB segment support, financial balancing, 100% test coverage*

#### **v0.3:** ✅ **CLI & Validation Engine** *(Completed)*
- ✅ Refactored CLI to work with new parser architecture
- ✅ 835 validation DSL with business rules 
- ✅ HIPAA compliance validation with 39+ rules
- ✅ Custom rule engine with YAML configuration
- ✅ Enhanced business rule engine with field-level validation
- ✅ **837P** (Professional Claims) full support with CLI integration
- ✅ **270/271** (Eligibility Inquiry/Response) parsing with CLI integration and validation
- ✅ **276/277** (Claim Status Inquiry/Response) parsing with CLI integration and validation

#### **v0.4:** **Healthcare Expansion** *(Q1 2025)*
- Plugin API for custom transaction sets
- Healthcare-specific data transformations
- Enhanced 837P business rules and HIPAA compliance

#### **v0.5:** **Claims Processing Suite** *(Q2 2025)*
- **837I** (Institutional Claims) support
- **837D** (Dental Claims) support  
- **278** (Healthcare Services Review) parsing
- Advanced claim analysis and reporting
- Integration with major clearinghouses

### 🚛 Logistics Track

#### **v0.6:** **Supply Chain Foundation** *(Q3 2025)*
- **850** (Purchase Order) full support
- **855** (Purchase Order Acknowledgment) parsing
- **810** (Invoice) processing
- **997** (Functional Acknowledgment) handling
- Cross-platform logistics CLI tools

#### **v0.6:** **Fulfillment Engine** *(Q2 2025)*
- **856** (Advance Shipping Notice) parsing
- **940/945** (Warehouse Shipping Orders/Advice)
- **944** (Stock Transfer Receipt Advice)
- **210** (Motor Carrier Freight Details)
- Real-time inventory and shipment tracking

### 🏗️ Enterprise Platform

#### **v0.7:** **Integration Platform** *(Q3 2025)*
- FastAPI service with REST/GraphQL APIs
- Docker containerization with Kubernetes support
- Authentication and authorization (OAuth2, SAML)
- Multi-tenant SaaS architecture
- Rate limiting and API gateway integration

#### **v0.8:** **Production Scale** *(Q4 2025)*
- High-performance streaming parser (millions of records/hour)
- Event-driven architecture with message queues
- Real-time EDI monitoring and alerting
- Advanced analytics and business intelligence
- Enterprise audit logs and compliance reporting

#### **v0.9:** **Ecosystem** *(Q1 2026)*
- SFTP/AS2/AS4 protocol support
- VAN (Value-Added Network) integrations
- Trading partner onboarding automation
- Intelligent document routing
- Machine learning for anomaly detection

### 🚀 Beyond v1.0

#### **v1.0:** **Industry Standard** *(Q2 2026)*
- Complete X12 5010 transaction set coverage (300+ document types)
- EDIFACT support for international logistics
- HL7/FHIR integration for healthcare interoperability
- Blockchain-based transaction verification
- AI-powered EDI document generation

#### **Future Innovations:**
- **Natural Language Processing:** Convert plain English to EDI
- **Smart Validation:** ML-powered business rule discovery
- **Predictive Analytics:** Supply chain and claims forecasting
- **Zero-Code Integration:** Visual workflow builder
- **Global Standards:** UN/CEFACT, GS1 support

### 💡 Open Core Strategy

**Free & Open Source:**
- Core parsing engine for all transaction sets
- Standard validation rules
- CLI tools and basic integrations
- Community plugins and extensions

**Enterprise Features:**
- Advanced analytics and reporting
- Priority support and SLA guarantees
- Enterprise security and compliance
- Managed cloud services
- Custom development and consulting

---

*Join us in building the future of EDI. Whether you're processing healthcare claims or managing global supply chains, edi-cli will be your foundation for reliable, scalable B2B data exchange.*

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for more information.

## License

The core `edi-cli` library and CLI are licensed under the [MIT License](LICENSE). Future enterprise modules will be licensed under a commercial license.
