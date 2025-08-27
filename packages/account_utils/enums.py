from enum import Enum, IntEnum

class CloseEventCode(Enum):
    '''relevant close events for personal account'''

    UNKNOWN_ERROR = (4000, True)
    UNKNOWN_OPCODE = (4001, True)
    DECODE_ERROR = (4002, True)
    NOT_AUTHENTICATED = (4003, True)
    FAILED_AUTHENTICATION = (4004, False)
    ALREADY_AUTHENTICATED = (4005, False)
    INVALID_SEQUENCE = (4007, True)
    RATE_LIMITED = (4008, True)
    SESSION_TIMEOUT = (4009, True)
    INVALID_API = (4012, False)
    INVALID_INTENT = (4013, False)

    def __init__(self, code: int, reconnect: bool):
        self.code = code
        self.reconnect = reconnect

class GatewayOpcode(IntEnum):
    '''relevant opcodes for personal account'''

    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    RESUME = 6
    RECONNECT = 7
    HELLO = 10
    HEARTBEAT_ACK = 11