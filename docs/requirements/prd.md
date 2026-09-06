# Maricho Product Requirements Document (PRD)

## 1. Personas

| Persona | Role | Primary Goal | Core Fear |
| :--- | :--- | :--- | :--- |
| **Tendai Ncube (24)** | Tradesman (Worker) | Get paid reliably for completed work. | Spending fare on phantom jobs; unpaid labor. |
| **Sithembile Ncube (52)** | Homeowner (Quick Hire) | Find a verified, accountable tradesman quickly. | Being overcharged; strangers in her home. |
| **Sipho Dube (41)** | Ops Manager (Crew Hire) | Staff a site reliably to avoid penalty clauses. | Day-four attrition; skill claims being false. |
| **Baba Moyo (47)** | Crew Lead (Aggregator) | Win large orders for his crew of twenty. | Platform routing around his existing network. |
| **Nomsa Sibanda (31)** | Domestic Worker | Secure recurring placements with stable rates. | Losing a placement over a misunderstanding. |

## 2. Core Functional Entities
- **Person:** ID, phone, guarantor, next of kin, role.
- **Skill:** Trade, grade, proof.
- **Service Area:** Suburbs covered, travel means.
- **Standing:** Grade, on-time rate, dispute rate, fill rate. Computed, never assigned.
- **Crew:** Lead + members.
- **Job:** Request, spec, booking, quote, evidence, sign-off.
- **Ledger Entry:** Deposit, balance, release.
- **Record Entry:** What was done, where, when, for whom, proof, their words. Immutable once signed off.

## 3. User Journeys & Business Rules

### 3.1. The Quick Hire Job Lifecycle
1. **Request:** Buyer describes problem (voice, photo, or text).
2. **Matching:** System returns exactly three workers. Match is based on: meaning (not keyword), declared service area/distance, availability, and standing. *Rule: If we cannot say why, we do not show them.*
3. **Booking & Deposit:** Buyer sees price band, books, and pays a deposit. Address is revealed *only* at this moment.
4. **Acceptance:** Worker is alerted, sees deposit is secured, and accepts. *Rule: Passing on a job costs nothing and does not affect ranking.*
5. **Execution:** Worker travels, checks in (offline capability), prices the job standing in front of it (buyer approves quote), works, and takes before/after photographs.
6. **Completion:** Buyer signs off and rates. Balance is released same-day. Record entry is written.

### 3.2. Dispute Resolution
- **Rule:** Design for the worker's worst day.
- **Process:**
  - Buyer raises concern. Money freezes.
  - Worker must answer before any consequence.
  - Worker's job photographs are attached automatically.
  - Worker can appeal via voice (speaking is enough).
  - Default outcome is a *return visit* (not a refund) to fix the issue.

## 4. Behavioral Acceptance Criteria (BDD)

| Feature | Scenario | Given | When | Then |
| :--- | :--- | :--- | :--- | :--- |
| **Matching** | Returning a shortlist | A buyer submits a plumbing request | The matching engine runs | It must return exactly 3 candidates with an explanation for each. |
| **Booking** | Hiding addresses | A buyer is browsing the 3 candidates | The buyer views a profile | The worker's location must only show suburb and distance band. |
| **Booking** | Revealing addresses | A buyer selects a worker | The buyer pays the deposit | The exact job address is revealed to the worker. |
| **Declining** | Passing on a job | A worker receives a job alert | The worker taps "Pass" | The worker's standing and ranking must not decrease. |
| **Disputes** | Initiating a dispute | A buyer marks "unhappy" | The dispute workflow triggers | The worker's standing is frozen (not dropped) pending their response. |
| **Records** | Modifying a record | A job is signed off | An admin tries to edit the record | The system must block edits and only allow appending corrections. |
