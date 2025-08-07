
import os
import sys
import logging
from logging import Logger

from typing import Optional

from packages import MessageDeleter
from dotenv import load_dotenv

load_dotenv(verbose=True)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
    )
error_logger: Logger = logging.getLogger(__name__)


def main():
    auth_token: Optional[str] = os.getenv("TOKEN")
    if not auth_token:
        error_logger.error("[!] Token cannot be found\n[!] Please ensure to create a .env in the discordApiPanel folder with the format:\n\t'TOKEN'=YOUR TOKEN")
        sys.exit(1)
    channel_id: str = input("Please enter the channel ID of the dms you'd like to wipe:\n")
    if not channel_id:
        error_logger.error('Channel ID cannot be empty')
        sys.exit(1)
    print("Starting deletion..\n")
    deleter: MessageDeleter = MessageDeleter(auth_token, "1398892808911458314")
    deleter.delete_messages()


if __name__ == "__main__":
    main()