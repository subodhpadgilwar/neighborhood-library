# Why We Built It This Way
## Architectural & Design Decision Log

> This document explains the reasoning behind every significant technical decision in the Neighborhood Library system. Each decision includes what was chosen, why it was chosen, and what alternatives were considered.

---

## 1. Overall Architecture — Layered / N-Tier

### Decision
Layered architecture with four distinct layers:
API → Service → Repository → Database

### Why
Each layer has exactly one responsibility.
The API layer handles HTTP concerns only.
The service layer owns all business logic.
The repository layer owns all database queries.
This means business logic is never mixed with
HTTP handling or raw SQL — changes in one layer
don't cascade into others.

### Benefits
- Business rules (e.g. "can't borrow unavailable book") live in one place — service layer
- Swapping PostgreSQL for another DB only requires changing repository layer
- Adding a CLI or background job reuses service layer without touching routes
- Easy to test each layer in isolation

### Alternatives Considered
Clean/Hexagonal Architecture — rejected because
it adds unnecessary abstraction (ports/adapters)
for a system of this scale. Layered gives the
same separation of concerns with less ceremony.

Flat structure (all logic in routes) — rejected
because business logic becomes untestable and
duplicated when adding new delivery mechanisms.

---

## 2. Framework — FastAPI over Django/Flask

### Decision
FastAPI with Python 3.11.15

### Why
FastAPI generates OpenAPI/Swagger documentation
automatically — zero extra work for a fully
interactive API explorer at /docs.
Pydantic v2 integration means request validation
is automatic and type-safe.
Async-first design matches our async SQLAlchemy
setup perfectly.
Python 3.11 is the most stable version with full
compatibility across our entire dependency stack.

### Alternatives Considered
Django REST Framework — mature but heavier.
Brings an ORM, admin panel, and auth system
we don't need. FastAPI is more appropriate
for a focused API-only service.

Flask — too minimal. Validation, serialization,
and docs would all need separate libraries
and manual wiring.

---

## 3. Database — PostgreSQL with Async SQLAlchemy

### Decision
PostgreSQL 15 with SQLAlchemy async + asyncpg driver

### Why
PostgreSQL is the most feature-complete open
source relational database. We use:
- UUID primary keys (native support)
- CheckConstraints (copies_available >= 0)
- ILIKE for case-insensitive search
- DATE_TRUNC for monthly analytics grouping
- Timezone-aware DateTime columns

Async SQLAlchemy with asyncpg means database
calls never block the event loop — the server
can handle other requests while waiting for DB.

### Alternatives Considered
MySQL — lacks some PostgreSQL features we use
(e.g. ILIKE, better JSON support).

Synchronous SQLAlchemy — simpler but blocks
the event loop on every DB call. Wrong choice
with FastAPI which is async-first.

SQLite — not suitable for production, no
concurrent write support.

---

## 4. Database Schema Design

### Decision
Four core tables: staff, books, members, 
lending_records with UUID primary keys and
proper foreign key relationships.

### Why

UUID primary keys:
Sequential integer IDs expose record counts
and are predictable — security concern.
UUIDs are opaque and safe to expose in URLs.

Separate tables per entity:
Normalization prevents data duplication.
Member contact info lives in members table only.
If email changes, one update propagates everywhere.

lending_records as junction table:
A lending record is its own entity — it has
its own attributes (borrowed_at, due_date,
returned_at, processed_by). A simple many-to-many
junction table would lose this information.

### Alternatives Considered
Integer primary keys — simpler but expose
business data (total record counts).

Embedding member info in lending_records —
rejected because it duplicates data and creates
update anomalies.

---

## 5. copies_available Counter Column

### Decision
Store copies_available as a column on books
table, decrement on borrow, increment on return.

### Why
The alternative is counting active lending
records every time:

  SELECT COUNT(*) FROM lending_records
  WHERE book_id = ? AND returned_at IS NULL

This is an O(n) query that gets slower as
lending history grows. With a counter column,
availability check is O(1) — just read one field.

We protect this with a database-level
CheckConstraint:
  copies_available >= 0
  
