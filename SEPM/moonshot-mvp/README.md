# SRM Cybersecurity Moonshot MVP

Monorepo MVP for a Zero Trust SOC platform.

## Stack
- Backend: FastAPI (Python)
- Frontend: Next.js + Tailwind CSS (dark-mode SOC UI)
- Data: PostgreSQL + Elasticsearch
- Security: OAuth2/JWT + MFA + device trust checks

## Directory Structure
- backend: FastAPI API, auth, schemas, SIEM generator
- backend/sql/schema.sql: explicit PostgreSQL schema reference
- frontend: Next.js SOC dashboard sample
- docker-compose.yml: local environment orchestration

## Run
1. From project root:
   docker compose up --build
2. Frontend:
   http://localhost:3000
3. Backend API docs:
   http://localhost:8000/docs

## Default SOC Analyst (seeded)
- Username: soc_analyst
- Password: ChangeMe123!
- Trusted device id: SOC-WS-001

## Zero Trust Access to SOC Dashboard
Calls to /soc/* require:
- Valid JWT access token
- MFA enabled for the user
- Trusted device id in header X-Device-Id

## Mock SIEM Generator
Inside backend container:
python scripts/mock_siem_generator.py

Defaults to generating 1500 alerts/minute.

## Security Notes
- Passwords are bcrypt-hashed
- SQLAlchemy ORM mitigates SQL injection risk
- Strict auth checks for sensitive routes
- Full API audit trail logging on each request
- Update JWT secret and SIEM API key before production
