# Maricho Database Schema Design

This document outlines the normalized, relational database schema for Maricho, designed for PostgreSQL.

## 1. Entity-Relationship Diagram (Mermaid)

```mermaid
erDiagram
    PERSONS ||--o{ SKILLS : has
    PERSONS ||--o{ SERVICE_AREAS : covers
    PERSONS ||--o| STANDINGS : maintains
    PERSONS ||--o{ CREWS : leads
    CREWS ||--|{ CREW_MEMBERS : includes
    PERSONS ||--o{ CREW_MEMBERS : "is member of"
    
    PERSONS ||--o{ JOBS : "requests (as buyer)"
    PERSONS ||--o{ JOBS : "assigned (as worker)"
    
    JOBS ||--o{ LEDGER_ENTRIES : generates
    JOBS ||--o| RECORD_ENTRIES : produces
    PERSONS ||--o{ RECORD_ENTRIES : owns

    PERSONS {
        uuid id PK
        varchar phone UK "NOT NULL"
        enum role "BUYER, WORKER, OPS, AGGREGATOR"
        varchar next_of_kin_phone
        uuid guarantor_id FK "nullable"
        timestamp created_at
    }

    SKILLS {
        uuid id PK
        uuid worker_id FK "NOT NULL"
        enum trade "PLUMBING, ELECTRICAL, SOLAR..."
        varchar grade "e.g., JOURNEYMAN"
        varchar proof_url
    }

    SERVICE_AREAS {
        uuid id PK
        uuid worker_id FK "NOT NULL"
        varchar suburb "NOT NULL"
        enum travel_means "BICYCLE, BAKKIE, WALKING"
    }

    STANDINGS {
        uuid worker_id PK, FK
        enum grade "REGISTERED, IDENTIFIED, APPRENTICE..."
        decimal on_time_rate "Default 100.00"
        decimal dispute_rate "Default 0.00"
        decimal fill_rate "Default 0.00"
        int jobs_completed "Default 0"
    }

    CREWS {
        uuid id PK
        uuid lead_id FK "UK (One crew per lead)"
        varchar name
    }

    CREW_MEMBERS {
        uuid crew_id PK, FK
        uuid worker_id PK, FK
    }

    JOBS {
        uuid id PK
        uuid buyer_id FK "NOT NULL"
        uuid worker_id FK "Nullable until accepted"
        enum status "REQUESTED, MATCHED, BOOKED, IN_PROGRESS, DISPUTED, COMPLETED, CANCELLED"
        varchar suburb "NOT NULL"
        text problem_description
        varchar problem_photo_url
        decimal quote_amount "Nullable until inspection"
        timestamp created_at
        timestamp updated_at
    }

    LEDGER_ENTRIES {
        uuid id PK
        uuid job_id FK "NOT NULL"
        decimal amount "NOT NULL, > 0"
        enum entry_type "DEPOSIT_HELD, BALANCE_COMMITTED, RELEASED, REFUNDED"
        timestamp created_at
    }

    RECORD_ENTRIES {
        uuid id PK
        uuid job_id FK "UK, NOT NULL"
        uuid worker_id FK "NOT NULL"
        text what_was_done "NOT NULL"
        text client_words
        varchar before_photo_url
        varchar after_photo_url
        timestamp signed_off_at "NOT NULL"
    }
```

## 2. Normalization & Constraints

The schema is normalized to **3NF (Third Normal Form)** to ensure data integrity and eliminate redundancy. 

### Core Constraints

1.  **Unique Identifiers (UUIDv4):** All primary keys utilize UUIDs to prevent ID guessing and support offline-first sync (clients can generate UUIDs locally before syncing).
2.  **Phone Number Uniqueness:** `PERSONS.phone` is constrained as `UNIQUE`. A single phone number is the primary identity anchor in Maricho.
3.  **Composite Unique Constraints:**
    *   `SKILLS`: `UNIQUE(worker_id, trade)` — A worker cannot have duplicate entries for the same trade.
    *   `SERVICE_AREAS`: `UNIQUE(worker_id, suburb)` — A worker cannot duplicate suburb coverage.
4.  **One-to-One Relationships enforced via PK/UK:**
    *   `STANDINGS`: `worker_id` serves as both the Primary Key and a Foreign Key to `PERSONS.id`, enforcing a strict 1:1 relationship.
    *   `RECORD_ENTRIES`: `job_id` is marked `UNIQUE`. A job can only generate exactly one immutable record entry.
5.  **Check Constraints:**
    *   `LEDGER_ENTRIES.amount`: `CHECK (amount > 0)` — Ledger movements cannot be negative; reversals are handled by creating a new `REFUNDED` entry rather than altering past entries (immutability).
6.  **Referential Integrity (Foreign Keys):**
    *   Deletions of a `PERSONS` row cascade to `SERVICE_AREAS` and `SKILLS`, but **RESTRICT** deletion if they are tied to a `JOBS` or `LEDGER_ENTRIES` record to preserve immutable history.
7.  **Data Types (Enums):**
    *   Strict enumeration types are used for `status`, `role`, `trade`, and `entry_type` to prevent arbitrary string insertion and maintain reporting cleanliness.

## 3. Immutability 

To align with the design principle *"A record entry is immutable"*:
*   `RECORD_ENTRIES` and `LEDGER_ENTRIES` tables will not have an `updated_at` column. 
*   We will implement database-level triggers to `RAISE EXCEPTION` on `UPDATE` or `DELETE` statements targeting these tables after creation. Corrections must be handled by appending new rows (e.g., a "Correction" table linked to the record, or specific ledger reversal types).
