from typing import Final

try:
    from src.BotBlocker.utils.crypto.hashing import SHA256
except ImportError:
    try:
        from utils.crypto.hashing import SHA256
    except ImportError:
        from crypto.hashing import SHA256


SHA256_BEAM: Final[SHA256] = SHA256(
    1000, hash_length = 11, salt_length = 0, serialization = "base62"
)


def get_beam_id(identifiable_information: list) -> str:
    """
    Generate a Beam ID from a list of identifiable information.

    Args:
        identifiable_information (list): A list of strings containing identifiable
                                          information that will be concatenated and hashed.

    Returns:
        str: A Beam ID that is 16 characters long, padded with "=" if necessary.
    """

    identifiable_information_str = ""
    for information in identifiable_information:
        if isinstance(identifiable_information, str):
            identifiable_information_str += information

    beam_id = SHA256_BEAM.hash(identifiable_information_str)

    while len(beam_id) < 16:
        beam_id += "="

    return beam_id
