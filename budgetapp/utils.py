import uuid


def generate_uuid_hex():
    """
    Generate a hexadecimal UUID.

    Returns:
        str: A string representing the hexadecimal UUID.
    """
    return uuid.uuid4().hex


def money_db_prep(value):
    return int(float(value) * 1000)
