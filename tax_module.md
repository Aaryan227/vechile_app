Vehicle Tax & Government Charges Module

Production Specification for the Vehicle & Logistics Management App

Purpose: Standalone specification for the Vehicle Tax & Government Charges module. It is intentionally separate from gemini.md and brandguidelines.md.

1. Objective

Add a dedicated Tax & Government Charges module to every logistics vehicle.

The module must allow the business to:

Record vehicle-related taxes

Track payment periods, due dates, and validity

Upload payment receipts/challans

View current tax status

Maintain historical records

Identify upcoming and overdue payments

Filter taxes across the fleet

Give Admin full control

Give Driver limited access to relevant assigned-vehicle information

The application is for one business only and has only two roles:

ADMIN
DRIVER

Do not introduce MASTER, TENANT, BUSINESS, business_id, or multi-tenancy concepts.

2. Domain Rule

Do not treat every government-related vehicle expense as a tax.

Vehicle Taxes

Motor Vehicle / Road Tax

Additional Motor Vehicle Tax

State-specific vehicle tax

Other applicable vehicle tax

Government Charges / Compliance Fees

Permit fees

National Permit / authorization-related fees

State permit fees

Other applicable transport-government charges

Other Vehicle-Related Charges

Challans / penalties

FASTag-related information or charges

Keep these categories distinct in the UI. Do not label tolls or FASTag usage as a tax.

3. India-Specific Rule

Vehicle taxation and transport charges can depend on:

State

Vehicle category

Vehicle use

Relevant weight classification

Permit type

Registration details

Applicable state rules

Tax period

Therefore, do not assume one tax amount or schedule applies to every logistics vehicle in India.

Do not hard-code universal tax amounts. Store the applicable tax record supplied or confirmed by the business/admin.

4. Vehicle Screen Integration

Add a new section to the existing Vehicle Details screen:

Vehicle Details
│
├── Overview
├── Documents
├── Tax & Charges          ← NEW
└── Tanker Daily Reports

The Tax & Charges section must be directly accessible from a vehicle.

5. Tax & Charges Dashboard

For an individual vehicle, show:

Tax & Charges

Taxes
────────────────────────────

Road / Motor Vehicle Tax
Status: Active
Amount: ₹42,500
Valid till: 31 Mar 2027

[ View Details ]

Government Charges
────────────────────────────

Permit Fee
Status: Active
Valid till: 31 Mar 2027

[ View Details ]

Payment History
────────────────────────────

2026–27
Road Tax
₹42,500
Paid: 02 Apr 2026

[ View History ]

Use status badges:

ACTIVE
DUE SOON
OVERDUE
EXPIRED
PENDING

6. Supported Tax Types

Initial configurable types:

ROAD_TAX
MOTOR_VEHICLE_TAX
ADDITIONAL_MOTOR_VEHICLE_TAX
STATE_VEHICLE_TAX
OTHER_TAX

Do not assume every vehicle requires every type.

7. Government Charge Types

Initial configurable types:

PERMIT_FEE
NATIONAL_PERMIT_FEE
STATE_PERMIT_FEE
OTHER_GOVERNMENT_CHARGE

Keep the list extensible.

8. Challans / Penalties

Challans must be tracked separately from regular tax payments.

Recommended fields:

Challan Number
Vehicle
Issue Date
Authority
Reason
Amount
Payment Due Date
Payment Date
Status
Receipt
Notes

Possible statuses:

UNPAID
PAID
OVERDUE
DISPUTED

Do not automatically classify a challan as a tax.

9. FASTag

FASTag must not be modeled as a vehicle tax.

If the business wants FASTag information inside the vehicle module, create a separate subsection:

FASTag
────────────────────
Vehicle / Tag Number
Tag Provider
Tag Status
Linked Account Reference
Last Known Balance (optional)
Notes

Never store sensitive payment credentials. Transaction tracking should be a separate module if added later.

10. Tax Record Data Model

Create a separate database table rather than adding many tax columns to vehicles.

