import string
import secrets

def generate_pin() -> str:
    """Generate a random 6-digit PIN."""
    return ''.join(secrets.choice(string.digits) for i in range(6))

def validate_pin(pin: str) -> bool:
    """Validate that the given PIN is a 6-digit string."""
    if not pin:
        return False
    return pin.isdigit() and len(pin) == 6
