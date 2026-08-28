from src.business_rules import decide_action, BELLHAVEN_PARENT_ID
from src.matcher import find_best_match, classify_match
from src.normalize import normalize_record


def build_current_facility_proposals(website_records, crm_accounts):
    proposals = []
    matched_ids = set()

    for website in website_records:
        best, second = find_best_match(website, crm_accounts)
        match_class = classify_match(best, second)

        if best:
            matched_ids.add(best["crm_record"].get("account_id"))

        decision = decide_action(
            website,
            best,
            match_class,
        )

        if decision["action"] == "NO_ACTION":
            continue

        proposals.append({
            "type": decision["action"],
            "website_record": website,
            "crm_record": best["crm_record"] if best else None,
            "match_score": (
                best["comparison"]["score"]
                if best
                else None
            ),
            "reason": decision["reason"],
            "requires_approval": True,
        })

    return proposals, matched_ids


def find_duplicate_pairs(crm_accounts):
    bellhaven_accounts = [
        account
        for account in crm_accounts
        if account.get("parent_id") == BELLHAVEN_PARENT_ID
    ]

    pairs = []

    for i in range(len(bellhaven_accounts)):
        for j in range(i + 1, len(bellhaven_accounts)):
            first = bellhaven_accounts[i]
            second = bellhaven_accounts[j]

            first_norm = normalize_record(first, "crm")
            second_norm = normalize_record(second, "crm")

            same_name = (
                first_norm["name"]
                == second_norm["name"]
                and bool(first_norm["name"])
            )

            same_address = (
                first_norm["address"]
                == second_norm["address"]
                and bool(first_norm["address"])
            )

            same_zip = (
                first_norm["zip"]
                == second_norm["zip"]
                and bool(first_norm["zip"])
            )

            if same_name and same_address and same_zip:
                pairs.append({
                    "type": "DUPLICATE_REVIEW",
                    "record_a": first,
                    "record_b": second,
                    "reason": (
                        "Both CRM accounts normalize to the same facility "
                        "name, street address, and ZIP code. A reviewer must "
                        "choose the surviving account before the other account "
                        "is marked Inactive and duplicate_of_account is set."
                    ),
                    "requires_approval": True,
                })

    return pairs


def build_stale_review_proposals(
    website_records,
    crm_accounts,
    matched_ids,
):
    proposals = []

    duplicate_ids = set()

    for pair in find_duplicate_pairs(crm_accounts):
        duplicate_ids.add(pair["record_a"].get("account_id"))
        duplicate_ids.add(pair["record_b"].get("account_id"))

    for account in crm_accounts:
        account_id = account.get("account_id")

        if account.get("parent_id") != BELLHAVEN_PARENT_ID:
            continue

        if account_id in matched_ids:
            continue

        if account_id in duplicate_ids:
            continue

        revenue = float(account.get("lifetime_revenue") or 0)
        ar = float(account.get("outstanding_ar") or 0)

        if revenue > 0 or ar > 0:
            proposal_type = "HISTORICAL_ACCOUNT_REVIEW"
            reason = (
                "Account is currently under Bellhaven but does not appear "
                "among current website facilities and contains financial "
                "history. Do not automatically inactivate or re-parent it."
            )
        else:
            proposal_type = "STALE_ACCOUNT_REVIEW"
            reason = (
                "Account is currently under Bellhaven but does not appear "
                "among current website facilities. Review ownership/history "
                "before changing status."
            )

        proposals.append({
            "type": proposal_type,
            "crm_record": account,
            "reason": reason,
            "requires_approval": True,
        })

    return proposals


def build_all_proposals(website_records, crm_accounts):
    current, matched_ids = build_current_facility_proposals(
        website_records,
        crm_accounts,
    )

    duplicates = find_duplicate_pairs(crm_accounts)

    stale = build_stale_review_proposals(
        website_records,
        crm_accounts,
        matched_ids,
    )

    return current + duplicates + stale
