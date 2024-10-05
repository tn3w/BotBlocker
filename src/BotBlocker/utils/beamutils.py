import secrets
import time
from typing import Final

try:
    from src.BotBlocker.utils.crypto.hashing import SHA256
    from src.BotBlocker.utils.fileutils import PICKLE
    from src.BotBlocker.utils.cons import REQUESTS_FILE_PATH
    from src.BotBlocker.utils.utils import generate_secure_random_string, Logger
except ImportError:
    try:
        from utils.fileutils import PICKLE
        from utils.cons import REQUESTS_FILE_PATH
        from utils.utils import generate_secure_random_string, Logger
        from utils.crypto.hashing import SHA256
    except ImportError:
        from utils import generate_secure_random_string, Logger
        from fileutils import PICKLE
        from cons import REQUESTS_FILE_PATH
        from crypto.hashing import SHA256


SHA256_BEAM: Final[SHA256] = SHA256(
    10000, hash_length = 11, salt_length = 0, serialization = "base62"
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
        if isinstance(information, str):
            identifiable_information_str += information

    beam_id = SHA256_BEAM.hash(identifiable_information_str)

    while len(beam_id) < 16:
        beam_id += "="

    return beam_id


def generate_random_beam_id() -> str:
    """
    Generate a random beam ID.

    Returns:
        str: A randomly generated beam ID, either 15 characters long 
             (with an '=' appended) or 16 characters long.
    """

    if secrets.choice([True, False]):
        return generate_secure_random_string(15, "a-zA-Z0-9") + "="

    return generate_secure_random_string(16, "a-zA-Z0-9")


class RequestLogger(Logger):
    """
    A class to log requests associated with specific beam IDs to a file.
    """


    def __init__(self, beam_id: str) -> None:
        """
        Initializes the RequestLogger with the specified file path.

        Args:
            beam_id (str): The unique identifier for being logged.

        Returns:
            None: Nothing.
        """

        self.beam_id = beam_id
        self.data = {}


    def _add(self, data: dict) -> None:
        """
        Adds a log entry for a specific beam ID.

        Args:
            data (dict): A dictionary containing the log data to be added.

        Returns:
            None: Nothing.
        """

        loaded_file_content = PICKLE.load(REQUESTS_FILE_PATH, default = {})
        if self.beam_id not in loaded_file_content:
            loaded_file_content[self.beam_id] = []

        if data in loaded_file_content[self.beam_id]:
            return

        loaded_file_content[self.beam_id].append(data)
        PICKLE.dump(REQUESTS_FILE_PATH, loaded_file_content, True)


    def log(self, **kwargs) -> None:
        """
        Logs an action taken on a specific beam ID.

        Args:
            **kwargs: Additional key-value pairs to include in the log entry. 
                       Keys will be truncated to the first two characters.

        Returns:
            None: Nothing.
        """

        kwargs = {key[:2]: value for key, value in kwargs.items()}

        if kwargs.get("en") is not True:
            self.data = kwargs
            return

        del kwargs["en"]

        data = {
            "ti": int(time.time())
        }
        data.update(self.data)
        data.update(kwargs)

        self._add(data)
