import hashlib
from pathlib import Path


def calculate_content_hash(file_path):
    file_path = Path(file_path)
    hasher = hashlib.sha256()

    with file_path.open(mode="rb") as file:
        while chunk := file.read(1024 * 1024):
            hasher.update(chunk)

    return hasher.hexdigest()