from .redmine_client import RedmineClient
from ..models import Project
from django.db import transaction

#ajišťuje synchronizaci projektů mezi systémem Redmine a lokální databází Django
def sync_projects(api_key):
    client = RedmineClient(api_key)
    data = client.fetch("projects")
    remote_ids = set(item["id"] for item in data)

    with transaction.atomic():
        for item in data:
            created_on = item.get("created_on")
            create_date = created_on.split("T")[0] if created_on else None
            parent_id = item.get("parent", {}).get("id")
            Project.objects.update_or_create(
                id=item["id"],
                defaults={
                    "name": item["name"],
                    "createDate": create_date,
                    "parent_id": parent_id,
                }
            )
        Project.objects.exclude(id__in=remote_ids).delete()

