import hashlib
import io

from app.services.hashing import sha256_of_stream


def test_sha256_matches_hashlib_and_rewinds_stream():
    data = b"x" * (3 * 1024 * 1024 + 7)  # más de un bloque
    stream = io.BytesIO(data)
    assert sha256_of_stream(stream) == hashlib.sha256(data).hexdigest()
    assert stream.tell() == 0
