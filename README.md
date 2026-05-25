# Neighborhood Library

## Overview

Neighborhood Library is a full-stack application for managing a community library: cataloging books, registering members, and tracking borrow/return activity. Staff use a web portal with JWT authentication; the REST API powers all data operations.

The backend is built for clarity and maintainability using async Python, PostgreSQL, and Docker-first deployment. The frontend is a Next.js staff portal with shadcn/ui.

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend | FastAPI, Uvicorn | Async HTTP API and ASGI server |
| Frontend | Next.js (App Router), shadcn/ui, TypeScript | Staff web portal |
| Database | PostgreSQL 15, SQLAlchemy 2 (async), asyncpg | Persistent storage and ORM access |
| Auth | python-jose, passlib (bcrypt), OAuth2 Bearer | JWT access tokens and password hashing |
| Migrations | Alembic | Versioned database schema changes |
| Containerization | Docker, Docker Compose | Local development and deployment |

## Frontend

- Next.js 14 with App Router
- shadcn/ui component library
- TypeScript throughout
- Axios with JWT interceptors

## Pages

| Page | Route | Description |
|------|-------|-------------|
| Login | `/login` | Staff authentication |
| Dashboard | `/` | Stats, overdue alerts, recent activity |
| Books | `/books` | Manage library books |
| Members | `/members` | Manage library members |
| Lending | `/lending` | Borrow and return operations |

## Default Login

| Field | Value |
|-------|-------|
| Email | `subodh@numinolabs.com` |
| Password | `NuminoLabs@2026` |

⚠️ Change password after first login

## Testing the App

Step-by-step manual test flow:

1. Login with default credentials
2. Dashboard shows 10 seeded books stats
3. Register a test member
4. Go to Lending → Borrow a book for that member
5. Dashboard shows active loan
6. Return the book
7. Try borrowing a book with 0 copies → should show error
8. Check overdue tab (will be empty on fresh install)

## Architecture

The application follows a **layered architecture**. Each layer has a single responsibility and depends only on the layer below it.

```
Request → API Layer → Service Layer → Repository Layer → PostgreSQL
```

**API layer** (`app/api/`) defines HTTP routes, request/response models, and authentication dependencies. It validates input via Pydantic schemas, maps HTTP status codes, and delegates all business rules to services. It does not contain database queries or domain logic.

**Service layer** (`app/services/`) implements business rules: duplicate checks, availability validation, loan lifecycle, and audit field assignment. Services raise domain-specific HTTP exceptions and coordinate multiple repository calls when needed.

**Repository layer** (`app/repositories/`) performs database access only—`select`, insert, update, and delete operations using async SQLAlchemy sessions. Repositories return ORM models and never raise HTTP exceptions.

**PostgreSQL** stores all persistent data. Timestamps are written in UTC; API responses convert them to the configured application timezone for clients.

## Project Structure

```
neighborhood-library/
├── docker-compose.yml          # Postgres + backend + frontend services
├── .env.example                # Pointer to backend environment setup
├── README.md
├── frontend/                   # Next.js staff portal
│   ├── Dockerfile
│   ├── app/                    # App Router pages
│   ├── components/             # UI and feature components
│   ├── lib/                    # API client, auth, utilities
│   ├── services/               # API service layer
│   └── types/                  # TypeScript types
└── backend/
    ├── Dockerfile              # Production/dev container image
    ├── requirements.txt        # Python dependencies
    ├── alembic.ini             # Alembic configuration
    ├── .env.example            # Environment variable template
    ├── logs/                   # Rotating application logs (mounted in Docker)
    ├── migrations/             # Alembic migration scripts
    │   ├── env.py              # Async migration runner
    │   └── versions/           # Revision files
    └── app/
        ├── main.py             # FastAPI app, middleware, exception handlers
        ├── config.py           # Pydantic settings from .env
        ├── database.py         # Async engine, session factory, Base
        ├── api/
        │   ├── deps.py         # get_db, get_current_staff dependencies
        │   └── v1/             # Versioned route modules
        ├── core/               # Cross-cutting utilities
        │   ├── security.py     # Password hashing, JWT encode/decode
        │   ├── logger.py       # File + console logging
        │   ├── timezone.py     # UTC ↔ local timezone helpers
        │   ├── exceptions.py   # Custom HTTPException subclasses
        │   └── seeder.py       # Default admin bootstrap
        ├── models/             # SQLAlchemy ORM models
        ├── schemas/            # Pydantic request/response models
        ├── services/           # Business logic
        └── repositories/       # Database queries
```

## Quick Start (Docker — Recommended)

1. Clone the repository.
2. Copy the environment template:
   ```bash
   cp backend/.env.example backend/.env
   ```
3. Edit `backend/.env` with your values (database credentials, `SECRET_KEY`, admin account).
4. Start the stack:
   ```bash
   docker compose up --build
   ```
