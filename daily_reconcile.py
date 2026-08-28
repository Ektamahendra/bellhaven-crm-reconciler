from src.scraper import scrape_all_communities
from src.crm_client import get_all_accounts
from src.proposals import build_all_proposals
from src.database import initialize_database, save_new_proposals


def main():
    initialize_database()

    website_records = scrape_all_communities()
    crm_accounts = get_all_accounts()

    proposals = build_all_proposals(
        website_records,
        crm_accounts
    )

    result = save_new_proposals(proposals)

    print("Website facilities:", len(website_records))
    print("CRM accounts:", len(crm_accounts))
    print("Generated proposals:", len(proposals))
    print("Save result:", result)


if __name__ == "__main__":
    main()
