import logging
from logging import Logger

from typing import Any, Optional
from .enums import GatewayOpcode

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
error_logger: Logger = logging.getLogger(__name__)

class StatusCycler:
    def __init__(self, token: str):
        self._token = token

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
    
    async def cycle_status(self) -> None:
        '''blahblah cycle'''