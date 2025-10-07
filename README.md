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

When `SEED_ON_START=true`, the system automatically loads demo users and sample data.

| Role | Username | Password |
|------|-----------|-----------|
| Procurement Manager | `peter.procurement` | `test123` |
| Requestor | `randy.requestor` | `test123` |
| Additional test users | see backend seed logs |

Use these to explore the portal and test the full workflow.

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

## 🧩 Next Steps

Planned improvements for the next iteration:

### 🔒 Authentication & Security
- Currently, JWTs are short-lived and stored in `sessionStorage` for demo simplicity.  
- In production, this will be replaced with **refresh tokens** and **secure cookie-based authentication**.

### 🤖 Agentic Structure
- Evolve to a **distributed, multi-agent architecture** where each agent (e.g. PDF extractor, classifier, validator) can run independently and communicate via an orchestrator queue.

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