import os
import sys
import json
import asyncio
from asyncio import sleep

import logging
from logging import Logger

from typing import List, Dict, Tuple, Any
import websockets
from websockets import ClientConnection

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
error_logger: Logger = logging.getLogger(__name__)

class StatusCycler:
    '''
    -keep heartbeat going
    -have list of statuses
    -every interval, send opcode 3(update presence) w next status

    ->handle disconnects/reconnects automatically
    ->save last sequence # to resume instead of starting over
    ->rate limit handling   
    '''

    def __init__(self, token: str):
        self.token = token
        self.gateway: str = "wss://gateway.discord.gg/?v=10&encoding=json"

    async def connect(self) -> Tuple[ClientConnection, Any]:
        websocket: ClientConnection = await websockets.connect(self.gateway)
        ws_response: Any = json.loads(await websocket.recv())
        print("heartbeat response: ", ws_response)
        return websocket, ws_response
    
    async def identity(self, websocket: ClientConnection):
        payload: Dict[str, int | Dict[str, str | int | Dict[str, str]]] = {
            "op": 2,
            "d": {
                "token": self.token,
                "intents": 512,
                "properties": {
                    "$os": "discordPanel",
                    "$browser": "discordPanel",
                    "$device": "discordPanel"
                }
            }
        }
        await websocket.send(json.dumps(payload))

    async def heartbeat(self, websocket: ClientConnection, interval: int):
        while True:
            if(heartbeat_loop := await websocket.send(json.dumps(
                {
                    "op": 1,
                    "d": None
                }
            ))):
                sys.stdout.write("Heartbeat sent")
                await sleep(interval / 1000)

    async def update(websocket: ClientConnection, )

