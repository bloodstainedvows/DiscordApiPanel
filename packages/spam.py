import random
import string

import logging
from logging import Logger

import requests
from requests import Response

from typing import Optional

from ratelimit_bypass import handle_ratelimit


logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
error_logger: Logger = logging.getLogger(__name__)

class MessageSpammer:

    def __init__(self, token: str, channel_id: str):
        self.token = token
        self.url: str = f"https://discord.com/api/v10/channels/{self.channel_id}/messages"
        self.channel_id = channel_id
        self.rate_count: int = 0
    
    def spam_message(self, message: Optional[str]) -> None:
        post_response: Response = requests.post(
            url=self.url,
            headers={"Authorization": self.token},
            json={"content": message if message else ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(random.randint(5, 15)))}
        )
        handle_ratelimit(post_response, self.rate_count)

