# Celery tasks for syncing indexed content to Meilisearch

from celery import shared_task

from apps.search.service import SearchService


def _serialize_for_search(obj) -> dict | None:
    """Convert a model instance to a Meilisearch document."""
    if not obj or obj.is_deleted:
        return None
    data = {}
    for field in obj._meta.get_fields():
        if hasattr(field, "column") and hasattr(obj, field.name):
            val = getattr(obj, field.name)
            if hasattr(val, "pk"):
                val = str(val.pk)
            elif hasattr(val, "isoformat"):
                val = val.isoformat()
            data[field.name] = str(val) if val is not None else None
    return data


def _index_model(model_instance, model_name: str) -> None:
    """Index a model instance in Meilisearch."""
    doc = _serialize_for_search(model_instance)
    if doc:
        service = SearchService()
        service.index_document(model_name, doc)


def _delete_from_index(model_instance, model_name: str) -> None:
    """Remove a model instance from Meilisearch."""
    service = SearchService()
    service.delete_document(model_name, str(model_instance.id))


@shared_task
def index_contact(contact_id: str) -> None:
    from apps.contacts.models import Contact

    try:
        obj = Contact.objects.get(id=contact_id)
        _index_model(obj, "contact")
    except Contact.DoesNotExist:
        pass


@shared_task
def index_deal(deal_id: str) -> None:
    from apps.pipelines.models import Deal

    try:
        obj = Deal.objects.get(id=deal_id)
        _index_model(obj, "deal")
    except Deal.DoesNotExist:
        pass


@shared_task
def index_account(account_id: str) -> None:
    from apps.contacts.models import Account

    try:
        obj = Account.objects.get(id=account_id)
        _index_model(obj, "account")
    except Account.DoesNotExist:
        pass


@shared_task
def index_note(note_id: str) -> None:
    from apps.notes.models import Note

    try:
        obj = Note.objects.get(id=note_id)
        _index_model(obj, "note")
    except Note.DoesNotExist:
        pass


@shared_task
def remove_from_index(model_name: str, obj_id: str) -> None:
    service = SearchService()
    service.delete_document(model_name, obj_id)
