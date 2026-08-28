# Bellhaven CRM Reconciler

A CRM reconciliation tool built for the Bellhaven Senior Living technical assessment.

The application compares Bellhaven's current website community data with CRM account records, identifies discrepancies, generates reviewable proposals, and requires human approval before making CRM changes.

## What It Does

- Scrapes Bellhaven community locations from the website
- Captures facility name, address, city, state, ZIP code, and care offerings
- Normalizes website and CRM data for comparison
- Matches website facilities to CRM accounts
- Identifies confident matches, records needing review, missing CRM accounts, duplicates, stale or historical accounts, and parent-account issues
- Applies Bellhaven financial-history and CHOW business rules
- Shows proposed changes and supporting evidence in a Streamlit review interface
- Requires reviewer approval before any CRM write
- Records approved and rejected decisions
- Prevents previously reviewed proposals from being repeatedly proposed
- Supports a scheduled daily reconciliation run

## Safety and Business Rules

CRM changes are never written automatically from a reconciliation proposal.

A reviewer must approve a proposed change before the CRM API is called.

For parent-account corrections, the application preserves historical records when an account has both lifetime revenue greater than zero and outstanding accounts receivable greater than zero.

Duplicate accounts are not deleted. The losing record is marked inactive and linked to the surviving account using `duplicate_of_account`.

## Project Structure

- `app.py` - Streamlit review application
- `daily_reconcile.py` - Daily reconciliation runner
- `run_pipeline.py` - Reconciliation pipeline
- `src/scraper.py` - Website data extraction
- `src/normalize.py` - Data normalization
- `src/matcher.py` - Matching logic
- `src/business_rules.py` - CRM and CHOW rules
- `src/proposals.py` - Proposal generation
- `src/database.py` - Proposal and decision persistence
- `src/crm_client.py` - CRM API client
- `.github/workflows/daily-reconciliation.yml` - Daily schedule

## Running Locally

Install dependencies:

`pip install -r requirements.txt`

Run the review application:

`streamlit run app.py`

Run reconciliation directly:

`python3 daily_reconcile.py`

## Environment Variables

The application expects the CRM authentication token to be provided through an environment variable:

`CRM_TOKEN`

For local development, this can be stored in a `.env` file.

For GitHub Actions, the token is stored securely as a repository secret and is not committed to source control.

## Idempotency

Proposal identities are persisted so rerunning reconciliation does not recreate proposals that are already known or reviewed.

A test rerun returned existing proposals as `already_known` rather than inserting duplicates.

## Daily Schedule

A GitHub Actions workflow is included at `.github/workflows/daily-reconciliation.yml`.

It is configured for a daily reconciliation run and also supports manual execution through `workflow_dispatch`.

CRM credentials should be stored as GitHub repository secrets rather than committed to source control.

## Technology

Python, Streamlit, SQLite, Requests, and GitHub Actions.



## Assessment Notes

Matching uses normalized facility names, addresses, city/state/ZIP information, and fuzzy comparison to identify the most likely CRM account for each website community. High-confidence records are classified automatically, while ambiguous records are routed to human review.

AI-assisted development was used for implementation support, debugging, and code review. Final reconciliation decisions and CRM approvals were made through the human-review workflow.

If I continued developing this system, I would move proposal and decision persistence from local SQLite to a durable production database, add automated test coverage for reconciliation and CHOW scenarios, improve entity-resolution confidence scoring, and add monitoring for scheduled reconciliation failures.
