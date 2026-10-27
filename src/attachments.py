import base64

IMAGE_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
}
TEXT_TYPES = {"txt", "md", "csv", "json", "py"}
ALLOWED_TYPES = [*IMAGE_TYPES, "pdf", *TEXT_TYPES]
MAX_FILE_MB = 5


def file_extension(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def is_text_file(name: str) -> bool:
    return file_extension(name) in TEXT_TYPES


def read_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def to_content_block(name: str, data: bytes) -> dict:
    """Turn an uploaded file into a content block Claude can read."""
    ext = file_extension(name)

    if ext in IMAGE_TYPES:
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": IMAGE_TYPES[ext],
                "data": base64.standard_b64encode(data).decode("utf-8"),
            },
        }

    if ext == "pdf":
        return {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": base64.standard_b64encode(data).decode("utf-8"),
            },
            "title": name,
        }

    if ext in TEXT_TYPES:
        return {
            "type": "document",
            "source": {"type": "text", "media_type": "text/plain", "data": read_text(data)},
            "title": name,
        }

    raise ValueError(f"Unsupported file type: {name}")
