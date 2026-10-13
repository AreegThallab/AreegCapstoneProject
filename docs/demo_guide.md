# DAWRAH Demo Guide

Use this guide to demonstrate DAWRAH to the instructor in a concise, technical, and product-focused flow.

## 1. Product Introduction

Introduce **دَوْرة | DAWRAH** as a rotating savings association management platform.

Key message:

> DAWRAH helps a Jamiyah organizer manage members, contribution reports, payout order, delivery confirmation, and reports without processing real money.

Target audience:

- Family Jamiyah organizers.
- Friend groups that coordinate monthly contributions.
- Small community groups that need a transparent tracking workflow.

Value:

- Replaces scattered chat messages and spreadsheets.
- Gives members visibility into payout turns and contribution status.
- Gives managers server-side controls for approvals, verification, and completion.

## 2. Suggested Demo Order

### Step 1: Landing Page

Show the public landing page.

Explain:

- DAWRAH is Arabic-first and RTL.
- It presents the product purpose before login.
- Public users can register or log in.

### Step 2: Login and Dashboard

Log in with a fictional demo account provided locally by the instructor/demo environment.

Show:

- Dashboard navigation.
- Notification indicators.
- Main actions: My Jamiyahs, Explore Jamiyahs, Create Jamiyah, Reports.

Do not show or publish passwords in slides or README.

### Step 3: Explore Jamiyahs

Open **Explore Jamiyahs**.

Demonstrate:

- Public Jamiyah discovery.
- Search/filter behavior where available.
- Status and capacity information.
- Empty or restricted cases if applicable.

### Step 4: My Jamiyahs

Open **My Jamiyahs**.

Show:

- Memberships grouped by the user's current Jamiyahs.
- Open, active, and completed lifecycle states.
- Access to details and payment tracking.

### Step 5: Jamiyah Details

Open a Jamiyah details page, preferably **جمعة الأصدقاء**.

Explain:

- Membership status.
- Current payout schedule.
- Approved members.
- Contribution amount and member capacity.
- Manager-only actions are protected by server-side authorization.

### Step 6: Membership Management

If using a manager account, demonstrate a public/open Jamiyah with pending and rejected requests.

Explain the rule:

- Only managers with approved membership can approve or reject requests.
- Capacity is enforced before approval.
- Rejected memberships cannot be silently converted through unauthorized routes.

### Step 7: Payout Schedule

Show an active Jamiyah with payout turns.

Explain:

- Payout turns are generated only when the Jamiyah is full.
- Each approved membership receives one payout turn.
- The `(jamiyah, position)` uniqueness rule prevents duplicate payout positions.

### Step 8: Payment Management

Open the payment dashboard.

Show:

- Pending, verified, and rejected payment examples.
- Duplicate payment prevention for the same member and round.
- Manager review workflow if using a manager account.

Technical note:

- `Payment.clean()` checks that the payment membership and payout turn belong to the same Jamiyah.
- A database uniqueness constraint protects one payment per member per payout round.

### Step 9: Delivery Confirmation

Show delivery status on a Jamiyah with verified payments.

Explain:

- A payout turn can be delivered only after all required payments for that turn are verified.
- Later turns cannot be delivered before previous turns.
- The final delivered turn marks the Jamiyah completed.

### Step 10: Reports

Open **Reports** and a per-Jamiyah report.

Highlight:

- Summary counts for Jamiyah statuses.
- Payment totals by status.
- Delivered payout totals.
- Per-turn verified contribution counts.

Technical note:

- Reports use filtering, relationship queries, `Count`, `Q`, and `annotate`.
- Report calculations are covered by automated tests.

## 3. Validation and Failure Examples

Choose one or two:

| Example | Expected Result |
|---|---|
| Create Jamiyah with past start date | Server-side validation rejects the date. |
| Try approving beyond capacity | Request remains pending or approval is blocked. |
| Try generating a payout schedule before capacity is full | Schedule is not created. |
| Try confirming delivery before all payments are verified | Delivery is blocked. |
| Open a protected manager route as a non-manager | Server returns a restricted response. |

## 4. Database Relationships to Explain

Use [ERD.md](ERD.md) during the technical discussion.

Core relationships:

- `User` has one `Profile`.
- `User` creates many `Jamiyahs`.
- `User` joins Jamiyahs through `Membership`.
- `Jamiyah` has many `Memberships`.
- Approved `Membership` may have one `PayoutTurn`.
- `Payment` links a `Membership`, `Jamiyah`, and `PayoutTurn`.

Important constraints:

- Unique Jamiyah membership per user.
- Unique payout position per Jamiyah.
- Unique payment per membership and payout turn.
- Cross-Jamiyah validation in `Payment` and `PayoutTurn`.

## 5. Technical Decisions

| Decision | Reason |
|---|---|
| Django authentication | Avoid manual password handling and use built-in session security. |
| Separate apps | Keeps accounts, Jamiyah workflow, payments, and reports organized. |
| Model validation plus tests | Protects data integrity outside normal views. |
| SQLite for local capstone | Simple setup for classroom review and local demonstration. |
| No real payment integration | Keeps project scope focused on management and tracking. |
| Environment variables | Keeps secrets and deployment settings out of source code. |

## 6. Market Potential

Describe DAWRAH as a focused workflow tool for small groups that already run Jamiyahs manually. The value is clarity, accountability, and easier record keeping.

Avoid claiming unverified market statistics. Present demand as a practical workflow need rather than a measured market size.

## 7. Limitations and Future Improvements

Current limitations:

- Does not process or transfer real money.
- No production deployment in the current repository state.
- Demo data is local and not packaged as a fixture.
- Notification records are derived from workflow state rather than stored separately.
- SQLite is not ideal for high-concurrency production use.

Future improvements:

- PostgreSQL deployment.
- Exportable reports.
- Dedicated notification model.
- Optional payment gateway integration as a clearly separated future feature.
- Multi-language support.

## 8. Closing

End by showing:

1. A completed Jamiyah report.
2. The ERD.
3. The test result summary.
4. The known limitations.

This demonstrates both product value and technical understanding.
