import sys
import ssl
import json
import platform

from enum import Enum

import asyncio
from asyncio import sleep

import logging
from logging import Logger

import websockets
from websockets import ClientConnection

from typing import Optional, Any, Dict, List, Tuple

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
error_logger: Logger = logging.getLogger(__name__)

class CloseCodes(Enum):
    UNKNOWN_ERROR = (4000, True)
    UNKNOWN_OPCODE = (4001, True)
    DECODE_ERROR = (4002, True)
    NOT_AUTHENTICATED = (4003, True)

    def __init__(self, code: int, reconnect: bool):
        self.code = code
        self.reconnect = reconnect

class HeartbeatConnectionError(Exception):
    def __init__(self, message: str, value: bool = False):
        super().__init__(message)
        self.value = value

class StatusCycler:
    def __init__(self, token: str) -> None:
        self.token = token
        self.gateway: str = "wss://gateway.discord.gg/?v=10&encoding=json"
        self.resume_url: Optional[str] = None
        self.session_id: Optional[str] = None
        self._websocket: Optional[ClientConnection] = None
        self.heartbeat_interval: Optional[int] = None
        self.sequence: Optional[int] = None

    async def connect(self) -> None:
        if self._websocket is None:
            self._websocket = await websockets.connect(self.gateway)


    async def initiate_cycler(self):
        if not self._websocket:
            error_logger.error('Websocket not connected')
            return
        hello_event: Any = json.loads(await self._websocket.recv())
        if hello_event['op'] != 10:
            error_logger.error(f'HELLO payload not received - opcode {hello_event['op']}')
            sys.exit(1)
        self.heartbeat_interval = hello_event['d']['heartbeat_interval']
    
    async def send_heartbeat(self) -> None:
        if not self._websocket:
            error_logger.error('Websocket not connected')
            return
        await self._websocket.send(json.dumps(
            {
                'op': 1,
                'd': self.sequence
            }
        ))

    async def heartbeat_ack(self, payload: Any) -> bool:
        if payload['op'] != 11:
            error_logger.error('Heartbeat ACK not received')
            return False
        return True
    
    async def heartbeat_cycle(self) -> None:
        running: bool = True
        while running:
            await sleep(self.heartbeat_interval / 1000) # type: ignore
            await self.send_heartbeat()
        
    async def send_identity(self) -> None:
        if not self._websocket:
            error_logger.error('Websocket not connected')
            return
        await self._websocket.send(json.dumps(
            {
                'op': 2,
                'd': {
                    'token': self.token,
                    'properties': {
                        'os': platform.system(),
                        'browser': 'discordPanel',
                        'device': 'discordPanel'
                    },
                    'intents': 0
                }
            }
        ))

    async def identify_payload(self, payload: Any):
        match payload['op']:
            case 0:
                event_type: str = payload['t']
                if event_type != 'READY':
                    error_logger.warning(f'Event received: {event_type}')
                    return
                self.resume_url = payload['d']['resume_gateway_url']
                self.session_id = payload['d']['session_id']
            case 10:
                self.heartbeat_interval = payload['d']['heartbeat_interval']
                asyncio.create_task(self.heartbeat_cycle())
                await self.send_identity()

    async def reconnect(self) -> None:


    '''async def cycle_statuses(self, websocket: ClientConnection):
        status_list: List[str] = [
            input("\nEnter the status you'd like to rotate:\n") for i in range(int(input("\nHow many statuses do you want to cycle through:\n")))
        ]
        status: int = 0
        while True:
            current_status = status_list[status]
            await self.update(websocket, current_status)
            status = (status + 1) % len(status_list)
            await sleep(25)'''


