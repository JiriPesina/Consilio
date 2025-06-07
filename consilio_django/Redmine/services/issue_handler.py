from .redmine_client import RedmineClient
from ..models import Issue
from django.db import transaction
from requests.exceptions import RequestException

def sync_issues(api_key):
    client = RedmineClient(api_key)
    data = client.fetch("issues")

    # Seznam ID, která právě Redmine vrací
    remote_ids = set(item["id"] for item in data)

    with transaction.atomic():
        # 1) Projdeme všechny položky z Redmine a vytvoříme / aktualizujeme je
        for item in data:
            due_date = item.get("due_date")
            Issue.objects.update_or_create(
                id=item["id"],
                defaults={
                    "project_id_id": item["project"]["id"],
                    "name": item["subject"],
                    "status": item["status"]["name"],
                    "priority": item["priority"]["name"],
                    "assigned_id": item.get("assigned_to", {}).get("id"),
                    "completion_percentage": item["done_ratio"],
                    "deadline": due_date,
                    "type": item["tracker"]["name"],
                }
            )

        # 2) Smažeme všechny Issue v DB, které v remote_ids nejsou
        Issue.objects.exclude(id__in=remote_ids).delete()

def assign_issue_to_user(api_key: str, issue_id: int, user_redmine_id: int) -> None:
    client = RedmineClient(api_key)
    payload = {"issue": {"assigned_to_id": user_redmine_id}}
    # využije session, která má hlavičky nastavené
    response = client.session.put(
        f"https://projects.olc.cz/issues/{issue_id}.json",
        json=payload
    )
    response.raise_for_status()


