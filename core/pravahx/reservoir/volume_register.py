"""Volume from dam register data."""


def get_dam_volume(dam_id: str) -> float:
    """Retrieve reservoir volume from the dam register.

    Args:
        dam_id: The unique identifier for the dam in the register.

    Returns:
        The reservoir volume in cubic meters.

    Raises:
        NotImplementedError: Until the dam register database is connected.
    """
    # This will eventually query the data.dams module
    raise NotImplementedError("Dam register lookup not yet implemented.")
