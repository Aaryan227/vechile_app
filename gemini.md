Gemini / Antigravity Project Instructions

Vehicle & Logistics Management Application

Source of truth: the provided APK defines the current application
flow/UI, while the tanker daily report screenshot/Excel structure
defines the tanker-report data model. Do not invent roles or business
entities that are not part of the requirements.

1. Project Understanding

Build a production-ready backend for a single-business vehicle and
logistics management application.

The application manages:

Admin users

Drivers

Logistics vehicles

Vehicle information

Vehicle documents

Tanker daily reports

Driver/vehicle-related records

Document expiry and operational reporting

There are only two application roles:

ADMIN
DRIVER

There is NO MASTER ROLE.

There is NO multi-tenant/business switching requirement.

Do not add MASTER, BUSINESS, TENANT, or business_id concepts
unless the company later explicitly requests them.

2. APK-Based Application Flow

The provided APK shows the following major areas:

Splash
  ↓
Login / Register
  ↓
Role-based application
  ├── Admin
  └── Driver

Observed screens/modules include:

Splash

Login

Registration

Home

Profile

Admin

Driver

Driver Detail

Vehicle-related screens

Vehicle Documents

Document Form

Tanker Daily Report

Tanker Entry

Reports

The backend should support this flow without coupling business logic to
individual UI screens.

3. Main Business Model

Use this simplified relationship:

USER
 ├── ADMIN
 └── DRIVER
       |
       └── VEHICLE
             |
             └── DOCUMENTS

VEHICLE
   |
   └── TANKER DAILY REPORT ENTRIES

The exact driver-to-vehicle relationship must follow the company's
operational rules.

If a vehicle can be reassigned between drivers, use a separate
assignment/history table instead of permanently storing only one driver.

4. Recommended Backend Stack

Use:

FastAPI

PostgreSQL

SQLAlchemy

Alembic

Pydantic

JWT authentication

Argon2 or bcrypt for password hashing

Object/file storage for uploaded documents

Do not use SQLite for the production deployment unless the company
explicitly requests it.

5. Backend Structure

Recommended:

app/
├── main.py
├── core/
│   ├── config.py
│   ├── security.py
│   ├── dependencies.py
│   └── exceptions.py
│
├── db/
│   ├── session.py
│   ├── base.py
│   └── models/
│       ├── user.py
│       ├── vehicle.py
│       ├── vehicle_assignment.py
│       ├── document.py
│       ├── tanker_report.py
│       └── audit_log.py
│
├── schemas/
│   ├── auth.py
│   ├── user.py
│   ├── vehicle.py
│   ├── document.py
│   ├── tanker_report.py
│   └── report.py
│
├── routers/
│   ├── auth.py
│   ├── users.py
│   ├── vehicles.py
│   ├── documents.py
│   ├── tanker_reports.py
│   ├── admin.py
│   └── reports.py
│
├── services/
│   ├── auth_service.py
│   ├── user_service.py
│   ├── vehicle_service.py
│   ├── document_service.py
│   ├── tanker_report_service.py
│   └── report_service.py
│
└── utils/
    ├── file_validation.py
    └── pagination.py

Do not put all routes/business logic in main.py.

6. User Roles

Only:

class UserRole(str, Enum):
    ADMIN = "admin"
    DRIVER = "driver"

ADMIN

Admin has full application access:

Users/drivers

Vehicles

Vehicle documents

Driver assignments

Tanker reports

Reports

Profile

Administrative actions

DRIVER

Driver access should be restricted to records/actions permitted for the
driver.

At minimum:

Own profile

Assigned vehicle(s)

Vehicle details permitted to the driver

Vehicle document uploads

Vehicle document viewing

Required operational entries

Never trust the frontend role.

All authorization must be enforced by FastAPI.

7. Authentication Routes

Use:

POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
POST /api/v1/auth/change-password
POST /api/v1/auth/logout

Public registration must never allow:

{
  "role": "admin"
}

from an untrusted client.

Admin creation should be controlled by an existing admin or an initial
deployment/bootstrap mechanism.

8. Authentication Security

Use:

Password
   ↓
Hash
   ↓
Database

Never store plaintext passwords.

JWT access token should contain at least:

{
  "sub": "user-id",
  "role": "driver"
}

Create reusable dependencies:

get_current_user()
get_current_admin()
get_current_driver()

Use get_current_admin() for admin-only routes.

Use get_current_driver() for driver-only routes.

9. User Model

Recommended:

users
-----
id
name
email
phone
password_hash
role
is_active
created_at
updated_at
last_login_at

Do not expose password_hash through Pydantic response models.

Add appropriate unique constraints to email/phone according to the
company's requirements.

10. Vehicle Model

The APK indicates vehicle-related information such as:

Vehicle number

Vehicle class

Chassis number

Engine / Motor number

Recommended:

vehicles
--------
id
vehicle_number
vehicle_class
make
model
manufacture_year
chassis_number
engine_number
status
created_at
updated_at

Do not invent fields unless required.

