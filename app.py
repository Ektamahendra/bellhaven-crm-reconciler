import streamlit as st




def execute_approved_change(proposal, survivor=None):
    """Apply a reviewer-approved CRM change."""
    proposal_type = proposal.get("type")
    crm = proposal.get("crm_record") or {}
    website = proposal.get("website_record") or {}

    if proposal_type == "REPARENT_EXISTING_ACCOUNT":
        update_account(
            crm["account_id"],
            {"parent_id": "0015QAPLGS3FVYEEEM"},
            dry_run=False,
        )
        return True

    if proposal_type == "CHOW_CREATE_NEW_ACCOUNT":
        execute_chow_change(proposal)
        return True

    if proposal_type == "CREATE_NEW_ACCOUNT":
        create_account(
            {
                "name": website.get("name"),
                "parent_id": "0015QAPLGS3FVYEEEM",
                "billing_street": website.get("address"),
                "billing_city": website.get("city"),
                "billing_state": website.get("state"),
                "billing_zip": website.get("zip"),
                "status": "Active",
                "note": "Created after approved Bellhaven reconciliation.",
            },
            dry_run=False,
        )
        return True

    if proposal_type == "DUPLICATE_REVIEW":
        a = proposal.get("record_a") or {}
        b = proposal.get("record_b") or {}

        if survivor == "Do not choose yet":
            raise ValueError("Choose Record A or Record B.")

        if survivor and survivor.startswith("Record A"):
            winner, loser = a, b
        else:
            winner, loser = b, a

        update_account(
            loser["account_id"],
            {
                "status": "Inactive",
                "duplicate_of_account": winner["account_id"],
                "note": "Duplicate confirmed by reviewer.",
            },
            dry_run=False,
        )
        return True

    if proposal_type == "STALE_ACCOUNT_REVIEW":
        update_account(
            crm["account_id"],
            {
                "status": "Inactive",
                "note": "Marked inactive after reviewer approval.",
            },
            dry_run=False,
        )
        return True

    return False

def execute_chow_change(proposal):
    """Execute an approved CHOW change following the assessment SOP."""
    website = proposal.get("website_record") or {}
    old_account = proposal.get("crm_record") or {}

    if not website or not old_account:
        raise ValueError("CHOW proposal is missing website_record or crm_record.")

    new_account = create_account(
        {
            "name": website.get("name"),
            "parent_id": "0015QAPLGS3FVYEEEM",
            "billing_street": website.get("address"),
            "billing_city": website.get("city"),
            "billing_state": website.get("state"),
            "billing_zip": website.get("zip"),
            "status": "Active",
            "note": "Created by Bellhaven reconciliation after approved CHOW review.",
        },
        dry_run=False,
    )

    new_account_id = new_account.get("account_id")
    if not new_account_id:
        raise ValueError("CRM did not return account_id for new CHOW account.")

    update_account(
        old_account["account_id"],
        {
            "chow_current_account": new_account_id,
            "note": (
                "Historical account preserved under CHOW SOP. "
                f"Current ownership continues in account {new_account_id}."
            ),
        },
        dry_run=False,
    )

    return new_account

from collections import Counter

from src.scraper import scrape_all_communities
from src.crm_client import get_all_accounts, update_account, create_account
from src.proposals import build_all_proposals
from src.database import (
    save_new_proposals,
    get_proposals,
    record_decision,
)

st.set_page_config(
    page_title="Bellhaven CRM Reconciliation",
    layout="wide",
)

st.title("Bellhaven CRM Reconciliation")
st.caption(
    "Daily CRM reconciliation with evidence, human review, "
    "and approval-gated writes."
)

# -------------------------
# Refresh / pipeline section
# -------------------------

if st.button("Run reconciliation now"):
    with st.spinner("Checking website and CRM..."):
        website = scrape_all_communities()
        crm = get_all_accounts()
        proposals = build_all_proposals(website, crm)
        result = save_new_proposals(proposals)

    st.success(
        f"Reconciliation complete. "
        f"New proposals: {result['inserted']} | "
        f"Already known: {result['already_known']}"
    )