So even if application logic has a bug,
the database refuses to let copies go negative.

### Alternatives Considered
COUNT query approach — simpler code but
performance degrades with scale. Wrong tradeoff
for a frequently-checked field.

---

## 6. Soft Delete over Hard Delete

### Decision
is_active flag on books, members, and staff
instead of DELETE statements.

### Why
Hard deleting a book that has lending_records
would break foreign key constraints or leave
orphaned history records.

Hard deleting a member erases their entire
borrowing history — unacceptable for a library
that may need to reference past loans.

Soft delete preserves all history while hiding
records from normal operations. Restore is
trivial — flip is_active back to True.

The updated_at and updated_by columns already
tell us who deactivated the record and when —
no need for separate deactivated_at column.

### Alternatives Considered
Hard delete with cascade — destroys history.
Unacceptable for audit and reference purposes.

Separate archive tables — moves records to
archive_books, archive_members on delete.
More complex than a simple boolean flag with
no meaningful benefit at this scale.

---

## 7. Audit Trail — AuditMixin

### Decision
AuditMixin with created_at, updated_at,
created_by, updated_by, is_active applied
to all models via inheritance.

### Why
Every record change should be traceable to a
specific staff member. Without this, there is
no way to answer "who added this book?" or
"who processed this loan?".

Using a mixin means these columns are defined
once and inherited — no risk of forgetting them
on a new model, no code duplication.

### Why Staff Doesn't Use AuditMixin
Staff model has created_by and updated_by
pointing to the staff table itself — a
self-referencing foreign key. SQLAlchemy
relationship loading has edge cases with
self-referencing FKs combined with mixins.
Staff gets created_at and updated_at manually
without the FK audit columns to keep it clean.

### Alternatives Considered
Separate audit_log table with old/new values —
more powerful (full change history) but
significantly more complex. Appropriate for
banking or healthcare systems. Overkill here.

No audit trail — rejected immediately.
Any production system needs accountability.

---

## 8. Authentication — JWT + HttpOnly Cookie Proxy

### Decision
JWT (JSON Web Tokens) with python-jose
and bcrypt password hashing, delivered to
the browser via HttpOnly cookie through
Next.js route handlers.

### Why
JWT is stateless — the server stores nothing.
Every request carries its own proof of identity
in the token. This means:
- No session table in the database
- No Redis needed for session storage
- Horizontal scaling works without sticky sessions
- Simple to implement and reason about

On the frontend we do not expose tokens to
browser JavaScript. Login route stores token
in an HttpOnly cookie, and Next.js proxy route
reads that cookie server-side and forwards
Authorization: Bearer headers to FastAPI.
This reduces token theft risk from XSS compared
to localStorage/sessionStorage token storage.

### Tradeoff Acknowledged
JWT tokens cannot be invalidated before expiry.
If a staff member is deactivated, their token
remains valid until expiry (60 minutes by default,
configurable via ACCESS_TOKEN_EXPIRE_MINUTES).
For a library system this is an acceptable tradeoff.
In a higher-security system we would maintain a
token blacklist in Redis.

### Alternatives Considered
Database sessions — requires session table,
adds DB query on every request just for auth.

OAuth2 / third-party auth — overkill for an
internal staff tool. Adds external dependency.

---

## 9. Custom Exception Classes

### Decision
Custom exception classes (BookNotFoundException,
AlreadyBorrowedException, etc.) over raw
HTTPException throughout the service layer.

### Why
Raw HTTPException scattered across service files:
- Inconsistent messages (typos, different wording)
- Change a message = hunt through every file
- No self-documentation of what can go wrong

Custom exceptions:
- Single source of truth for every error message
- Change once, fixed everywhere
- Service method signatures implicitly document
  what can go wrong (readable like a contract)
- Zero performance impact — only instantiated
  on the unhappy path

### Performance Concern (Anticipated)
Exceptions are only instantiated when something
goes wrong — the unhappy path. The happy path
(successful requests) never touches them.
Instantiating a small Python class is nanoseconds.
This is not a performance consideration.

