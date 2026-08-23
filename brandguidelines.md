Brand Guidelines

Vehicle & Logistics Management Application

The provided APK is the visual and interaction reference. These
guidelines are for Gemini/Antigravity when implementing or modifying
the UI.

1. Product Identity

This is a professional vehicle and logistics management application
for a single business.

The product should communicate:

Reliability

Operational clarity

Safety

Professional fleet management

Efficient data entry

Easy document management

Clear reporting

Avoid:

gaming-style UI

social-media patterns

excessive gradients

decorative dashboards

unnecessary animations

excessive visual effects

2. Application Roles

There are exactly two roles:

ADMIN
DRIVER

There is no Master role.

UI must never create or display Master-specific navigation.

Admin and Driver should share the same visual language but expose
different actions.

3. APK Reference Flow

Observed application areas include:

Splash
  ↓
Login / Registration
  ↓
Role-based Home
  ├── Admin
  └── Driver

Observed screens include:

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

Preserve this information hierarchy when connecting the UI to the
FastAPI backend.

4. Visual Personality

Use:

Clean + Professional + Operational + Trustworthy

The interface should prioritize:

Clarity
   >
Fast task completion
   >
Operational information
   >
Decoration

5. Navigation

Use role-aware navigation.

Example:

ADMIN
Home | Vehicles | Reports | Profile

DRIVER
Home | Vehicles | Documents | Profile

The exact navigation must follow the existing APK and approved product
requirements.

Do not display an admin action simply because the frontend route exists.
The backend remains the source of truth for permissions.

6. Typography

Use a clean modern sans-serif font.

Suggested hierarchy:

Page title:       24–28 px
Section heading:  18–20 px
Card title:       16–18 px
Body:             14–16 px
Helper text:      12–14 px
Button:           14–16 px

Use font weight primarily to establish hierarchy.

Do not overuse bold text.

7. Color System

Use a restrained enterprise palette.

Centralize colors in the application's theme.

Use semantic tokens:

primary
onPrimary
primaryContainer
onPrimaryContainer

secondary
surface
surfaceContainer
surfaceContainerHigh
onSurface
onSurfaceVariant

error
success
warning
info

Do not scatter hard-coded colors across individual components.

Do not introduce random gradients.

8. Status System

Statuses must be understandable through text/icons as well as color.

VALID          → success
ACTIVE         → success
EXPIRING_SOON  → warning
PENDING        → warning
EXPIRED        → error
FAILED         → error
INACTIVE       → error/info
UPLOADED       → info

Example:

⚠ Insurance
  Expiring Soon

Do not use only an orange/green/red dot with no label.

9. Admin Dashboard

The admin dashboard should focus on operational information.

Recommended hierarchy:

Admin Overview
      ↓
Key metrics
      ↓
Document alerts
      ↓
Vehicle / Driver information
      ↓
Recent activity

Possible metrics:

Total Vehicles
Active Vehicles
Total Drivers
Expired Documents
Documents Expiring Soon

Do not add charts just for decoration.

10. Driver Experience

The Driver experience should be task-focused.

Prioritize:

Assigned vehicle

Vehicle details

Required documents

Document upload

Expiring/expired documents

Profile

Avoid exposing admin controls.

11. Vehicle UI

The vehicle number should be the primary identifier.

Example:

MH12AB1234
Truck

Driver
Rahul Kumar

Documents
8 Total
1 Expiring Soon

Keep cards concise.

Detailed vehicle information belongs on the vehicle-detail screen.

Vehicle fields may include:

Vehicle Number
Vehicle Class
Chassis Number
Engine / Motor Number

Do not add unexplained fields.

12. Vehicle Documents

The APK contains a dedicated document-management workflow.

The document UI should clearly expose:

Document Type
Document Number
Issue Date
Expiry Date
File

Possible document categories:

RC
Insurance
Permit
Fitness
PUC
Other

The exact list should remain configurable.

13. Upload UI

The upload flow should clearly indicate:

Upload Document

PDF / JPG / PNG
Maximum size: configured limit

[ Choose File ]

After upload:

insurance.pdf

Uploaded successfully

[ View ] [ Replace ]

Show upload progress when the file is large.

Disable repeated submissions while an upload is in progress.

14. Forms

Use consistent form fields.

Example:

Vehicle Number *
[________________]

Vehicle Class *
[ Select ]

Chassis No.
[________________]

Engine / Motor No.
[________________]

Rules:

Clear labels

Required indicator

Inline validation

Helpful errors

Date pickers for dates

