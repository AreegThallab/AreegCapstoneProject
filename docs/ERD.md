# DAWRAH ERD

This Entity Relationship Diagram (ERD) documents the Django models, their fields, and the relationships used in **DAWRAH | دَوْرة**.

## Entity Relationship Diagram

![DAWRAH entity relationship diagram showing User, Profile, Jamiyah, Membership, PayoutTurn, and Payment, with their fields and relationship links.](images/erd-diagram.png)

> If the SVG does not display in your Markdown viewer, open the [PNG version](images/erd-diagram.png).

<details>
<summary>View editable Mermaid diagram source</summary>

```mermaid
erDiagram
    AUTH_USER {
        int id PK
        string username
        string email
        string password
        string first_name
        string last_name
        bool is_active
        bool is_staff
        datetime date_joined
    }

    PROFILE {
        int id PK
        int user_id FK "unique"
        string full_name
        string phone_number "unique, +9665XXXXXXXX"
    }

    JAMIYAH {
        int id PK
        int creator_id FK
        string name
        text description
        decimal contribution_amount
        int max_members
        string frequency "weekly or monthly"
        date start_date "nullable"
        string visibility "public or private"
        uuid invite_token "unique"
        string status "open, active, completed, cancelled"
        datetime created_at
        datetime completed_at "nullable"
    }

    MEMBERSHIP {
        int id PK
        int jamiyah_id FK
        int user_id FK
        string role "manager or member"
        string status "pending, approved, rejected"
        datetime joined_at
        datetime completion_seen_at "nullable"
    }

    PAYOUT_TURN {
        int id PK
        int jamiyah_id FK
        int membership_id FK "one-to-one"
        int position
        date payout_date
        datetime delivered_at "nullable"
        int delivered_by_id FK "nullable"
        datetime recipient_seen_at "nullable"
    }

    PAYMENT {
        int id PK
        int jamiyah_id FK
        int membership_id FK
        int payout_turn_id FK
        string status "pending, verified, rejected"
        datetime reported_at
        int reviewed_by_id FK "nullable"
        datetime reviewed_at "nullable"
    }

    AUTH_USER ||--|| PROFILE : "has profile"
    AUTH_USER ||--o{ JAMIYAH : "creates"
    AUTH_USER ||--o{ MEMBERSHIP : "joins"
    AUTH_USER ||--o{ PAYMENT : "reviews optionally"
    AUTH_USER ||--o{ PAYOUT_TURN : "confirms delivery optionally"

    JAMIYAH ||--o{ MEMBERSHIP : "has members"
    JAMIYAH ||--o{ PAYOUT_TURN : "has payout schedule"
    JAMIYAH ||--o{ PAYMENT : "has contribution records"

    MEMBERSHIP ||--o| PAYOUT_TURN : "receives up to one payout turn"
    MEMBERSHIP ||--o{ PAYMENT : "reports payments"
    PAYOUT_TURN ||--o{ PAYMENT : "collects round payments"
```

</details>

## Relationship Notes

| Relationship | Cardinality and Optionality | Implementation |
|---|---|---|
| `User` to `Profile` | One user has one profile. | `Profile.user` is `OneToOneField(User, on_delete=CASCADE)`. |
| `User` to `Jamiyah` | One user may create many Jamiyahs. | `Jamiyah.creator` is `ForeignKey(User, on_delete=PROTECT)`. |
| `Jamiyah` to `Membership` | One Jamiyah may have many memberships. | `Membership.jamiyah` is `ForeignKey(Jamiyah, on_delete=CASCADE)`. |
| `User` to `Membership` | One user may belong to many Jamiyahs. | `Membership.user` is `ForeignKey(User, on_delete=CASCADE)`. |
| `Membership` to `PayoutTurn` | An approved membership may have one payout turn. | `PayoutTurn.membership` is `OneToOneField(Membership, on_delete=CASCADE)`. |
| `Jamiyah` to `PayoutTurn` | One Jamiyah may have many payout turns after schedule generation. | `PayoutTurn.jamiyah` is `ForeignKey(Jamiyah, on_delete=CASCADE)`. |
| `Jamiyah` to `Payment` | One Jamiyah may have many contribution records. | `Payment.jamiyah` is a foreign key to `Jamiyah`. |
| `Payment` to `Membership` | One membership may have many payment records, one per payout turn. | `Payment.membership` is `ForeignKey(Membership, on_delete=CASCADE)`. |
| `Payment` to `PayoutTurn` | One payout turn may have many payment records. | `Payment.payout_turn` is `ForeignKey(PayoutTurn, on_delete=CASCADE)`. |
| `Payment.reviewed_by` | Optional reviewer. | `ForeignKey(User, null=True, blank=True, on_delete=SET_NULL)`. |
| `PayoutTurn.delivered_by` | Optional delivery confirmer. | `ForeignKey(User, null=True, blank=True, on_delete=SET_NULL)`. |

## Constraints and Data Integrity

| Model | Constraint or Rule |
|---|---|
| `Profile` | `phone_number` is unique and validated using the format `+9665XXXXXXXX`. |
| `Jamiyah` | `contribution_amount >= 1`, `max_members >= 2`, and `invite_token` is unique. |
| `Membership` | Unique `(jamiyah, user)` prevents dupliٍcate membership rows. |
| `PayoutTurn` | Unique `(jamiyah, position)` prevents duplicate payout order positions. |
| `PayoutTurn` | `clean()` ensures the selected membership belongs to the same Jamiyah and is approved. |
| `Payment` | Unique `(membership, payout_turn)` prevents duplicate contribution records for the same round. |
| `Payment` | `clean()` ensures the membership and payout turn both belong to the same Jamiyah. |

## Workflow State Model

| Entity | States |
|---|---|
| `Jamiyah.status` | `open`, `active`, `completed`, `cancelled` |
| `Membership.status` | `pending`, `approved`, `rejected` |
| `Payment.status` | `pending`, `verified`, `rejected` |

### Jamiyah Lifecycle

- **`open`**: The Jamiyah is created and can accept eligible membership requests.
- **`active`**: The payout schedule has been generated and the Jamiyah is operating.
- **`completed`**: All payout turns have confirmed delivery.
- **`cancelled`**: An eligible open Jamiyah is cancelled; its records are retained instead of being deleted.

The normal lifecycle is `open` → `active` → `completed`. Cancellation is an alternative outcome for an eligible `open` Jamiyah, not a step after completion.

> **Diagram scope:** This document describes the entities and constraints supplied for the project. Confirm field definitions and on-delete behavior against the final Django models before submission.
