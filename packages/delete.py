import random
import logging
from logging import Logger

import requests
from time import sleep
from requests import Response

from typing import Any, List

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
error_logger: Logger = logging.getLogger(__name__)

class MessageDeleter:
    
    def __init__(self, token: str, channel_id: str):
        self.token = token
        self.channel_id = channel_id
        self.base_endpoint: str = f"https://discord.com/api/v9/channels/{self.channel_id}/messages"
        self.rate_count: int = 0

    def exponential_backoff(self, retry_after: float, attempt: int) -> float:
        '''me when the CS lesson on time complexities comes in handy pray emoji
        exponential vs quadratic head ahh no srsly i actualy confused 2^n and n^2'''
        return (retry_after / 1000.0) * (2 ** attempt)

    def handle_ratelimit(self, response: Response) -> None:
        '''USING ELSE STATEMENTS ARENT A CRIME GUYS I DONT KNOW HOW ELSE TO DO IT THIS IMMEDIATE SECOND THX'''
        if response.ok:
            return
        if response.status_code == 429:
            self.rate_count += 1
            retry_header: Any = response.headers.get('retry-after')
           
            if self.rate_count == random.randrange(3, 6):
                sleep(self.exponential_backoff(int(retry_header), self.rate_count))
            else:
                sleep(int(retry_header))
            return
        error_logger.error(f'{response.status_code} - {response.reason}')

    def delete_messages(self) -> None:
        while True:
            get_response: Response = requests.get(
                url=self.base_endpoint,
                headers={"Authorization": self.token}
            ) #default is 50 remember that lock in
            self.handle_ratelimit(get_response)

            json_response: Any = get_response.json()
            if not json_response:
                print("All messages have been deleted\n")
                break
            
            message_ids: List[str] = [message['id'] for message in json_response]
            for id in message_ids:
                delete_request: Response = requests.delete(
                    url=f"{self.base_endpoint}/{id}",
                    headers={"Authorization": self.token}
                )
                self.handle_ratelimit(delete_request)
            