# HubSpot CRM Integration

This repository contains a robust **Flask** application for **HubSpot CRM** integration, featuring:

1. **Proactive Token Refresh** for HubSpot OAuth tokens.  
2. **Rate Limiting** using Tenacity for 429 or transient server errors.  
3. **Marshmallow Validations** for contacts, deals, and tickets.  
4. **Structured Logging** in JSON format.  
5. **Swagger/OpenAPI** documentation served via Docker.  
6. **Docker & Docker Compose** setup for easy deployment.  
7. **Robust Pagination** (cursor-based or offset-based) for retrieving large data sets.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running Locally (Without Docker)](#running-locally-without-docker)
- [Docker Setup](#docker-setup)
- [API Documentation (Swagger/OpenAPI)](#api-documentation-swaggeropenapi)
- [Endpoints](#endpoints)
- [Pagination Approaches](#pagination-approaches)
- [Structured Logging](#structured-logging)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## Project Overview

This application integrates with **HubSpot CRM** to:

- **Create or update** contacts, deals, and tickets.  
- **Retrieve** newly created objects.  
- Enforce best practices like **token refresh**, **rate-limit handling**, and **data validation**.

It is designed to be **production-ready**, featuring:

- **Proactive Token Refresh**: Minimizes downtime and race conditions around token expiry.  
- **Exponential Backoff** for 429 or server errors.  
- **Marshmallow** for structured validation.  
- **OpenAPI** specs, served via **Swagger UI**.

---

## Features

1. **Proactive Token Refresh**  
   - Stores `expires_in` from HubSpot and refreshes ~60s before token expiry.  
   - Avoids first-request failures when a token expires.

2. **Rate Limiting with Tenacity**  
   - Retries on 429 or 5xx responses (configurable).  
   - Exponential backoff to reduce stress on HubSpot’s APIs.

3. **Marshmallow Validation**  
   - ContactSchema, DealSchema, TicketSchema ensure mandatory fields and correct types.  
   - 400 responses for invalid payloads.

4. **Structured Logging**  
   - Outputs logs in JSON format for easy aggregation and monitoring.  
   - Additional fields can be injected (e.g., request_id) for advanced debugging.

5. **OpenAPI/Swagger**  
   - Full specification in `docs/openapi.yaml`.  
   - Served at `/docs` for interactive API exploration.

6. **Dockerized**  
   - `docker-compose.yml` to run the app, a Postgres DB, and the test container with a single command.

7. **Pagination**  
   - Supports either **HubSpot’s cursor-based** approach or **local offset/cursor-based** queries.  
   - Ensures large data sets can be handled efficiently.

---

## Installation

1. **Clone** this repository:
   ```bash
   git clone https://github.com/yourorg/hubspot-crm-integration.git
   cd hubspot-crm-integration

2. **Set up** a Python virtual environment (optional but recommended):
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration
- .env file(in the project root or in your environment variables):
    Copy the .env.example file and provide your own credentials as required.

- The application reads these vars in config.py to set up OAuth, DB connections, logging levels, etc.

## Running Locally (Without Docker)
```bash
export FLASK_ENV=development
flask run
# or
python -m app.main
```
Your app is available at http://localhost:5001.
- Swagger UI: Documentation available at `/docs/openapi.yaml`

## Docker Setup
1. Build & Launch:
```bash
docker compose up --build
```
2. Services:
- db: PostgreSQL database.
- test: Runs migrations & tests, then exits.
- web: The Flask app with Gunicorn.

When it starts, the test container will run your tests. If all pass, the web container will proceed to serve on http://localhost:5001.

## API Documentation (Swagger/OpenAPI)
A dedicated file docs/openapi.yaml provides the full specification. By default, it’s served at:
```bash
GET /api/docs/
```

An interactive UI is available there, letting you try endpoints.

## Endpoints

1. POST /crm/register
    - Purpose: Create or update a contact, plus deals and tickets.
    - Body (JSON):
    ```json
    {
    "contact": {
        "email": "[email protected]",
        "firstname": "John",
        "lastname": "Doe",
        "phone": "123-456-7890"
    },
    "deals": [
        {
        "dealname": "New Deal",
        "amount": 1200,
        "dealstage": "appointmentscheduled"
        }
    ],
    "tickets": [
        {
        "subject": "Billing Issue",
        "description": "Customer cannot pay",
        "category": "billing",
        "hs_pipeline": "support",
        "hs_ticket_priority": "HIGH",
        "hs_pipeline_stage": "1"
        }
    ]
    }   
    ```
    - Response:
    ```json
    {
        "success": true,
        "message": "Contact, Deal(s), and Ticket(s) processed successfully.",
        "contact_id": "12345",
        "deal_ids": ["67890"],
        "ticket_ids": ["98765"]
    }
    ```

2. GET /crm/objects
    - Purpose: Retrieve newly created CRM objects from HubSpot.
    - Query Params: limit, after (cursor-based for HubSpot).
    - Response:
    ```json
    {
    "contacts": [...],
    "next_after": "..."
    }
    ```

3. GET /objects/local
    - Purpose: Retrieve locally stored references with offset-based pagination.
    - Query Params: page, limit.
    - Response:
```json
{
    "page": 1,
    "limit": 20,
    "total_pages": 5,
    "total_records": 100,
    "results": [...]
}
```

## Pagination Approaches
This application supports:
- HubSpot Cursor-Based:
    - Use after param from response.
    - Typically: GET /crm/v3/objects/... ?limit=20&after=<cursor>.
- Local Offset-Based:
    - For DB queries: page + limit.
- Local Cursor/Keyset:
    - If you have massive data sets.
    - GET /objects/local-cursor?limit=20&after=<id>.

## Structured Logging
All logs are output in JSON with fields like asctime, name, levelname, message. Example snippet from the logs:
```json
{
  "asctime": "2025-03-20 13:54:31,045",
  "name": "app.routes.crm",
  "levelname": "INFO",
  "message": "Handling /crm/register request"
}
```
Logs go to stdout so Docker or your environment can collect them.

## Testing
- Pytest is used for both unit and integration tests.
- Marshmallow validations are tested to ensure 400 errors on invalid input.
- Rate-limit logic tested with a 429 mock, verifying Tenacity’s retries.
- Run Tests Locally:
```bash
FLASK_ENV=testing pytest --maxfail=1 --disable-warnings -q
```
- Run Tests in Docker:
```bash
docker compose up --build
```

## Contributing
1. Fork the repo and create feature branches.
2. Open Pull Requests with details on your changes.
3. Please maintain consistent code style and update relevant docs or tests.

## License

MIT License

Enjoy your fully featured, production-grade HubSpot CRM Integration with:

- Proactive token refresh
- Tenacity-based rate limiting
- Marshmallow validations
- Structured logging
- Docker
- Swagger docs
- Pagination

Feel free to create issues or pull requests to enhance this project further!