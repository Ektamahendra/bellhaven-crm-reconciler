import hashlib
import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/reconciler.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


def initialize_database():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS proposals (
                proposal_id TEXT PRIMARY KEY,
                proposal_type TEXT NOT NULL,
                subject_name TEXT,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                decision_note TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT
            )
            """
        )

        conn.commit()


def proposal_identity(proposal):
    proposal_type = proposal.get("type", "")

    website = proposal.get("website_record") or {}
    crm = proposal.get("crm_record") or {}
    record_a = proposal.get("record_a") or {}
    record_b = proposal.get("record_b") or {}

    identity = {
        "type": proposal_type,

        "website_name": website.get("name"),
        "website_url": website.get("source_url"),

        "crm_account_id": crm.get("account_id"),

        "record_a_id": record_a.get("account_id"),
        "record_b_id": record_b.get("account_id"),
    }

    raw = json.dumps(
        identity,
        sort_keys=True,
        default=str,
    )

    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def proposal_subject(proposal):
    website = proposal.get("website_record") or {}
    crm = proposal.get("crm_record") or {}
    record_a = proposal.get("record_a") or {}

    return (
        website.get("name")
        or crm.get("name")
        or record_a.get("name")
        or "Unknown"
    )


def save_new_proposals(proposals):
    initialize_database()

    inserted = 0
    skipped = 0

    with get_connection() as conn:
        for proposal in proposals:
            proposal_id = proposal_identity(proposal)

            existing = conn.execute(
                """
                SELECT proposal_id
                FROM proposals
                WHERE proposal_id = ?
                """,
                (proposal_id,),
            ).fetchone()

            if existing:
                skipped += 1
                continue

            conn.execute(
                """
                INSERT INTO proposals (
                    proposal_id,
                    proposal_type,
                    subject_name,
                    payload_json,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, 'PENDING', ?)
                """,
                (
                    proposal_id,
                    proposal.get("type"),
                    proposal_subject(proposal),
                    json.dumps(proposal, default=str),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )

            inserted += 1

        conn.commit()

    return {
        "inserted": inserted,
        "already_known": skipped,
    }


def get_proposals(status=None):
    initialize_database()

    with get_connection() as conn:
        if status:
            rows = conn.execute(
                """
                SELECT *
                FROM proposals
                WHERE status = ?
                ORDER BY created_at, proposal_id
                """,
                (status,),
            ).fetchall()

        else:
            rows = conn.execute(
                """
                SELECT *
                FROM proposals
                ORDER BY created_at, proposal_id
                """
            ).fetchall()

    results = []

    for row in rows:
        item = dict(row)
        item["proposal"] = json.loads(item.pop("payload_json"))
        results.append(item)

    return results


def record_decision(proposal_id, status, note=""):
    if status not in {"APPROVED", "REJECTED"}:
        raise ValueError(
            "status must be APPROVED or REJECTED"
        )

    initialize_database()

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE proposals
            SET
                status = ?,
                decision_note = ?,
                decided_at = ?
            WHERE proposal_id = ?
            """,
            (
                status,
                note,
                datetime.now().isoformat(timespec="seconds"),
                proposal_id,
            ),
        )

        conn.commit()


if __name__ == "__main__":
    initialize_database()
    print(f"DATABASE READY: {DB_PATH}")
