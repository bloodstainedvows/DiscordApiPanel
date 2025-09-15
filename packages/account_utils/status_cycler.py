import logging
from logging import Logger

from .gateway import Gateway
from .enums import GatewayOpcode
from typing import Any, Optional, List, Dict

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
error_logger: Logger = logging.getLogger(__name__)

class StatusCycler:
    def __init__(self, token: str):
        self._token = token
        self.status_list: List[Dict[str, str]] = []
        self.current_index: int = 0

    def status_payload(self, status: str, emoji_id: Optional[str], emoji_name: Optional[str]) -> Any:
        status_payload: Any = {
            'op': GatewayOpcode.PRESENCE_UPDATE,
            'd': {
                'since': None,
                'activities': [
                    {
                        'type': 4,
                        'state': status,
                        'name': 'Custom Status',
                        'id': 'custom'
                    }
                ],
                'status': 'dnd',
                'afk': False
            }
        }
        
        if not emoji_name or not emoji_id:
            return status_payload
        status_payload['d']['activities'][0]['emoji'] = {}
        status_payload['d']['activities'][0]['emoji']['name'] = emoji_name
        status_payload['d']['activities'][0]['emoji']['id'] = emoji_id
        return status_payload
    
    async def next_status(self) -> Any:
        if not self.status_list:
            return
        
        current_status: Dict[str, str] = self.status_list[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.status_list)

        return self.status_payload(current_status['status'], current_status['emoji_id'], current_status['status_emoji'])

    async def setup(self) -> None:
        status_count: int = int(input('\nHow many statuses would you like to cycle through: '))
        for i in range(status_count):
            status_dict: Dict[str, str] = {'status': input('\nEnter status: ').strip()}

            if (status_emoji := input('\nEnter the emoji name associated with this status [NOTE: enter to skip]: ')):
                status_dict['emoji'] = status_emoji
            if (emoji_id := input('Enter the emoji id [NOTE: enter to skip]: ')):
                status_dict['emoji_id'] = emoji_id

            self.status_list.append(status_dict)

    async def cycle_statuses(self) -> None:
        '''blah blah blah'''
   