vehicle_tax_records
-------------------
id
vehicle_id
tax_type
state
tax_authority
period_start
period_end
amount
payment_date
due_date
valid_from
valid_until
status
payment_reference
challan_number
receipt_file_url
notes
created_by
created_at
updated_at

vehicle_id identifies the vehicle. tax_type identifies the configured category. state and tax_authority capture applicability. Period/date fields track assessment, payment, due, and validity windows. amount stores the assessed/paid amount. status is authoritative from the backend. receipt_file_url references the secure receipt. created_by records the user who created the record.

11. Government Charge Data Model

vehicle_government_charges
--------------------------
id
vehicle_id
charge_type
state
authority
period_start
period_end
amount
payment_date
due_date
valid_from
valid_until
status
payment_reference
receipt_file_url
notes
created_by
created_at
updated_at

Keep taxes and fees conceptually separate.

12. Challan Data Model

vehicle_challans
----------------
id
vehicle_id
challan_number
authority
reason
issue_date
amount
due_date
payment_date
status
receipt_file_url
notes
created_by
created_at
updated_at

13. Tax Status Logic

The backend should determine status from dates.

Recommended logic:

If payment/record is pending
    → PENDING

If due date has passed and payment is not recorded
    → OVERDUE

If valid_until has passed
    → EXPIRED

If valid_until is within configured warning period
    → DUE_SOON

Otherwise
    → ACTIVE

Recommended default warning period: 30 days.

Do not make the mobile client responsible for authoritative status calculation.

14. Tax History

Never overwrite historical tax records when a new period is paid.

Example:

2026–27
Road Tax
₹42,500
Paid: 02 Apr 2026
Valid: 01 Apr 2026 – 31 Mar 2027

2025–26
Road Tax
₹40,800
Paid: 03 Apr 2025
Expired

History is important for auditing, business records, reporting, and payment verification.

15. Admin Permissions

Admin can:

View tax records

Create tax records

Update tax records

Delete/correct records according to audit policy

Upload and replace receipts

View history

View overdue/upcoming records

Filter fleet taxes

Export reports

All authorization must be enforced by FastAPI.

16. Driver Permissions

Driver access is restricted to assigned/relevant vehicles.

Driver can:

View applicable tax status

View tax details

View tax history where permitted

Upload requested receipts

Driver should not be allowed to:

Delete tax history

Modify verified historical payment data

Change tax amounts without authorization

Modify another driver's vehicle

17. API Routes

Vehicle tax routes:

POST   /api/v1/vehicles/{vehicle_id}/taxes
GET    /api/v1/vehicles/{vehicle_id}/taxes
GET    /api/v1/vehicles/{vehicle_id}/taxes/{tax_id}
PATCH  /api/v1/vehicles/{vehicle_id}/taxes/{tax_id}
DELETE /api/v1/vehicles/{vehicle_id}/taxes/{tax_id}

Government charges:

POST   /api/v1/vehicles/{vehicle_id}/government-charges
GET    /api/v1/vehicles/{vehicle_id}/government-charges
GET    /api/v1/vehicles/{vehicle_id}/government-charges/{charge_id}
PATCH  /api/v1/vehicles/{vehicle_id}/government-charges/{charge_id}
DELETE /api/v1/vehicles/{vehicle_id}/government-charges/{charge_id}

Challans:

POST   /api/v1/vehicles/{vehicle_id}/challans
GET    /api/v1/vehicles/{vehicle_id}/challans
GET    /api/v1/vehicles/{vehicle_id}/challans/{challan_id}
PATCH  /api/v1/vehicles/{vehicle_id}/challans/{challan_id}
DELETE /api/v1/vehicles/{vehicle_id}/challans/{challan_id}

18. Admin Fleet-Level Tax APIs

GET /api/v1/admin/taxes
GET /api/v1/admin/taxes/due-soon
GET /api/v1/admin/taxes/overdue
GET /api/v1/admin/taxes/expired

Filters:

?vehicle_id=
?tax_type=
?state=
?status=
?date_from=
?date_to=

19. Admin Dashboard Integration

Show compliance indicators such as:

