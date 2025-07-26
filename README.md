# edi-cli

A modern, open-source EDI toolkit.

**edi-cli** is a developer-first toolkit for parsing, validating, and transforming Electronic Data Interchange (EDI) files. It provides a fast, well-tested core library and a user-friendly command-line interface (CLI) to streamline working with complex EDI formats.

## Why Open Core?

We believe that core EDI parsing and validation should be a commodity. By open-sourcing the core, we aim to foster a community of contributors and build a robust foundation for a wide range of EDI applications. Our open-core model allows us to offer a free, powerful toolkit for developers while providing a clear path to commercial, enterprise-grade features like a hosted API, SFTP watchers, and advanced auditing capabilities.

## Quickstart (5 minutes)

1.  **Install `edi-cli`:**

    ```bash
    pip install edi-cli
    ```

2.  **Convert an EDI file to JSON:**

    ```bash
    edi convert examples/datasets/sample-835.edi --to json --out output.json
    ```

3.  **Convert to CSV for analysis:**

    ```bash
    edi convert examples/datasets/sample-835.edi --to csv --out claims.csv
    ```

4.  **Validate with business rules:**

    ```bash
    edi validate examples/datasets/sample-835.edi --rule-set business
    ```

5.  **HIPAA compliance validation:**

    ```bash
    edi validate examples/datasets/sample-835.edi --rule-set hipaa --verbose
    ```

6.  **Inspect file structure:**

    ```bash
    edi inspect examples/datasets/sample-835.edi
    ```

## Roadmap

Our vision is to build the most comprehensive, developer-friendly EDI toolkit for healthcare and logistics. From simple parsing to enterprise-grade integration, we're creating the infrastructure that powers modern B2B data exchange.

### 🏥 Healthcare Track

#### **v0.1:** ✅ **Foundation** 
*835 parse → JSON/CSV, CLI, tests, docs*

#### **v0.2:** ✅ **Validation Engine** 
*835 validation DSL with business rules, HIPAA compliance validation, custom rule engine with YAML configuration, field-level validation with detailed error reporting*

#### **v0.3:** **Healthcare Core** *(Q3 2024)*
- **837P** (Professional Claims) full support
- **270/271** (Eligibility Inquiry/Response) parsing
- **276/277** (Claim Status Inquiry/Response) parsing
- Plugin API for custom transaction sets
- Healthcare-specific data transformations

#### **v0.4:** **Claims Processing Suite** *(Q4 2024)*
- **837I** (Institutional Claims) support
- **837D** (Dental Claims) support  
- **278** (Healthcare Services Review) parsing
- Advanced claim analysis and reporting
- Integration with major clearinghouses

### 🚛 Logistics Track

#### **v0.5:** **Supply Chain Foundation** *(Q1 2025)*
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