vehicle_number should be searchable and normally unique for this
single business.

11. Driver ↔ Vehicle Assignment

If a vehicle can have different drivers at different times, use:

vehicle_assignments
-------------------
id
vehicle_id
driver_id
assigned_from
assigned_to
is_active
created_at

This allows historical tracking.

Do not allow a driver to access a vehicle merely because they know its
ID.

Every vehicle query must verify authorization.

12. Vehicle Document Module

The APK contains a vehicle-document workflow and document upload form.

Document types may include:

RC
INSURANCE
PERMIT
FITNESS
PUC
OTHER

Keep the list configurable.

Recommended:

documents
---------
id
vehicle_id
document_type
document_number
issue_date
expiry_date
file_name
file_url
mime_type
file_size
uploaded_by
status
created_at
updated_at

The document file should not be stored directly inside the vehicle
table.

13. File Upload Security

Accept only configured document types such as:

PDF
JPG/JPEG
PNG

Validate:

MIME type

extension

file size

file content where practical

Never trust a user-provided path.

Generate storage names on the server.

Never expose private storage credentials.

Use authenticated download endpoints or signed URLs.

14. Document Expiry

Document status should be based on the expiry date.

Possible states:

VALID
EXPIRING_SOON
EXPIRED

Provide:

GET /api/v1/documents/expired
GET /api/v1/documents/expiring-soon

Admin dashboard should be able to show:

Total Vehicles
Total Drivers
Expired Documents
Documents Expiring Soon

15. Tanker Daily Report

The supplied tanker report screenshot is a monthly tanker tracker
spreadsheet.

Visible title/context:

TANKER DAILY REPORT
Kings Petroleum
Monthly Tanker Tracker

The visible spreadsheet structure contains columns including:

Sl no
Date
U/L point
RTKM
Rate
Freight
Pump
HSD Ltr
HSD Rate
HSD Amt
Khuraki

The screenshot also shows rate/reference information near the top,
including:

12/14 Kl
3.559476 Per KM ...
FDZ
182.733368 Per KL
1611

The exact formulas/business meanings of these reference values must be
confirmed with the company before hard-coding them.

16. Tanker Report Data Model

Do not model the entire Excel sheet as one giant database row.

Use a normalized monthly/report-entry structure.

Recommended:

tanker_reports
--------------
id
report_date
vehicle_id
driver_id
ul_point
rtkm
rate
freight
pump
hsd_ltr
hsd_rate
hsd_amount
khuraki
created_by
created_at
updated_at

If the business confirms that a report is grouped into months,
optionally add a monthly report/header model:

tanker_monthly_reports
----------------------
id
year
month
created_at
updated_at

and connect daily entries to it.

Do not introduce fields for calculations that have not been confirmed.

17. Tanker Report Calculations

The screenshot contains numeric relationships such as:

RTKM
Rate
Freight

HSD Ltr
HSD Rate
HSD Amt

For example, HSD amount appears to correspond to:

HSD Ltr × HSD Rate

Do not blindly hard-code spreadsheet formulas into the backend until the
company confirms the intended formula and rounding rules.

Important questions to confirm:

Is Freight = RTKM × Rate?

What does RTKM mean exactly?

Is the rate fixed or configurable?

How is HSD Rate selected?

Is HSD Amount always HSD Ltr × HSD Rate?

What does Khuraki represent?

What is FDZ?

What do 12/14 KL and 1611 represent?

Are there different rates based on U/L point or vehicle class?

Should zero-entry rows be stored?

Once confirmed, put these calculations in a service layer, not in the
router.

18. Tanker Report API

Recommended:

POST   /api/v1/tanker-reports
GET    /api/v1/tanker-reports
GET    /api/v1/tanker-reports/{id}
PATCH  /api/v1/tanker-reports/{id}
DELETE /api/v1/tanker-reports/{id}

Filtering:

GET /api/v1/tanker-reports?month=4&year=2025
GET /api/v1/tanker-reports?vehicle_id=...
GET /api/v1/tanker-reports?date_from=...&date_to=...
GET /api/v1/tanker-reports?ul_point=...

Admin can view/manage all records.

Driver can only access records permitted by the business rules.

19. Excel-Compatible Reporting

Because the existing business process uses a spreadsheet, the backend
should eventually support exporting tanker data in an Excel-compatible
structure.

Suggested endpoint:

GET /api/v1/tanker-reports/export?month=4&year=2025

The export should preserve the business column order:

Sl no
Date
U/L point
RTKM
Rate
Freight
Pump
HSD Ltr
HSD Rate
HSD Amt
Khuraki

Do not change the column meanings without business confirmation.

20. Admin Routes

Recommended:

GET    /api/v1/admin/dashboard

GET    /api/v1/admin/drivers
GET    /api/v1/admin/drivers/{id}
POST   /api/v1/admin/drivers
PATCH  /api/v1/admin/drivers/{id}
DELETE /api/v1/admin/drivers/{id}

GET    /api/v1/admin/vehicles
POST   /api/v1/admin/vehicles
PATCH  /api/v1/admin/vehicles/{id}
DELETE /api/v1/admin/vehicles/{id}

