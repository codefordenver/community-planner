import re
from typing import Any, Dict, Optional

import redis
import ujson
from django.conf import settings

from zerver.lib.utils import generate_random_token

# Redis accepts keys up to 512MB in size, but there's no reason for us to use such size,
# so we want to stay limited to 1024 characters.
MAX_KEY_LENGTH = 1024

class ZulipRedisError(Exception):
    pass

class ZulipRedisKeyTooLongError(ZulipRedisError):
    pass

class ZulipRedisKeyOfWrongFormatError(ZulipRedisError):
    pass

def get_redis_client() -> redis.StrictRedis:
    return redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT,
                             password=settings.REDIS_PASSWORD, db=0)

def put_dict_in_redis(redis_client: redis.StrictRedis, key_format: str,
                      data_to_store: Dict[str, Any],
                      expiration_seconds: int,
                      token_length: int=64,
                      token: Optional[str]=None) -> str:
    key_length = len(key_format) - len('{token}') + token_length
    if key_length > MAX_KEY_LENGTH:
        error_msg = "Requested key too long in put_dict_in_redis. Key format: %s, token length: %s"
        raise ZulipRedisKeyTooLongError(error_msg % (key_format, token_length))
    if token is None:
        token = generate_random_token(token_length)
    key = key_format.format(token=token)
    with redis_client.pipeline() as pipeline:
        pipeline.set(key, ujson.dumps(data_to_store))
        pipeline.expire(key, expiration_seconds)
        pipeline.execute()

    return key

def get_dict_from_redis(redis_client: redis.StrictRedis, key_format: str, key: str,
                        ) -> Optional[Dict[str, Any]]:
    # This function requires inputting the intended key_format to validate
    # that the key fits it, as an additionally security measure. This protects
    # against bugs where a caller requests a key based on user input and doesn't
    # validate it - which could potentially allow users to poke around arbitrary redis keys.
    if len(key) > MAX_KEY_LENGTH:
        error_msg = "Requested key too long in get_dict_from_redis: %s"
        raise ZulipRedisKeyTooLongError(error_msg % (key,))
    validate_key_fits_format(key, key_format)

    data = redis_client.get(key)
    if data is None:
        return None
    return ujson.loads(data)

def validate_key_fits_format(key: str, key_format: str) -> None:
    assert "{token}" in key_format
    regex = key_format.format(token=r"[a-zA-Z0-9]+")

    if not re.fullmatch(regex, key):
        raise ZulipRedisKeyOfWrongFormatError(f"{key} does not match format {key_format}")
