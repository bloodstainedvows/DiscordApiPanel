import random
from time import sleep
from typing import Any
from requests import Response

import logging
from logging import Logger

error_logger: Logger = logging.getLogger(__name__)

def exponential_backoff(retry_after: float, attempt: int) -> float:
        return (retry_after / 1000.0) * (2 ** attempt)

def handle_ratelimit(response: Response, rate_count: int) -> None:
    if response.ok:
        sleep(1)
        return
    if response.status_code == 429:
        rate_count += 1
        retry_header: Any = response.headers.get('retry-after')
        
        if rate_count == random.randrange(3, 5):
            sleep(exponential_backoff(float(retry_header), rate_count))
        else:
            sleep(float(retry_header))
        return
    error_logger.error(f'{response.status_code} - {response.reason}')