GET    /api/v1/admin/documents
GET    /api/v1/admin/tanker-reports

Every admin route must enforce admin authorization.

21. Driver Routes

Recommended:

GET   /api/v1/driver/profile
PATCH /api/v1/driver/profile

GET   /api/v1/driver/vehicles
GET   /api/v1/driver/vehicles/{vehicle_id}

GET   /api/v1/driver/vehicles/{vehicle_id}/documents
POST  /api/v1/driver/vehicles/{vehicle_id}/documents

GET   /api/v1/driver/tanker-reports
POST  /api/v1/driver/tanker-reports

Exact driver permissions must follow company requirements.

22. API Design

Use:

/api/v1

REST naming

Pydantic schemas

SQLAlchemy

Alembic

pagination

filtering/search

consistent HTTP status codes

structured errors

OpenAPI documentation

UTC timestamps

Use:

400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
413 Payload Too Large
422 Validation Error
500 Internal Server Error

Never return stack traces to the client.

23. Audit Logs

Important actions should be recorded:

LOGIN
CREATE
UPDATE
DELETE
UPLOAD_DOCUMENT
DELETE_DOCUMENT
ASSIGN_VEHICLE
UNASSIGN_VEHICLE
CREATE_TANKER_REPORT
UPDATE_TANKER_REPORT
DELETE_TANKER_REPORT

Recommended:

audit_logs
----------
id
user_id
action
entity_type
entity_id
metadata
created_at

Never log passwords, JWT secrets, or sensitive authentication
credentials.

24. Development Rules for Antigravity

Before changing code:

Inspect the existing repository.

Identify existing architecture and dependencies.

Reuse existing abstractions.

Do not duplicate authentication logic.

Do not create a second database/session implementation.

Do not add a Master role.

Do not add multi-tenancy.

Do not add business_id.

Do not invent tanker-report formulas.

Add Alembic migrations for schema changes.

Add tests for important behavior.

Do not rewrite unrelated modules.

25. First Prompt for Antigravity

Read gemini.md and brandguidelines.md completely before changing
the project.

The application has exactly two roles: ADMIN and DRIVER.

This is a single-business application. Do not implement multi-tenancy
or a Master role.

The APK is the UI/workflow reference.

The tanker-report screenshot is the spreadsheet/data reference.

First inspect the repository and produce:

Current project architecture

Existing authentication implementation

Existing database models

Existing API routes

Missing entities

Missing relationships

Required migrations

Tanker report implementation plan

Potential conflicts with the reference APK

Questions requiring business clarification

Do not make major changes until this analysis is complete.

26. Authentication Implementation Prompt

Implement authentication according to gemini.md.

Roles: - ADMIN - DRIVER

Implement:

password hashing

JWT access tokens

refresh token architecture if required

login

registration

current-user endpoint

password change

role-based FastAPI dependencies

Public registration must never create an ADMIN.

Add schemas, service logic, migration, tests, and routes.

Do not modify unrelated modules.

27. Vehicle and Document Prompt

Implement the vehicle and vehicle-document modules according to
gemini.md.

Implement:

vehicle CRUD

driver assignment

assignment history if required

document metadata

secure PDF/image uploads

document access control

document expiry status

A driver must never access another driver's restricted
vehicle/document by changing an ID in the URL.

Add migration, schemas, services, routes, validation, and tests.

28. Tanker Report Prompt

Implement the Tanker Daily Report module according to gemini.md.

The existing business reference is a monthly tanker tracker
spreadsheet.

Initial fields:

Date

U/L point

RTKM

Rate

Freight

Pump

HSD Ltr

HSD Rate

HSD Amt

Khuraki

Do not hard-code calculation formulas until the business rules are
confirmed.

Provide CRUD, filtering by month/date/vehicle/U-L point,
authorization, validation, and Excel-compatible export.

Keep calculation logic inside a service layer.

29. Quality Gate

Before marking a feature complete:

[ ] ADMIN authentication works
[ ] DRIVER authentication works
[ ] ADMIN authorization is enforced
[ ] DRIVER authorization is enforced
[ ] No MASTER role exists
[ ] No multi-tenancy exists
[ ] No business_id exists
[ ] Passwords are hashed
[ ] Secrets are environment variables
[ ] Migrations exist
[ ] File uploads are validated
[ ] Vehicle access is permission-checked
[ ] Document access is permission-checked
[ ] Tanker report validation exists
[ ] Tanker calculations are not invented
[ ] Tests cover important paths
[ ] OpenAPI documentation works
[ ] No unrelated code was changed

30. Final Principle

Build around the real business domain, not just the screens.

The current domain is:

Single Business
     |
     +-- Admin
     |
     +-- Drivers
     |
     +-- Vehicles
     |      |
     |      +-- Documents
     |
     +-- Tanker Daily Reports
     |
     +-- Operational Reports

Keep the architecture simple, secure, maintainable, and extensible
without adding unnecessary abstractions.