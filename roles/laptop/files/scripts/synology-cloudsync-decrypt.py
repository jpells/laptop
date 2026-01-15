#!/usr/bin/env -S uv run --script
"""Synology CloudSync Decryption script."""

# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "pycryptodome>=3.23.0",
#     "lz4>=4.4.5",
# ]
# ///

import base64
import hashlib
import io
from collections import OrderedDict
from pathlib import Path
from typing import BinaryIO

import lz4.frame
from Crypto.Cipher import AES

# CloudSync file format constants
MAGIC = b"__CLOUDSYNC_ENC__"

# TLV (Type-Length-Value) header bytes
TLV_DICT_START = 0x42
TLV_DICT_END = 0x40
TLV_STRING = 0x10
TLV_BYTES = 0x11
TLV_INT = 0x01

# AES constants
AES_BLOCK_SIZE = 16

# CLI constants
EXPECTED_ARGC = 4

type TLVObject = None | OrderedDict[str | bytes | int, "TLVObject"] | str | bytes | int


def read_object(f: BinaryIO) -> TLVObject:
    """Read a TLV-encoded object from the file stream."""
    s = f.read(1)
    if len(s) == 0:
        return None
    header_byte = s[0]

    if header_byte == TLV_DICT_START:
        return read_dict(f)
    if header_byte == TLV_DICT_END:
        return None
    if header_byte == TLV_STRING:
        length = int.from_bytes(f.read(2), "big")
        return f.read(length).decode("utf-8")
    if header_byte == TLV_BYTES:
        length = int.from_bytes(f.read(2), "big")
        return f.read(length)
    if header_byte == TLV_INT:
        length = f.read(1)[0]
        return int.from_bytes(f.read(length), "big")
    msg = f"Unknown type byte: 0x{header_byte:02X}"
    raise ValueError(msg)


def read_dict(f: BinaryIO) -> OrderedDict[str | bytes | int, TLVObject]:
    """Read a dictionary from the file stream."""
    result: OrderedDict[str | bytes | int, TLVObject] = OrderedDict()
    while True:
        key = read_object(f)
        if key is None:
            break
        # Keys cannot be dicts or None in our protocol
        if isinstance(key, OrderedDict):
            msg = "Dictionary keys cannot be dictionaries"
            raise TypeError(msg)
        value = read_object(f)
        result[key] = value
    return result


def openssl_kdf(
    password: bytes,
    salt: bytes,
    key_size: int = 32,
    iv_size: int = 16,
) -> tuple[bytes, bytes]:
    """OpenSSL EVP_BytesToKey key derivation function.

    Uses 1000 iterations when salt is present, 1 iteration otherwise.
    """
    count = 1 if salt == b"" else 1000
    result = b""
    prev = b""

    while len(result) < key_size + iv_size:
        temp = prev + password + salt
        for _ in range(count):
            temp = hashlib.md5(temp, usedforsecurity=False).digest()
        prev = temp
        result += temp

    return result[:key_size], result[key_size : key_size + iv_size]


def strip_pkcs7_padding(data: bytes) -> bytes:
    """Remove PKCS7 padding from decrypted data."""
    if len(data) == 0:
        msg = "Empty data"
        raise ValueError(msg)
    if len(data) % AES_BLOCK_SIZE != 0:
        msg = "Data not 16-byte aligned"
        raise ValueError(msg)

    pad_len = data[-1]
    if pad_len == 0 or pad_len > AES_BLOCK_SIZE:
        msg = f"Invalid padding length: {pad_len}"
        raise ValueError(msg)

    # Verify all padding bytes
    for i in range(1, pad_len + 1):
        if data[-i] != pad_len:
            msg = "Invalid PKCS7 padding"
            raise ValueError(msg)

    return data[:-pad_len]


def decrypt_with_password(ciphertext: bytes, password: bytes, salt: bytes) -> bytes:
    """Decrypt data using password and salt with OpenSSL KDF."""
    key, iv = openssl_kdf(password, salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ciphertext)
    return strip_pkcs7_padding(plaintext)


class _ParsedMetadata:
    """Container for parsed CloudSync metadata."""

    __slots__ = ("compress", "enc_key1", "encrypted_chunks", "file_md5_hash", "salt")

    def __init__(self) -> None:
        self.enc_key1: str | None = None
        self.salt: bytes | None = None
        self.compress: int = 0
        self.file_md5_hash: str | None = None
        self.encrypted_chunks: list[bytes] = []


def _extract_salt(obj: OrderedDict[str | bytes | int, TLVObject]) -> bytes:
    """Extract and validate salt from metadata object."""
    salt_value = obj.get("salt")
    if isinstance(salt_value, str):
        return salt_value.encode("latin-1")
    if isinstance(salt_value, bytes):
        return salt_value
    msg = "salt must be str or bytes"
    raise TypeError(msg)