# -------------------------
# Load current data
# -------------------------

website = scrape_all_communities()
crm = get_all_accounts()
pending = get_proposals("PENDING")
approved = get_proposals("APPROVED")
rejected = get_proposals("REJECTED")

# -------------------------
# Summary metrics
# -------------------------

c1, c2, c3, c4 = st.columns(4)

c1.metric("Website facilities", len(website))
c2.metric("CRM accounts", len(crm))
c3.metric("Pending review", len(pending))
c4.metric(
    "Decided",
    len(approved) + len(rejected),
)

st.divider()

# -------------------------
# Proposal filters
# -------------------------

st.subheader("Review queue")

types = sorted(
    {
        row["proposal_type"]
        for row in pending
    }
)

selected_type = st.selectbox(
    "Filter by proposal type",
    ["ALL"] + types,
)

visible = [
    row
    for row in pending
    if selected_type == "ALL"
    or row["proposal_type"] == selected_type
]

st.write(f"Showing {len(visible)} pending proposals")

# -------------------------
# Proposal cards
# -------------------------

for row in visible:
    proposal = row["proposal"]
    proposal_id = row["proposal_id"]

    website_record = proposal.get("website_record") or {}
    crm_record = proposal.get("crm_record") or {}
    record_a = proposal.get("record_a") or {}
    record_b = proposal.get("record_b") or {}

    subject = (
        website_record.get("name")
        or crm_record.get("name")
        or record_a.get("name")
        or row.get("subject_name")
        or "Unknown"
    )

    with st.expander(
        f"{proposal['type']} — {subject}",
        expanded=False,
    ):
        st.markdown(
            f"**Reason:** {proposal.get('reason', '')}"
        )

        if proposal.get("match_score") is not None:
            st.write(
                f"Match confidence score: "
                f"{proposal['match_score']}"
            )

        # Website evidence
        if website_record:
            st.markdown("### Website evidence")

            wc1, wc2 = st.columns(2)

            with wc1:
                st.write(
                    "Name:",
                    website_record.get("name", ""),
                )
                st.write(
                    "Address:",
                    website_record.get("address", ""),
                )
                st.write(
                    "City:",
                    website_record.get("city", ""),
                )

            with wc2:
                st.write(
                    "State:",
                    website_record.get("state", ""),
                )
                st.write(
                    "ZIP:",
                    website_record.get("zip", ""),
                )
                st.write(
                    "Care offerings:",
                    ", ".join(
                        website_record.get(
                            "care_offerings",
                            [],
                        )
                    ),
                )

        # CRM evidence
        if crm_record:
            st.markdown("### CRM evidence")

            cc1, cc2 = st.columns(2)

            with cc1:
                st.write(
                    "Account:",
                    crm_record.get("name", ""),
                )
                st.write(
                    "Account ID:",
                    crm_record.get(
                        "account_id",
                        "",
                    ),
                )
                st.write(
                    "Parent:",
                    crm_record.get(
                        "parent_name",
                        "",
                    ),
                )
                st.write(
                    "Status:",
                    crm_record.get(
                        "status",
                        "",
                    ),
                )

            with cc2:
                st.write(
                    "Lifetime revenue:",
                    crm_record.get(
                        "lifetime_revenue",
                        0,
                    ),
                )
                st.write(
                    "Outstanding AR:",
                    crm_record.get(
                        "outstanding_ar",
                        0,
                    ),
                )
                st.write(
                    "CHOW current account:",
                    crm_record.get(
                        "chow_current_account",
                        "",
                    ),
                )
                st.write(
                    "Duplicate of:",
                    crm_record.get(
                        "duplicate_of_account",
                        "",
                    ),
                )

        # Duplicate review evidence
        if record_a and record_b:
            st.markdown("### Duplicate candidate")

            st.info(
                "These two CRM records appear to represent the same "
                "physical facility, but a reviewer must decide which "
                "record should survive."
            )

            st.markdown("### Why was this flagged?")
            st.write("✓ Same facility name")
            st.write("✓ Same normalized street address")
            st.write("✓ Same city, state, and ZIP")
            st.write("✓ Same Bellhaven parent")

            st.markdown("### Compare the two CRM records")

            d1, d2 = st.columns(2)

            with d1:
                st.markdown("#### Record A")
                st.write("**Account ID:**", record_a.get("account_id", ""))
                st.write("**Name:**", record_a.get("name", ""))
                st.write("**Address:**", record_a.get("billing_street", ""))
                st.write(
                    "**City / State / ZIP:**",
                    record_a.get("billing_city", ""),
                    record_a.get("billing_state", ""),
                    record_a.get("billing_zip", ""),
                )
                st.write("**Phone:**", record_a.get("phone", ""))
                st.write(
                    "**Lifetime revenue:**",
                    record_a.get("lifetime_revenue", 0),
                )
                st.write(
                    "**Outstanding AR:**",
                    record_a.get("outstanding_ar", 0),
                )

            with d2:
                st.markdown("#### Record B")
                st.write("**Account ID:**", record_b.get("account_id", ""))
                st.write("**Name:**", record_b.get("name", ""))
                st.write("**Address:**", record_b.get("billing_street", ""))
                st.write(
                    "**City / State / ZIP:**",
                    record_b.get("billing_city", ""),
                    record_b.get("billing_state", ""),
                    record_b.get("billing_zip", ""),
                )
                st.write("**Phone:**", record_b.get("phone", ""))
                st.write(
                    "**Lifetime revenue:**",
                    record_b.get("lifetime_revenue", 0),
                )
                st.write(
                    "**Outstanding AR:**",
                    record_b.get("outstanding_ar", 0),
                )

            st.warning(
                "The phone numbers differ. The system will not "
                "automatically decide which CRM record should survive."
            )

            survivor = st.radio(
                "Which record should remain active?",
                [
                    "Do not choose yet",
                    f"Record A — {record_a.get('account_id', '')}",
                    f"Record B — {record_b.get('account_id', '')}",
                ],
                key=f"survivor_{proposal_id}",
            )

        # Dry-run preview for direct re-parenting
        if (
            proposal["type"]
            == "REPARENT_EXISTING_ACCOUNT"
            and crm_record
        ):
            st.markdown("### Proposed CRM change")

            preview = update_account(
                crm_record["account_id"],
                {
                    "parent_id":
                    "0015QAPLGS3FVYEEEM"
                },
                dry_run=True,
            )

            st.json(preview)

        note = st.text_area(
            "Reviewer note",
            key=f"note_{proposal_id}",
        )

        approve_col, reject_col = st.columns(2)

        with approve_col:
            if st.button(
                "Approve",
                key=f"approve_{proposal_id}",
                use_container_width=True,
            ):
                if proposal["type"] == "DUPLICATE_REVIEW" and survivor == "Do not choose yet":
                    st.error("Choose Record A or Record B before approving.")
                    st.stop()

                did_write = execute_approved_change(proposal, locals().get('survivor'))

                record_decision(
                    proposal_id,
                    "APPROVED",
                    note,
                )

                if did_write:
                    st.success("Approved and written to CRM.")
                else:
                    st.success("Approved and recorded. No CRM change required.")

                st.rerun()

        with reject_col:
            if st.button(
                "Reject",
                key=f"reject_{proposal_id}",
                use_container_width=True,
            ):
                record_decision(
                    proposal_id,
                    "REJECTED",
                    note,
                )

                st.info(
                    "Rejected and recorded."
                )

                st.rerun()

# -------------------------
# Decision history
# -------------------------

st.divider()
st.subheader("Decision history")

history = approved + rejected

if not history:
    st.write("No decisions recorded yet.")
else:
    counts = Counter(
        row["status"]
        for row in history
    )

    st.write(
        {
            "approved": counts.get(
                "APPROVED",
                0,
            ),
            "rejected": counts.get(
                "REJECTED",
                0,
            ),
        }
    )

    for row in history:
        st.write(
            row["status"],
            "|",
            row["proposal_type"],
            "|",
            row["subject_name"],
            "|",
            row.get(
                "decision_note",
                "",
            ),
        )
