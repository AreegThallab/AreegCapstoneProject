# DAWRAH | Verification Record

**Project:** DAWRAH | دَوْرة  
**Verification Date:** October 13, 2026  
**Project Type:** Individual Django Capstone Project

## 1. Verification Overview

This document records the verification activities performed for DAWRAH, a Django-based platform for managing rotating savings associations (Jamiyahs).

The verification process focuses on application functionality, database integrity, authentication, authorization, user workflows, security configuration, interface usability, and reproducibility.

Verification activities are divided into:

- **Automated Verification:** Checks and tests executed using Django.
- **Screenshot and Documentation Verification:** Evidence captured and documented from the application.
- **Manual Acceptance Verification:** User-interface scenarios requiring direct human testing.
- **Known Limitations:** Current prototype boundaries and improvements planned before production deployment.

Results are reported according to the evidence available. Passing automated tests does not automatically mean every manual acceptance scenario has been verified.

---

## 2. Automated Verification

The following commands were executed locally on October 13, 2026.

| Command | Status | Actual Result |
|---|---|---|
| `python manage.py check` | PASS | System check identified no issues (0 silenced). |
| `python manage.py test` | PASS | All 72 discovered tests passed. |
| `python manage.py makemigrations --check --dry-run` | PASS | No changes detected. |

### Django Test Execution

```text
Found 72 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
........................................................................
----------------------------------------------------------------------
Ran 72 tests in 134.470s

OK
Destroying test database for alias 'default'...
```

**Summary:**

| Metric | Result |
|---|---|
| Total tests executed | 72 |
| Tests passed | 72 |
| Test failures | 0 |
| Test errors | 0 |
| Django system check issues | 0 |
| Pending model migrations | 0 |
| Execution time | 134.470 seconds |

**Outcome:** All automated tests discovered by Django passed successfully.

These results confirm the behavior covered by the existing test suite. They do not replace manual interface testing, a security audit, or a complete fresh-installation verification.

---

## 3. Functional Verification

DAWRAH implements the following application workflows.

The table identifies functional areas included in the implemented system and their expected behavior. The overall automated test suite passed, while direct manual confirmation of every scenario remains a separate activity.

| Functional Area | Expected Behavior |
|---|---|
| Registration | Create a user account and associated profile after successful validation. |
| Authentication | Authenticate existing users using Django's authentication system. |
| Profile management | Update permitted profile information. |
| Jamiyah creation | Create a Jamiyah and assign its creator as the approved manager. |
| Jamiyah editing | Permit eligible managers to edit OPEN Jamiyahs without an existing payout schedule. |
| Jamiyah cancellation | Cancel eligible OPEN Jamiyahs while preserving their records. |
| Membership requests | Allow eligible users to request membership. |
| Membership approval | Permit managers to approve or reject pending requests. |
| Capacity validation | Prevent approved memberships from exceeding the Jamiyah capacity. |
| Payout scheduling | Generate payout turns when the required approved memberships are available. |
| Contribution reporting | Record member-reported contributions without transferring money. |
| Contribution verification | Allow managers to verify or reject reported contributions. |
| Payout delivery | Record confirmation of an eligible payout delivery. |
| Jamiyah completion | Mark the Jamiyah COMPLETED when all required turns are delivered. |
| Reports | Display summaries derived from Jamiyah, membership, payment, and payout records. |
| Notifications | Present notification information based on existing workflow states. |

### CRUD Implementation

DAWRAH provides Create, Read, Update, and safe retirement functionality for its primary workflow.

| Operation | Implementation |
|---|---|
| Create | Create Jamiyahs, membership requests, payment records, and payout schedules. |
| Read | Display Jamiyahs, memberships, payment statuses, payout turns, and reports. |
| Update | Edit eligible Jamiyahs, update profile data, review memberships and payments, and confirm deliveries. |
| Safe retirement | Cancel eligible Jamiyahs without permanently deleting associated records. |

Cancellation is used instead of permanent deletion to preserve relevant historical information.

---

## 4. Database and ORM Verification

DAWRAH uses Django models, migrations, and ORM queries to manage relational application data.

### Main Models

