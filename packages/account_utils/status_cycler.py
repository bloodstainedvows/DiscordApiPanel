import sys
import ssl
import json
import platform

from .enums import CloseEventCode, GatewayOpcode

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

    async def close_websocket(self) -> None:
        if self._websocket:
            await self._websocket.close()
            return
    
    async def send_heartbeat(self) -> None:
        if not self._websocket:
            error_logger.error('Websocket not connected')
            return
        await self._websocket.send(json.dumps(
            {
                'op': GatewayOpcode.HEARTBEAT,
                'd': self.sequence
            }
        ))

    async def heartbeat_ack(self, payload: Any) -> bool:
        if payload['op'] != GatewayOpcode.HELLO:
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
                'op': GatewayOpcode.IDENTIFY,
                'd': {
                    'token': self.token,
                    'properties': {
                        'os': platform.system(),
                        'browser': 'discordPanel',
                        'device': 'discordPanel'
                    },
                    'intents': 0
                }}))

    async def identify_payload(self, payload: Any):
        match payload['op']:
            case GatewayOpcode.DISPATCH:
                event_type: str = payload['t']
                if event_type != 'READY':
                    error_logger.warning(f'Event received: {event_type}')
                    return
                self.resume_url = payload['d']['resume_gateway_url']
                self.session_id = payload['d']['session_id']
            case GatewayOpcode.HELLO:
                self.heartbeat_interval = payload['d']['heartbeat_interval']
                asyncio.create_task(self.heartbeat_cycle())
                await self.send_identity()

    async def code_true(self, code: int) -> bool:

        close_event: Optional[CloseEventCode] = None

        for close_code in CloseEventCode:
            if close_code.code == code:
                close_event = close_code
                break

        if not close_event:
            error_logger.error('Closed code not identified')
            return False
        
        if not close_event.reconnect:
            error_logger.warning('reconnection unavailable')
            return False
        
        await self.reconnect()
    
    async def reconnect(self):
        if not self.resume_url:
            error_logger.error('No valid resume gateway')
            return
        self._websocket = await websockets.connect(uri=self.resume_url, ssl=True)
        await self._websocket.send(json.dumps(
            {
                'op': GatewayOpcode.RESUME,
                'd': {
                    'token': self.token,
                    'session_id': self.session_id,
                    'seq': self.sequence
                }
            }
        ))
