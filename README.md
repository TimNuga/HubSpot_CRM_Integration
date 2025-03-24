# HubSpot CRM Integration

A production-ready **Flask** application that integrates with HubSpot’s CRM to create or update contacts, deals, and tickets, then store a local reference for subsequent retrieval. It also manages OAuth token refresh, rate-limiting logic, validation, and includes an **OpenAPI** specification for documentation.

## Table of Contents

1. Overview
2. Folder Structure
3. Installation
4. Configuration
5. Running the App
6. Testing
7. API Endpoints
8. OpenAPI Specification
9. Additional Notes

---

## 1. Overview

This project provides:

- **Contacts Upsert**: Create or update HubSpot contacts.
- **Deals Upsert**: Create or update deals, optionally associated with a contact.
- **Tickets Creation**: Always create new tickets, optionally associated with contact/deal.
- **Local Storage**: Tracks newly created CRM objects in the database (`CreatedCRMObject`).
- **Token Management**: Refreshes HubSpot OAuth tokens automatically, stored in `HubspotAuth`.
- **Rate Limiting**: Retries on 429/5xx using Tenacity, raising custom errors if it persists.
- **Validation**: Marshmallow schemas for contacts, deals, tickets.
- **OpenAPI Docs**: Provided in `static/openapi.yaml`.

---

## 2. Folder Structure

```text
app/
  ├── __init__.py
  ├── config.py
  ├── extensions.py
  ├── main.py
  ├── models.py
  ├── routes.py
  ├── controllers/
  │   └── hubspot_controller.py
  ├── integrations/
  │   └── hubspot_api.py
  ├── schemas/
  │   └── hubspot_schema.py
  ├── services/
  │   ├── hubspot_service.py
  │   └── oauth_service.py
  └── utils/
      ├── __init__.py
      ├── api_responses.py
      ├── constants.py
      ├── errors.py
      └── rate_limit_handler.py

tests/
  ├── conftest.py
  ├── integration_tests/
  └── unit_tests/

static/
  └── openapi.yaml

Dockerfile
docker-compose.yml
.env

--- 

## 3. Installation

```bash
1) Clone the repository:

git clone https://github.com/yourusername/hubspot-crm-integration.git cd hubspot-crm-integration

2) (Optional) Create a virtual environment

python3 -m venv venv source venv/bin/activate # or venv\Scripts\activate for Windows

3) Install dependencies

pip install -r requirements.txt 


4. Configuration

Environment Variables: Copy .env.example to .env and fill in:
FLASK_ENV (development, testing, or production)
SECRET_KEY
DATABASE_URL (e.g. postgresql://user:password@localhost:5432/dbname)
HubSpot: HUBSPOT_CLIENT_ID, HUBSPOT_CLIENT_SECRET, HUBSPOT_REFRESH_TOKEN, HUBSPOT_OAUTH_TOKEN_URL, HUBSPOT_API_BASE_URL
Logging / Rate Limit: e.g. LOG_LEVEL=INFO
Database: A PostgreSQL DB is recommended. If using Docker Compose, the db container is automatically set up.
```

5. Running the App

Using Docker Compose
```bash 
docker-compose up --build 
```

The Flask app will be available on port 5001 (configurable in docker-compose.yml).
A DB container will also be started, if defined.
Running Locally Without Docker
    1) Ensure DATABASE_URL is set or in .env
```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/hubspot"
```

    2) Run migrations (if using Flask-Migrate)

```bash
flask db upgrade
```

    3) Start the app

```bash
flask run --host=0.0.0.0 --port=5001 
```

6. Testing



Run all tests:
```bash
pytest tests/ --maxfail=1 --disable-warnings
```

Run only unit or integration tests:

```bash
pytest tests/unit_tests pytest tests/integration_tests ```
```

Unit Tests: Isolate services, schemas, or rate-limiting logic.
Integration Tests: Use the Flask test client (test_client) to exercise endpoints.

7. API Endpoints

All routes mount at /api via register_routes. The major endpoints are:

```bash
POST /api/contacts: Create/update (upsert) a contact.
PUT /api/contacts: Same upsert logic, but via PUT method.
POST /api/deals: Create/update a deal.
PUT /api/deals: Update or create a deal if not found.
POST /api/tickets: Always create a new ticket.
GET /api/new-crm-objects: Retrieve newly created local CRM objects (contacts, deals, tickets) with pagination.
Each endpoint uses Marshmallow validation and references logic in HubSpotService.
```

8. OpenAPI Specification

We include a Swagger/OpenAPI file under static/openapi.yaml. It describes all endpoints with the /api prefix:
```bash
/api/contacts (POST/PUT)
/api/deals (POST/PUT)
/api/tickets (POST)
/api/new-crm-objects (GET)
Here is the recommended snippet inside openapi.yaml to reflect the actual routes (copy-paste as needed):
```

```yaml 
openapi: 3.0.3 info: title: HubSpot CRM Integration API description: > This API integrates with HubSpot to create/update contacts, deals, tickets, and retrieve newly created CRM objects from the local DB. version: "1.0.0"
```

servers:

```bash
url: /api description: "Base path for CRM routes."
paths: /contacts: ... /deals: ... /tickets: ... /new-crm-objects: ... components: schemas: ... ```
```

You can then serve /api/docs using Flask’s static file support or integrate a Swagger UI blueprint.

9. Additional Notes

Token Management: HubspotOAuthService handles refresh tokens, stored in HubspotAuth.
Rate Limiting: request_with_tenacity in rate_limit_handler.py retries on 429 or 5xx, final attempt raising a custom error if it persists.
Local DB: The CreatedCRMObject table tracks newly created objects for retrieval via GET /api/new-crm-objects.
Contributing: Pull requests and issues are welcome to expand features or address bugs.
