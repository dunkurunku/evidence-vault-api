import hashlib
from typing import BinaryIO

CHUNK = 1024 * 1024


def sha256_of_stream(stream: BinaryIO) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(CHUNK), b""):
        digest.update(chunk)
    stream.seek(0)
    return digest.hexdigest()
