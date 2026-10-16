import os
import base64
import secrets
from Crypto.Cipher import AES

CURRENT_KEY_FILE = "enc.key"
OLD_KEY_FILE = "old_enc.key"


def load_key(key_file=CURRENT_KEY_FILE):
    """
    Load key from file.
    Key file contains a base64 encoded 32-byte key.
    """
    with open(key_file, "r") as f:
        return base64.b64decode(f.read().strip())


def save_key(key_bytes, key_file):
    with open(key_file, "w") as f:
        f.write(base64.b64encode(key_bytes).decode("utf-8"))


def key_rotation():
    """
    Move current enc.key to old_enc.key and create a new enc.key.
    """
    if os.path.exists(CURRENT_KEY_FILE):
        with open(CURRENT_KEY_FILE, "r") as src:
            current_key = src.read()

        with open(OLD_KEY_FILE, "w") as dst:
            dst.write(current_key)

    new_key = secrets.token_bytes(32)
    save_key(new_key, CURRENT_KEY_FILE)


def _decrypt_with_key(encoded_value, key):
    cipher = AES.new(key, AES.MODE_GCM)

    decoded = base64.b64decode(encoded_value)
    decrypted = cipher.decrypt(decoded)

    padding_length = decrypted[-1]

    if padding_length < 1 or padding_length > AES.block_size:
        raise ValueError("Invalid padding")

    if decrypted[-padding_length:] != bytes([padding_length]) * padding_length:
        raise ValueError("Invalid padding")

    return decrypted[:-padding_length].decode("utf-8")


def is_encrypted(value):
    if not isinstance(value, str) or not value:
        return False

    try:
        decoded = base64.b64decode(value, validate=True)

        if not decoded or len(decoded) % AES.block_size != 0:
            return False

        keys_to_try = []

        if os.path.exists(CURRENT_KEY_FILE):
            keys_to_try.append(load_key(CURRENT_KEY_FILE))

        if os.path.exists(OLD_KEY_FILE):
            keys_to_try.append(load_key(OLD_KEY_FILE))

        for key in keys_to_try:
            try:
                _decrypt_with_key(value, key)
                return True
            except Exception:
                pass

        return False

    except Exception:
        return False


def encrypt_decrypt_string(input_string, mode="encrypt"):
    if mode == "encrypt":
        key = load_key(CURRENT_KEY_FILE)

        cipher = AES.new(key, AES.MODE_GCM)

        padding_len = AES.block_size - (len(input_string.encode("utf-8")) % AES.block_size)

        padded = input_string + chr(padding_len) * padding_len

        encrypted = cipher.encrypt(padded.encode("utf-8"))

        return base64.b64encode(encrypted).decode("utf-8")

    elif mode == "decrypt":

        keys_to_try = []

        if os.path.exists(CURRENT_KEY_FILE):
            keys_to_try.append(load_key(CURRENT_KEY_FILE))

        if os.path.exists(OLD_KEY_FILE):
            keys_to_try.append(load_key(OLD_KEY_FILE))

        for key in keys_to_try:
            try:
                return _decrypt_with_key(input_string, key)
            except Exception:
                pass

        raise ValueError("Unable to decrypt with current or previous key")

    else:
        raise ValueError("Mode must be 'encrypt' or 'decrypt'")





if not os.path.exists(CURRENT_KEY_FILE):
    save_key(secrets.token_bytes(32), CURRENT_KEY_FILE)

encrypted = encrypt_decrypt_string("hello world", "encrypt")
print(f"Encrypted: {encrypted}")

print(f"Is Encrypted: {is_encrypted(encrypted)}")

decrypted = encrypt_decrypt_string(encrypted, "decrypt")
print(f"Decrypted: {decrypted}")

print(f"Is Decrypted Value Encrypted: {is_encrypted(decrypted)}")