### Alternatives Considered
Raw HTTPException inline — simpler but leads to
inconsistent messages and harder maintenance.

Return error objects instead of raising — 
breaks FastAPI's exception handling flow and
requires callers to check return values.

---

## 10. Timezone Strategy — UTC Storage, Local Serving

### Decision
All datetimes stored as UTC in PostgreSQL.
Converted to configured local timezone
(APP_TIMEZONE) in Pydantic response schemas.
Frontend receives ISO 8601 strings with
timezone offset included.

### Why
Storing local time in a database is a known
anti-pattern. If the library moves timezone,
or staff access from different locations,
local time data becomes ambiguous or wrong.
UTC is unambiguous — one moment in time,
globally consistent.

Conversion at the schema layer means:
- Every response is automatically converted
- No route or service needs to think about it
- Change APP_TIMEZONE in .env = done, no code change

Frontend receives "2026-05-24T15:30:00+05:30"
The +05:30 offset tells the browser exactly
what time it is — no client-side conversion needed.

### Alternatives Considered
Store local time — common mistake. Breaks on
timezone changes and multi-location access.

Convert in routes — inconsistent, easy to forget
on new endpoints.

Convert on frontend — frontend has to know
the server timezone. Tight coupling.

---

## 11. Repository Pattern

### Decision
Separate repository classes for each entity
with only database query methods.
No business logic in repositories.

### Why
Repositories are the only place that knows
about SQLAlchemy. If we ever change the ORM
or database, only repository files change.

Services never write raw queries — they call
repository methods. This means:
- Business logic is testable without a database
  (mock the repository)
- Database queries are findable in one place
- No SQL scattered across business logic

### Alternatives Considered
Active Record pattern (model knows how to
save itself) — couples business logic to
database library. Django uses this. It works
but makes testing harder.

No repository layer (services query directly) —
mixes concerns, harder to maintain.

---

## 12. Pydantic Schemas — Separate from Models

### Decision
Separate Pydantic schemas for every operation
(BookCreate, BookUpdate, BookResponse) distinct
from SQLAlchemy models.

### Why
SQLAlchemy models represent database tables.
Pydantic schemas represent API contracts.
They are different things with different jobs.

BookCreate doesn't have id, created_at, copies_available
— those are set by the server, not the client.
BookUpdate has all fields optional — different
from BookCreate where title and author are required.
BookResponse includes computed fields (is_overdue,
created_by name) that don't exist as columns.

Merging these would require compromises that
weaken both the database model and the API contract.

---

## 13. Seeder — Idempotent Startup

### Decision
Database seeders run on every app startup.
Check before inserting — never duplicate.

### Why
Without a seeder, a developer cloning the repo
has no way to log in — no admin account exists.
They'd have to manually insert into the database.
This is undocumented, error-prone, and unfriendly.

Idempotent design means the seeder is safe
to run on every restart. It checks if the
admin email exists before creating. Restarting
the app 100 times creates exactly one admin.

Sample books seeder pre-populates 10 realistic
books so the app is immediately usable for
testing without manual data entry.

### Alternatives Considered
SQL init scripts in Docker — runs once on
container creation. Doesn't work if container
is recreated. Less flexible than Python code.

Manual DB insert instructions in README —
error-prone, easy to miss, bad developer experience.

---

## 14. copies_available in Borrow Modal Dropdown

### Decision
Only show books with copies_available > 0
in the borrow modal dropdown. Filter inactive
books out too.

### Why
Defense in depth. The backend enforces this
rule and returns 400 if violated. But showing
unavailable books in the dropdown just to
reject them at submission is poor UX.

Staff should only see books they can actually
borrow. Filtering at the UI level prevents
the round trip of selecting, submitting,
and seeing an error for something that was
never going to work.

---

## 15. Barcode/QR Scanning

### Decision
@zxing/browser for in-browser barcode and
QR code scanning without native app.

### Why
Most books already have ISBN-13 barcodes
on the back cover. Scanning eliminates manual
typing which is slow and error-prone.
@zxing/browser handles both barcodes and QR
codes in one library, works in all modern
browsers, and requires no backend changes —
the scanned ISBN is just used to look up
the book via existing GET /books/isbn/{isbn}.

