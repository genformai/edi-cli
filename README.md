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
- **AST Architecture Refactor**: Clean separation with transaction-specific AST modules (ast_835.py, ast_837p.py, etc.)
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
