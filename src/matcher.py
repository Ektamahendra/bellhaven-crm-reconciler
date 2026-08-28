from rapidfuzz.fuzz import ratio

from src.normalize import normalize_record


def compare_records(website_record, crm_record):
    web = normalize_record(website_record, "website")
    crm = normalize_record(crm_record, "crm")

    name_score = ratio(web["name"], crm["name"])
    address_score = ratio(web["address"], crm["address"])

    city_match = web["city"] == crm["city"] and bool(web["city"])
    state_match = web["state"] == crm["state"] and bool(web["state"])
    zip_match = web["zip"] == crm["zip"] and bool(web["zip"])

    score = 0

    score += name_score * 0.35
    score += address_score * 0.35

    if zip_match:
        score += 20

    if city_match:
        score += 5

    if state_match:
        score += 5

    return {
        "score": round(score, 2),
        "name_score": round(name_score, 2),
        "address_score": round(address_score, 2),
        "city_match": city_match,
        "state_match": state_match,
        "zip_match": zip_match,
    }


def find_best_match(website_record, crm_accounts):
    candidates = []

    for crm_record in crm_accounts:
        comparison = compare_records(website_record, crm_record)

        candidates.append({
            "crm_record": crm_record,
            "comparison": comparison,
        })

    candidates.sort(
        key=lambda item: item["comparison"]["score"],
        reverse=True,
    )

    best = candidates[0] if candidates else None
    second = candidates[1] if len(candidates) > 1 else None

    return best, second


def classify_match(best, second=None):
    if not best:
        return "NO_MATCH"

    best_score = best["comparison"]["score"]
    second_score = (
        second["comparison"]["score"]
        if second
        else 0
    )

    gap = best_score - second_score

    if best_score >= 92 and gap >= 8:
        return "CONFIDENT"

    if best_score >= 78:
        return "NEEDS_REVIEW"

    return "NO_MATCH"
