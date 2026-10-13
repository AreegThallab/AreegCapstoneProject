<p align="center">
  <img src="static/images/dawrah-logo.svg" alt="DAWRAH logo" width="190">
</p>

# دَوْرة | DAWRAH

**A Django-based platform for organizing rotating savings associations (Jamiyahs)—without handling real money.**

DAWRAH brings together membership management, contribution tracking, payout scheduling, delivery confirmations, and reporting in one Arabic-first web application. It was developed as a **capstone prototype** to demonstrate an end-to-end Django workflow with role-based access and data integrity checks.

> **Project scope:** DAWRAH records and verifies *reported* financial activity; it does **not** collect, hold, transfer, or process funds.

## 1. Problem & Proposed Solution

Informal savings groups are often coordinated through messages and spreadsheets. This can make it difficult to establish who belongs to a group, which contributions have been reported, whose payout turn is next, and whether delivery was confirmed.

DAWRAH provides a structured record of these steps so managers and members can follow the same workflow and review the same information.

### Intended Users

| Audience | Primary need |
|---|---|
| Jamiyah organizers | Manage membership requests, payout schedules, reported payments, and delivery confirmations. |
| Jamiyah members | Follow their membership, upcoming turns, contribution status, and reports. |
| Families and small groups | Organize a rotating savings association without relying on scattered messages. |

## 2. Features

### Accounts & User Experience

- Registration, login, logout, and editable profiles using Django authentication.
- Arabic right-to-left (RTL) interface with responsive layouts.
- Light and Dark Mode, with the selected theme designed to persist through **Django Sessions and a preference Cookie** rather than browser local storage.
- Dashboard information and notification indicators derived from existing application records.
- Custom Arabic 404 page.

### Jamiyah Management

- Create **public** and **private** Jamiyahs with configurable contribution amount, capacity, frequency, and start date.
- Join requests with `pending`, `approved`, and `rejected` states.
- Manager-controlled approvals and rejections, with member-capacity checks.
- Explore page restricted to **PUBLIC + OPEN** Jamiyahs.
- Edit eligible **OPEN** Jamiyahs before payout scheduling begins.
- Cancel eligible **OPEN** Jamiyahs without deleting associated history.
- Lifecycle states: `open`, `active`, `completed`, and `cancelled`.
- Invitation link support for private Jamiyahs.

### Contributions & Payouts

- Generate a weekly or monthly payout schedule once the required approved membership count is reached.
- Record contribution reports for each member and payout turn.
- Manager verification or rejection of reported payments.
- Prevent duplicate payment records for the same member and turn.
- Confirm payout delivery only when the required contributions are verified and relevant workflow checks pass.
- Mark the Jamiyah **completed** after its payout turns have been confirmed as delivered.

### Reports

- Summary counts for Jamiyah statuses.
- Detailed per-Jamiyah reports, including contribution verification and payout delivery records.
- Profile sections separating **current**, **completed**, and **cancelled** Jamiyahs.

## 3. Screenshots & Illustrated Demo

The main screenshots below show the interface. The [Illustrated Demo Guide](docs/demo_guide.md) provides an expanded walkthrough using **15 manually captured screenshots**, including Light and Dark Mode.

| Screen | Preview |
|---|---|
| Landing page | ![DAWRAH landing page](docs/screenshots/landing.png) |
| Dashboard | ![Dashboard](docs/screenshots/dashboard.png) |
| My Jamiyahs | ![My Jamiyahs](docs/screenshots/my-jamiyahs.png) |
| Explore | ![Explore](docs/screenshots/explore.png) |
| Jamiyah details | ![Jamiyah details](docs/screenshots/jamiyah-details.png) |
| Payment management | ![Payment management](docs/screenshots/payments.png) |
| Reports | ![Reports dashboard](docs/screenshots/reports.png) |

Additional walkthrough screenshots are stored in `docs/screenshots/demo-guide/`, including `01_landing_light.png` and `15_landing_dark.png`.

## 4. Technical Stack

