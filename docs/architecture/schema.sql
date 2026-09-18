-- Maricho Database Schema (reference snapshot)
--
-- This file mirrors the schema produced by the Alembic migrations under
-- backend/migrations/versions/. Alembic is the source of truth for schema
-- changes (see engineering_standards.md §3) — this file is kept in sync for
-- reference/onboarding only and must never be run directly against a
-- database.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE roleenum AS ENUM ('BUYER', 'WORKER', 'OPS', 'AGGREGATOR');
CREATE TYPE jobstatusenum AS ENUM ('REQUESTED', 'MATCHED', 'BOOKED', 'IN_PROGRESS', 'DISPUTED', 'COMPLETED', 'CANCELLED');
CREATE TYPE ledgerentrytypeenum AS ENUM ('DEPOSIT_HELD', 'BALANCE_COMMITTED', 'RELEASED', 'REFUNDED');
CREATE TYPE tradeenum AS ENUM ('PLUMBING', 'ELECTRICAL', 'SOLAR', 'WELDING', 'BUILDING', 'APPLIANCE_REPAIR');
CREATE TYPE disputestatusenum AS ENUM ('OPEN', 'RESOLVED_RETURN_VISIT');
CREATE TYPE creworderstatusenum AS ENUM ('REQUESTED', 'MATCHED', 'BOOKED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');
CREATE TYPE gradeenum AS ENUM ('REGISTERED', 'IDENTIFIED', 'APPRENTICE', 'JOURNEYMAN', 'EXPERT');
CREATE TYPE currencyenum AS ENUM ('USD', 'ECOCASH', 'ZWG');

-- Approximate suburb centroids for MVP distance banding (Stage One pilot,
-- Bulawayo). Refine with surveyed coordinates before widening coverage.
CREATE TABLE suburbs (
    name VARCHAR(100) PRIMARY KEY,
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL
);

INSERT INTO suburbs (name, latitude, longitude) VALUES
    ('Nkulumane', -20.2050, 28.5300),
    ('Njube', -20.1970, 28.5420),
    ('Entumbane', -20.2200, 28.5500),
    ('Luveve', -20.1550, 28.5300),
    ('Hillside', -20.1850, 28.6300),
    ('Kumalo', -20.1750, 28.6450);

CREATE TABLE persons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    role roleenum NOT NULL,
    next_of_kin_phone VARCHAR(20),
    guarantor_id UUID REFERENCES persons(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    trade tradeenum NOT NULL,
    grade gradeenum,
    proof_url VARCHAR(255),
    CONSTRAINT uq_skills_worker_trade UNIQUE (worker_id, trade)
);

CREATE TABLE service_areas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    suburb VARCHAR(100) NOT NULL REFERENCES suburbs(name),
    travel_means VARCHAR(50), -- BICYCLE, BAKKIE, WALKING
    CONSTRAINT uq_service_areas_worker_suburb UNIQUE (worker_id, suburb)
);

CREATE TABLE standings (
    worker_id UUID PRIMARY KEY REFERENCES persons(id) ON DELETE CASCADE,
    grade gradeenum DEFAULT 'REGISTERED',
    on_time_rate DECIMAL(5,2) DEFAULT 100.00,
    dispute_rate DECIMAL(5,2) DEFAULT 0.00,
    fill_rate DECIMAL(5,2) DEFAULT 0.00,
    jobs_completed INTEGER DEFAULT 0
);

-- Progressive vetting tiers (ADR-005, database_schema_design.md §9). Feeds
-- app/vetting.py::recompute_grade(), which sets standings.grade above.
CREATE TABLE worker_vetting (
    worker_id UUID PRIMARY KEY REFERENCES persons(id) ON DELETE CASCADE,
    id_photo_url VARCHAR(255),
    id_submitted_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE worker_references (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE worker_vouches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE, -- vouched for
    voucher_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE, -- the voucher
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_worker_vouches_worker_voucher UNIQUE (worker_id, voucher_id),
    CONSTRAINT check_worker_vouches_no_self_vouch CHECK (worker_id != voucher_id)
);

CREATE TABLE crews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL UNIQUE REFERENCES persons(id) ON DELETE CASCADE,
    name VARCHAR(100)
);

