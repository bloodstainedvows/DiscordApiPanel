import json
import platform

import logging
from logging import Logger

import asyncio
from asyncio import sleep
from typing import Optional, Any

import websockets
from websockets import ClientConnection

from .enums import CloseEventCode, GatewayOpcode, ConnectionResult

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
error_logger: Logger = logging.getLogger(__name__)

class StatusCycler:
    def __init__(self, token: str) -> None:
        self.token = token
        self.gateway: str = "wss://gateway.discord.gg/?v=10&encoding=json"
        self.resume_url: Optional[str] = None
        self.session_id: Optional[str] = None
        self._websocket: Optional[ClientConnection] = None
        self.heartbeat_interval: Optional[int] = None
        self.heartbeat_acknowledged: bool = True  # Start as True
        self.sequence: Optional[int] = None

    async def start_connection(self) -> None:
        match await self.connect(): 
            case ConnectionResult.ALREADY_CONNECTED:
                error_logger.warning('Connection already established')
            case ConnectionResult.SUCCESS:
                response_payload: Any = json.loads(await self._websocket.recv()) # type: ignore
                if response_payload['op'] != GatewayOpcode.HELLO:
                    error_logger.error('Hello event not received - terminating')
                    return
                self.heartbeat_interval = response_payload['d']['heartbeat_interval']
                asyncio.create_task(self.heartbeat_cycle())

                if not await self.send_identity():
                    return
                await self.main_loop()
            case ConnectionResult.RETRY:
                await sleep(5)
                await self.start_connection()
            case ConnectionResult.TERMINATE:
                return

    async def connect(self) -> ConnectionResult:
        if self._websocket is not None:
            return ConnectionResult.ALREADY_CONNECTED
        try:
            self._websocket = await websockets.connect(self.gateway, ssl=True)
            return ConnectionResult.SUCCESS
        except websockets.exceptions.ConnectionClosedError as e:
            error_logger.warning(f'Connection closed: {e}\n Retrying..')
            return ConnectionResult.RETRY
        except ConnectionRefusedError:
            error_logger.error('Connection refused, exiting..')
            return ConnectionResult.TERMINATE

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

    async def heartbeat_cycle(self) -> None:
        running: bool = True
        while running:
            await sleep(self.heartbeat_interval / 1000) # type: ignore
            
            if not self.heartbeat_acknowledged:
                error_logger.error('Heartbeat not acknowledged, closing connection')
                running = False
                await self.close_websocket()
                break
                
            self.heartbeat_acknowledged = False
            await self.send_heartbeat()
        
    async def send_identity(self) -> bool:
        if not self._websocket:
            error_logger.error('Websocket not connected')
            return False
        try:
            await self._websocket.send(json.dumps({
                'op': GatewayOpcode.IDENTIFY,
                'd': {
                    'token': self.token,
                    'properties': {
                        'os': platform.system(),
                        'browser': 'discordPanel',
                        'device': 'discordPanel'
                    },
                    'intents': 0
                }
            }))
            return True
        except:
            error_logger.error('Identity payload couldnt be sent')
            return False

    async def handle_payload(self, payload: Any):
        match payload['op']:
            case GatewayOpcode.DISPATCH:
                event: str = payload['t']
                if event == 'READY':
                    self.resume_url = payload['d']['resume_gateway_url']
                    self.session_id = payload['d']['session_id']
                    error_logger.info('Ready event received')
                else:
                    error_logger.info(f'Event received: {event}')
            
            case GatewayOpcode.HEARTBEAT:
                await self.send_heartbeat()

            case GatewayOpcode.HEARTBEAT_ACK:
                self.heartbeat_acknowledged = True

            case GatewayOpcode.INVALID_SESSION:
                error_logger.warning('Invalid session occured, initiating reconnect')
                await self.reconnect()
            
            case GatewayOpcode.RECONNECT:
                await self.reconnect()
            
            case _:
                error_logger.warning(f'Unrecognized opcode: {payload["op"]}')

        if 's' in payload and payload['s'] is not None:
            self.sequence = payload['s']

    async def main_loop(self):
        while True:
            try:
                message = await self._websocket.recv() # type: ignore
                payload = json.loads(message)
                await self.handle_payload(payload)
            except websockets.exceptions.ConnectionClosed as e:
                if not await self.code_true(e.code):
                    break

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
        return True
    
    async def reconnect(self) -> bool:
        if not self.resume_url:
            error_logger.error('No valid resume gateway')
            return False
            
        try:
            self._websocket = await websockets.connect(uri=self.resume_url, ssl=True)
            await self._websocket.send(json.dumps({
                'op': GatewayOpcode.RESUME,
                'd': {
                    'token': self.token,
                    'session_id': self.session_id,
                    'seq': self.sequence
                }
            }))
            
            response = json.loads(await self._websocket.recv())
            if response['op'] == GatewayOpcode.INVALID_SESSION:
                error_logger.warning('Invalid session received - starting new session')
                self._websocket = await websockets.connect(uri=self.gateway, ssl=True)
                
                hello_payload = json.loads(await self._websocket.recv())
                if hello_payload['op'] == GatewayOpcode.HELLO:
                    self.heartbeat_interval = hello_payload['d']['heartbeat_interval']
                    asyncio.create_task(self.heartbeat_cycle())
                
                if not await self.send_identity():
                    await self.close_websocket()
                    error_logger.error('Failed reconnection')
                    return False
            return True
            
        except Exception as e:
            error_logger.error(f'Reconnection failed: {e}')
            return False

    async def update_presence(self, status: str, emoji_name: Optional[str], emoji_id: Optional[str]) -> None:
        if not self._websocket:
            error_logger.error('Websocket not connected')
            return
            
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
        
        '''if emoji_name or emoji_id:
            status_payload['d']['activities'][0]['emoji'] = {}
            if emoji_name:
                status_payload['d']['activities'][0]['emoji']['name'] = emoji_name
            if emoji_id:
                status_payload['d']['activities'][0]['emoji']['id'] = emoji_id
        
        await self._websocket.send(json.dumps(status_payload))'''