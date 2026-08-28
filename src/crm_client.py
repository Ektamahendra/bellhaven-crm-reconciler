import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://analyst-assessment-production.up.railway.app/api/v1"
CRM_TOKEN = os.getenv("CRM_TOKEN")


def get_all_accounts(page_size=50):
    if not CRM_TOKEN:
        raise RuntimeError("CRM_TOKEN is missing from .env")

    accounts = []
    page = 1

    while True:
        response = requests.get(
            f"{BASE_URL}/accounts",
            headers={"Authorization": f"Bearer {CRM_TOKEN}"},
            params={"page": page, "page_size": page_size},
            timeout=20,
        )

        response.raise_for_status()
        payload = response.json()

        records = payload.get("data", [])
        total = payload.get("total", 0)

        accounts.extend(records)

        if not records or len(accounts) >= total:
            break

        page += 1

    return accounts


if __name__ == "__main__":
    accounts = get_all_accounts()
    print(f"TOTAL ACCOUNTS FETCHED: {len(accounts)}")

    if accounts:
        print(f"FIRST ACCOUNT: {accounts[0].get('name')}")
        print(f"LAST ACCOUNT: {accounts[-1].get('name')}")


def get_account(account_id):
    response = requests.get(
        f"{BASE_URL}/accounts/{account_id}",
        headers={
            "Authorization": f"Bearer {CRM_TOKEN}",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def update_account(account_id, changes, dry_run=True):
    """
    Update an existing CRM account.

    dry_run=True is the default safety boundary.
    Nothing is written unless dry_run is explicitly False.
    """

    payload = {
        key: value
        for key, value in changes.items()
        if value is not None
    }

    if dry_run:
        return {
            "dry_run": True,
            "method": "PATCH",
            "account_id": account_id,
            "payload": payload,
        }

    response = requests.patch(
        f"{BASE_URL}/accounts/{account_id}",
        headers={
            "Authorization": f"Bearer {CRM_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    response.raise_for_status()
    return response.json()


def create_account(fields, dry_run=True):
    """
    Create a CRM account.

    dry_run=True by default so account creation cannot occur accidentally.
    """

    payload = {
        key: value
        for key, value in fields.items()
        if value is not None
    }

    if dry_run:
        return {
            "dry_run": True,
            "method": "POST",
            "payload": payload,
        }

    response = requests.post(
        f"{BASE_URL}/accounts",
        headers={
            "Authorization": f"Bearer {CRM_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    response.raise_for_status()
    return response.json()