CREATE TABLE crew_members (
    crew_id UUID NOT NULL REFERENCES crews(id) ON DELETE CASCADE,
    worker_id UUID NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    PRIMARY KEY (crew_id, worker_id)
);

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    buyer_id UUID NOT NULL REFERENCES persons(id),
    worker_id UUID REFERENCES persons(id),
    status jobstatusenum NOT NULL,
    trade tradeenum NOT NULL,
    suburb VARCHAR(100) NOT NULL REFERENCES suburbs(name),
    address TEXT NOT NULL, -- hidden from workers until booking (see database_schema_design.md §4)
    landmark_narrative TEXT, -- additive geo-grounding, see §2.10
    latitude DECIMAL(9,6), -- additive GPS pin, see §2.10
    longitude DECIMAL(9,6), -- additive GPS pin, see §2.10
    problem_description TEXT,
    problem_photo_url VARCHAR(255),
    -- Set once at booking (ADR-002, see database_schema_design.md §10).
    -- Every ledger entry written afterward reuses this value.
    currency currencyenum,
    -- Two-tier quote breakdown (ADR-003, see database_schema_design.md §2.11).
    -- Set together by POST /jobs/{id}/quote; quote_amount is server-computed,
    -- never accepted directly from the client.
    labor_amount DECIMAL(10,2),
    materials_amount DECIMAL(10,2),
    quote_amount DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_job_quote_equals_labor_plus_materials CHECK (
        (quote_amount IS NULL AND labor_amount IS NULL AND materials_amount IS NULL)
        OR (quote_amount IS NOT NULL AND labor_amount IS NOT NULL
            AND materials_amount IS NOT NULL
            AND quote_amount = labor_amount + materials_amount)
    )
);

CREATE TABLE ledger_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id),
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    entry_type ledgerentrytypeenum NOT NULL,
    currency currencyenum NOT NULL DEFAULT 'USD', -- see database_schema_design.md §10
    external_reference VARCHAR(100), -- gateway transaction ref, nullable, see §10
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- worker_id is denormalized from jobs.worker_id (via job_id) for
-- worker-scoped record queries without a join; see
-- database_schema_design.md §2.9. Kept in sync by the
-- check_record_entry_worker_matches_job() trigger below.
CREATE TABLE record_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID UNIQUE NOT NULL REFERENCES jobs(id),
    worker_id UUID NOT NULL REFERENCES persons(id),
    what_was_done TEXT NOT NULL,
    client_words TEXT,
    before_photo_url VARCHAR(255),
    after_photo_url VARCHAR(255),
    signed_off_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE disputes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id),
    raised_by_id UUID NOT NULL REFERENCES persons(id), -- the buyer
    reason TEXT NOT NULL,
    status disputestatusenum NOT NULL,
    worker_response TEXT, -- nullable until the worker answers
    before_photo_url VARCHAR(255),
    after_photo_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP WITH TIME ZONE
);

-- Crew Hire (Stage Two scope, built ahead of schedule — see
-- database_schema_design.md §6). A parallel booking/ledger structure to
-- jobs/ledger_entries, kept separate rather than overloading them.
CREATE TABLE crew_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    buyer_id UUID NOT NULL REFERENCES persons(id), -- the organization
    crew_id UUID REFERENCES crews(id), -- nullable until booked
    status creworderstatusenum NOT NULL,
    trade tradeenum NOT NULL,
    suburb VARCHAR(100) NOT NULL REFERENCES suburbs(name),
    address TEXT NOT NULL, -- hidden from the crew until booking
    landmark_narrative TEXT, -- additive geo-grounding, see §2.10
    latitude DECIMAL(9,6), -- additive GPS pin, see §2.10
    longitude DECIMAL(9,6), -- additive GPS pin, see §2.10
    workers_needed INTEGER NOT NULL CHECK (workers_needed > 0),
    problem_description TEXT,
    -- Set once at booking (ADR-002, see database_schema_design.md §10).
    currency currencyenum,
    -- Two-tier quote breakdown (ADR-003, see database_schema_design.md §2.11).
    labor_amount DECIMAL(10,2),
    materials_amount DECIMAL(10,2),
    quote_amount DECIMAL(10,2),
    completion_note TEXT, -- no per-worker RecordEntry analog exists for crews
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_crew_order_quote_equals_labor_plus_materials CHECK (
        (quote_amount IS NULL AND labor_amount IS NULL AND materials_amount IS NULL)
        OR (quote_amount IS NOT NULL AND labor_amount IS NOT NULL
            AND materials_amount IS NOT NULL
            AND quote_amount = labor_amount + materials_amount)
    )
);

