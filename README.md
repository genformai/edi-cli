# edi-cli

A modern, open-source EDI toolkit.

**edi-cli** is a developer-first toolkit for parsing, validating, and transforming Electronic Data Interchange (EDI) files. It provides a fast, well-tested core library and a user-friendly command-line interface (CLI) to streamline working with complex EDI formats.

## Why Open Source EDI?

Despite a market dominated by commercial vendors, significant and compelling open-source opportunities exist for Electronic Data Interchange (EDI). The inertia and legacy architecture of many established solutions have created gaps that a modern, developer-focused open-source project could effectively fill. The key lies in shifting the paradigm from monolithic, all-in-one platforms to more flexible, composable, and developer-centric tools that align with contemporary software development practices.

Here are some of the most promising open-source opportunities in the EDI space:

### 1. The Developer-Centric EDI Toolkit: "EDI-as-Code"
The most significant opportunity lies in creating a suite of tools that treat EDI as a development concern, not just a business process. This "EDI-as-Code" approach would resonate strongly with modern DevOps and software engineering teams.

**Core Components:** This toolkit would include a high-performance parsing and serialization library for various EDI standards (X12, EDIFACT), a powerful and intuitive mapping engine that uses a declarative syntax (like YAML or a domain-specific language), and a robust validation framework.

**Version Control and CI/CD:** A key innovation would be to enable the management of EDI maps and configurations within a Git repository. This would allow for versioning, collaborative development, and integration into CI/CD pipelines for automated testing and deployment.

**Command-Line Interface (CLI):** A powerful and scriptable CLI would be essential for developers to integrate EDI processes into their existing workflows and automation scripts.

### 2. A Modern, API-First EDI Translator
Many businesses are moving towards API-driven architectures. An open-source EDI solution that bridges the gap between legacy EDI and modern RESTful APIs would be incredibly valuable.

**Lightweight and Embeddable:** Instead of a large, standalone application, this would be a lightweight, embeddable engine that can be easily integrated into existing applications and microservices.

**Automatic API Generation:** A truly innovative feature would be the ability to automatically generate an OpenAPI (Swagger) specification from an EDI implementation guide, and vice-versa. This would dramatically simplify the process of exposing EDI data as a modern API.

**JSON-Native:** The tool would work natively with JSON, allowing for easy manipulation and integration of EDI data within modern applications before translating to and from the rigid EDI format.

### 3. A User-Friendly, Self-Hosted Web UI for EDI Management
While the backend can be developer-focused, a user-friendly front-end is still crucial for business users and support teams. An open-source project could provide a modern, intuitive web interface for managing the entire EDI lifecycle.

**Visual Mapping Tool:** A drag-and-drop interface for creating and managing EDI maps would lower the barrier to entry for non-developers.

**Intuitive Dashboard and Monitoring:** A dashboard providing real-time visibility into transaction status, errors, and partner activity would be a significant improvement over the often-clunky interfaces of older systems.

**Simplified Partner Management:** An easy-to-use interface for onboarding new trading partners and configuring their specific requirements would be a major selling point.

### 4. Cloud-Native and Serverless EDI
As businesses increasingly move to the cloud, there is a need for EDI solutions that can leverage the benefits of cloud-native architectures.

**Serverless-First Design:** An EDI translator designed to run efficiently on serverless platforms like AWS Lambda, Azure Functions, or Google Cloud Functions would offer incredible scalability and cost-effectiveness.

**Containerized Deployment:** Providing well-documented Docker and Kubernetes configurations would allow for easy deployment and scaling in any cloud environment.

**Integration with Cloud Services:** The tool could offer native integrations with cloud services like object storage (S3, Blob Storage) for archiving, queuing services (SQS, Azure Service Bus) for message processing, and cloud-based databases for logging and analytics.

### 5. Niche Industry-Specific Solutions
Instead of trying to be a one-size-fits-all solution, an open-source project could focus on the specific needs of a particular industry, such as healthcare (HIPAA), logistics, or retail. This would allow for a more tailored and feature-rich offering that could compete effectively with commercial vendors in that niche.

---

By focusing on these areas, an open-source EDI project could gain significant traction. The key to success would be to learn from the successes of other open-source projects: build a strong community, prioritize developer experience, and offer a more flexible and modern alternative to the entrenched incumbents. The opportunity is ripe for a project that empowers developers to solve their own EDI challenges with tools that feel familiar and powerful.

📖 **[Read the full "Why Open Source EDI?" deep dive →](docs/why-open-source-edi.md)**

## What Works Now (v0.2.0)

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

**Key Features:**
- ✅ **Comprehensive Segment Support**: BPR, TRN, DTM, N1, NM1, PER, REF, CLP, CAS, SVC, SVD, PLB, LX + all envelope segments
- ✅ **Enhanced Parsing Logic**: REF*TJ as Tax ID (not NPI), CAS triplet support, composite SVC parsing (HC:99213:25)
- ✅ **Financial Balancing**: Out-of-balance detection comparing BPR vs Claims+PLB totals
- ✅ **Provider Level Adjustments (PLB)**: Full PLB segment parsing with reason codes and amounts
- ✅ **Advanced Data Handling**: Dynamic delimiter detection, optional quantity handling, DTM qualifiers
- ✅ **Robust Error Handling**: Integrated with StandardErrorHandler and contextual error reporting
- ✅ **100% Test Coverage**: 72/72 tests passing with comprehensive edge case coverage

### 🚧 **CLI - Under Development**

The command-line interface exists but needs updates to work with the refactored parser:

```bash
# Will be available after CLI refactoring:
# pip install edi-cli
# edi convert sample-835.edi --to json
# edi validate sample-835.edi --rule-set business
```

## Quickstart (Library Usage)

1.  **Install the library:**

    ```bash
    pip install edi-cli  # Core library included
    ```

2.  **Parse an 835 file:**

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

3.  **Convert to JSON:**

    ```python
    import json
    json_data = t835.to_dict()
    print(json.dumps(json_data, indent=2))
    ```

## Roadmap

Our vision is to build the most comprehensive, developer-friendly EDI toolkit for healthcare and logistics. From simple parsing to enterprise-grade integration, we're creating the infrastructure that powers modern B2B data exchange.

### 🏥 Healthcare Track

#### **v0.1:** ✅ **Foundation** *(Released)*
*Basic 835 parsing, CLI framework, initial test coverage*

#### **v0.2:** ✅ **Enhanced 835 Parser** *(Current - Released)*
*Comprehensive 835 parser refactor with segment dispatcher architecture, enhanced parsing logic (REF*TJ, CAS triplets, composite SVC), PLB segment support, financial balancing, 100% test coverage*

#### **v0.3:** 🚧 **CLI & Validation Engine** *(In Progress)*
- Refactor CLI to work with new parser architecture
- 835 validation DSL with business rules
- HIPAA compliance validation 
- Custom rule engine with YAML configuration
- Field-level validation with detailed error reporting

#### **v0.4:** **Healthcare Core** *(Q1 2025)*
- **837P** (Professional Claims) full support
- **270/271** (Eligibility Inquiry/Response) parsing
- **276/277** (Claim Status Inquiry/Response) parsing
- Plugin API for custom transaction sets
- Healthcare-specific data transformations

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
