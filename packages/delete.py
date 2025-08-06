import random
import logging
from logging import Logger

import requests
from time import sleep
from requests import Response

from typing import Union, Type, Optional, Any, Tuple

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
error_logger: Logger = logging.getLogger(__name__)

class MessageDeleter:
    
    def __init__(self, token: str, channel_id: str):
        self.token = token
        self.channel_id = channel_id

    def exponential_backoff(self, retry_after: float, attempt: int) -> float:
        '''me when the CS lesson on time complexities comes in handy pray emoji
        exponential vs quadratic head ahh no srsly i actualy confused 2^n and n^2'''
        return (retry_after / 1000.0) * (2 ** attempt)

    def get_first_id(self) -> str:
        message_response: Response = requests.get(
            url=f"https://discord.com/api/v9/channels/{self.channel_id}/messages",
            headers={"Authorization": self.token}
        )
        return message_response.json()[0]['id']

    def delete_message(self) -> None:
        current_id = self.get_first_id()

        while True:
            delete_request: Response = requests.delete(
                url=f"https://discord.com/api/v9/channels/{self.channel_id}/messages/{current_id}",
                params={'before': current_id},
                headers={"Authorization": self.token}
            )
            if not delete_request.ok:
                error_count: int = 0
                if delete_request.status_code == 429:
                    wait_time: Any = delete_request.headers.get("retry-after")
                    error_logger.warning(f"Rate limit hit- waiting {wait_time} seconds")
                    error_count+= 1
                    if error_count == random.randrange(3, 6):
                        sleep(self.exponential_backoff(wait_time, error_count))
                    else:
                        sleep(wait_time)
                else:
                    error_logger.error(f"{delete_request.status_code} - {delete_request.reason.upper()}")






while True:
    message_response: Response = requests.get(
                url=f"https://discord.com/api/v9/channels/{self.channel_id}/messages",
                headers={"Authorization": self.token}
            )
    for message in message_response.json():
        requests.delete(
            url=f"https://discord.com/api/v9/channels/{self.channel_id}/messages/{message_response['id']}",
            headers={"Authorization": self.token}
        )