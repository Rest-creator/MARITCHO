-- Initial Database Schema for Maricho

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE persons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL, -- BUYER, WORKER, OPS
    guarantor_id UUID REFERENCES persons(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE service_areas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    suburb VARCHAR(100) NOT NULL,
    travel_means VARCHAR(50) -- BICYCLE, BAKKIE, WALKING
);

CREATE TABLE standings (
    worker_id UUID PRIMARY KEY REFERENCES persons(id) ON DELETE CASCADE,
    grade VARCHAR(50) DEFAULT 'REGISTERED', -- REGISTERED, IDENTIFIED, APPRENTICE, JOURNEYMAN, EXPERT
    on_time_rate DECIMAL(5,2) DEFAULT 100.00,
    dispute_rate DECIMAL(5,2) DEFAULT 0.00,
    fill_rate DECIMAL(5,2) DEFAULT 0.00
);

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    buyer_id UUID REFERENCES persons(id),
    worker_id UUID REFERENCES persons(id),
    status VARCHAR(50) NOT NULL, -- REQUESTED, MATCHED, BOOKED, IN_PROGRESS, DISPUTED, COMPLETED
    suburb VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ledger_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id),
    amount DECIMAL(10,2) NOT NULL,
    type VARCHAR(50) NOT NULL, -- DEPOSIT_HELD, BALANCE_COMMITTED, RELEASED, REFUNDED
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE record_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) UNIQUE,
    worker_id UUID REFERENCES persons(id),
    what_was_done TEXT NOT NULL,
    client_words TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
