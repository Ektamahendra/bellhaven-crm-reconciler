import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://analyst-assessment-production.up.railway.app"

SEED_PAGES = [
    "/",
    "/communities",
    "/about",
]


def get_community_links():
    found = {}

    for path in SEED_PAGES:
        url = urljoin(BASE_URL, path)

        response = requests.get(url, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            name = anchor.get_text(" ", strip=True)

            if href.startswith("/communities/"):
                full_url = urljoin(BASE_URL, href)

                if full_url not in found:
                    found[full_url] = name

    return [
        {
            "name": name,
            "url": url,
        }
        for url, name in sorted(found.items())
    ]


def parse_community_page(url):
    response = requests.get(url, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" | ", strip=True)

    title = soup.title.string if soup.title else ""
    name = title.split("—")[0].strip() if title else ""

    address_match = re.search(
        r"Address\s*\|\s*(.*?)\s*\|\s*([A-Za-z .'-]+),\s*([A-Z]{2})\s+(\d{5})",
        text
    )

    care_match = re.search(
        r"Care Offerings\s*\|\s*(.*?)(?:\s*\|\s*Administrator|\s*\|\s*Phone|\s*\|\s*← Back)",
        text
    )

    if not address_match:
        raise ValueError(f"Could not parse address for {url}")

    street = address_match.group(1).strip()
    city = address_match.group(2).strip()
    state = address_match.group(3).strip()
    zip_code = address_match.group(4).strip()

    care_offerings = []

    if care_match:
        raw_care = care_match.group(1).strip()
        care_offerings = [
            item.strip()
            for item in raw_care.split(",")
            if item.strip()
        ]

    return {
        "name": name,
        "address": street,
        "city": city,
        "state": state,
        "zip": zip_code,
        "care_offerings": care_offerings,
        "source_url": url,
    }


def scrape_all_communities():
    links = get_community_links()
    communities = []

    for item in links:
        community = parse_community_page(item["url"])
        communities.append(community)

    return communities


if __name__ == "__main__":
    communities = scrape_all_communities()

    print(f"TOTAL COMMUNITIES SCRAPED: {len(communities)}")

    for community in communities:
        print(
            community["name"],
            "|",
            community["address"],
            "|",
            community["city"],
            community["state"],
            community["zip"],
            "|",
            ", ".join(community["care_offerings"]),
        )