| Layer | Technology |
|---|---|
| Backend | Python, Django |
| Database | SQLite for the capstone/development environment |
| Frontend | Django Templates, HTML, CSS, and existing JavaScript for unrelated interactions |
| Authentication | Django authentication and authorization checks |
| Theme preference | Django Sessions, HTTP Cookies, server-rendered templates, CSS |
| Testing | Django `TestCase` |
| Configuration | Environment variables loaded for application settings |

Exact dependency versions are maintained in [`requirements.txt`](requirements.txt).

## 5. Project Structure

```text
Dawrah/
├── accounts/                 # Registration and profiles
├── config/                   # Settings, URLs, shared application configuration
├── jamiyahs/                 # Jamiyahs, memberships, payout turns
├── transactions/             # Contribution reporting and review
├── reports/                  # Aggregated and individual reports
├── templates/                # Shared and page-specific Django templates
├── static/                   # Styles, scripts, logo, icons, assets
├── docs/
│   ├── ERD.md
│   ├── verification.md
│   ├── demo_guide.md
│   └── screenshots/
├── manage.py
├── .env.example
└── requirements.txt
```

## 6. Data Model & Business Rules

The main models are `Profile`, `Jamiyah`, `Membership`, `PayoutTurn`, and `Payment`, alongside Django's built-in `User`.

| Model | Responsibility |
|---|---|
| `Profile` | One-to-one user profile information. |
| `Jamiyah` | Association details, creator, settings, and lifecycle. |
| `Membership` | User participation, role, and approval status. |
| `PayoutTurn` | Recipient, position, scheduled date, and delivery confirmation. |
| `Payment` | Reported contribution and its review state for a given turn. |

Integrity safeguards include uniqueness of `(jamiyah, user)` for memberships, `(jamiyah, position)` for payout order, and `(membership, payout_turn)` for payments. Model and view validations also check that a payment, its membership, and its payout turn belong to the same Jamiyah and restrict sensitive actions to authorized managers.

**ORM evidence:** related-object lookups, filtering by user/role/status, ordering, aggregation (`Count`), and annotations used in discovery and reporting.

See the [ERD](docs/ERD.md) for the actual entities, foreign keys, and relationship cardinalities.

## 7. Core Workflow

1. Register or sign in.
2. Create a Jamiyah; its creator becomes its manager and an approved member.
3. Members request to join; the manager approves or rejects requests.
4. Once the Jamiyah is full, the manager arranges and generates payout turns.
5. Members report contributions made outside the platform.
6. The manager verifies or rejects reported contributions.
7. Once an eligible turn satisfies the verification rules, the manager confirms delivery.
8. After all turns are delivered, the Jamiyah becomes `completed`.
9. Users can review their history and reports.

**Alternative lifecycle:** an eligible `open` Jamiyah may be cancelled before a payout schedule is generated; cancellation preserves records instead of deleting them.

## 8. Installation & Local Setup (Windows)

### Clone and prepare the environment

```powershell
git clone <repository-url>
cd Dawrah
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use this only in the current terminal session, then retry the activation command:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Configure application secrets

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

Set your own environment values in `.env`:

```dotenv
DJANGO_SECRET_KEY=replace-with-a-strong-unique-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

Generate a secure key locally if needed:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Never commit `.env`, production secrets, credentials, or `db.sqlite3` to the repository. For deployment, set `DJANGO_DEBUG=False`, configure the actual hostnames, and review production security settings.

### Create tables and run

```powershell
python manage.py migrate
python manage.py runserver
```

Open: `http://127.0.0.1:8000/`

### Run checks and tests

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

See [Verification Record](docs/verification.md) for documented testing evidence. **Re-run these commands after the final theme and documentation changes before recording an updated test count.**

## 9. Security & Responsible Configuration

The capstone includes security improvements made during development:

- **Secret key protection:** `SECRET_KEY` was moved away from a hardcoded project value to the `DJANGO_SECRET_KEY` environment setting, with a safe `.env.example` template. Any previously exposed or shared key should be rotated rather than reused.
- **Deployment controls:** `DEBUG` and `ALLOWED_HOSTS` are environment-driven instead of being fixed for all environments.
- **Sensitive files:** local `.env` and SQLite database files should be excluded from Git using `.gitignore`.
- **Authentication:** Django's password hashing and built-in authentication are used, rather than manually comparing or storing plain-text passwords.
- **Authorization:** views validate manager/member permissions and relevant lifecycle states; hiding a button in the template is not the only restriction.
- **Request protection:** state-changing operations use POST forms with Django CSRF protection.
- **Data integrity:** validated relationships and duplicate-prevention rules reduce inconsistent records.
- **Theme persistence:** theme preferences contain only `light` or `dark`, not credentials or personal information.