5. Open the staff portal at [http://localhost:3000](http://localhost:3000) and API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

The backend container runs `alembic upgrade head` before starting Uvicorn. Postgres must become healthy before the API starts.

### Frontend environment

For local development (without Docker), create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

When using Docker Compose, the frontend image is built with `NEXT_PUBLIC_API_URL=http://localhost:8000` so the browser can reach the API on the host-mapped port.

## Manual Setup (Without Docker)

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- pip

### Steps

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — set DATABASE_URL to your local Postgres instance
# Example: postgresql+asyncpg://postgres:password@localhost:5432/neighborhood_library

alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) when the server is running.

## Environment Variables

Configure these in `backend/.env`:

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `POSTGRES_USER` | PostgreSQL username | `postgres` | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | `your_password` | Yes |
| `POSTGRES_DB` | Database name | `neighborhood_library` | Yes |
| `POSTGRES_HOST` | Database host | `postgres` (Docker) / `localhost` | Yes |
| `POSTGRES_PORT` | Database port | `5432` | Yes |
| `DATABASE_URL` | Async SQLAlchemy URL | `postgresql+asyncpg://postgres:pass@postgres:5432/neighborhood_library` | Yes |
| `APP_ENV` | Runtime environment label | `development` | No |
| `APP_PORT` | API port (documentation) | `8000` | No |
| `SECRET_KEY` | JWT signing secret | `long-random-string` | Yes |
| `ALGORITHM` | JWT algorithm | `HS256` | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes | `480` | No |
| `ADMIN_EMAIL` | Default admin email (seeder) | `admin@example.com` | Yes |
| `ADMIN_PASSWORD` | Default admin password (seeder) | `change-me` | Yes |
| `ADMIN_FULL_NAME` | Default admin display name | `Admin User` | Yes |
| `APP_TIMEZONE` | Timezone for API responses | `Asia/Kolkata` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `LOG_RETENTION_DAYS` | Days of rotated log files to keep | `30` | No |

## Default Admin

On every startup, the application runs an **idempotent seeder** that ensures a default staff account exists using `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `ADMIN_FULL_NAME` from `.env`. If the account already exists, seeding is skipped.

**Important:** Change the default admin password after your first login. Do not use default credentials in production.

Log in via `POST /api/v1/auth/login` (OAuth2 form: `username` = email, `password` = password), then use the returned Bearer token for protected routes.

## API Documentation

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## API Endpoints

Base URL: `http://localhost:8000`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Health check for Docker/monitoring | No |
| POST | `/api/v1/auth/login` | Staff login (returns JWT) | No |
| POST | `/api/v1/auth/register` | Register additional staff | Yes |
| GET | `/api/v1/auth/me` | Current staff profile | Yes |
| GET | `/api/v1/books` | List books (pagination) | No |
| POST | `/api/v1/books` | Create a book | Yes |
| GET | `/api/v1/books/{id}` | Get book by ID | No |
| PUT | `/api/v1/books/{id}` | Update a book | Yes |
| DELETE | `/api/v1/books/{id}` | Delete a book | Yes |
| GET | `/api/v1/members` | List members | Yes |
| POST | `/api/v1/members` | Register a member | Yes |
| GET | `/api/v1/members/{id}` | Get member by ID | Yes |
| PUT | `/api/v1/members/{id}` | Update a member | Yes |
| GET | `/api/v1/members/{id}/loans` | Active loans for a member | Yes |
| POST | `/api/v1/lending/borrow` | Borrow a book | Yes |
| PUT | `/api/v1/lending/{id}/return` | Return a borrowed book | Yes |
| GET | `/api/v1/lending` | List all active loans | Yes |
| GET | `/api/v1/lending/overdue` | List overdue loans | Yes |

Protected routes require header: `Authorization: Bearer <access_token>`.

## Database Schema

| Table | Description |
|-------|-------------|
| **staff** | Library staff accounts (email, hashed password, admin flag). Does not use the shared audit mixin. |
| **books** | Catalog entries with title, author, optional ISBN/genre, and copy counters (`copies_total`, `copies_available`). |
| **members** | Patrons who borrow books (name, email, optional phone/address). |
| **lending_records** | Borrow events linking a book and member with `borrowed_at`, `due_date`, and optional `returned_at`. |

**Relationships**

- `lending_records.book_id` → `books.id`
- `lending_records.member_id` → `members.id`
- `books`, `members`, and `lending_records` track `created_by` / `updated_by` → `staff.id` (audit mixin)

A loan with `returned_at = NULL` is considered active. Overdue loans are active loans where `due_date` is before the current UTC time.

## Key Design Decisions

- **UTC storage, local time serving** — Timestamps are persisted in UTC (`DateTime(timezone=True)`). API responses convert to `APP_TIMEZONE` for display.
- **Layered architecture** — Routes, services, and repositories are separated to keep HTTP, business rules, and SQL concerns isolated.
- **`copies_available` counter** — Availability is tracked with a denormalized counter updated on borrow/return for fast checks and simple constraints.
- **Idempotent seeder** — Default admin creation is safe to run on every startup and never blocks application boot on failure.
- **Custom exceptions** — Services raise typed `HTTPException` subclasses for consistent status codes and messages.
- **Rotating file logs** — Daily log rotation with configurable retention; console and file handlers use the application timezone in log timestamps.

## Running Tests

Tests coming soon.
