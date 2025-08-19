import os
import sys
import logging
from logging import Logger

from typing import Optional

from packages import *
from dotenv import load_dotenv

load_dotenv(verbose=True)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
    )
error_logger: Logger = logging.getLogger(__name__)

def valid_channel(channel_id: str) -> bool:
    if not channel_id:
        error_logger.error('Channel ID cannot be empty')
        return False
    return True

def setup_deleter(token: str) -> None:
    channel_id: str = input("\nPlease enter the channel ID of the dms you'd like to wipe:\n")
    if not valid_channel(channel_id):
        return
    deleter: MessageDeleter = MessageDeleter(token, channel_id)
    deleter.delete_messages()

def setup_spammer(token: str) -> None:
    channel_id: str = input("Please enter the channel ID of the dms you'd like to spam:\n")
    if not valid_channel(channel_id):
        return
    spammer: MessageSpammer = MessageSpammer(token, channel_id)
    spammer.spam_message(input("\nWhat would you like to spam:\n"))


def main():
    auth_token: Optional[str] = os.getenv("TOKEN")
    if not auth_token:
        error_logger.error("[!] Token cannot be found\n[!] Please ensure to create a .env in the discordApiPanel folder with the format:\n\t'TOKEN'=YOUR TOKEN")
        sys.exit(1)


if __name__ == "__main__":
    main()