import sys
import ssl
import json
import platform
from asyncio import sleep

import logging
from logging import Logger

import websockets
from websockets import ClientConnection

from typing import Optional, Any, Dict, List

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
error_logger: Logger = logging.getLogger(__name__)

class StatusCycler:
    def __init__(self, token: str) -> None:
        self.token = token
        self.gateway: str = "wss://gateway.discord.gg/?v=10&encoding=json"
        self.heartbeat_interval: Optional[int] = None
        self.sequence: Optional[int] = None

    async def initiate_cycler(self):
        async with websockets.connect(self.gateway, ssl=True) as websocket:
            hello_event: Any = json.loads(await websocket.recv())
            if hello_event['op'] != 10:
                error_logger.error(f'HELLO payload not received - opcode {hello_event['op']}')
                sys.exit(1)
            self.heartbeat_interval = hello_event['d']['heartbeat_interval']
            await websocket.send(json.dumps(
                {
                    'op': 2,
                    'd': {
                        'token': self.token,
                        'properties': {
                            'os': platform.system(),
                            'browser': 'discordPanel',
                            'device': 'discordPanel'
                        }
                        'intents': 0
                    }
                }
            ))
    
    async def send_heartbeat(self, websocket: ClientConnection):
        await websocket.send(json.dumps(
            {
                'op': 1,
                'd': self.sequence
            }
        ))
        await sleep(self.heartbeat_interval / 1000) # type: ignore

    async def cycle_statuses(self, websocket: ClientConnection):
        status_list: List[str] = [
            input("\nEnter the status you'd like to rotate:\n") for i in range(int(input("\nHow many statuses do you want to cycle through:\n")))
        ]
        status: int = 0
        while True:
            current_status = status_list[status]
            await self.update(websocket, current_status)
            status = (status + 1) % len(status_list)
            await sleep(25)


