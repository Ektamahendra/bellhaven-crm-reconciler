BELLHAVEN_PARENT_ID = "0015QAPLGS3FVYEEEM"
BELLHAVEN_PARENT_NAME = "Bellhaven Senior Living (Parent Account)"


def to_number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def decide_action(website_record, best_match, match_class):
    if not best_match:
        return {
            "action": "CREATE_NEW_ACCOUNT",
            "reason": "No suitable CRM account was found for this website facility.",
            "requires_approval": True,
        }

    crm = best_match["crm_record"]
    score = best_match["comparison"]["score"]

    if match_class == "NEEDS_REVIEW":
        return {
            "action": "REVIEW_MATCH",
            "reason": f"Best match scored {score}, so identity should be confirmed by a reviewer.",
            "requires_approval": True,
        }

    if match_class == "NO_MATCH":
        return {
            "action": "CREATE_NEW_ACCOUNT",
            "reason": "No sufficiently reliable CRM match was found.",
            "requires_approval": True,
        }

    current_parent_id = crm.get("parent_id") or ""

    if current_parent_id == BELLHAVEN_PARENT_ID:
        return {
            "action": "NO_ACTION",
            "reason": "Facility is confidently matched and already belongs to the correct Bellhaven parent.",
            "requires_approval": False,
        }

    revenue = to_number(crm.get("lifetime_revenue"))
    outstanding_ar = to_number(crm.get("outstanding_ar"))

    if revenue > 0 and outstanding_ar > 0:
        return {
            "action": "CHOW_CREATE_NEW_ACCOUNT",
            "reason": (
                "Facility needs a different parent, but the existing account has both "
                "historical revenue and outstanding AR. Preserve the old account, create "
                "a new account under Bellhaven, and link the old account through "
                "chow_current_account."
            ),
            "requires_approval": True,
        }

    return {
        "action": "REPARENT_EXISTING_ACCOUNT",
        "reason": (
            "Facility is confidently matched but has the wrong or missing parent. "
            "The account does not have both historical revenue and outstanding AR, "
            "so the SOP allows the existing account to be re-parented directly."
        ),
        "requires_approval": True,
    }
