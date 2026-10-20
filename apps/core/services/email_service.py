import datetime
from apps.core.models import SharedInbox
from typing import Optional

def get_inbox_by_pin(pin: str) -> Optional[SharedInbox]:
    """Retrieve the shared inbox by its unique PIN."""
    try:
        return SharedInbox.objects.get(pin=pin)
    except SharedInbox.DoesNotExist:
        return None

def check_expiry(inbox: SharedInbox) -> bool:
    """Check if the inbox link has expired using pure Date fields."""
    if not inbox.expiry:
        return False
    return datetime.date.today() > inbox.expiry