| Model | Responsibility |
|---|---|
| `Profile` | Stores additional information associated with a Django user. |
| `Jamiyah` | Stores association details, contribution requirements, and lifecycle status. |
| `Membership` | Connects users to Jamiyahs with roles and membership statuses. |
| `PayoutTurn` | Records scheduled payout turns and delivery confirmations. |
| `Payment` | Stores contribution reports and manager review information. |

### Data Integrity Rules

| Rule | Expected Behavior |
|---|---|
| Unique membership | Prevent multiple membership records for the same user and Jamiyah. |
| Unique payout position | Prevent duplicate payout positions within one Jamiyah. |
| One payout turn per membership | Prevent a membership from receiving duplicate payout-turn assignments. |
| Unique contribution record | Prevent duplicate payment records for the same membership and payout turn. |
| Cross-Jamiyah consistency | Prevent a payment or payout turn from referencing an incompatible Jamiyah membership. |
| Manager authorization | Restrict sensitive operations to authorized managers. |
| Membership capacity | Prevent approvals beyond the maximum permitted member count. |

### ORM Capabilities

| ORM Requirement | Application Usage |
|---|---|
| CRUD | Creating and updating records and safely cancelling Jamiyahs. |
| Filtering | Filtering associations by membership, visibility, status, and search criteria. |
| Ordering | Displaying memberships, Jamiyahs, and payout turns in meaningful order. |
| Relationship queries | Querying related users, Jamiyahs, memberships, payments, and turns. |
| Aggregation | Calculating totals and counts for dashboards and reports. |
| Annotation | Calculating related counts for individual queryset results. |

The database structure is documented in [ERD.md](ERD.md).

**Migration verification:** `python manage.py makemigrations --check --dry-run` reported no model changes requiring additional migrations.

---

## 5. Security and Access Verification

DAWRAH includes security-related configuration and server-side access controls.

| Security Area | Implemented Approach |
|---|---|
| Authentication | Django authentication system. |
| Password handling | Django's built-in password hashing and authentication mechanisms. |
| Authorization | Server-side membership and manager permission checks. |
| CSRF protection | Django CSRF protection for state-changing form requests. |
| Secret key configuration | `DJANGO_SECRET_KEY` is loaded from environment configuration rather than being hardcoded in application source. |
| Debug configuration | `DJANGO_DEBUG` controls development debugging behavior. |
| Host configuration | Allowed hosts must be configured appropriately for the target environment. |
| Sensitive files | Local `.env` and database files must not be committed or included in public submissions. |
| Error handling | A custom Arabic 404 page is implemented. |

### Security Configuration Notes

The Django `SECRET_KEY` was moved from hardcoded project configuration into an environment-based setting.

A safe `.env.example` file documents the required configuration without publishing real secrets.

This reduces the risk of exposing the application secret through source code.

**Verification limitation:** A successful Django system check does not constitute a comprehensive security audit or prove that all production deployment settings are correctly configured.

Before production deployment, the application requires additional review of host configuration, HTTPS, secure cookies, database security, permissions, and deployment settings.

---

## 6. Light and Dark Mode Verification

DAWRAH supports Light Mode and Dark Mode while preserving the original visual identity.

The final theme implementation uses Django Sessions and HTTP Cookies rather than JavaScript-based preference storage.

### Theme Implementation

| Component | Responsibility |
|---|---|
| Django Session | Stores the active theme preference for the current session. |
| HTTP Cookie | Persists the selected theme preference across sessions. |
| Django View | Processes the theme-changing POST request. |
| CSRF protection | Protects the form submission. |
| Context processor | Makes the active theme available to templates. |
| Django templates | Apply the selected theme using the `data-theme` attribute. |
| CSS | Displays the corresponding Light or Dark appearance. |

The theme toggle is designed to work without JavaScript.

### Expected Theme Behavior

- New users receive the default Light Mode unless a valid preference is available.
- Users can switch between Light Mode and Dark Mode.
- The selected theme is stored in the Django Session.
- A persistent cookie retains the preference across sessions.
- Only supported theme values are accepted.
- The theme is applied consistently across the application's shared templates.
- Existing JavaScript used for unrelated functionality remains independent of theme persistence.

Theme-related automated tests form part of the Django test suite. All 72 discovered tests passed.

