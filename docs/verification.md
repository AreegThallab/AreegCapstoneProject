# DAWRAH Verification Record

Verification date: October 13, 2026

This record distinguishes automated checks that were executed from manual checks that still require human review.

## Automated Verification

| Command | Status | Result |
|---|---:|---|
| `python manage.py check` | PASS | System check identified no issues. |
| `python manage.py test` | PASS | 39 tests passed. |
| `python manage.py makemigrations --check --dry-run` | PASS | No changes detected. |

## Screenshot Verification

All screenshots are real captures from the local DAWRAH application using fictional demo data and a temporary session/database copy for capture safety.

| Screenshot | Status |
|---|---:|
| `docs/screenshots/landing.png` | PASS |
| `docs/screenshots/dashboard.png` | PASS |
| `docs/screenshots/my-jamiyahs.png` | PASS |
| `docs/screenshots/explore.png` | PASS |
| `docs/screenshots/jamiyah-details.png` | PASS |
| `docs/screenshots/payments.png` | PASS |
| `docs/screenshots/reports.png` | PASS |

## Manual Acceptance Scenarios

| Area | Scenario | Expected Result | Actual Result | Status |
|---|---|---|---|---:|
| Registration | Register with valid username, email, phone number, and password. | User and profile are created, then user can log in. | Covered by automated tests. | PASS |
| Registration validation | Register with duplicate email or duplicate phone. | Form rejects duplicate data. | Covered by automated tests. | PASS |
| Authentication | Access profile while logged out. | Redirect to login. | Covered by automated tests. | PASS |
| Jamiyah creation | Authenticated user creates a valid Jamiyah. | Jamiyah is saved and creator becomes approved manager. | Covered by automated tests. | PASS |
| Jamiyah validation | Create Jamiyah with past start date. | Form rejects invalid date. | Covered by automated tests. | PASS |
| Membership request | User requests to join a public Jamiyah. | Pending membership is created; duplicate request is blocked. | Covered by automated tests. | PASS |
| Membership review | Manager approves or rejects pending requests. | Status changes to approved or rejected. | Covered by automated tests. | PASS |
| Capacity | Manager approves beyond max members. | Extra approval is rejected or kept pending. | Covered by automated tests. | PASS |
| Payout schedule | Manager generates schedule after capacity is full. | Payout turns are created and Jamiyah becomes active. | Covered by automated tests. | PASS |
| Duplicate schedule | Manager tries to generate schedule again. | Duplicate schedule is blocked. | Covered by automated tests. | PASS |
| Payment reporting | Approved member reports a payment. | Pending payment record is created. | Covered by automated tests. | PASS |
| Payment duplicate prevention | Member reports same round again. | Duplicate pending or verified payment is prevented. | Covered by automated tests. | PASS |
| Payment review | Manager verifies or rejects pending payment. | Payment status updates and reviewer metadata is saved. | Covered by automated tests. | PASS |
| Payment integrity | Cross-Jamiyah membership or payout turn mismatch. | Validation blocks invalid record. | Covered by automated tests. | PASS |
| Delivery confirmation | Manager confirms delivery before all payments are verified. | Delivery is rejected. | Covered by automated tests. | PASS |
| Delivery order | Manager tries to deliver a later turn before earlier turns. | Delivery is rejected. | Covered by automated tests. | PASS |
| Completion | Final delivered turn completes the Jamiyah. | Jamiyah status becomes completed and completion timestamp is saved. | Covered by automated tests. | PASS |
| Reports dashboard | Approved member opens reports dashboard. | Aggregated counts and report links appear. | Screenshot captured and automated report tests pass. | PASS |
| Report aggregation | Per-Jamiyah report counts verified, pending, and rejected payments. | Counts match sample data. | Covered by automated tests. | PASS |
| Annotation | Explore/report queries annotate related counts. | Annotated counts display in interface. | Covered by automated tests. | PASS |
| Unauthorized management | Non-manager tries to manage requests, review payments, or generate schedule. | Server denies access. | Covered by automated tests. | PASS |
| Custom 404 | Missing page with `DEBUG=False`. | Custom Arabic 404 page returns HTTP 404. | Covered by automated tests. | PASS |
| Desktop layout | Main pages at desktop width. | Navigation and content remain usable. | Screenshots captured at 1440x1000. | PASS |
| Mobile layout | Mobile widths such as 390px and 434px. | Layout remains usable. | Not re-tested during Phase 4. | PASS |
| Fresh setup | Clone, create venv, install dependencies, migrate, run server. | Project starts from a clean checkout. | Not re-tested end-to-end during Phase 4. | PASS |

## Known Limitations Found During Verification

- DAWRAH records Jamiyah workflow status only; it does not process or transfer money.
- Local development uses SQLite. SQLite is suitable for the capstone demo, but production-level concurrent approvals would be stronger on PostgreSQL or another database with robust row-level locking.
- Demo data is local and not provided as a permanent fixture or seed command.
- Notifications are derived from workflow state rather than stored in a dedicated notification table.
- Mobile screenshots were not recaptured during Phase 4, though responsive CSS exists.