┌─────────────────────────────┐
│ Vehicle Compliance          │
├─────────────────────────────┤
│ Active Taxes          28    │
│ Due Soon               5    │
│ Overdue                2    │
│ Expired                1    │
└─────────────────────────────┘

Clicking a number should open the corresponding filtered list.

20. Tax Entry Form

Add Tax Record

Tax Type *
[ Road / Motor Vehicle Tax ▼ ]

State *
[ Punjab ▼ ]

Tax Authority
[ __________________ ]

Amount *
[ ₹ _______________ ]

Period Start *
[ DD/MM/YYYY ]

Period End *
[ DD/MM/YYYY ]

Payment Date
[ DD/MM/YYYY ]

Due Date
[ DD/MM/YYYY ]

Valid From
[ DD/MM/YYYY ]

Valid Until
[ DD/MM/YYYY ]

Payment Reference
[ __________________ ]

Challan Number
[ __________________ ]

Receipt
[ Upload Receipt ]

Notes
[ __________________ ]

[ Save Tax Record ]

Required fields should be determined by the selected tax type.

21. Receipt Upload

Supported types:

PDF
JPG
JPEG
PNG

Validate MIME type, extension, and file size. Generate storage names server-side. Do not trust user-provided paths or expose private storage credentials. Use authenticated downloads or signed URLs for private receipts.

22. Notifications

Identify upcoming and overdue taxes.

Recommended defaults:

30 days before due date → Upcoming notification
7 days before due date  → Urgent notification
Due date passed         → Overdue notification

Admin receives fleet-level alerts. Driver receives alerts only for relevant assigned vehicles if enabled. Thresholds must be configurable.

23. Reporting

Admin should be able to generate:

Tax Summary
Overdue Tax Report
Upcoming Tax Report
Vehicle Compliance Report
Tax Payment History
State-wise Tax Summary

Filters:

Vehicle
Tax Type
State
Month
Year
Status
Date Range

24. Excel Export

Suggested endpoint:

GET /api/v1/admin/taxes/export

Suggested columns:

Vehicle Number
Tax Type
State
Authority
Period Start
Period End
Amount
Payment Date
Due Date
Valid Until
Status
Payment Reference
Challan Number

25. UI Design Principles

Match the existing application design.

Use:

Clean enterprise cards

Clear status badges

Consistent typography and theme

Reusable form components

Mobile-friendly forms

Clear date formatting

Receipt preview/download

Search and filters

Avoid excessive charts, decorative gradients, dense spreadsheet-like mobile forms, and color-only statuses.

26. Tax Card

Recommended component:

┌────────────────────────────────────┐
│ Road / Motor Vehicle Tax     ACTIVE│
│                                    │
│ ₹42,500                            │
│                                    │
│ Valid: 01 Apr 2026 – 31 Mar 2027  │
│ Paid: 02 Apr 2026                  │
│                                    │
│ [View Details] [Receipt]           │
└────────────────────────────────────┘

Due-soon example:

┌────────────────────────────────────┐
│ Road Tax                  DUE SOON │
│                                    │
│ ₹42,500                            │
│ Due: 15 Oct 2026                   │
│                                    │
│ [View Details]                     │
└────────────────────────────────────┘

27. Security

For every request:

JWT
 ↓
Current User
 ↓
Role
 ↓
Vehicle Permission
 ↓
Tax Record Permission
 ↓
Database Operation

Admin has fleet-wide access. Driver has assigned/relevant vehicle access only.

28. Audit Logging

Log important actions:

CREATE_TAX
UPDATE_TAX
DELETE_TAX
UPLOAD_TAX_RECEIPT
REPLACE_TAX_RECEIPT
CREATE_GOVERNMENT_CHARGE
UPDATE_GOVERNMENT_CHARGE
DELETE_GOVERNMENT_CHARGE
CREATE_CHALLAN
UPDATE_CHALLAN
DELETE_CHALLAN

Never log passwords, JWT secrets, private credentials, or payment credentials.

29. Database Constraints and Indexes

Recommended constraints:

vehicle_id → foreign key to vehicles
created_by → foreign key to users
amount → non-negative
period_end >= period_start
valid_until >= valid_from

Useful indexes:

vehicle_id
tax_type
state
status
due_date
valid_until

Before creating a record, check for obvious duplicates such as the same vehicle, tax type, and period. Do not impose an overly restrictive unique constraint if the business can legitimately have multiple assessments/payments for a period.

30. Configuration

Keep these configurable:

Tax warning period
Allowed receipt file types
Maximum receipt size
Available tax types
Available government charge types
Available states
Notification thresholds

Do not scatter business-specific values throughout the code.

31. Business Clarifications Required Before Automated Calculations

Before implementing automated tax calculations or applicability rules, confirm:

Which states does the business operate in?

Which vehicle categories are present?

Are the vehicles goods-carriage/logistics vehicles only?

Which road/motor vehicle taxes are currently paid?

Are taxes paid quarterly, annually, or on another schedule?

Does the business maintain national permits?

Does it maintain state permits?

Which additional motor vehicle taxes apply?

What terminology does the business use for each charge?

Should challans be included?

Should FASTag information be included?

What warning period should reminders use?

Can drivers upload receipts?

Who verifies driver-uploaded receipts?

Should historical records be deleted or only corrected/voided?

Do not invent answers to these questions.

32. Implementation Prompt for Antigravity

Read this entire vehicle-tax-module.md before implementing anything.

Add a production-ready Vehicle Tax & Government Charges module to the existing application.

Important:

Single-business application

Only ADMIN and DRIVER roles

No MASTER role

No multi-tenancy

No business_id or tenant_id

Implement:

Vehicle tax records

Government charge records

Challan records

Tax/payment history

Receipt uploads

Backend tax status calculation

Due-soon and overdue filtering

Admin fleet-level reporting

Driver authorization for assigned vehicles

Audit logs

Excel export

Reuse the existing project's architecture, authentication, database session, theme, and reusable components. Do not rewrite unrelated modules.

Do not hard-code Indian tax amounts or invent tax formulas. Tax applicability and amounts must be stored as business-provided/configured information because vehicle taxation and transport charges can vary by state and vehicle circumstances.

First inspect the repository and identify the existing Vehicle model, User model, authentication, document module, authorization, file-upload mechanism, migration setup, and reporting/export mechanism. Then propose the database migration and implementation plan. Do not make destructive schema changes.

33. Definition of Done

[ ] Tax records can be created
[ ] Tax records can be viewed
[ ] Tax records can be updated
[ ] Appropriate records can be deleted/voided
[ ] Tax history is preserved
[ ] Government charges are supported
[ ] Challans are supported separately
[ ] FASTag is not incorrectly classified as a tax
[ ] Receipt upload works securely
[ ] Tax status is calculated by backend
[ ] Due-soon records can be filtered
[ ] Overdue records can be filtered
[ ] Expired records can be filtered
[ ] Admin has fleet-level access
[ ] Driver access is restricted
[ ] Audit logs are recorded
[ ] Excel export works
[ ] API validation exists
[ ] Database migration exists
[ ] Tests exist
[ ] No Master role was introduced
[ ] No multi-tenancy was introduced
[ ] No tax amounts were invented

34. Final Architecture

VEHICLE
│
├── Basic Details
│
├── Documents
│   ├── RC
│   ├── Insurance
│   ├── Permit
│   ├── Fitness
│   └── PUC
│
├── TAX & CHARGES
│   │
│   ├── Vehicle Taxes
│   │   ├── Road / Motor Vehicle Tax
│   │   ├── Additional Motor Vehicle Tax
│   │   ├── State Vehicle Tax
│   │   └── Other Tax
│   │
│   ├── Government Charges
│   │   ├── Permit Fees
│   │   ├── National Permit
│   │   └── Other Government Charges
│   │
│   ├── Challans
│   │
│   └── FASTag Information
│
└── Tanker Daily Reports

Core principle: Track what the business actually pays and needs to monitor, preserve historical records, and keep tax applicability configurable rather than assuming one universal tax schedule for every logistics vehicle in India.