**Manual verification:** Final browser checks with JavaScript disabled and a fresh browser session should be recorded separately before submission if not already completed.

---

## 7. Screenshot and Documentation Verification

Screenshots were captured manually from the DAWRAH application to document its interface and core features.

The illustrated guide references 15 screenshots.

### Screenshot Inventory

| Screenshot | Purpose |
|---|---|
| `01_landing_light.png` | Landing page in Light Mode. |
| `02_login.png` | User login. |
| `03_register.png` | Account registration. |
| `04_dashboard.png` | Main dashboard. |
| `05_my_jamiyahs.png` | User's Jamiyahs. |
| `06_explore_jamiyahs.png` | Public Jamiyah discovery. |
| `07_create_jamiyah_form.png` | Jamiyah creation form. |
| `08_profile.png` | User profile. |
| `09_jamiyah_details.png` | Jamiyah details and management controls. |
| `10_membership_requests.png` | Membership review and approval controls. |
| `11_payout_timeline.png` | Payout schedule and turn tracking. |
| `12_payment_tracking.png` | Contribution tracking and payment statuses. |
| `13_reports_dashboard.png` | Reports and statistics dashboard. |
| `14_jamiyah_report_detail.png` | Individual Jamiyah report. |
| `15_landing_dark.png` | Landing page in Dark Mode. |

**Location:** `docs/screenshots/demo-guide/`

Screenshots illustrate the current application interface. They do not independently prove all backend validations or complete every business workflow.

The screenshots and descriptions are documented in [demo_guide.md](demo_guide.md).

Before submission, verify that the screenshots do not reveal passwords, private phone numbers, personal email addresses, invitation tokens, or other sensitive information.

---

## 8. Manual Acceptance Scenarios

The following scenarios should be verified directly through the application interface.

**Status definitions:**
- **PASS:** Executed manually and the actual outcome matched the expected outcome.
- **FAIL:** Executed manually and did not behave as expected.
- **PENDING:** Not yet independently verified manually or no execution evidence has been recorded.

| Area | Manual Test Scenario | Expected Result | Status |
|---|---|---|---|
| Registration | Register using valid account information. | User account and profile are created successfully. | PENDING |
| Registration validation | Submit duplicate account information. | Validation prevents invalid registration. | PENDING |
| Authentication | Access a protected page without login. | User is redirected to login. | PENDING |
| Jamiyah creation | Create a valid Jamiyah. | New Jamiyah is saved and displayed. | PENDING |
| Jamiyah validation | Submit invalid required fields or dates. | Helpful validation errors appear. | PENDING |
| Jamiyah editing | Edit an eligible OPEN Jamiyah. | Updates are saved correctly. | PENDING |
| Jamiyah cancellation | Cancel an eligible OPEN Jamiyah. | Confirmation is required and records are preserved. | PENDING |
| Membership requests | Submit a new membership request. | Request enters the pending state. | PENDING |
| Membership review | Approve and reject pending requests. | Membership states update correctly. | PENDING |
| Capacity | Attempt approval beyond the member limit. | Approval is blocked. | PENDING |
| Payout schedule | Generate turns for a full Jamiyah. | Valid payout schedule is created. | PENDING |
| Duplicate schedule | Attempt to generate another schedule. | Duplicate generation is prevented. | PENDING |
| Contribution reporting | Report an eligible contribution. | Payment record enters pending review. | PENDING |
| Contribution review | Verify or reject a pending contribution. | Payment status and review details update. | PENDING |
| Delivery confirmation | Confirm delivery after required contributions are verified. | The payout turn is marked delivered. | PENDING |
| Delivery validation | Attempt premature or out-of-order delivery. | Restricted operation is blocked according to implemented rules. | PENDING |
| Completion | Confirm the final eligible payout delivery. | Jamiyah changes to COMPLETED. | PENDING |
| Reports | Open the reports dashboard and an individual report. | Displayed values reflect the saved data. | PENDING |
| Explore filtering | Search available public associations. | Only PUBLIC and OPEN Jamiyahs appear. | PENDING |
| Profile sections | Review current, completed, and cancelled Jamiyahs. | Each Jamiyah appears in the appropriate section. | PENDING |
| Theme switching | Switch between Light Mode and Dark Mode. | The selected theme is displayed and remembered. | PENDING |
| Responsive layout | Review the main pages on mobile and desktop. | Pages remain readable without unintended horizontal overflow. | PENDING |
| Custom 404 | Navigate to a missing page with `DEBUG=False`. | Custom Arabic 404 page appears. | PENDING |
| Fresh setup | Install and run the application from a clean checkout. | Application starts successfully using documented instructions. | PENDING |