Manual input is always available as fallback —
if camera is denied or unavailable, staff can
still type the ISBN or select from dropdown.
The scanning feature enhances but never
replaces manual workflows.

---

## 16. Analytics — Single Summary Endpoint

### Decision
GET /analytics/summary returns all dashboard
stats (books, members, loans, overdue) in one
call instead of four separate requests.

### Why
Dashboard loads four stat cards simultaneously.
Four separate API calls means four round trips
to the server, four database queries, and the
dashboard only fully renders when the last one
completes. A single endpoint runs all counts
in one database round trip and returns together.

Dashboard load time is effectively the slowest
of four calls vs just one call. Meaningful
difference on slower connections.

---

## 17. Lending History — Server-side Filtering

### Decision
All filtering, sorting, and pagination for
lending history happens on the server via
query parameters. Frontend sends filter state
as query params, backend builds dynamic query.

### Why
Fetching all lending records and filtering
on the frontend is not viable — a busy library
could have thousands of records. Sending all
of them to the browser wastes bandwidth and
makes the UI slow.

Server-side filtering with pagination means
only the records the user is actually viewing
are transferred. The database does what databases
are optimized for — filtering and sorting
large datasets efficiently.

---

## 18. Shelf Location — Text Field over Table

### Decision
shelf_location as a simple text field on books
(e.g. "Section A - Shelf 3") rather than a
separate locations table with foreign key.

### Why
A locations table would require:
- New model, migration, repository, service, routes
- Frontend location management page
- Dropdown in book form instead of text input

For a small neighborhood library with a handful
of sections, this is significant overhead for
minimal benefit. A text field is flexible —
staff enter whatever format makes sense for
their physical library layout.

If the library grows and needs structured
location management, migrating from text to
a FK relationship is straightforward.

### Supports Scanning
Shelf location supports both manual text entry
and barcode/QR scanning using the same scanner
component as ISBN. If the library prints location
QR codes on shelves, staff scan to fill the field —
eliminating typos in location names.

---

## 19. Docker — One Command Setup

### Decision
docker-compose.yml that starts PostgreSQL,
backend, and frontend together with one command.

### Why
"Works on my machine" is the most common
failure mode of developer handoffs.
Docker Compose guarantees identical environment
on any machine with Docker Desktop installed.

The postgres service has a healthcheck.
Backend depends_on postgres with
condition: service_healthy — so migrations
never run against a postgres that isn't ready.
This ordering is explicit in the compose file,
not hoped for via sleep timers.

Logs volume is mounted outside the container
so logs persist across container restarts.

---

## 20. API Versioning — /api/v1

### Decision
All endpoints prefixed with /api/v1.

### Why
API versioning from day one costs nothing
and prevents painful migrations later.
If a breaking change is needed, /api/v2
endpoints can be added alongside /api/v1
without breaking existing clients.

Without versioning, any breaking change
requires all clients to update simultaneously —
impossible in practice.

---

## Summary Table

| Decision | Chosen | Key Reason |
|---|---|---|
| Architecture | Layered N-Tier | Separation of concerns |
| Framework | FastAPI | Auto docs, async, Pydantic |
| Database | PostgreSQL async | Feature-rich, type-safe |
| Primary Keys | UUID | Security, opacity |
| Availability | Counter column | O(1) vs O(n) count query |
| Delete strategy | Soft delete | Preserve history |
| Audit trail | AuditMixin | Accountability, DRY |
| Auth | JWT + HttpOnly proxy cookie | Stateless auth with reduced token exposure |
| Errors | Custom exceptions | Consistency, maintainability |
| Timezone | UTC store, local serve | Correctness, flexibility |
| Seeder | Idempotent startup | Developer experience |
| Location | Text field | Right size for problem |
| Scanning | @zxing/browser | No native app needed |
| Analytics | Single endpoint | Fewer round trips |
| History | Server-side filter | Scale, performance |
| Versioning | /api/v1 prefix | Future-proof |
