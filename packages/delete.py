import logging
from logging import Logger

import requests
from enum import Enum
from time import sleep
from requests import Response

from typing import Union, Type, Optional, Any

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
error_logger: Logger = logging.getLogger(__name__)

"""dont know why i needed this since the requests module has built in status code attributes but its ok maybve i will use it later meow"""
class HttpCodes(Enum):
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    RATE_LIMIT = 429
    INTERNAL_SERVER_ERROR = 500

class MessageDeleter:

    token: str = ""

    @classmethod
    def set_token(cls: Type['MessageDeleter'], token: str):
        cls.token = token


    @classmethod
    def get_msg_batch(cls: Type['MessageDeleter'], channel_id: str) -> Optional[str]:
        message_response: Response = requests.get(
            url=f"https://discord.com/api/v9/channels/{channel_id}/messages",
            headers={"Authorization": cls.token}
        )
        if not message_response.ok:
            error_logger.warning(f"[{message_response.status_code}] - {message_response.reason}")
            return
        return message_response.json()[-1]['id']