**Note:** Some of these behaviors are covered by automated tests or represented in screenshots. Their manual status remains PENDING until a separate hands-on verification is performed and documented.

---

## 9. Demo-Specific Behavior

### Early Payout Delivery and Jamiyah Completion

DAWRAH is currently implemented as an educational capstone prototype.

For demonstration purposes, the system allows an eligible payout turn to be confirmed as delivered before its scheduled payout date, provided the other implemented conditions are satisfied.

This behavior makes it possible to demonstrate the full Jamiyah lifecycle during a short presentation without waiting several weeks or months for scheduled payout dates.

As a result, a Jamiyah can reach the COMPLETED state before the scheduled dates of all its payout turns.

**This is an intentional demo limitation, not the intended behavior for a future production release.**

### Planned Production Improvement

Before a real-world launch, DAWRAH would require server-side enforcement of payout eligibility based on the scheduled date.

Additional production considerations may include:

- Preventing delivery confirmation before the scheduled payout date.
- Defining an authorized exception or rescheduling workflow.
- Recording detailed audit information for delivery-related actions.
- Verifying financial and operational requirements appropriate to the intended real-world use.

The prototype's current design is intended to demonstrate the workflow and business relationships rather than operate a real financial service.

---

## 10. Known Limitations

| Limitation | Current Implementation | Future Improvement |
|---|---|---|
| Financial transfers | DAWRAH records contributions and delivery confirmations without executing transfers. | Consider suitable payment integration only after regulatory, security, and operational review. |
| Early payout completion | Eligible turns may be confirmed before scheduled dates for demonstration purposes. | Enforce scheduled-date restrictions and authorized exceptions in the backend. |
| Database concurrency | SQLite is used for local development and demonstration. | Consider PostgreSQL and verify concurrent update behavior. |
| Notifications | Notifications are derived from application workflow data. | Introduce dedicated persistent notifications if needed. |
| Demo data | Sample records are local and no permanent seed fixture is provided. | Provide a safe, reproducible demo data setup. |
| Localization | The interface is primarily Arabic. | Add full English localization if required. |
| Deployment | Production deployment readiness is not established by local tests alone. | Perform hosting, HTTPS, security, and production configuration checks. |
| Security | Environment-based settings and server-side controls are implemented. | Perform further security testing before public launch. |
| Manual verification | Automated tests passed, but the complete manual acceptance record is not yet finalized. | Execute and record all remaining manual tests and fresh setup results. |

---

## 11. Final Verification Summary

| Verification Category | Result |
|---|---|
| Django system check | PASS |
| Automated Django tests | PASS — 72/72 |
| Migration consistency check | PASS |
| Core Django application structure | Implemented |
| Database relationships and integrity rules | Implemented; covered in project tests and documentation |
| Authentication and authorization | Implemented; included in automated verification |
| Light/Dark Mode | Implemented; browser-level final review recommended |
| ERD documentation | Available |
| Illustrated demo documentation | Available — 15 screenshot references |
| Manual acceptance verification | Pending final documented execution |
| Fresh installation verification | Pending final documented execution |
| Production readiness | Not claimed |

### Conclusion

DAWRAH successfully passed its final reported automated Django verification on October 13, 2026, with **72 tests passed**, **zero system check issues**, and **no pending model migrations**.

The implemented prototype provides a structured workflow for Jamiyah creation, membership management, contribution tracking, payout scheduling, delivery confirmation, and reporting.

The project also includes environment-based security configuration, role-based access controls, database validation, an Arabic RTL interface, and session- and cookie-based theme management.

Before final submission, the remaining manual acceptance scenarios, fresh setup, and repository privacy checks should be completed and documented.

DAWRAH remains an educational prototype. Its current limitations, particularly early payout completion and the absence of real financial transfers, are explicitly acknowledged and identified as areas requiring additional work before real-world deployment.