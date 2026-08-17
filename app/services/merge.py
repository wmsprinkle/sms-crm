import re


def render(body: str, contact) -> str:
    """Fill {{first_name}} and any CSV field into a message body."""
    data = {"first_name": contact.first_name or "there", **(contact.fields or {})}
    return re.sub(r"\{\{\s*(\w+)\s*\}\}",
                  lambda m: str(data.get(m.group(1), "")), body)