CREATE TABLE crew_order_ledger_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    crew_order_id UUID NOT NULL REFERENCES crew_orders(id),
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    entry_type ledgerentrytypeenum NOT NULL,
    currency currencyenum NOT NULL DEFAULT 'USD', -- see database_schema_design.md §10
    external_reference VARCHAR(100), -- gateway transaction ref, nullable, see §10
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Immutability: ledger_entries, record_entries, and crew_order_ledger_entries
-- may only be inserted, never updated or deleted, per the immutable-record
-- design principle.
CREATE OR REPLACE FUNCTION prevent_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION '% is immutable: % not permitted on table %', TG_TABLE_NAME, TG_OP, TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ledger_entries_immutable
    BEFORE UPDATE OR DELETE ON ledger_entries
    FOR EACH ROW EXECUTE FUNCTION prevent_mutation();

CREATE TRIGGER record_entries_immutable
    BEFORE UPDATE OR DELETE ON record_entries
    FOR EACH ROW EXECUTE FUNCTION prevent_mutation();

-- Enforces record_entries.worker_id (see the comment on that table above)
-- stays in sync with jobs.worker_id. INSERT-only guard: record_entries is
-- already immutable, so no UPDATE path needs the same protection.
CREATE OR REPLACE FUNCTION check_record_entry_worker_matches_job()
RETURNS TRIGGER AS $$
DECLARE
    job_worker_id UUID;
BEGIN
    SELECT worker_id INTO job_worker_id FROM jobs WHERE id = NEW.job_id;
    IF job_worker_id IS NULL OR job_worker_id != NEW.worker_id THEN
        RAISE EXCEPTION
            'record_entries.worker_id (%) does not match jobs.worker_id (%) for job_id %',
            NEW.worker_id, job_worker_id, NEW.job_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER record_entries_worker_matches_job
    BEFORE INSERT ON record_entries
    FOR EACH ROW EXECUTE FUNCTION check_record_entry_worker_matches_job();

CREATE TRIGGER crew_order_ledger_entries_immutable
    BEFORE UPDATE OR DELETE ON crew_order_ledger_entries
    FOR EACH ROW EXECUTE FUNCTION prevent_mutation();

-- Admin-editable EcoCash merchant credentials (ADR-002, see
-- database_schema_design.md §10). Entered/rotated from the running system
-- (OPS-only endpoints), never env vars. api_key is plaintext today — a
-- known, documented limitation, not an oversight.
CREATE TABLE payment_gateway_configs (
    provider VARCHAR(20) PRIMARY KEY, -- e.g. 'ECOCASH'
    merchant_code VARCHAR(100),
    api_key VARCHAR(255),
    base_url VARCHAR(255),
    is_sandbox BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Append-only audit trail of every EcoCash webhook call received.
-- Deliberately not reconciled back into the immutable ledger tables above
-- by mutation — see database_schema_design.md §10.
CREATE TABLE ecocash_callback_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_reference VARCHAR(100) NOT NULL,
    raw_payload TEXT NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_ecocash_callback_logs_external_reference
    ON ecocash_callback_logs (external_reference);

CREATE TRIGGER ecocash_callback_logs_immutable
    BEFORE UPDATE OR DELETE ON ecocash_callback_logs
    FOR EACH ROW EXECUTE FUNCTION prevent_mutation();
