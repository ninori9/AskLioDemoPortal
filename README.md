# 🧩 AskLio Procurement System

## 🏷️ Purpose

The designed system aims to simplify how organizations handle internal purchase requests, vendor offers, and approval workflows.

In many companies, employees (requestors) who need to buy a product or service must submit a formal procurement request to their purchasing department.  
The system streamlines this process by allowing users to:
- **Upload vendor offers or quotes (PDFs)**, which are automatically analyzed and structured using LLM-based agents.  
- **Auto-fill procurement requests** based on the extracted data (items, prices, taxes, totals, etc.).  
- **Automatically classify the request** into the correct **commodity group**, removing the need for users to choose from complex internal categories.  
- **Ensure data integrity**, with full validation, reconciliation, and change logging.

Procurement managers can then:
- **Review**, **approve**, or **edit** each request.  
- **Manually correct** the commodity group suggested by the AI agent.  
- **Track every change** in a complete audit trail.  
- **Monitor the lifecycle** of each request, with statuses like *Open*, *In Progress*, and *Closed* for transparency and traceability.

In short: The system connects requestors and procurement teams through an intelligent, semi-automated workflow — reducing manual effort, errors, and time to approval.

---

## 🚀 How to Start

### 1️⃣ Environment Setup

Create your local `.env` file in the project root:

````
cp template.env .env
````

Then open `.env` and adjust the values as needed.  
`template.env` contains detailed descriptions for every variable.

---

### 2️⃣ Start the System

Run the local stack using Docker Compose:

````
docker compose -f docker-compose.local.yml up --build -d
````

This will start:
- 🗄️ Postgres database  
- 🧠 Weaviate vector database  
- ⚙️ FastAPI backend  
- 💻 Angular frontend portal  

After build and startup, visit:

**👉 http://localhost:4200**

---

### 3️⃣ Seed Data and Test Login

When `SEED_ON_START=true`, the system automatically loads **demo users**, **commodity groups**, and a few **example procurement requests** for testing.  
This lets you explore the portal immediately without creating data manually.

| Role | Username | Password | Department | Notes |
|------|-----------|-----------|-------------|--------|
| 🧑‍💼 Procurement Manager | `peter.procurement` | `test123` | Procurement | Full access to manage and classify requests |
| 🙋‍♂️ Requestor | `randy.requestor` | `test123` | HR | Can create new requests and upload vendor offers |
| 🙋‍♀️ Requestor | `jane.smith` | `test123` | Creative Marketing | Can create new requests with automatic PDF extraction |
| 🧾 Dual Role (Manager + Requestor) | `max.mueller` | `test123` | Accounting | Has both manager and requestor permissions |

#### Additional Seed Data
- 💼 **Commodity groups** for automatic AI classification  
- 📦 **Sample procurement requests** with example statuses and change logs  

Use these accounts to log in and test the full workflow.

---

## ⚙️ Technical Overview

### 🧭 System Components

| Component | Description |
|------------|-------------|
| **asklio-portal** | Angular frontend for both **requestors** and **procurement managers**. Handles request creation, review, and agent results visualization. |
| **asklio-procurement-backend** | FastAPI backend that supports all CRUD operations related to procurement requests, users, and commodity groups. Integrates LLM-based agents for PDF extraction and commodity classification. |

---

### 🧠 Agent Architecture

#### 🧾 PDF Extraction Agent
- **Step 1:** Uses PDF parsing libraries to extract text (and structure if possible).  
- **Step 2:** Sends extracted text to a **language model** with a structured system prompt to parse procurement data (titles, vendors, VAT IDs, line items, totals).  
- **Fallback:** If structured extraction fails (e.g., corrupted text or missing tables), the agent sends the full PDF file to the LLM for direct extraction.  
- **Reconciliation:** Validates that all line totals and summary fields add up; if not, marks uncertain values as `null`.

#### 🏷️ Commodity Group Classification Agent
- **Step 1:** Matches each procurement request to potential **commodity groups** (categories of goods/services).  
- **Step 2:** Retrieves example requests from the **Weaviate vector database** for the top candidates.  
- **Step 3:** Re-runs the LLM to compare and select the best-fitting commodity group with a confidence score.

---

## 🧪 Testing

Unit tests focus on the core business logic inside the backend — especially the **procurement service**, which handles request creation, total calculations, and data integrity checks.

### Run Tests

You can run the test suite directly inside the backend container:

```
docker compose -f docker-compose.local.yml exec backend sh -lc "pytest -v"
```

---

## 🧩 Next Steps

Planned improvements for the next iteration:

### 🔒 Authentication & Security
- Currently, JWTs are short-lived and stored in `sessionStorage` for demo simplicity.  
- In production, this will be replaced with **refresh tokens** and **secure cookie-based authentication**.

### 🤖 Agentic Structure
- Evolve to a **distributed, multi-agent architecture** where each agent (e.g. PDF extractor, classifier, validator) can run independently and communicate via an orchestrator queue.

### 🧪 Testing & Quality Assurance
- Improved **testing** for backend services (FastAPI + agents).  
- Set up **GitHub Actions CI** for automated test and linting runs on pull requests.

### 🚀 Deployment & DevOps
- Containerize the entire stack for **production-ready deployment** (e.g., Docker Swarm or Kubernetes).  
- Add **logging and monitoring** (e.g., OpenTelemetry, Prometheus, Grafana) for observability of agent behavior and performance.

### 💡 Usability & UI Enhancements
- Introduce **search and filtering** for procurement requests.  
- Add **bulk status updates** for managers. 

### ✅ Additional Agents
- **Validation & Plausibility Checks**  
  e.g., verify VAT IDs, check consistency of totals, or validate supplier legitimacy.  
- **Offer Comparison**  
  Compare multiple offers for the same request (price, delivery time, category, etc.) and rank options intelligently.  
- **Document Linking**  
  Automatically relate invoices to their corresponding offers and purchase orders.

---

## 🧱 Stack Summary

| Layer | Tech |
|--------|------|
| Frontend | Angular + Material |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Vector Store | Weaviate |
| LLM Provider | OpenAI API |
| Containerization | Docker Compose |
| Auth | JWT (demo), cookie planned |
| AI Functions | Extraction, classification, validation |

---

## 👩‍💻 Local Development Tips

- You can restart the backend individually with hot reload:

````
docker compose exec backend uvicorn app.main:app --reload
```

- Access pgAdmin or similar via `POSTGRES_HOST=db`, port `5432`.
- View Weaviate schema at [http://localhost:8080/v1/schema](http://localhost:8080/v1/schema).

---