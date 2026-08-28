import re


STREET_REPLACEMENTS = {
    "street": "st",
    "st.": "st",
    "road": "rd",
    "rd.": "rd",
    "avenue": "ave",
    "ave.": "ave",
    "boulevard": "blvd",
    "blvd.": "blvd",
    "lane": "ln",
    "ln.": "ln",
    "drive": "dr",
    "dr.": "dr",
    "court": "ct",
    "ct.": "ct",
    "highway": "hwy",
    "hwy.": "hwy",
    "parkway": "pkwy",
    "pkwy.": "pkwy",
    "north": "n",
    "south": "s",
    "east": "e",
    "west": "w",
}


def normalize_text(value):
    if value is None:
        return ""

    value = str(value).lower().strip()
    value = value.replace("&", "and")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_name(value):
    value = normalize_text(value)

    removable_words = {
        "the",
        "senior",
        "living",
        "healthcare",
        "centre",
        "center",
    }

    words = [
        word
        for word in value.split()
        if word not in removable_words
    ]

    return " ".join(words)


def normalize_address(value):
    value = normalize_text(value)

    words = value.split()

    normalized_words = [
        STREET_REPLACEMENTS.get(word, word)
        for word in words
    ]

    return " ".join(normalized_words)


def normalize_zip(value):
    if value is None:
        return ""

    digits = re.sub(r"\D", "", str(value))

    return digits[:5]


def normalize_record(record, source):
    if source == "website":
        return {
            "name": normalize_name(record.get("name")),
            "address": normalize_address(record.get("address")),
            "city": normalize_text(record.get("city")),
            "state": normalize_text(record.get("state")),
            "zip": normalize_zip(record.get("zip")),
        }

    if source == "crm":
        return {
            "name": normalize_name(record.get("name")),
            "address": normalize_address(record.get("billing_street")),
            "city": normalize_text(record.get("billing_city")),
            "state": normalize_text(record.get("billing_state")),
            "zip": normalize_zip(record.get("billing_zip")),
        }

    raise ValueError("source must be 'website' or 'crm'")


if __name__ == "__main__":
    examples = [
        ("210 Orchard Lane", "210 ORCHARD LN."),
        ("Bellhaven of Maplewood", "Bellhaven of Maplewood Senior Living"),
    ]

    print("NORMALIZATION TEST")

    print(
        normalize_address(examples[0][0]),
        "==",
        normalize_address(examples[0][1]),
    )

    print(
        normalize_name(examples[1][0]),
        "==",
        normalize_name(examples[1][1]),
    )