def _process_metadata_object(
    obj: OrderedDict[str | bytes | int, TLVObject],
    metadata: _ParsedMetadata,
) -> None:
    """Process a metadata object and update the metadata container."""
    if "enc_key1" in obj:
        enc_key1_value = obj.get("enc_key1")
        if not isinstance(enc_key1_value, str):
            msg = "enc_key1 must be a string"
            raise TypeError(msg)
        metadata.enc_key1 = enc_key1_value

    if "salt" in obj:
        metadata.salt = _extract_salt(obj)

    if "compress" in obj:
        compress_value = obj.get("compress", 0)
        if not isinstance(compress_value, int):
            msg = "compress must be an integer"
            raise TypeError(msg)
        metadata.compress = compress_value

    if "file_md5" in obj:
        file_md5_value = obj.get("file_md5")
        if not isinstance(file_md5_value, str):
            msg = "file_md5 must be a string"
            raise TypeError(msg)
        metadata.file_md5_hash = file_md5_value


def _process_data_object(
    obj: OrderedDict[str | bytes | int, TLVObject],
    metadata: _ParsedMetadata,
) -> None:
    """Process a data object and append chunk to metadata container."""
    chunk = obj.get("data")
    if chunk:
        if not isinstance(chunk, bytes):
            msg = "data chunk must be bytes"
            raise TypeError(msg)
        metadata.encrypted_chunks.append(chunk)


def _parse_cloudsync_stream(stream: io.BytesIO) -> _ParsedMetadata:
    """Parse CloudSync data stream and extract metadata and encrypted chunks."""
    metadata = _ParsedMetadata()

    while True:
        obj = read_object(stream)
        if obj is None:
            break

        if isinstance(obj, dict):
            obj_type = obj.get("type")
            if obj_type == "metadata":
                _process_metadata_object(obj, metadata)
            elif obj_type == "data":
                _process_data_object(obj, metadata)

    return metadata


def _decrypt_session_key(enc_key1: str, password: str, salt: bytes) -> bytes:
    """Decrypt the encrypted key to get the session key."""
    enc_key1_bytes = base64.b64decode(enc_key1)
    session_key = decrypt_with_password(enc_key1_bytes, password.encode(), salt)

    # The session key is a hex string, convert to bytes
    if all(c in b"0123456789abcdefABCDEF" for c in session_key):
        session_key = bytes.fromhex(session_key.decode("ascii"))

    return session_key


def _decrypt_chunks(encrypted_chunks: list[bytes], session_key: bytes) -> bytes:
    """Decrypt all data chunks with the session key."""
    decrypted_data = b""
    for chunk in encrypted_chunks:
        key, iv = openssl_kdf(session_key, b"")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_chunk = strip_pkcs7_padding(cipher.decrypt(chunk))
        decrypted_data += decrypted_chunk
    return decrypted_data


def _verify_md5(data: bytes, expected_hash: str | None) -> None:
    """Verify MD5 hash of decrypted data if hash is provided."""
    if expected_hash:
        actual_md5 = hashlib.md5(data, usedforsecurity=False).hexdigest()
        if actual_md5 != expected_hash:
            msg = f"MD5 mismatch: expected {expected_hash}, got {actual_md5}"
            raise ValueError(msg)


def decrypt_cloudsync(encrypted_path: str, password: str, output_path: str) -> None:
    """Decrypt a Synology CloudSync encrypted file."""
    data = Path(encrypted_path).read_bytes()

    # Verify magic header
    if not data.startswith(MAGIC):
        msg = "Not a CloudSync encrypted file"
        raise ValueError(msg)

    # Skip magic (17 bytes) + MD5 hash (32 bytes)
    stream = io.BytesIO(data[49:])
    metadata = _parse_cloudsync_stream(stream)

    if metadata.enc_key1 is None or metadata.salt is None:
        msg = "Missing encryption metadata (enc_key1 or salt)"
        raise ValueError(msg)

    # Stage 1: Decrypt enc_key1 to get session key
    session_key = _decrypt_session_key(metadata.enc_key1, password, metadata.salt)

    # Stage 2: Decrypt data chunks
    decrypted_data = _decrypt_chunks(metadata.encrypted_chunks, session_key)

    # Decompress if needed (LZ4 frame format)
    if metadata.compress:
        decrypted_data = lz4.frame.decompress(decrypted_data)

    # Verify and write output
    _verify_md5(decrypted_data, metadata.file_md5_hash)
    Path(output_path).write_bytes(decrypted_data)
    print(f"Decryption successful! Output: {output_path}")  # noqa: T201


if __name__ == "__main__":
    import sys

    if len(sys.argv) != EXPECTED_ARGC:
        print(  # noqa: T201
            "Usage: synology-cloudsync-decrypt <encrypted_file> <password> <output>",
        )
        print("\nDecrypt Synology CloudSync encrypted files.")  # noqa: T201
        print("\nExample:")  # noqa: T201
        print("  synology-cloudsync-decrypt encrypted.txt mypassword decrypted.txt")  # noqa: T201
        sys.exit(1)

    decrypt_cloudsync(sys.argv[1], sys.argv[2], sys.argv[3])
