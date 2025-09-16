import logging
from logging import Logger

import requests
from requests import Response

from typing import Any, List

from .ratelimit_bypass import handle_ratelimit

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
error_logger: Logger = logging.getLogger(__name__)

class MessageDeleter:
    
    def __init__(self, token: str, channel_id: str):
        self.token = token
        self.channel_id = channel_id
        self.base_endpoint: str = f"https://discord.com/api/v10/channels/{self.channel_id}/messages"
        self.rate_count: int = 0

        self.user_id: Any = requests.get(
            url=f"https://discord.com/api/v10/users/@me",
            headers={"Authorization": self.token}
        ).json()['id']
        
    def delete_messages(self) -> None:
        while True:
            get_response: Response = requests.get(
                url=self.base_endpoint,
                headers={"Authorization": self.token}
            ) #default is 50 remember that lock in
            self.rate_count = handle_ratelimit(get_response, self.rate_count)

            json_response: Any = get_response.json()
            if not json_response:
                print("All messages have been deleted\n")
                break
            
            user_msgs: List[str] = [message for message in json_response if message['author']['id'] == self.user_id]
            message_ids: List[str] = [message['id'] for message in user_msgs] # type: ignore

            for id in message_ids:
                delete_request: Response = requests.delete(
                    url=f"{self.base_endpoint}/{id}",
                    headers={"Authorization": self.token}
                )
                self.rate_count = handle_ratelimit(delete_request, self.rate_count)