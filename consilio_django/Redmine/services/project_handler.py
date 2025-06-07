from .redmine_client import RedmineClient
from ..models import Project
from django.db import transaction

def sync_projects(api_key):
    client = RedmineClient(api_key)
    data = client.fetch("projects")

    # Sada ID všech projektů, která právě Redmine vrací
    remote_ids = set(item["id"] for item in data)

    with transaction.atomic():
        # 1) Aktualizace nebo vytvoření všech projektů z Redmine
        for item in data:
            created_on = item.get("created_on")
            create_date = created_on.split("T")[0] if created_on else None

            Project.objects.update_or_create(
                id=item["id"],  # id je PK našeho Project
                defaults={
                    "name": item["name"],
                    "createDate": create_date
                }
            )

        # 2) Smazání všech projektů v DB, jejichž id není v remote_ids
        Project.objects.exclude(id__in=remote_ids).delete()

