import ulid


def get_uuid() -> str:
    """
    Generate a new UUID using ULID.
    """
    return ulid.new().uuid

