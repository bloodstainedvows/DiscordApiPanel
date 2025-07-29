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
        error_logger.error("Token cannot be found")
        sys.exit(1)
                    
if __name__ == "__main__":
    main()