Dropdowns for fixed categories

File picker for documents

Preserve entered values when validation fails

15. Tanker Daily Report

The provided Excel/screenshot is the reference for the tanker-report
workflow.

The report is titled:

TANKER DAILY REPORT

and is associated with:

Kings Petroleum
Monthly Tanker Tracker

The visible spreadsheet columns are:

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

The screen should present these fields in a way that is easy to enter
and review.

16. Tanker Report UI

Do not attempt to display the raw Excel grid exactly on a small phone
screen.

For mobile, prefer:

Tanker Daily Report

Date
[ 04/04/2025 ]

U/L Point
[ Pakuria KSK ]

RTKM
[ 265.6 ]

Rate
[ 3.559476 ]

Freight
[ 11344.77 ]

Pump
[ Pakuria KSK ]

HSD Ltr
[ 0 ]

HSD Rate
[ 0 ]

HSD Amount
[ 0 ]

Khuraki
[ ... ]

[ Save Entry ]

For report history, use compact cards or a horizontally scrollable table
depending on the target device.

17. Monthly Tanker Report

The reference spreadsheet is organized as a monthly tracker.

Provide filtering such as:

Month
Year
Date range
Vehicle
U/L Point

A report list should make it easy to identify:

Date

U/L point

Vehicle/related identifier

Freight

HSD

Amounts

Do not hide important operational numbers behind multiple screens.

18. Calculated Values

The spreadsheet contains:

RTKM
Rate
Freight

HSD Ltr
HSD Rate
HSD Amt

The UI may display calculated values as read-only if the backend defines
the formula.

Do not assume or display formulas that have not been confirmed by the
business.

If a value is calculated by the backend:

Rate
[ 3.559476 ]

Freight
[ Calculated ]

Make calculated/read-only values visually distinguishable from
user-entered values.

19. Empty States

Use helpful empty states.

Example:

No vehicles yet

Add a vehicle to start managing
documents and reports.

[ Add Vehicle ]

For tanker reports:

No tanker entries for this month.

[ Add Entry ]

20. Loading States

Use:

skeletons for major content

progress indicators for uploads

disabled buttons during submission

Never leave users uncertain about whether an action succeeded.

21. Errors

Errors must be actionable.

Bad:

Error

Better:

Unable to upload the document.
Please check the file type and try again.

Never display FastAPI stack traces to users.

22. Confirmation

Destructive actions should require confirmation.

Example:

Delete document?

This action cannot be undone.

[ Cancel ] [ Delete ]

Use a clearly destructive style for Delete.

23. Accessibility

Maintain:

readable contrast

sufficiently large touch targets

clear labels

meaningful icons

text + icon for important statuses

no color-only information

visible focus/interaction states where supported

24. Responsive Design

Primary target:

Android mobile

If web/tablet support is added:

Mobile
  → cards / single-column forms

Tablet
  → two-column forms where useful

Desktop
  → sidebar + content / data tables

Do not simply stretch a mobile layout onto desktop.

25. Component Consistency

Create reusable components for:

AppBar
PrimaryButton
SecondaryButton
TextInput
Dropdown
DatePicker
VehicleCard
DocumentCard
StatusBadge
MetricCard
UploadCard
ConfirmationDialog
EmptyState
LoadingState

Do not create slightly different versions of the same component for
every screen.

26. UI Rules for Antigravity

Before changing UI:

Inspect the existing component/theme structure.

Reuse existing components.

Preserve the APK's overall flow.

Keep Admin and Driver experiences separate.

Do not add a Master section.

Keep the product professional and operational.

Do not introduce random colors.

Do not introduce random fonts.

Do not introduce excessive animations.

Do not redesign unrelated screens.

27. Prompt for UI Work

Read gemini.md and brandguidelines.md.

The APK is the visual and navigation reference.

The application has only ADMIN and DRIVER roles.

Do not create a Master role or Master navigation.

The tanker daily report screenshot is the data-entry/reporting
reference.

Before changing a screen, inspect its existing implementation and
preserve the established visual language.

Use centralized theme tokens and reusable components.

Make the tanker-report workflow optimized for mobile data entry while
keeping the monthly-report information structure recognizable.

Do not invent business calculations or fields.

If a requirement is ambiguous, flag it instead of guessing.

28. Product Principle

This is an operational logistics application.

Every design decision should make it easier to:

Manage vehicles
Manage documents
Track drivers
Enter tanker data
Review reports
Identify expired/expiring documents

The interface should remain simple, reliable, and fast.