These controls improve the prototype but **do not constitute a production security audit**. Deployment requires further checks of HTTPS, secure cookies, database backups, allowed origins/hosts, operational logging, and secret management.

## 10. Prototype Limitations & Planned Production Improvements

DAWRAH is an educational **demonstration prototype**, not a production-ready financial service. The following boundaries are intentional or remain future work:

| Area | Current capstone behavior | Intended production improvement |
|---|---|---|
| **Scheduled payout timing** | For demonstration purposes, an otherwise eligible payout turn can be confirmed **before its scheduled calendar date**, allowing the complete Jamiyah lifecycle to be demonstrated within a short presentation. | Enforce date-based eligibility on the server so a payout cannot be confirmed before its scheduled date, accounting for the configured timezone and business rules. Add tests for early, on-time, and late delivery. |
| **Real payments** | Contributions and payout deliveries are **recorded**, not transferred or independently confirmed by a payment provider. | Evaluate regulated payment-provider integration, reconciliation, dispute handling, and relevant legal/compliance requirements before handling funds. |
| **Database** | SQLite supports the local demonstration and coursework workflow. | Consider PostgreSQL, transactional/concurrency testing, backup and recovery procedures, and production monitoring. |
| **Notifications** | Notifications are calculated from existing workflow records; no dedicated notification-delivery system is required for the prototype. | Add delivery channels, scheduling, and a persistent notification/audit trail if product requirements justify them. |
| **Deployment** | Local application and documentation; production hosting is outside the current demonstrated scope. | Set up HTTPS hosting, environment secrets, secure cookie settings, observability, and deployment checks. |
| **Localization** | Arabic-first RTL interface. | Consider additional languages and accessibility review with target users. |
| **Demo data** | Local test data and manually captured interface screenshots; no permanent seed/fixture command. | Provide reproducible, non-sensitive seed data and automated demo setup. |

### Why early completion is allowed in the demo

A Jamiyah may be configured with weekly or monthly dates extending beyond the presentation day. To show **payment verification → delivery confirmation → final completion** in one live demonstration, the prototype focuses on **workflow integrity** rather than enforcing that the scheduled date has arrived.

This is a **known simulation constraint**, not a claim that real payouts should occur early. The existing prerequisites for delivery confirmation (including required verified contributions and sequence rules) remain relevant. **Before any real-world launch**, date enforcement must be implemented and tested at the backend, rather than relying on the UI alone.

### Security distinction

The previous secret-key configuration was a **development security issue that was addressed**, not a feature of the prototype or a limitation intentionally left in place. The remaining deployment/security work is listed separately above to avoid presenting the capstone as production hardened.

## 11. Documentation

- [ERD — Database Relationships](docs/ERD.md)
- [Verification Record](docs/verification.md)
- [Illustrated Demo Guide — 15 Screenshots](docs/demo_guide.md)
- [Security Setup](SECURITY_SETUP.md)

## 12. Acknowledgments & AI Use

DAWRAH was developed **individually** as a Django capstone project, drawing on Python/Django coursework and official documentation. I was responsible for defining the project idea, requirements, business rules, and overall implementation decisions.

**AI assistance was used to support the website's visual design and frontend development**, including exploring layout ideas, refining the user interface, improving responsive styling, and helping write and adjust JavaScript for interactive elements. AI was also used as a supporting tool for code review, test planning, security-configuration guidance, and documentation drafting.

AI-generated suggestions and code were reviewed, adapted, and integrated into the project by me rather than accepted without verification. The project's application logic and final decisions remained under my responsibility.

The Light/Dark Mode preference is intended to use **Django Sessions and Cookies rather than JavaScript**; this description should be confirmed against the final implementation before submission.

---

**DAWRAH | دَوْرة — Organized savings circles, clearer records, and a transparent workflow.**
